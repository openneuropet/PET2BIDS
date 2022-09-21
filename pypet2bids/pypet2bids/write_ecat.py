"""
This program will create an ecat file if provided an ecat schema and a dictionary of values to populate that schema
with.

First this program collects the same schemas that read_ecat.py does, from read_ecat import ecat_header_maps.
Next this program selects one of the header maps as speficified by some input e.g. if given: ecat7.3 it would 
select the standard image matrix at: ecat_header_maps['ecat_headers']['73']['mainheader'] 
and the subheader map at: ecat_header_maps['ecat_headers']['73']['11'] or whatever number is corresponding to 
the type of ecat header you wish to write. Perhaps these should belong in a reverse sort of dictionary going to
need to create the directory byte block(s) for an ecat. Basically, reverse the process of reading the 
directory in lines 227 through 257 in ecat_read. 
    
    determine the number of frames in the image/pixel data
    create empty table(s) of dtype >i4 dimensions of 4 rows by 64 columns 
    fill empty tables w/ zeros
    place the number 2 in the second row, first column of the table if it's the only directory table or the last 
    directory
    table.
    final output should be a bytes: 1024 type object.
    
After generating the table you should then be able to write the main header, write the directory table,
then write each subheader and corresponding pixel data


:Author: Anthony Galassi

:Copyright: Open NeuroPET team
"""

import struct
from math import ceil, floor
from pypet2bids.read_ecat import  ecat_header_maps, get_buffer_size
import numpy
from pathlib import Path

def write_header(ecat_file, schema: dict, values: dict = {}, byte_position: int = 0, seek: bool = False):
    """
    Given a filepath and a schema this function will write an ecat header to a file. If supplied a dictionary of values
    it will populate the written header with them, if not it will fill the header with empty values. If a byte position
    argument is supplied write_header will write to the byte position in the file supplied at file path, else it will
    seek to the end of the file and write there.
    :param ecat_file: the ecat file to be written
    :param schema: dictionary schema of the ecat header
    :param values: dictionary of values corresponding to the 'variable_name' entries in the schema dictionary
    :param byte_position: offset to write the header at, default is at the zero'th byte position.
    :param seek: if True use the provided byte position argument else, collect byte position form opened ecat_file
    :return: the end byte position, spoilers this will be 512 bytes offset from byte_position if that argument is
    supplied.
    """

    if not seek:
        byte_position = ecat_file.tell()

    for entry in schema:
        byte_position, variable_name, struct_fmt = entry['byte'], entry['variable_name'], entry[
            'struct']
        struct_fmt = '>' + struct_fmt
        byte_width = struct.calcsize(struct_fmt)
        value_to_write = values.get(variable_name, None)

        # if no value is supplied in the value dict, pack with empty bytes as well
        if not value_to_write:
            pack_empty = True
        # set variable to false if neither of these conditions is met
        else:
            pack_empty = False

        # for fill or empty values supplied in the values dictionary
        if pack_empty:
            fill = byte_width * 'x'
            ecat_file.write(struct.pack(fill))
        elif 's' in struct_fmt:
            value_to_write = bytes(value_to_write, 'ascii')
            ecat_file.write(struct.pack(struct_fmt, value_to_write))
        # for all other cases
        else:
            if type(value_to_write) is tuple and len(value_to_write) > 1:
                value_to_write = list(value_to_write)
            elif type(value_to_write) is not list:
                value_to_write = [value_to_write]
            try:
                ecat_file.write(struct.pack(struct_fmt, *value_to_write))
            except struct.error as err:
                if values['DATA_TYPE'] == 5 and 'MAX' in variable_name:
                    value_to_write = 32767
                elif values['DATA_TYPE'] == 5 and 'MIN' in variable_name:
                    value_to_write = -32767
                    print('Uncertain how to handle min and max datatypes for float arrays when writing ecats.\n'
                          'if you know more about what header min and max values should be in the case of an float32\n'
                          'image matrix please consider making a pull request to this library or posting an issue.')
                else:
                    print(f"Oh no {value_to_write} is out of range for {struct_fmt}, variable {variable_name}")
                    raise err
    return byte_width + byte_position


def create_directory_table(num_frames: int = 0, pixel_dimensions: dict = {}, pixel_byte_size: int = 2):
    """
    Creates directory tables for an ecat file when provided with the number of frames, the total number of pixels
    per frame, and the byte size of each of those pixels. Ecat's can have int16 (2 byte widths) or float 32 (4 byte
    widths) pixel values. This table will then be used to look up each subheader and it's corresponding pixel data
    after it is written.
    :param num_frames: number of frames taken during the ecat scan, a.k.a. time dimension
    :param pixel_dimensions: a dictionary such as {'x': 2, 'y': 2, 'z': 2}, the relevant information is contained within
    the values, not the keys. However, those keys may be important w/ cylindrical ecat files, at this point it is
    undetermined.
    :param pixel_byte_size: the width of each pixel's value in bytes.
    :return: a list containing 2 dimensional directory tables populated w/ elements corresponding to the byte position
    of the frame info of the ECAT.
    """
    # first determine the number of byte blocks the directory table(s) require based on the
    # number of frames
    required_directory_blocks = ceil(num_frames / 31)

    # determine the width of the frame byte blocks with the pixel dimensions and data sizes
    pixel_volume = numpy.product([*pixel_dimensions.values()])

    # still not sure what some of these numbers mean, but we populate the first column of the byte array with them
    directory_tables = []

    # create entries for the directory table
    directory_order = [i + 1 for i in range(num_frames)]

    # why is the initial table byte position equal to 3? Because the first header and pixel data lies
    # after the main header byte block at position 0 to 1 and the directory table itself occupies byte blocks
    # 1 to 2, thus the first frame (header and pixel data) will land at byte block number 3! Whoopee!
    table_byte_position = 3 #1 + required_directory_blocks
    for i in range(required_directory_blocks):
        # initialize empty 4 x 32 array
        table = numpy.ndarray((4, 32), dtype='>i4')

        # populate first column of table with codes and undetermined codes
        # note these table values are only extrapolated from a data set w/ 45 frames and datasets with less than
        # 31 frames. Behavior or values for frames numbering above 45 (or more specifically 62) is unknown.
        if i == (required_directory_blocks - 1):
            frames_to_iterate = num_frames % 31
            table[0, 0] = 31 - frames_to_iterate # number of un-used columns in the directory table
            table[1, 0] = 2  # stop value
            table[2, 0] = 2  # stop value
            table[3, 0] = frames_to_iterate  # number of frames referenced in this table
        else:
            frames_to_iterate = floor(num_frames / 31) * 31
            table[0, 0] = 0
            table[1, 0] = 0  # note this is just a placeholder the real value is entered after the final position of the
            # last entry in the first directory is calculated
            table[2, 0] = 0
            table[3, 0] = frames_to_iterate

        for column in range(frames_to_iterate):
            if column != 0:
                table_byte_position += 1
            elif column == 0 and i == 1:
                table_byte_position += 2
            table[0, column + 1] = directory_order.pop(0)
            table[1, column + 1] = table_byte_position
            # frame byte position is shifted
            table_byte_position = int((pixel_byte_size * pixel_volume) / 512 + table_byte_position)
            table[2, column + 1] = table_byte_position
            table[3, column + 1] = 1

        # VERY IMPORTANT
        if i != (required_directory_blocks - 1):
            table[1, 0] = table[2, column + 1] + 1

        directory_tables.append(table)

    return directory_tables


def write_directory_table(file, directory_tables: list, seek: bool = False):
    """
    Given a list of numpy.ndarray tables and a file path, this function flattens the directory tables to be written
    into the filepath as bytes strings, then writes the bytes strings to the end of the file, returning the byte position
    it left off on.
    :param file: an ecat file that has been initialized with it's main header information
    :param directory_tables: a list of directory tables (1 to 2) that are 4x32 in dimensions and of dtype int32.
    :param seek: seek to directory table position at 512 bytes, defaults to writing at current position of
    file read head.
    :return: The byte position after writing
    """
    # flatten the lists into byte strings

    for n, table in enumerate(directory_tables):
        # first table lies directly after the main header byte block, which is 512 bytes from the start of the file

        if n == 0:
            if seek:
                file.seek(512)
            else:
                pass
        # additional directory table positions are recorded in the previous directory table in row 1 column 0
        else:
            next_table_position = directory_tables[n - 1][1, 0] - 1
            file.seek(512 * next_table_position)
        transpose_table = numpy.transpose(table)
        flattened_transpose = numpy.reshape(transpose_table, (4, -1)).flatten()

        for index in range(flattened_transpose.size):
            file.write(struct.pack('>l', flattened_transpose[index]))

    return file.tell()


def write_pixel_data(ecat_file, pixel_data: numpy.ndarray, byte_position: int=None, seek: bool=None):
    if seek and byte_position:
        ecat_file.seek(byte_position)
    #elif (seek and not byte_position) or (byte_position and not seek):
        #raise Exception("Must provide seek boolean and byte position")
    else:
        pass
    flattened_pixels = pixel_data.flatten().tobytes()
    ecat_file.write(flattened_pixels)
    return 0


def write_ecat(ecat_file: Path,
               mainheader_schema: dict,
               mainheader_values: dict,
               subheaders_values: list,
               subheader_schema: dict,
               number_of_frames: int,
               pixel_x_dimension: int,
               pixel_y_dimension: int,
               pixel_z_dimension: int,
               pixel_byte_size: int,
               pixel_data: list=[]):

    # open the ecat file!
    with open(ecat_file, 'w+b') as outfile:

        # first things first, write the main header with supplied information
        write_header(ecat_file=outfile,
                     schema=mainheader_schema,
                     values=mainheader_values)
        position_post_header_write = outfile.tell()
        # create the directory table
        directory_table = create_directory_table(num_frames=number_of_frames,
                                                 pixel_dimensions={'x':pixel_x_dimension,
                                                                   'y':pixel_y_dimension,
                                                                   'z':pixel_z_dimension},
                                                 pixel_byte_size=pixel_byte_size)
        # write the directory tabel to the file
        write_directory_table(file=outfile,
                              directory_tables=directory_table)

        position_post_table_write = outfile.tell()
        # write subheaders followed by pixel data
        for index, subheader in enumerate(subheaders_values):
            position = outfile.tell()
            table_position = directory_table[0][1, index + 1] * 512
            write_header(ecat_file=outfile,
                         schema=subheader_schema,
                         values=subheader,
                         byte_position=outfile.tell())
            position_post_subheader_write = outfile.tell()
            write_pixel_data(ecat_file=outfile,
                             pixel_data=pixel_data[index])
            position_post_subheader_pixel_data_write = outfile.tell()

    return ecat_file
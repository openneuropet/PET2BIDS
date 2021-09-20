import struct
from math import ceil, floor
from read_ecat import ecat_header_maps, get_buffer_size
import numpy

"""
This program will create an ecat file if provided an ecat schema and a dictionary of values to populate that schema
with.

# First this program collects the same schemas that read_ecat.py does,

from read_ecat import ecat_header_maps

# next this program selects one of the header maps as speficified by some input e.g. if given:

ecat7.3

# it would select the standard image matrix at:

ecat_header_maps['ecat_headers']['73']['mainheader'] 

# and  the subheader map at: 

ecat_header_maps['ecat_headers']['73']['11'] 

# or whatever number is corresponding to the type
# of ecat header you wish to write. Perhaps these should belong in a reverse sort of dictionary

# going to need to create the directory byte block(s) for an ecat. Basically, reverse the process of reading the 
directory in lines 227 through 257 in ecat_read. 
    
    determine the number of frames in the image/pixel data
    create empty table(s) of dtype >i4 dimensions of 4 rows by 64 columns 
    fill empty tables w/ zeros
    place the number 2 in the second row, first column of the table if it's the only directory table or the last 
    directory
    table.
    final output should be a bytes: 1024 type object.
    
# after generating the table may you should then be able to write the main header, write the directory table,
then write each subheader and corresponding pixel data

"""


def write_header(ecat_file, schema: dict, values: dict = {}, byte_offset: int = 0):
    """
    Given a filepath and a schema this function will write an ecat header to a file. If supplied a dictionary of values
    it will populate the written header with them, if not it will fill the header with empty values. If a byte position
    argument is supplied write_header will write to the byte position in the file supplied at file path, else it will
    seek to the end of the file and write there.
    :param file: the ecat file to be written
    :param schema: dictionary schema of the ecat header
    :param values: dictionary of values corresponding to the 'variable_name' entries in the schema dictionary
    :param byte_offset: offset to write the header at, default is at the zero'th byte position.
    :return: the end byte position, spoilers this will be 512 bytes offset from byte_position if that argument is
    supplied.
    """
    for entry in schema:
        byte_position, variable_name, struct_fmt = entry['byte'] + byte_offset, entry['variable_name'], entry['struct']
        struct_fmt = '>' + struct_fmt
        byte_width = struct.calcsize(struct_fmt)
        value_to_write = values.get(variable_name, None)

        # if it's a fill variable pack it with empty bytes
        if 'fill' in variable_name.lower():
            pack_empty = True
        # if no value is supplied in the value dict, pack with empty bytes as well
        elif 'fill' not in variable_name.lower() and not value_to_write:
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
            ecat_file.write(struct.pack(struct_fmt, *value_to_write))
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
    required_directory_blocks = ceil(num_frames/32)

    # determine the width of the frame byte blocks with the pixel dimensions and data sizes
    pixel_volume = numpy.product([*pixel_dimensions.values()])

    # still not sure what some of these numbers mean, but we populate the first column of the byte array with them
    directory_tables = []

    # create entries for the directory table
    directory_order = [i+1 for i in range(num_frames)]

    table_byte_position = 1 + required_directory_blocks
    for i in range(required_directory_blocks):
        # initialize empty 4 x 64 array
        table = numpy.ndarray((4, 64), dtype='>i4')

        # populate first column of table with codes and undetermined codes
        # note these table values are only extrapolated from a data set w/ 45 frames and datasets with less than
        # 31 frames. Behavior or values for frames numbering above 45 (or more specifically 62) is unknown.
        if i == (required_directory_blocks - 1):
            frames_to_iterate = num_frames % 31
            table[0, 0] = 17
            table[1, 0] = 2  # stop value
            table[2, 0] = 2  # stop value
            table[3, 0] = frames_to_iterate  # number of frames referenced in this table
        else:
            frames_to_iterate = floor(num_frames / 31) * 31
            table[0, 0] = 0
            table[1, 0] = 1337
            table[2, 0] = 0
            table[3, 0] = frames_to_iterate

        for column in range(frames_to_iterate):
            if column != 0:
                table_byte_position += 1
            table[0, column + 1] = directory_order.pop(0)
            table[1, column + 1] = table_byte_position
            table_byte_position = int((pixel_byte_size * pixel_volume)/512 + table_byte_position)
            table[2, column + 1] = table_byte_position
            table[3, column + 1] = 1
        directory_tables.append(table)

    return directory_tables


def write_directory_table(file, directory_tables: list):
    """
    Given a list of numpy.ndarray tables and a file path, this function flattens the directory tables to be written
    into the filepath as bytes strings, then writes the bytes strings to the end of the file, returning the byte position
    it left off on.
    :param file: an ecat file that has been initialized with it's main header information
    :param directory_tables: a list of directory tables (1 to 2) that are 4x64 in dimensions and of dtype int32.
    :return: The byte position after writing
    """
    # flatten the lists into byte strings
    flattened_lists = []
    for table in directory_tables:
        make_it_flat = table.flatten(order='F')
        flattened_lists.append(make_it_flat.tobytes())

    for table in flattened_lists:
        file.write(table)
    return 512 * (1 + len(tables))


def write_pixel_data(file, pixel_data: numpy.ndarray):
    flattened_pixels = pixel_data.flatten(order='F').tobytes()
    file.write(flattened_pixels)
    return 0


if __name__ == "__main__":

    with open('bytes.v', 'wb') as outfile:
        x = write_header(outfile, ecat_header_maps['ecat_headers']['73']['mainheader'], {'MAGIC_NUMBER': "Anthony"})
        fake_data = numpy.ndarray([4, 4, 4, 4], dtype='>i2')
        tables = create_directory_table(num_frames=4, pixel_dimensions={'x': 4, 'y': 4, 'z': 4}, pixel_byte_size=2)
        write_directory_table(outfile, tables)
        for i in range(4):
            write_header(outfile, ecat_header_maps['ecat_headers']['73']['7'])
            write_pixel_data(outfile, fake_data[:, :, :, i])




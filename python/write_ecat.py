import struct

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


def write_header(filepath: str, schema: dict, values: dict = {}, byte_offset: int = 0):
    """
    Given a filepath and a schema this function will write an ecat header to a file. If supplied a dictionary of values
    it will populate the written header with them, if not it will fill the header with empty values. If a byte position
    argument is supplied write_header will write to the byte position in the file supplied at file path, else it will
    seek to the end of the file and write there.
    :param filepath: path to the ecat file to be written
    :param schema: dictionary schema of the ecat header
    :param values: dictionary of values corresponding to the 'variable_name' entries in the schema dictionary
    :param byte_offset: offset to write the header at, default is at the zero'th byte position.
    :return: the end byte position, spoilers this will be 512 bytes offset from byte_position if that argument is
    supplied.
    """

    # open file for writing bytes
    with open(filepath, 'wb') as outfile:

        for entry in schema:
            byte_position, data_type, variable_name = entry['byte'] + byte_offset, entry['type'], entry['variable_name']
            byte_width = get_buffer_size(data_type, variable_name)
            write_these_bytes = []
            value_to_write = values.get(variable_name, None)
            if 'Character' in data_type:
                if not value_to_write:
                    value_to_write = 'X' * byte_width
                if len(value_to_write) != byte_width:
                    padding_format = str((byte_width - len(value_to_write))) + 'x'
                    padding = struct.pack(padding_format)
                else:
                    padding = b''
                write_these_bytes = bytes(value_to_write, 'ascii') + padding
            elif 'Integer' in data_type:
                if not value_to_write:
                    value_to_write = [0]
                if byte_width == 4 and 'fill' not in variable_name.lower():
                    struct_format = '>i'
                elif byte_width == 2 and 'fill' not in variable_name.lower():
                    struct_format = '>h'
                else:
                    if len(value_to_write) != byte_width:
                        value_to_write = value_to_write*byte_width

                    struct_format = '>' + str(byte_width) + 'h'

                write_these_bytes = struct.pack(struct_format, *value_to_write)
            elif 'Real' in data_type:
                num_of_fs = int(byte_width/4)
                struct_format = '>' + str(num_of_fs) + 'f'
                if not value_to_write:
                    value_to_write = [0.0]*num_of_fs

                write_these_bytes = struct.pack(struct_format, *value_to_write)
            #print(f"Variable nam print(byte_position)e: {variable_name}, type: {data_type}, value to write: {value_to_write}", f'bytes: {write_these_bytes}')
            outfile.write(write_these_bytes)

    return byte_width + byte_position


def write_directory_table(filepath: str, num_frames: int = 0, byte_position: int = -1):
    pass


def write_pixel_data(filepath: str, pixel_data: numpy.ndarray, byte_position: int = -1):
    pass


if __name__ == "__main__":
    x = write_header('bytes.txt', ecat_header_maps['ecat_headers']['73']['mainheader'], {'MAGIC_NUMBER': "Anthony"})
    print(x)




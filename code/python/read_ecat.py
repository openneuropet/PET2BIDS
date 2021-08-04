import json
import os.path
import struct
from os import path
from os.path import join
import pathlib
import re
import numpy

parent_dir = pathlib.Path(__file__).parent.resolve()
code_dir = parent_dir.parent

# collect ecat header maps
try:
    with open(join(code_dir, 'ecat_headers.json'), 'r') as infile:
        ecat_header_maps = json.load(infile)
except FileNotFoundError:
    raise Exception("Unable to load header definitions and map from ecat_headers.json. Aborting.")


def get_ecat_bytes(path_to_ecat: str):
    """
    Opens an ecat file and reads the entrie file into memory to return a bytes object
    not terribly memory efficient for large or parallel reading of ecat files.
    :param path_to_ecat: path to an ecat file, however will literally open any file an read it
    in as bytes. TODO Perhaps add some validation to this.
    :return: a bytes object
    """
    # check if file exists
    if path.isfile(path_to_ecat):
        with open(path_to_ecat, 'rb') as infile:
            ecat_bytes = infile.read()
    else:
        raise Exception(f"No such file found at {path_to_ecat}")

    return ecat_bytes


def read_bytes(path_to_bytes: str, byte_start: int, byte_stop: int = -1):
    """

    :param path_to_bytes:
    :param byte_start:
    :param byte_stop:
    :return:
    """
    if not os.path.isfile(path_to_bytes):
        raise Exception(f"{path_to_bytes} is not a valid file.")

    # open that file
    bytes_to_read = open(path_to_bytes, 'rb')

    # move to start byte
    bytes_to_read.seek(byte_start, 0)

    # read a section of bytes from bytestart to byte stop
    byte_width = byte_stop
    sought_bytes = bytes_to_read.read(byte_width)

    bytes_to_read.close()
    return sought_bytes


def collect_specific_bytes(bytes_object, start_position, width, relative_to=0):
    """
    Collects specific bytes within a bytes object.
    :param bytes_object: an opened bytes object
    :param start_position: the position to start to read at
    :param width: how far to read from the start position
    :param relative_to: position relative to 0 -> start of file/object, 1 -> current position of seek head,
    2 -> end of file/object
    :return: the bytes starting at position
    """
    # navigate to byte position
    content = bytes_object[start_position: start_position + width]
    return {"content": content, "new_position": start_position + width}


def get_buffer_size(data_type, variable_name):
    """
    Determine the byte width of a variable as defined in the ecat_headers.json
    such that Fill(6) will return 6
    :param data_type:
    :param variable_name:
    :return: the number of bytes to expand a buffer to
    """
    first_split = variable_name.split('(')
    if len(first_split) == 2:
        fill_scalar = int(first_split[1][:-1])
    else:
        fill_scalar = 1
    scalar = int(re.findall(r'\d+', data_type)[0]) * fill_scalar

    return scalar


def get_header_data(header_data_map: dict = {}, ecat_file: str = '', byte_offset: int = 0):
    """
    Collects the header data from an ecat file, by default starts at byte position 0 (aka byte offset)
    for any header that is not the main header this offset will need to be provided
    :param header_data_map: The dictionary mapping of header data this dict must have following form:
    "ecat72_mainheader": [
      {
        "byte": 0,
        "variable_name": "MAGIC_NUMBER",
        "type": "Character*14",
        "comment": "UNIX file type identification number (NOT PART OF THE MATRIX HEADER DATA)"
      },
      {
        "byte": 14,
        "variable_name": "ORIGINAL_FILE_NAME",
        "type": "Character*32",
        "comment": "Scan file’s creation name"
      },
      {
        "byte": 46,
        "variable_name": "SW_VERSION",
        "type": "Integer*2",
        "comment": "Software version number"
      },
      .
      .
      .
     ]
    :param ecat_file: the path to the ecat file that is being read
    :param byte_offset: position to start reading bytes at, the data in the header_data_map is relative
    to this value. E.g. the main header lies at byte 0 of the ecat_file while, the subheader for frame n
    lies at byte n*512
    :return: a dictionary w/ keys corresponding to the variable_name in each header field and their
    accompanying values and the last byte position read e.g. -> {'key': value, ....}, 512
    """
    header = {}
    for values in header_data_map:
        byte_position, data_type, variable_name = values['byte'], values['type'], values['variable_name']
        byte_width = get_buffer_size(data_type, variable_name)
        relative_byte_position = byte_position + byte_offset
        something = read_bytes(ecat_file, relative_byte_position, byte_width)
        if 'Character' in data_type:
            something_filtered = bytes(filter(None, something))
            something_to_string = str(something_filtered, 'UTF-8')
        elif 'Integer' in data_type:
            something_to_string = int.from_bytes(something, 'big')
        elif 'Real' in data_type:
            number_of_fs = int(byte_width / 4)
            something_to_real = struct.unpack('>' + number_of_fs * 'f', something)
            if len(something_to_real) > 1:
                something_to_string = list(something_to_real)
            else:
                something_to_string = something_to_real[0]

        # print(byte_position, data_type, variable_name, something, something_filtered, something_to_string)
        header[variable_name] = something_to_string
        read_head_position = relative_byte_position + byte_width

    return header, read_head_position


def read_ecat_7(ecat_file: str, calibrated: bool = False):
    """
    Reads in an ecat file and collects the main header data, subheader data, and imagining data.
    :param ecat_file: path to an ecat file, does not handle compression currently
    :param calibrated: if True, will scale the raw imaging data by the SCALE_FACTOR in the subheader and
    CALIBRATION_FACTOR in the main header
    :return: main_header, a list of subheaders for each frame, the imagining data from the subheaders
    """
    # use ecat header 72 to collect bytes from ecat file
    ecat_main_header = ecat_header_maps['ecat_headers']['ecat72_mainheader']
    main_header, read_to = get_header_data(ecat_main_header, ecat_file)
    # end collect main header

    """
    Some notes about the file directory/sorted directory:

    The first or 0th column of the file directory correspond to the nature of the directory itself:
    row 0: ??? No idea, some integer
    row 1: Byte position of this table/directory
    row 2: not sure in testing it seems to be 0 most times..
    row 3: The number of frames/additional columns in the file. If the number of columns of this array
    is n, it would contain n-1 frames. 

    The values in sorted_directory correspond to the following for all columns except the first column
    row 0: Not sure, but we sort on this, perhaps it's the frame start time
    row 1: the start byte block position of the frame data
    row 2: end byte block position of the frame data
    row 3: ??? Number of frames contained in w/ in the byte blocks between row 1 and 2?
    """

    # Collecting First Part of File Directory/Index
    next_block = read_bytes(
        path_to_bytes=ecat_file,
        byte_start=read_to,
        byte_stop=read_to + 512)

    directory = None
    while True:
        # if [4,1] of the directory is 0 break
        # if [2,1] of the directory is 2 break

        read_that_byte_array = numpy.frombuffer(next_block, dtype=numpy.dtype('>i4'), count=-1)
        # reshape 1d array into 2d
        reshaped = numpy.transpose(numpy.reshape(read_that_byte_array, (-1, 4)))
        # chop off columns after 32
        reshaped = reshaped[:, 0:32]
        # get directory size/number of frames in dir from 1st column 4th row of the array in the buffer
        directory_size = reshaped[3, 0]
        if directory_size == 0:
            break
        # on the first pass do this
        if directory is None:
            directory = reshaped[:, 1:directory_size + 1]
        else:
            directory = numpy.append(directory, reshaped[:, 1:directory_size + 1], axis=1)
        # determine if this is the last directory by examining the 2nd row of the first column of the buffer
        next_directory_position = reshaped[1, 0]
        if next_directory_position == 2:
            break
        # looks like there is more directory to read, collect some more bytes
        next_block = read_bytes(
            path_to_bytes=ecat_file,
            byte_start=(next_directory_position-1) * 512,
            byte_stop=next_directory_position * 512
        )

    # sort the directory contents as they're sometimes out of order
    sorted_directory = directory[:, directory[0].argsort()]

    # determine subheader type by checking main header
    subheader_type_number = main_header['FILE_TYPE']

    """
    Subheader types correspond to these enumerated types as defined below:
    00 = unknown, 
    01 = Sinogram, 
    02 = Image - 16, 
    03 = Attenuation Correction, 
    04 = Normalization, 
    05 = PolarMap, 
    06 = Volume 8, 
    07 = Volume 16, 
    08 = Projection 8, 
    09 = Projection 16, 
    10 = Image 8, 
    11 = 3D Sinogram 16, 
    12 = 3D Sinogram 8, 
    13 = 3D Normalization, 
    14 = 3D Sinogram Fit)

    Presently, only types 03, 05, 07, 11, and 13 correspond to known subheader types. If the
    value in FILE_TYPE is outside of this range the subheaders will not be read and this will
    raise an exception.
    """

    # here we map the file types to the subheader byte tables/jsons defined in ecat_header_maps
    subheader_types = {
        0: None,
        1: None,
        2: None,
        3: ecat_header_maps['ecat_headers']['ecat72_subheader_matrix_attenuation_files'],
        4: None,
        5: ecat_header_maps['ecat_headers']['ecat72_subheader_matrix_polar_map_files'],
        6: None,
        7: ecat_header_maps['ecat_headers']['ecat72_subheader_matrix_image_files'],
        8: None,
        9: None,
        10: None,
        11: ecat_header_maps['ecat_headers']['ecat72_subheader_3d_matrix_scan_files'],
        12: None,
        13: ecat_header_maps['ecat_headers']['ecat72_subheader_3d_normalized_files']
    }

    # collect the bytes map file for the designated subheader, note some are not supported.
    subheader_map = subheader_types.get(subheader_type_number)

    if not subheader_map:
        raise Exception(f"Unsupported data type: {subheader_type_number}")

    # collect subheaders and pixel data
    subheaders, data = [], []
    for i in range(len(sorted_directory.T)):
        frame_number = i + 1
        print(f"Reading subheader from frame {frame_number}")

        # collect frame info/column
        frame_info = sorted_directory[:, i]
        frame_start = frame_info[1]
        frame_stop = frame_info[2]

        frame_start_byte_position = 512 * (frame_start - 1)  # sure why not
        # read subheader
        subheader, byte_position = get_header_data(subheader_map,
                                                   ecat_file,
                                                   byte_offset=frame_start_byte_position)

        # collect pixel data from file
        pixel_data = read_bytes(path_to_bytes=ecat_file,
                                byte_start=512 * frame_start,
                                byte_stop=512 * frame_stop)

        # calculate size of matrix for pixel data, may vary depending on image type (polar, 3d, etc.)
        if subheader_type_number == 7:
            image_size = [subheader['X_DIMENSION'], subheader['Y_DIMENSION'], subheader['Z_DIMENSION']]
            # check subheader for pixel datatype
            if subheader['DATA_TYPE'] == 5:
                pixel_data_type = '>f4'
            elif subheader['DATA_TYPE'] == 6:
                pixel_data_type = '>i2'

            # read it into a one dimensional matrix
            pixel_data_matrix = numpy.frombuffer(pixel_data,
                                                 dtype=numpy.dtype(pixel_data_type),
                                                 count=image_size[0] * image_size[1] * image_size[2])
            # reshape 1d matrix into 2d, using order F for fortran to keep parity w/ matlab converters
            pixel_data_matrix_2d = numpy.reshape(pixel_data_matrix,
                                                 (image_size[0] * image_size[1], image_size[2]),
                                                 order='F')
            # just making debugging less awful memory wise
            del pixel_data_matrix
            # reshape into 3d
            pixel_data_matrix_3d = numpy.reshape(pixel_data_matrix_2d,
                                                 (image_size[0], image_size[1], image_size[2]),
                                                 order='F')
            # again freeing that memory old style.
            del pixel_data_matrix_2d
        else:
            raise Exception(f"Unable to determine frame image size, unsupported image type {subheader_type_number}")

        if calibrated:
            calibration_factor = subheader['SCALE_FACTOR'] * main_header['ECAT_CALIBRATION_FACTOR']
            calibrated_pixel_data_matrix_3d = calibration_factor * pixel_data_matrix_3d
            data.append(calibrated_pixel_data_matrix_3d)
        else:
            data.append(pixel_data_matrix_3d)

        subheaders.append(subheader)

    # return 4d array instead of list of 3d arrays
    pixel_data_matrix_4d = numpy.zeros(tuple(image_size + [len(data)]), dtype=numpy.dtype(pixel_data_type))
    for index, frame in enumerate(data):
        pixel_data_matrix_4d[:, :, :, index] = frame

    return main_header, subheaders, pixel_data_matrix_4d

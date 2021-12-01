import numpy
import dotenv
from write_ecat import *
from read_ecat import read_ecat, ecat_header_maps
import os

# reference ecat
# defaults???
# make a class? maybe
# check env for path to golden ecat file
dotenv.load_dotenv(dotenv.find_dotenv())

# collect path to golden ecat file
golden_ecat_path = os.environ['GOLDEN_ECAT']

# collect skeleton header
skeleton_main_header, skeleton_subheader, _ = read_ecat(os.environ['GOLDEN_ECAT_TEMPLATE_ECAT'],
                                                        collect_pixel_data=False)
# collect skeleton directory table


number_of_frames = 4
one_dimension = 16
# generate known 'pixel' data e.g. 4 frames with volume = 4x4x4
number_of_array_elements = (one_dimension**3) * number_of_frames


# -32768 and 32767
image_min = -32768
image_max = 32767
spacing = int((image_max - image_min) / number_of_array_elements)

integer_pixel_data = numpy.arange(image_min, image_max, dtype=numpy.int16, step=spacing)


while integer_pixel_data.size != number_of_array_elements:
    integer_pixel_data = integer_pixel_data[:-1]

# edit the header to suit the new file
header_to_write = skeleton_main_header
header_to_write['NUM_FRAMES'] = one_dimension
header_to_write['ORIGINAL_FILE_NAME'] = 'GoldenECAT'
header_to_write['STUDY_TYPE'] = 'Golden'
header_to_write['PATIENT_ID'] = 'PerfectPatient'
header_to_write['PATIENT_NAME'] = 'Majesty'
header_to_write['FACILITY_NAME'] = 'Virtual'

# Write header to file
with open(golden_ecat_path, 'wb') as ecat_file:
    write_header(ecat_file=ecat_file,
                 schema=ecat_header_maps['ecat_headers']['73']['mainheader'],
                 values=header_to_write)

    # collect subset of skeleton frames
    subheaders_to_write = skeleton_subheader[0:one_dimension]

    for subheader in subheaders_to_write:
        subheader['X_DIMENSION'] = one_dimension  # pixel data is 3-d this is 1/3 root of the 3d array.
        subheader['Y_DIMENSION'] = one_dimension
        subheader['Z_DIMENSION'] = one_dimension
        subheader['IMAGE_MIN'] = integer_pixel_data.min()
        subheader['IMAGE_MAX'] = integer_pixel_data.max()
        subheader['ANNOTATION'] = 'This patient is very small.'
        subheader['DATA_TYPE'] = 6

    # generate a directory table for the golden ecat
    directory = create_directory_table(
        num_frames=number_of_frames,
        pixel_dimensions={'x': one_dimension, 'y': one_dimension, 'z': one_dimension},
        pixel_byte_size=2)

    # write the directory to file
    after_table_position = write_directory_table(ecat_file, directory)
    seek_position = ecat_file.tell()
    assert seek_position == after_table_position

    # move forward 512 bytes as directory tables may be 1024 bytes, this one however is only 512
    ecat_file.seek(512, 1)

    # reshape pixel data into 3-d arrays
    pixels_to_collect = one_dimension ** 3
    frames = []
    temp_three_d_arrays = numpy.array_split(integer_pixel_data, number_of_frames)
    for i in range(number_of_frames):
        frames.append(temp_three_d_arrays[i].reshape(one_dimension, one_dimension, one_dimension))

    # write frame data (subheaders and pixel data)
    # for the number of entries in the directory
    for index in range(directory[0][3, 0]):
        subheader_and_frame_byte_position = 512 * directory[0][1, index + 1]
        assert ecat_file.tell() == subheader_and_frame_byte_position
        pixel_seek = write_header(ecat_file=ecat_file,
                                  schema=ecat_header_maps['ecat_headers']['73']['7'],
                                  values=subheaders_to_write[index])

        assert ecat_file.tell() == subheader_and_frame_byte_position + 512
        write_pixel_data(ecat_file=ecat_file,
                         pixel_data=frames[index])


golden_ecat_main_header, golden_ecat_subheaders, golden_ecat_pixel_data = read_ecat(golden_ecat_path)

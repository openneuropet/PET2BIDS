import numpy
import dotenv
from write_ecat import *
from read_ecat import read_ecat, ecat_header_maps
import os

# check env for path to golden ecat file
dotenv.load_dotenv(dotenv.find_dotenv())

# collect path to golden ecat file
golden_ecat_path = os.environ['GOLDEN_ECAT']

# collect skeleton header
skeleton_main_header, skeleton_subheader, _ = read_ecat(os.environ['GOLDEN_ECAT_TEMPLATE_ECAT'],
                                                        collect_pixel_data=False)

# generate known 'pixel' data e.g. 4 frames with volume = 4x4x4
number_of_array_elements = 256

number_of_frames = 4

spacing = int((2147483647) / number_of_array_elements)

integer_pixel_data = numpy.arange(0, 2147483647, step=spacing)

one_dimension = int(number_of_array_elements ** (1 / 4))

while integer_pixel_data.size != number_of_array_elements:
    integer_pixel_data = integer_pixel_data[:-1]

# edit the header to suit the new file
header_to_write = skeleton_main_header
header_to_write['NUM_FRAMES'] = one_dimension
header_to_write['ORIGINAL_FILE_NAME'] = 'Golden_ECAT'
header_to_write['STUDY_TYPE'] = 'Golden'
header_to_write['PATIENT_ID'] = 'Perfect_Patient'
header_to_write['PATIENT_NAME'] = 'Majesty'
header_to_write['FACILITY_NAME'] = 'Virtual'

# Write header to file
with open(golden_ecat_path, 'wb') as ecat:
    write_header(ecat_file=ecat,
                 schema=ecat_header_maps['ecat_headers']['73']['mainheader'],
                 values=header_to_write,
                 byte_offset=0)

# collect subset of skeleton frames
subheaders_to_write = skeleton_subheader[0:one_dimension]

for subheader in subheaders_to_write:
    subheader['X_DIMENSION'] = one_dimension  # pixel data is 4-d, this is the 1/4 root of the flat array
    subheader['Y_DIMENSION'] = one_dimension
    subheader['Z_DIMENSION'] = one_dimension
    subheader['IMAGE_MIN'] = integer_pixel_data.min()
    subheader['IMAGE_MAX'] = integer_pixel_data.max()
    subheader['ANNOTATION'] = 'This patient is very small.'

# generate a directory table for the golden ecat
directory = create_directory_table(
    int(number_of_array_elements ** (1 / 4)),
    {'x': one_dimension, 'y': one_dimension, 'z': one_dimension},
    pixel_byte_size=2)

# write the directory to file
with open(golden_ecat_path, 'r+b') as ecat_file:
    write_directory_table(ecat_file, directory)

# reshape pixel data into 3-d arrays
pixels_to_collect = one_dimension ** 3
frames = []
for i in range(int(integer_pixel_data.size / pixels_to_collect)):
    temp_three_d_array = integer_pixel_data[i * pixels_to_collect:(i + 1) * pixels_to_collect]
    frames.append(temp_three_d_array.reshape(4, 4, 4))
integer_pixel_data = integer_pixel_data.reshape(4, 4, 4, 4)

# write frame data (subheaders and pixel data)
with open(golden_ecat_path, 'r+b') as ecat:
    # for the number of entries in the directory
    for index in range(directory[0][3, 0]):
        seek_to = 512 * directory[0][1, index + 1]
        pixel_seek = write_header(ecat_file=ecat,
                                  schema=ecat_header_maps['ecat_headers']['73']['7'],
                                  values=subheaders_to_write[index],
                                  byte_offset=seek_to)
        write_pixel_data(ecat_file=ecat,
                         byte_position=pixel_seek,
                         pixel_data=frames[index]
                         )
        print(subheaders_to_write[index])
        print(frames)

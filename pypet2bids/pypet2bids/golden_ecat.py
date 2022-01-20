import numpy
import dotenv
from write_ecat import *
from read_ecat import read_ecat, ecat_header_maps
import os
from math import e
from pathlib import Path

# reference ecat
# defaults???
# make a class? maybe
# check env for path to golden ecat file
dotenv.load_dotenv(dotenv.find_dotenv())

# collect path to golden ecat file
int_golden_ecat_path = os.environ['GOLDEN_ECAT_INTEGER']
float_golden_ecat_path = os.environ['GOLDEN_ECAT_FLOAT']


# collect skeleton header
skeleton_main_header, skeleton_subheader, _ = read_ecat(os.environ['GOLDEN_ECAT_TEMPLATE_ECAT'],
                                                        collect_pixel_data=False)
# collect skeleton directory table

number_of_frames = 4
one_dimension = 16
# generate known 'pixel' data e.g. 4 frames with volume = 4x4x4
number_of_array_elements = (one_dimension**3) * number_of_frames

# first generate integer pixel data
# -32768 and 32767
image_min = -32768
image_max = 32767
spacing = int((image_max - image_min) / number_of_array_elements)

integer_pixel_data = numpy.arange(image_min, image_max, dtype=numpy.int16, step=spacing)

# now we write the integer pixel data to a file for testing
integer_data_save_path = Path(int_golden_ecat_path)
numpy.savetxt(integer_data_save_path.with_suffix('.txt'), integer_pixel_data, fmt='%d')

while integer_pixel_data.size != number_of_array_elements:
    integer_pixel_data = integer_pixel_data[:-1]

# reshape pixel data into 3-d arrays
pixels_to_collect = one_dimension ** 3
frames = []
temp_three_d_arrays = numpy.array_split(integer_pixel_data, number_of_frames)
for i in range(number_of_frames):
    frames.append(temp_three_d_arrays[i].reshape(one_dimension, one_dimension, one_dimension))

# edit the header to suit the new file
header_to_write = skeleton_main_header
header_to_write['NUM_FRAMES'] = one_dimension
header_to_write['ORIGINAL_FILE_NAME'] = 'GoldenECATInteger'
header_to_write['STUDY_TYPE'] = 'Golden'
header_to_write['PATIENT_ID'] = 'PerfectPatient'
header_to_write['PATIENT_NAME'] = 'Majesty'
header_to_write['FACILITY_NAME'] = 'Virtual'

subheaders_to_write = skeleton_subheader[0:number_of_frames]
for subheader in subheaders_to_write:
        subheader['X_DIMENSION'] = one_dimension  # pixel data is 3-d this is 1/3 root of the 3d array.
        subheader['Y_DIMENSION'] = one_dimension
        subheader['Z_DIMENSION'] = one_dimension
        subheader['IMAGE_MIN'] = integer_pixel_data.min()
        subheader['IMAGE_MAX'] = integer_pixel_data.max()
        subheader['ANNOTATION'] = 'This patient is very small.'
        subheader['DATA_TYPE'] = 6



write_ecat(ecat_file=int_golden_ecat_path,
           mainheader_schema=ecat_header_maps['ecat_headers']['73']['mainheader'],
           mainheader_values=header_to_write,
           subheaders_values=subheaders_to_write,
           subheader_schema=ecat_header_maps['ecat_headers']['73']['7'],
           number_of_frames=number_of_frames,
           pixel_x_dimension=one_dimension,
           pixel_y_dimension=one_dimension,
           pixel_z_dimension=one_dimension,
           pixel_byte_size=2,
           pixel_data=frames
           )

# now read it
int_golden_ecat_main_header, int_golden_ecat_subheaders, int_golden_ecat_pixel_data = read_ecat(int_golden_ecat_path)

# lastly we generate a float ecat
image_min = -3.4*e**38
image_max = 3.4*e**38
spacing = int((image_max - image_min)/number_of_array_elements)

float_pixel_data = numpy.arange(image_min, image_max, dtype=numpy.float32, step=spacing)

# save just the float data to a txt file
float_pixel_data_path = Path(float_golden_ecat_path)
numpy.savetxt(float_pixel_data_path.with_suffix('.txt'), float_pixel_data)


frames = []
temp_thre_d_arrays = numpy.array_split(float_pixel_data, number_of_frames)
for i in range(number_of_frames):
    frames.append(temp_three_d_arrays[i].reshape(one_dimension, one_dimension, one_dimension))

# edit the header to suit the new file
header_to_write = skeleton_main_header
header_to_write['NUM_FRAMES'] = one_dimension
header_to_write['ORIGINAL_FILE_NAME'] = 'GoldenECATInteger'
header_to_write['STUDY_TYPE'] = 'Golden'
header_to_write['PATIENT_ID'] = 'PerfectPatient'
header_to_write['PATIENT_NAME'] = 'Majesty'
header_to_write['FACILITY_NAME'] = 'Virtual'


subheaders_to_write = skeleton_subheader[0:number_of_frames]
for index, subheader in enumerate(subheaders_to_write):
        subheader['X_DIMENSION'] = one_dimension  # pixel data is 3-d this is 1/3 root of the 3d array.
        subheader['Y_DIMENSION'] = one_dimension
        subheader['Z_DIMENSION'] = one_dimension
        subheader['IMAGE_MIN'] = frames[index].min()
        subheader['IMAGE_MAX'] = frames[index].max()
        subheader['ANNOTATION'] = 'This patient is very small.'
        subheader['DATA_TYPE'] = 5


write_ecat(ecat_file=float_golden_ecat_path,
           mainheader_schema=ecat_header_maps['ecat_headers']['73']['mainheader'],
           mainheader_values=header_to_write,
           subheaders_values=subheaders_to_write,
           subheader_schema=ecat_header_maps['ecat_headers']['73']['7'],
           number_of_frames=number_of_frames,
           pixel_x_dimension=one_dimension,
           pixel_y_dimension=one_dimension,
           pixel_z_dimension=one_dimension,
           pixel_byte_size=4,
           pixel_data=frames
           )

# validate float_ecat
float_golden_ecat_main_header, float_golden_ecat_subheaders, float_golden_ecat_pixel_data = read_ecat(float_golden_ecat_path)

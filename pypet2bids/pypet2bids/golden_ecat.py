import numpy
import dotenv
from pypet2bids.write_ecat import *
from pypet2bids.read_ecat import read_ecat, ecat_header_maps
import os
from math import e
from pathlib import Path
from scipy.io import savemat

'''
This script exists solely to create an ecat with pixel values ranging from 0 to 32767 with a minimum number of frames.
This evenly pixel spaced ecat that has a small number of frames will be used to evaluate the accuracy and precision
of a number of tools that convert or otherwise manipulate ecat data by supplying a ecat image and a corresponding text
file containing the pixel data of that ecat.

This ECAT file and script is thus referred to as the Golden ECAT b/c it represents the perfect standard by which to 
judge all ECATs.

The accompanying text file is formatted such that the pixel values are written one per line:

0
1
2
3
.
.
.
32767

These values are then transformed into a set of NxNxNxF where N = the dimension of a matrix, and F = the total number of
frames within the ecat. 

Anthony Galassi - 2022
----------------------------------------------
Copyright Open NeuroPET team
'''
def main():
    script_path = Path(__file__).absolute()
    ecat_validation_folder = os.path.join(script_path.parent.parent.parent, 'ecat_validation/')

    # Path to a reference/skeleton ecat as well as output paths for saving the created ecats to are stored in
    # environment variables or a .env file
    dotenv.load_dotenv(dotenv.find_dotenv())

    # collect path to golden ecat file
    int_golden_ecat_path = os.environ['GOLDEN_ECAT_INTEGER']
    int_golden_ecat_path_stem = Path(int_golden_ecat_path).stem

    # collect skeleton header and subheaders.
    skeleton_main_header, skeleton_subheader, _ = read_ecat(os.environ['GOLDEN_ECAT_TEMPLATE_ECAT'],
                                                            collect_pixel_data=False)
    number_of_frames = 4
    one_dimension = 16
    # generate known 'pixel' data e.g. 4 frames with volume = 4x4x4
    number_of_array_elements = (one_dimension**3) * number_of_frames

    # first generate integer pixel data
    # 0 to 32767
    image_min = 0
    image_max = 32767
    spacing = round((image_max - image_min) / number_of_array_elements)

    #integer_pixel_data = numpy.arange(image_min, image_max, dtype=numpy.ushort, step=spacing)
    integer_pixel_data = numpy.arange(image_min, image_max, dtype=">H", step=spacing)

    # save data for analysis in matlab
    matlab_struct = {}

    # reshape pixel data into 3-d arrays
    pixels_to_collect = one_dimension ** 3
    frames = []
    temp_three_d_arrays = numpy.array_split(integer_pixel_data, number_of_frames)
    for i in range(number_of_frames):
        frames.append(temp_three_d_arrays[i].reshape(one_dimension, one_dimension, one_dimension))
        matlab_struct[f"frame_{i + 1}_pixel_data"] = frames[i]

    # edit the header to suit the new file
    header_to_write = skeleton_main_header
    header_to_write['NUM_FRAMES'] = 4
    header_to_write['ORIGINAL_FILE_NAME'] = 'GoldenECATInteger'
    header_to_write['STUDY_TYPE'] = 'Golden'
    header_to_write['PATIENT_ID'] = 'PerfectPatient'
    header_to_write['PATIENT_NAME'] = 'Majesty'
    header_to_write['FACILITY_NAME'] = 'Virtual'
    header_to_write['NUM_PLANES'] = one_dimension
    header_to_write['ECAT_CALIBRATION_FACTOR'] = 1.0

    subheaders_to_write = skeleton_subheader[0:number_of_frames]
    for subheader in subheaders_to_write:
            subheader['X_DIMENSION'] = one_dimension  # pixel data is 3-d this is 1/3 root of the 3d array.
            subheader['Y_DIMENSION'] = one_dimension
            subheader['Z_DIMENSION'] = one_dimension
            subheader['IMAGE_MIN'] = integer_pixel_data.min()
            subheader['IMAGE_MAX'] = integer_pixel_data.max()
            subheader['ANNOTATION'] = 'This patient is very small.'
            subheader['DATA_TYPE'] = 6
            subheader['SCALE_FACTOR'] = 1

    matlab_struct['subheaders'] = subheaders_to_write
    matlab_struct['mainheader'] = header_to_write

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

    savemat(os.path.join(ecat_validation_folder, (int_golden_ecat_path_stem + '.mat'))
            , matlab_struct)

    # now read it just to make sure what was created is a real file and not error riddled.
    int_golden_ecat_main_header, int_golden_ecat_subheaders, int_golden_ecat_pixel_data = read_ecat(int_golden_ecat_path)


if __name__ == "__main__":
    main()
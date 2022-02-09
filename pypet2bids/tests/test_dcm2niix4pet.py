from pypet2bids.dcm2niix4pet import *
import pytest
import dotenv
import os
from pathlib import Path

# collect paths to test files/folders
dotenv.load_dotenv(dotenv.find_dotenv())

test_dicom_image_folder = os.environ['TEST_DICOM_IMAGE_FOLDER']
test_dicom_convert_metadata_path = os.environ['TEST_DICOM_CONVERT_METADATA_PATH']
test_dicom_convert_nifti_output_path = os.environ['TEST_DICOM_CONVERT_NIFTI_OUTPUT_PATH']

def test_extract_dicom_header():
    assert 0 == 1

def test_run_dcm2niix():
    converter = Dcm2niix4PET(test_dicom_image_folder, test_dicom_convert_nifti_output_path)
    converter.run_dcm2niix()
    contents_output = os.listdir(test_dicom_convert_nifti_output_path)
    created_jsons = [file for file in contents_output if '.json' in file]
    created_niftis = [file for file in contents_output if '.nii' in file]

    dcm2niix_output = {}
    for file in created_jsons:
        path_object = Path(file)
        output_file_stem = os.path.join(*path_object.parents, path_object.stem)
        if dcm2niix_output.get(output_file_stem, None):
            dcm2niix_output[output_file_stem] = dcm2niix_output[output_file_stem].append(file)
        else:
            dcm2niix_output[output_file_stem]  = []

    for file in created_niftis:
        path_object = Path(file)
        output_file_stem = os.path.join(*path_object.parents, path_object.stem)
        if dcm2niix_output.get(output_file_stem, None):
            dcm2nnix_output[output_file_stem] = dcm2iix[output_file_stem].append(file)
        else:
            dcm2niix_output[output_file_stem]  = []

    print("DonE!")

if __name__ == '__main__':
    test_run_dcm2niix()


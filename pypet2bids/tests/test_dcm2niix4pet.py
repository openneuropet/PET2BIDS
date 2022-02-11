from pypet2bids.dcm2niix4pet import Dcm2niix4PET, dicom_datetime_to_dcm2niix_time, check_json, collect_date_time_from_file_name
import pytest
import dotenv
import os
from pathlib import Path
import pydicom
from tempfile import TemporaryDirectory
import json

# collect paths to test files/folders
dotenv.load_dotenv(dotenv.find_dotenv())

test_dicom_image_folder = os.environ['TEST_DICOM_IMAGE_FOLDER']
test_dicom_convert_metadata_path = os.environ['TEST_DICOM_CONVERT_METADATA_PATH']
test_dicom_convert_nifti_output_path = os.environ['TEST_DICOM_CONVERT_NIFTI_OUTPUT_PATH']

# collect dicoms from test input path
representative_dicoms = {}
for root, folders, files in os.walk(test_dicom_image_folder):
    # sort files by order
    files.sort()
    for f in files:
        try:
            dicom_header = pydicom.dcmread(os.path.join(root, f))
            representative_dicoms[dicom_header.SeriesDescription] = {'filepath': os.path.join(root, f), 'header': dicom_header}
            break

        except pydicom.errors.InvalidDicomError:
            pass


def test_check_json(capsys):
    with TemporaryDirectory() as tempdir:
        tempdir_path = Path(tempdir)
        bad_json = {"Nothing": "but trouble"}
        bad_json_path = os.path.join(tempdir, 'bad_json.json')
        with open(bad_json_path, 'w') as outfile:
            json.dump(bad_json, outfile)

        check_json(bad_json_path)
        check_output = capsys.readouterr()

        assert f'WARNING!!!! Manufacturer is not present in {bad_json_path}' in check_output.out

def test_extract_dicom_headers():
    converter = Dcm2niix4PET(test_dicom_image_folder, test_dicom_convert_nifti_output_path)
    converter.extract_dicom_headers()
    for key, value in converter.dicom_headers.items():
        assert os.path.isfile(os.path.join(test_dicom_image_folder, key))
        assert type(value) is pydicom.dataset.FileDataset


def test_dicom_datetime_to_dcm2niix_time():
    # given the test_time, and test_date below the result of dicom_datetime_to_dcm2niix_time should output
    # the correct_answer as written below

    # The filename's %t refers to the time of study (from 0008,0020 and 0008,0030) - Chris Rorden 2022
    test_time = "163940"
    test_date = "20211206"
    dcm2niix_output = "20211206163940"
    result = dicom_datetime_to_dcm2niix_time(date=test_date, time=test_time)
    assert result == dcm2niix_output


def test_match_dicom_header_to_file():
    # given a list of paths match_dicom_header_to_file will correctly match the a specific dicom header to
    # each file path and return that grouping in the form of a series_description + time entry in a dictionary with
    # the following keys { 'dicom_header': ..., associated_files: [ ...nii.gz, ...json, ...tsv, ...json]
    assert 'up' == 'down'


def test_collect_date_from_file_name():
    # given a file output from dcm2niix, this function will extract the AcquistionDate and AcquisitionTime
    with TemporaryDirectory() as tempdir:
        tempdir_path = Path(tempdir)
        converter = Dcm2niix4PET(test_dicom_image_folder, tempdir_path)
        converter.extract_dicom_headers()

        first_dicom_header = converter.dicom_headers[next(iter(converter.dicom_headers))]
        StudyDate = first_dicom_header.StudyDate
        StudyTime = str(round(float(first_dicom_header.StudyTime)))

        # run dcm2niix to convert these dicoms
        converter.run_dcm2niix()

        # collect filenames
        dcm2niix_output = os.listdir(tempdir)

        for file in dcm2niix_output:
            collected_date = collect_date_time_from_file_name(file)
            assert collected_date[0] == StudyDate
            assert collected_date[1] == StudyTime


def test_run_dcm2niix():
    converter = Dcm2niix4PET(test_dicom_image_folder, test_dicom_convert_nifti_output_path, file_format = '%p_%i_%t_%s')
    converter.run_dcm2niix()
    contents_output = os.listdir(test_dicom_convert_nifti_output_path)
    created_jsons = [file for file in contents_output if '.json' in file]
    created_niftis = [file for file in contents_output if '.nii' in file]

    dcm2niix_output = {}
    for file in created_jsons:
        path_object = Path(file)
        output_file_stem = os.path.join(*path_object.parents, path_object.stem)
        if dcm2niix_output.get(output_file_stem, None):
            dcm2niix_output[output_file_stem] = dcm2niix_output[output_file_stem].append(path_object.resolve())
        else:
            dcm2niix_output[output_file_stem]  = []
            dcm2niix_output[output_file_stem].append(path_object.resolve())

    for file in created_niftis:
        path_object = Path(file)
        output_file_stem = os.path.join(*path_object.parents, path_object.stem)
        if dcm2niix_output.get(output_file_stem, None):
            dcm2nnix_output[output_file_stem] = dcm2iix[output_file_stem].append(path_object.resolve())
        else:
            dcm2niix_output[output_file_stem]  = []
            dcm2niix_output[output_file_stem].append(path_object.resolve())

    print("DonE!")

if __name__ == '__main__':
    test_collect_date_from_file_name()

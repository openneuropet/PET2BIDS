from pypet2bids.dcm2niix4pet import (
    Dcm2niix4PET,
    dicom_datetime_to_dcm2niix_time,
    collect_date_time_from_file_name,
)
from pypet2bids.update_json_pet_file import (
    check_meta_radio_inputs,
    check_json,
    update_json_with_dicom_value,
)

import shutil
import dotenv
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import json
from os.path import join
import pydicom
import subprocess
from unittest import TestCase


# collect config files
# fields to check for
module_folder = Path(__file__).parent.resolve()
python_folder = module_folder.parent
pet2bids_folder = python_folder.parent
spreadsheet_folder = join(pet2bids_folder, "spreadsheet_conversion")


# collect paths to test files/folders
dotenv.load_dotenv(dotenv.find_dotenv())

test_dicom_image_folder = os.environ["TEST_DICOM_IMAGE_FOLDER"]
test_dicom_convert_metadata_path = os.environ["TEST_DICOM_CONVERT_METADATA_PATH"]
test_dicom_convert_nifti_output_path = os.environ[
    "TEST_DICOM_CONVERT_NIFTI_OUTPUT_PATH"
]

# collect dicoms from test input path
representative_dicoms = {}
for root, folders, files in os.walk(test_dicom_image_folder):
    # sort files by order
    files.sort()
    for f in files:
        try:
            dicom_header = pydicom.dcmread(os.path.join(root, f))
            representative_dicoms[dicom_header.SeriesDescription] = {
                "filepath": os.path.join(root, f),
                "header": dicom_header,
            }
            break

        except pydicom.errors.InvalidDicomError:
            pass


def test_check_json(capsys):
    from pypet2bids.helper_functions import logger as log

    logger = log("pypet2bids")
    with TemporaryDirectory() as tempdir:
        tempdir_path = Path(tempdir)
        bad_json = {"Nothing": "but trouble"}
        bad_json_path = os.path.join(tempdir, "bad_json.json")
        with open(bad_json_path, "w") as outfile:
            json.dump(bad_json, outfile)

        check_results = check_json(bad_json_path)
        check_output = capsys.readouterr()

        assert check_results["Manufacturer"] == {"key": False, "value": False}
        # assert f'WARNING - Manufacturer is not present in {bad_json_path}' in check_output.out


def test_extract_dicom_headers():
    converter = Dcm2niix4PET(
        test_dicom_image_folder, test_dicom_convert_nifti_output_path
    )
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
    # given a list of paths match_dicom_header_to_file will correctly match the a specific dicom header(s) to
    # each file path and return that grouping in the form of a series_description + time entry in a dictionary with
    # the following keys { 'dicom_header': ..., associated_files: [ ...nii.gz, ...json, ...tsv, ...json]
    with TemporaryDirectory() as tempdir:
        tempdir_path = Path(tempdir)
        converter = Dcm2niix4PET(test_dicom_image_folder, tempdir_path)
        dicom_headers = converter.extract_dicom_headers()

        converter.run_dcm2niix()

        headers_to_files = converter.match_dicom_header_to_file()

        for keys, output_files in headers_to_files.items():
            dicom_header = converter.dicom_headers[keys]
            dicom_study_time = dicom_datetime_to_dcm2niix_time(dicom_header)
            for output_file in output_files:
                # first check nifti json
                if ".json" in output_file:
                    # assert json filename follows our standard conventions
                    assert dicom_study_time in output_file
                    with open(output_file) as nifti_json:
                        nifti_dict = json.load(nifti_json)
                        assert dicom_header.SeriesNumber == nifti_dict["SeriesNumber"]

                # check .nii as well
                if ".nii" in output_file or ".nii.gz" in output_file:
                    assert dicom_study_time in output_file


def test_collect_date_from_file_name():
    # given a file output from dcm2niix, this function will extract the AcquistionDate and AcquisitionTime
    with TemporaryDirectory() as tempdir:
        tempdir_path = Path(tempdir)
        converter = Dcm2niix4PET(test_dicom_image_folder, tempdir_path)
        converter.extract_dicom_headers()

        first_dicom_header = converter.dicom_headers[
            next(iter(converter.dicom_headers))
        ]
        StudyDate = first_dicom_header.StudyDate
        StudyTime = str(round(float(first_dicom_header.StudyTime)))
        if len(StudyTime) < 6:
            StudyTime = (6 - len(StudyTime)) * "0" + StudyTime

        # run dcm2niix to convert these dicoms
        converter.run_dcm2niix()

        # collect filenames
        dcm2niix_output = os.listdir(tempdir)

        for file in dcm2niix_output:
            collected_date = collect_date_time_from_file_name(file)
            assert collected_date[0] == StudyDate
            assert collected_date[1] == StudyTime


def test_run_dcm2niix():
    converter = Dcm2niix4PET(
        test_dicom_image_folder,
        test_dicom_convert_nifti_output_path,
        file_format="%p_%i_%t_%s",
        silent=True,
    )
    converter.run_dcm2niix()
    contents_output = os.listdir(test_dicom_convert_nifti_output_path)
    created_jsons = [file for file in contents_output if ".json" in file]
    created_niftis = [file for file in contents_output if ".nii" in file]

    dcm2niix_output = {}
    for file in created_jsons:
        path_object = Path(file)
        checks = check_json(
            join(test_dicom_convert_nifti_output_path, path_object), silent=True
        )
        output_file_stem = os.path.join(*path_object.parents, path_object.stem)
        if dcm2niix_output.get(output_file_stem, None):
            dcm2niix_output[output_file_stem] = dcm2niix_output[
                output_file_stem
            ].append(path_object.resolve())
        else:
            dcm2niix_output[output_file_stem] = []
            dcm2niix_output[output_file_stem].append(path_object.resolve())

    for file in created_niftis:
        path_object = Path(file)
        output_file_stem = os.path.join(*path_object.parents, path_object.stem)
        if dcm2niix_output.get(output_file_stem, None):
            dcm2niix_output[output_file_stem] = dcm2niix_output[
                output_file_stem
            ].append(path_object.resolve())
        else:
            dcm2niix_output[output_file_stem] = []
            dcm2niix_output[output_file_stem].append(path_object.resolve())

    assert len(created_niftis) == len(created_jsons)


def test_manufacturers():
    # As far as we know there are these three manufacturers
    manufacturers = ["phillips", "siemens", "ge"]

    # make sure paths are attached with vendor/manufacturer specific dicoms
    manufacturer_paths = {}
    for manu in manufacturers:
        dicom_folder_path = os.environ[f"TEST_DICOM_IMAGE_FOLDER_{manu.upper()}"]

        if dicom_folder_path != "":
            dicom_folder_path = Path(dicom_folder_path)
            if dicom_folder_path.exists():
                manufacturer_paths[manu] = {"dicom_path": dicom_folder_path}

        # open a temporary directory to write output to
        with TemporaryDirectory() as tempdir:
            tempdir_path = Path(tempdir)
            # create output path for every existing manufacturer
            manus = manufacturer_paths.keys()
            for manu in manus:
                nifti_path = os.path.join(tempdir_path, f"{manu}_nifti_output")
                os.mkdir(nifti_path)
                manufacturer_paths[manu]["nifti_path"] = nifti_path

                # convert these things
                input_path = manufacturer_paths[manu]["dicom_path"]
                output_path = manufacturer_paths[manu]["nifti_path"]
                converter = Dcm2niix4PET(input_path, output_path)

                converter.run_dcm2niix()
                print(f"running conversion on images at {input_path}")
                # add jsons to the manufacturer_paths
                output_path_files = os.listdir(output_path)
                jsons = [
                    os.path.join(output_path, output_json)
                    for output_json in output_path_files
                    if ".json" in output_json
                ]

                manufacturer_paths[manu]["json_path"] = jsons

            # now check the output of the jsons, see if the fields are all there
            for key, value in manufacturer_paths.items():
                print(key, value)


def test_update_json_with_dicom_value():
    """
    b/c dicom we don't run this test using github actions
    first checks to see if this is running in github actions, and if so does nothing.
    else it runs on a set of test dicoms and checks to see fields from the dicom header
    get inserted into the sidecar.json produced by dcm2niix during the conversion from dicom to nii
    :return: None
    """
    # check to see if this is running in github actions
    running_in_github = os.getenv("CI", "false")
    if running_in_github.lower() != "true":
        # open temporary directory b/c manual cleanup is a bother
        with TemporaryDirectory() as tempdir:
            test_json_path = Path(os.path.join(tempdir, "test.json"))
            with open(test_json_path, "w") as outfile:
                json.dump({}, outfile)

            # now check json, we should be missing everything from it as it's an empty set
            missing_fields = check_json(test_json_path)

            # now we collect a dicom header
            dicom_headers = []

            dicom_folder = os.getenv("TEST_DICOM_IMAGE_FOLDER", "")

            # possible dicoms
            possible_dicoms = [
                os.path.join(dicom_folder, d) for d in os.listdir(dicom_folder)
            ]
            # we don't need all of the dicom 10% should be good
            for i in range(int(0.2 * len(possible_dicoms))):
                # 100 is plenty
                if len(dicom_headers) >= 100:
                    break
                try:
                    dicom = pydicom.dcmread(possible_dicoms[i])
                    dicom_headers.append(dicom)
                except TypeError:
                    pass

            # now that we have dicom headers we can use our insert method to insert missing metadata
            # into a json
            update_json_with_dicom_value(
                test_json_path, missing_fields, dicom_headers[0]
            )

            # load json to make assertions
            with open(test_json_path, "r") as infile:
                test_json = json.load(infile)

            # only checking a handful of fields as every dicom varies, but our test data has the following fields
            # filled in
            check_fields = [
                "Manufacturer",
                "InstitutionName",
                "Units",
                "InstitutionalDepartmentName",
            ]
            for field in check_fields:
                assert test_json.get(field, "") != ""


def test_additional_arguments():
    additional_args = {"additional1": 1, "additional2": 2}
    with TemporaryDirectory() as tempdir:
        converter = Dcm2niix4PET(
            test_dicom_image_folder,
            tempdir,
            file_format="%p_%i_%t_%s",
            silent=True,
            additional_arguments=additional_args,
        )
        converter.run_dcm2niix()
        contents_output = os.listdir(tempdir)
        created_jsons = [
            os.path.join(tempdir, file) for file in contents_output if ".json" in file
        ]

        # load in json, make sure fields are there
        with open(created_jsons[0], "r") as infile:
            json_contents = json.load(infile)

        for key, value in additional_args.items():
            assert json_contents.get(key, "") == value


def test_check_meta_radio_inputs():
    # test first conditional given InjectedRadioactivity and InjectedMass
    given = {"InjectedRadioactivity": 10, "InjectedMass": 10}
    solution = {
        "InjectedRadioactivityUnits": "MBq",
        "InjectedMassUnits": "ug",
        "SpecificRadioactivityUnits": "Bq/g",
        "SpecificRadioactivity": 1,
    }
    solution.update(given)
    this = check_meta_radio_inputs(given)
    TestCase().assertEqual(this, solution)

    # first case + adding in a value for SpecificRadioactivity
    given = {
        "InjectedRadioactivity": 10,
        "InjectedMass": 10,
        "SpecificRadioactivity": 1,
    }
    solution = {
        "InjectedRadioactivityUnits": "n/a",
        "InjectedMassUnits": "ug",
        "SpecificRadioactivityUnits": "Bq/g",
    }
    solution.update(given)
    this = check_meta_radio_inputs(given)
    TestCase().assertEqual(this, solution)

    # second case + SpecificRadioactivityUnits adde to given
    solution.update({"SpecificRadioactivityUnits": "Bq/g"})
    given.update({"SpecificRadioactivityUnits": "Bq/g"})
    this = check_meta_radio_inputs(given)
    TestCase().assertEqual(this, solution)

    # test second conditional given InjectedRadioactivity and SpecificRadioactivity
    given = {"InjectedRadioactivity": 10, "SpecificRadioactivity": 10}
    solution = {
        "InjectedRadioactivityUnits": "MBq",
        "InjectedMass": 1000000000000.0,
        "InjectedMassUnits": "ug",
        "SpecificRadioactivityUnits": "Bq/g",
        "SpecificRadioactivity": 10,
    }
    solution.update(given)
    this = check_meta_radio_inputs(given)
    TestCase().assertEqual(this, solution)

    # test SpecificRadioactivity is okay
    given = {"InjectedRadioactivity": 44.4, "InjectedMass": 6240}
    solution = {
        "InjectedRadioactivityUnits": "Bq/g",
        "InjectedMass": given["InjectedMass"],
        "InjectedMassUnits": "ug",
        "SpecificRadioactivityUnits": "Bq/g",
        "SpecificRadioactivity": (given["InjectedRadioactivity"] * (10**6))
        / (given["InjectedMass"] * (10**6)),
    }
    this = check_meta_radio_inputs(given)
    TestCase().assertEqual(
        this["SpecificRadioactivity"], solution["SpecificRadioactivity"]
    )

    # check calc injected mass is okay
    given = {"InjectedRadioactivity": 44, "SpecificRadioactivity": 7.1154 * (10**9)}
    InjectedMass = (
        (given["InjectedRadioactivity"] * (10**6))
        / (given["SpecificRadioactivity"])
        * (10**6)
    )
    this = check_meta_radio_inputs(given)
    TestCase().assertEqual(this["InjectedMass"], InjectedMass)

    # check InjectedRadioactivity is okay
    given = {"SpecificRadioactivity": 7.1154 * (10**9), "InjectedMass": 6240}
    InjectedRadioactivity = (
        (given["InjectedMass"] / (10**6)) * given["SpecificRadioactivity"]
    ) / 10**6
    this = check_meta_radio_inputs(given)
    TestCase().assertEqual(this["InjectedRadioactivity"], InjectedRadioactivity)

    # check SpecificRadioactivity is okay
    given = {"MolarActivity": 135192600, "MolecularWeight": 19}
    SpecificRadioactivity = (given["MolarActivity"] * 1000) / given["MolecularWeight"]
    this = check_meta_radio_inputs(given)
    TestCase().assertEqual(this["SpecificRadioactivity"], SpecificRadioactivity)

    # check MolecularWeight is okay
    given = {"MolarActivity": 135192600, "SpecificRadioactivity": 7.1154 * (10**9)}
    MolecularWeight = (given["MolarActivity"] * 1000) / SpecificRadioactivity
    this = check_meta_radio_inputs(given)
    TestCase().assertEqual(this["MolecularWeight"], MolecularWeight)

    # check MolarActivity is okay
    given = {"MolecularWeight": 19, "SpecificRadioactivity": 7.1154 * (10**9)}
    MolarActivity = (given["MolecularWeight"] * given["SpecificRadioactivity"]) / 1000
    this = check_meta_radio_inputs(given)
    TestCase().assertEqual(this["MolarActivity"], MolarActivity)


def test_get_convolution_kernel():
    convolution_kernel_strings = []


def test_run_dcm2niix4pet_with_full_blood_sheet():
    """
    Runs dcm2niix4pet over a set of test dicoms with an accompanying spreadsheet formatted such that the resulting
    output files include PET BIDS valid:
        - json's (one for _pet.nii.gz, and one for _blood.tsv)
        - nifti's (one for _pet.nii.gz)
        - tsv's (one for the manul blood sample e.g. *_recording-manual_blood.tsv)
    :return: None
    :rtype: None
    """
    spreadsheet = os.path.join(
        spreadsheet_folder, "single_subject_sheet", "subject_metadata_example.xlsx"
    )
    with TemporaryDirectory() as tempdir:
        destination = os.path.join(tempdir, "bids_test_dir/sub-01/pet")
        dcm2niix4pet = Dcm2niix4PET(
            image_folder=test_dicom_image_folder,
            destination_path=destination,
            metadata_path=spreadsheet,
            silent=True,
        )
        dcm2niix4pet.convert()
        contents_output = [
            os.path.join(destination, f) for f in os.listdir(destination)
        ]

        # copy over dataset_description.json to bids dir
        dataset_description = {
            "Name": "PET Single Subject w/ sheet",
            "BIDSVersion": "1.6.0",
            "DatasetType": "raw",
            "License": "CCBY",
            "Authors": [
                "Cyril Pernet",
                "Sune Høgild Keller",
                "Gabriel Gonzalez-Escamilla",
                "Søren Baarsgaard Hansen",
                "Maqsood Yaqub",
            ],
            "HowToAcknowledge": "Please cite the repository URL",
        }

        with open(
            os.path.join(tempdir, "bids_test_dir", "dataset_description.json"), "w"
        ) as f:
            json.dump(dataset_description, f, indent=4)

        # copy over a readme file, we use the one in the metadata folder
        readme = os.path.join(pet2bids_folder, "metadata/", "README")
        shutil.copy(readme, os.path.join(tempdir, "bids_test_dir"))

        # run the bids validator on the output
        command = ["bids-validator", os.path.join(tempdir, "bids_test_dir")]
        validation = subprocess.run(command, capture_output=True)

        # check exit code of subprocess
        assert validation.returncode == 0
        # verify that the output is as expected
        output = validation.stdout.decode("utf-8")
        assert "This dataset appears to be BIDS compatible" in output


if __name__ == "__main__":
    test_update_json_with_dicom_value()

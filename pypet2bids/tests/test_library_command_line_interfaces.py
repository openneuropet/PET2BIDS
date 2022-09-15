import os
import subprocess
import tempfile
import pathlib
import json
import pdb

TESTS_DIR = pathlib.Path(__file__).resolve().parent
PYPET2BIDS_DIR = TESTS_DIR.parent
PET2BIDS_DIR = PYPET2BIDS_DIR.parent

# obtain ecat file path
ecat_file_path = PET2BIDS_DIR / 'ecat_validation' / 'ECAT7_multiframe.v.gz'
dicom_source_folder = os.getenv('TEST_DICOM_IMAGE_FOLDER', None)
if dicom_source_folder:
    dicom_source_folder = pathlib.Path(dicom_source_folder)
if not dicom_source_folder:
    dicom_source_folder = PET2BIDS_DIR / 'OpenNeuroPET-Phantoms' / 'source' / 'SiemensBiographPETMR-NRU'
if not dicom_source_folder.exists():
    raise FileNotFoundError(dicom_source_folder)


dcm2niix4pet = PYPET2BIDS_DIR / 'pypet2bids' / 'dcm2niix4pet.py'
ecatpet2bids = PYPET2BIDS_DIR / 'pypet2bids' / 'ecat_cli.py'

dataset_description_dictionary = {
  "_Comment": "This is a very basic example of a dataset description json",
  "Name": "PET Brain phantoms",
  "BIDSVersion": "1.7.0",
  "DatasetType": "raw",
  "License": "CC0",
  "Authors": [
    "Author1 Surname1",
    "Author2 Surname2",
    "Author3 Surname3",
    "Author4 Middlename4 Surname4",
    "Author5 Middlename5 Surname5"
  ],
  "HowToAcknowledge": "No worries this is fake.",
  "ReferencesAndLinks": ["No you aren't getting any", "Don't bother to ask", "Fine, https://fake.fakelink.null"]
}


# TODO parse these from pyproject.toml [tool.poetry.scripts]
check_for_these_being_installed = {
    'dcm2niix4pet': False,
    'ecatpet2bids': False,
    'pet2bids-spreadsheet-template': False,
    'convert-pmod-to-blood': False,
    'bids-validator': False
}


# check to see if cli's are installed
def test_cli_are_on_path():
    for cli in check_for_these_being_installed.keys():
        check_installed = subprocess.run(f"{cli} -h", shell=True, capture_output=True)
        if check_installed.returncode == 0:
            check_for_these_being_installed[cli] = True
        assert check_installed.returncode == 0, f"{cli} should be installed and reachable via command line, this will" \
                                                f"cause further tests to fail."


def test_for_show_examples_argument():
    installed_cli = [key for key in check_for_these_being_installed.keys() if check_for_these_being_installed[key] is True]
    for installed in installed_cli:
        check_for_show_examples = subprocess.run(f"{installed} --show-examples", shell=True, capture_output=True)
        assert check_for_show_examples.returncode == 0, f"{installed} does not have a --show-examples option"


def test_kwargs_produce_valid_conversion(tmp_path):

    # prepare a set of kwargs (stolen from a valid bids subject/dataset, mum's the word ;) )
    full_set_of_kwargs = {
            "Modality": "PT",
            "Manufacturer": "Siemens",
            "ManufacturersModelName": "Biograph 64_mCT",
            "InstitutionName": "NIH",
            "InstitutionalDepartmentName": "NIMH MIB",
            "InstitutionAddress": "10 Center Drive, Bethesda, MD 20892",
            "DeviceSerialNumber": "60005",
            "StationName": "MIAWP60005",
            "PatientPosition": "FFS",
            "SoftwareVersions": "VG60A",
            "SeriesDescription": "PET Brain Dyn TOF",
            "ProtocolName": "PET Brain Dyn TOF",
            "ImageType": [
                "ORIGINAL",
                "PRIMARY"
            ],
            "SeriesNumber": 6,
            "ScanStart": 2,
            "TimeZero": "10:39:46",
            "InjectionStart": 0,
            "AcquisitionNumber": 2001,
            "ImageComments": "Frame 1 of 33^AC_CT_Brain",
            "Radiopharmaceutical": "ps13",
            "RadionuclidePositronFraction": 0.997669,
            "RadionuclideTotalDose": 714840000.0,
            "RadionuclideHalfLife": 1220.04,
            "DoseCalibrationFactor": 30806700.0,
            "ConvolutionKernel": "XYZ Gauss2.00",
            "Units": "Bq/mL",
            "ReconstructionName": "PSF+TOF",
            "ReconstructionParameterUnits": [
                "None",
                "None"
            ],
            "ReconstructionParameterLabels": [
                "subsets",
                "iterations"
            ],
            "ReconstructionParameterValues": [
                21,
                3
            ],
            "ReconFilterType": "XYZ Gauss",
            "ReconFilterSize": 2.0,
            "AttenuationCorrection": "measured,AC_CT_Brain",
            "DecayFactor": [
                1.00971
            ],
            "FrameTimesStart": [
                0
            ],
            "FrameDuration": [
                30
            ],
            "SliceThickness": 2,
            "ImageOrientationPatientDICOM": [
                1,
                0,
                0,
                0,
                1,
                0
            ],
            "ConversionSoftware": [
                "dcm2niix",
                "pypet2bids"
            ],
            "ConversionSoftwareVersion": [
                "v1.0.20211006",
                "0.0.8"
            ],
            "TracerName": "[11C]PS13",
            "TracerRadionuclide": "11C",
            "InjectedRadioactivity": 714840000.0,
            "InjectedRadioactivityUnits": "Bq",
            "InjectedMass": 5.331647109063877,
            "InjectedMassUnits": "nmol",
            "SpecificRadioactivity": 341066000000000,
            "SpecificRadioactivityUnits": "Bq/mol",
            "ModeOfAdministration": "bolus",
            "AcquisitionMode": "dynamic",
            "ImageDecayCorrected": True,
            "ImageDecayCorrectionTime": 0,
            "ReconMethodName": "Point-Spread Function + Time Of Flight",
            "ReconMethodParameterLabels": [
                "subsets",
                "iterations"
            ],
            "ReconMethodParameterUnits": [
                "none, none"
            ],
            "ReconMethodParameterValues": [
                21,
                3
            ],
            "Haematocrit": 0.308
    }

    # convert kwargs to string
    kwargs_string = ''
    for key, value in full_set_of_kwargs.items():
        kwargs_string += f'{key}' + '=' + '"' + f'{str(value)}' + '" '

    # test ecat converter

    # obtain ecat file path
    ecat_file_path = PET2BIDS_DIR / 'ecat_validation' / 'ECAT7_multiframe.v.gz'

    # create ecat dir
    ecat_bids_dir = tmp_path / "ecat_test/sub-ecat/ses-test/pet"
    ecat_bids_dir.mkdir(parents=True, exist_ok=True)

    # we're going to want a dataset description json at a minimum
    dataset_description_path = ecat_bids_dir.parent.parent.parent / "dataset_description.json"
    with open(dataset_description_path, 'w') as outfile:
        json.dump(dataset_description_dictionary, outfile, indent=4)

    ecat_bids_nifti_path = ecat_bids_dir / "sub-ecat_ses-test_pet.nii"
    convert_ecat_command = f"python {ecatpet2bids} {ecat_file_path} --convert --nifti {ecat_bids_nifti_path} --kwargs {kwargs_string}"

    convert_ecat = subprocess.run(convert_ecat_command, shell=True, capture_output=True)

    # run validator
    cmd = f"bids-validator {ecat_bids_dir.parent.parent.parent} --ignoreWarnings"
    validate_ecat = subprocess.run(cmd, shell=True, capture_output=True)

    assert validate_ecat.returncode == 0, cmd

    # now do the same thing for dcm2niix4pet
    destination_path = tmp_path / "dicom_test/sub-dicom/ses-test/pet"
    destination_path.mkdir(parents=True, exist_ok=True)

    dicom_source_folder = os.getenv('TEST_DICOM_IMAGE_FOLDER', None)
    if dicom_source_folder:
        dicom_source_folder = pathlib.Path(dicom_source_folder)
    if not dicom_source_folder:
        dicom_source_folder = PET2BIDS_DIR / 'OpenNeuroPET-Phantoms' / 'source' / 'SiemensBiographPETMR-NRU'
    if not dicom_source_folder.exists():
        raise FileNotFoundError(dicom_source_folder)

    dataset_description_path = destination_path.parent.parent.parent / 'dataset_description.json'
    with open(dataset_description_path, 'w') as outfile:
        json.dump(dataset_description_dictionary, outfile, indent=4)

    # pass parsed objects to dcm2niix4pet
    convert_dicom_command = f"python {dcm2niix4pet} {dicom_source_folder} --destination-path {destination_path} --kwargs {kwargs_string}"

    convert_dicom = subprocess.run(convert_dicom_command, shell=True, capture_output=True)

    dicom_cmd = f"bids-validator {destination_path.parent.parent.parent} --ignoreWarnings"
    validate_dicom = subprocess.run(dicom_cmd, shell=True, capture_output=True)

    assert validate_dicom.returncode == 0, validate_dicom.stdout


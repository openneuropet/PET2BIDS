import os
import subprocess
import tempfile
import pathlib
import json
import pdb
from pypet2bids.ecat import Ecat

TESTS_DIR = pathlib.Path(__file__).resolve().parent
PYPET2BIDS_DIR = TESTS_DIR.parent
PET2BIDS_DIR = PYPET2BIDS_DIR.parent

# obtain ecat file path
ecat_file_path = PET2BIDS_DIR / 'ecat_validation' / 'ECAT7_multiframe.v.gz'
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
                "none", "none"
            ],
            "ReconMethodParameterValues": [
                21,
                3
            ],
            "Haematocrit": 0.308
    }

    # test ecat converter

    # create ecat dir
    ecat_bids_dir = tmp_path / "ecat_test/sub-ecat/ses-test/pet"
    ecat_bids_dir.mkdir(parents=True, exist_ok=True)

    # we're going to want a dataset description json at a minimum
    dataset_description_path = ecat_bids_dir.parent.parent.parent / "dataset_description.json"
    with open(dataset_description_path, 'w') as outfile:
        json.dump(dataset_description_dictionary, outfile, indent=4)

    ecat_bids_nifti_path = ecat_bids_dir / "sub-ecat_ses-test_pet.nii"

    # run ecat converter
    convert_ecat = Ecat(ecat_file=str(ecat_file_path),
                        nifti_file=str(ecat_bids_nifti_path),
                        kwargs=full_set_of_kwargs,
                        collect_pixel_data=True)

    convert_ecat.convert()

    # run validator
    cmd = f"bids-validator {ecat_bids_dir.parent.parent.parent} --ignoreWarnings"
    validate_ecat = subprocess.run(cmd, shell=True, capture_output=True)

    assert validate_ecat.returncode == 0, cmd


def test_spreadsheets_produce_valid_conversion_ecatpet2bids(tmp_path):
    # collect spreadsheets
    single_subject_spreadsheet = (
            PET2BIDS_DIR / 'spreadsheet_conversion/single_subject_sheet/subject_metadata_example.xlsx')

    ecatpet2bids_test_dir = tmp_path / 'ecatpet2bids_spreadsheet_input'
    ecatpet2bids_test_dir.mkdir(parents=True, exist_ok=True)
    subject_folder = ecatpet2bids_test_dir / 'sub-singlesubjectspreadsheetecat' / 'ses-test' / 'pet'

    cmd = (f"python {ecatpet2bids} {ecat_file_path} "
           f"--nifti {subject_folder}/sub-singlesubjectspreadsheetecat_ses-test_pet.nii.gz "
           f"--metadata-path {single_subject_spreadsheet} "
           f"--convert")

    spreadsheet_ecat = Ecat(ecat_file=str(ecat_file_path),
                            nifti_file=str(subject_folder) + '/sub-singlesubjectspreadsheetecat_ses-test_pet.nii.gz',
                            metadata_path=single_subject_spreadsheet,
                            collect_pixel_data=True)

    spreadsheet_ecat.convert()

    # copy over dataset_description
    dataset_description_path = ecatpet2bids_test_dir / 'dataset_description.json'
    with open(dataset_description_path, 'w') as outfile:
        json.dump(dataset_description_dictionary, outfile, indent=4)

    validator_cmd = f"bids-validator {ecatpet2bids_test_dir} --ingnoreWarnings"
    validate_ecat_w_spreadsheet = subprocess.run(validator_cmd, shell=True, capture_output=True)

    assert validate_ecat_w_spreadsheet.returncode == 0




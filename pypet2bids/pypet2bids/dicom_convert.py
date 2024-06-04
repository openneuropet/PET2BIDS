"""
this function does

:format:
:param:
:return:

:Authors: Anthony Galassi
:Copyright: Open NeuroPET team
"""

import os.path
import importlib.util
import subprocess
import pandas
import pandas as pd
from os.path import isdir, isfile
from os import listdir, walk, makedirs
import pathlib
import json
import pydicom
import re
import platform
from numpy import cumsum
from tempfile import TemporaryDirectory
from pathlib import Path
from argparse import ArgumentParser


class Convert:
    """
    This class is an all in one dicom to bids converter that uses dcm2niix to convert images and then post conversion
    uses a collection of python methods and libraries to extract, modify, and write PET imaging metadata into BIDS
    text files associated with blood, radioligand, and imaging metadata not contained in the nifti generated by dcm2niix

    Because dcm2niix does such an excellent job most of the methods in this class are only available after it has
    converted the imaging data from dicom into nifti.
    """

    def __init__(
        self,
        image_folder: str,
        metadata_path: str = None,
        destination_path: str = None,
        subject_id: str = "",
        session_id: str = "",
        metadata_translation_script_path: str = None,
    ):

        self.image_folder = image_folder
        self.metadata_path = metadata_path
        self.destination_path = None
        self.subject_id = subject_id
        self.session_id = session_id
        self.metadata_dataframe = None  # dataframe object of text file metadata
        self.metadata_translation_script_path = metadata_translation_script_path
        self.dicom_header_data = {}  # extracted data from dicom header
        self.nifti_json_data = {}  # extracted data from dcm2niix generated json file
        self.blood_json_data = {}

        # if no destination path is supplied plop nifti into the same folder as the dicom images
        if not destination_path:
            self.destination_path = self.image_folder
        else:
            # make sure destination path exists
            if isdir(destination_path):
                self.destination_path = destination_path
                pass
            else:
                print(
                    f"No folder found at destination, creating folder(s) at {destination_path}"
                )
                makedirs(destination_path)

        if self.check_for_dcm2niix() != 0:
            raise Exception(
                "dcm2niix error:\n"
                + "The converter relies on dcm2niix.\n"
                + "dcm2niix was not found in path, try installing or adding to path variable."
            )

        self.extract_dicom_header()
        # create strings for output files
        if self.session_id:
            self.session_string = "_ses-" + self.session_id
        elif self.session_id == "autogeneratesessionid":
            # if no session is supplied create a datestring from the dicom header
            self.session_string = (
                "_ses-"
                + self.dicom_header_data.SeriesDate
                + self.dicom_header_data.SeriesTime
            )
        else:
            self.session_string = ""

        # now for subject id
        if subject_id:
            self.subject_id = subject_id
        else:
            self.subject_id = str(self.dicom_header_data.PatientID)
            # check for non-bids values
            self.subject_id = re.sub(r"[^a-zA-Z0-9\d\s:]", "", self.subject_id)

        self.subject_string = "sub-" + self.subject_id
        # no reason not to convert the image files immediately if dcm2niix is there
        self.run_dcm2niix()

        # extract all metadata
        self.extract_nifti_json()  # this will extract the data from the dcm2niix sidecar and store it in self.nifti_json_data
        if self.metadata_path:
            self.extract_metadata()
            # build output structures for metadata
            bespoke_data = self.bespoke()

            # assign output structures to class variables
            self.future_json = bespoke_data["future_nifti_json"]
            self.future_blood_tsv = bespoke_data["future_blood_tsv"]
            self.future_blood_json = bespoke_data["future_blood_json"]
            self.participant_info = bespoke_data["participants_info"]

    @staticmethod
    def check_for_dcm2niix():
        """
        Just checks for dcm2niix using the system shell, returns 0 if dcm2niix is present.
        :return: status code of the command dcm2niix
        """
        check = subprocess.run(
            "dcm2niix -h",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return check.returncode

    def extract_dicom_header(self, additional_fields=[]):
        """
        Opening up files till a dicom is located, then extracting any header information
        to be used during and after the conversion process. This includes patient/subject id,
        as well any additional frame or metadata that's required for conversion.
        :return: dicom header information to self.subject_id and/or self.dicom_header_data
        """

        for root, dirs, files in os.walk(self.image_folder):
            for f in files:
                try:
                    dicom_header = pydicom.dcmread(os.path.join(root, f))

                    # collect subject/patient id if none is supplied
                    if self.subject_id is None:
                        self.subject_id = dicom_header.PatientID

                    self.dicom_header_data = dicom_header
                    break

                except pydicom.errors.InvalidDicomError:
                    pass

    def extract_nifti_json(self):
        """
        Collects the information contained in the wanted information list and adds it to self.
        :return: dictionary representation of information contained w/ in nifti sidecar json.
        """

        # look for nifti json in destination folder
        pet_json = None
        collect_contents = listdir(self.destination_path)
        for filepath in collect_contents:
            if ".json" in filepath:
                pet_json = os.path.join(self.destination_path, filepath)
                break
            else:
                for root, dirs, files in os.walk(self.destination_path):
                    for f in files:
                        if ".json" in f:
                            pet_json = os.path.join(root, f)
                            break

        if pet_json is None:
            raise Exception("Unable to find json file for nifti image")

        with open(pet_json, "r") as infile:
            self.nifti_json_data = json.load(infile)

    def extract_metadata(self):
        """
        Opens up a metadata file and reads it into a pandas dataframe
        :return: a pd dataframe object
        """
        # collect metadata from spreadsheet
        metadata_extension = pathlib.Path(self.metadata_path).suffix
        self.open_meta_data(metadata_extension)

    def open_meta_data(self, extension):
        """
        Opens a text metadata file with the pandas method most appropriate for doing so based on the metadata
        file's extension.
        :param extension: The extension of the file
        :return: a pandas dataframe representation of the spreadsheet/metadatafile
        """
        methods = {"excel": pd.read_excel, "csv": pd.read_csv}

        if "xls" in extension:
            proper_method = "excel"
        else:
            proper_method = extension

        try:
            use_me_to_read = methods.get(proper_method, None)
            self.metadata_dataframe = use_me_to_read(self.metadata_path)
        except IOError as err:
            raise err(f"Problem opening {self.metadata_path}")

    def run_dcm2niix(self):
        """
        Just passing some args to dcm2niix using the good ole shell
        :return: N/A
        """
        with TemporaryDirectory() as tempdir:
            tempdir_pathlike = Path(tempdir)

            convert = subprocess.run(
                f"dcm2niix -w 1 -z y -o {tempdir_pathlike} {self.image_folder}",
                shell=True,
                capture_output=True,
            )
            if (
                convert.returncode != 0
                and bytes("Skipping existing file named", "utf-8") not in convert.stdout
                or convert.stderr
            ):
                print(convert.stderr)
                raise Exception("Error during image conversion from dcm to nii!")

            # collect contents of the tempdir
            files_created_by_dcm2niix = [
                os.path.join(tempdir_pathlike, file)
                for file in listdir(tempdir_pathlike)
            ]

            # split files by json and nifti
            niftis = [
                Path(nifti) for nifti in files_created_by_dcm2niix if "nii.gz" in nifti
            ]
            sidecars = [
                Path(sidecar)
                for sidecar in files_created_by_dcm2niix
                if ".json" in sidecar
            ]

            # order lists
            niftis.sort()
            sidecars.sort()

            move_dictionary = {}
            # loop through and rename files, if there is more than one nifti or json per session add the run label
            nifti_run_number, sidecar_run_number = "", ""
            for index, nifti in enumerate(niftis):
                if len(niftis) > 1:
                    nifti_run_number = str(index + 1)
                    nifti_run_number = "_" + nifti_run_number.zfill(
                        len(nifti_run_number) + 1
                    )
            new_nifti_name = (
                self.subject_string
                + self.session_string
                + nifti_run_number
                + "_pet.nii.gz"
            )
            move_dictionary[str(nifti)] = os.path.join(
                self.destination_path, new_nifti_name
            )

            for index, sidecar in enumerate(sidecars):
                if len(sidecars) > 1:
                    sidecar_run_number = str(index + 1)
                    sidecar_run_number = "_" + zfill(len(sidecar_run_number) + 1)
            new_sidecar_name = (
                self.subject_string
                + self.session_string
                + sidecar_run_number
                + "_pet.json"
            )
            move_dictionary[str(sidecar)] = os.path.join(
                self.destination_path, new_sidecar_name
            )

            # move files to actual destination
            for old_file_path, new_file_path in move_dictionary.items():
                subprocess.run(f"mv {old_file_path} {new_file_path}", shell=True)

    def bespoke(self):
        """
        This function attempts to collect and organize imaging metadata from PET text and imaging files into BIDS
        compliant text files. At a minimum this function extracts additional dicom header data that is not included
        into the nifti sidecar after the conversion from dicom to nifti.

        :return: dictionary containing BIDS nifti sidecar data, blood data tsv, blood json, and participants list tsv

        """
        future_nifti_json = {
            "Manufacturer": self.nifti_json_data.get("Manufacturer"),
            "ManufacturersModelName": self.nifti_json_data.get(
                "ManufacturersModelName"
            ),
            "Units": "Bq/mL",
            "TracerName": self.nifti_json_data.get("Radiopharmaceutical"),
            "TracerRadionuclide": self.nifti_json_data.get("RadionuclideTotalDose", 0)
            / 10**6,
            "InjectedRadioactivityUnits": "MBq",
            "FrameTimesStart": [
                int(entry)
                for entry in (
                    [0]
                    + list(cumsum(self.nifti_json_data["FrameDuration"]))[
                        0 : len(self.nifti_json_data["FrameDuration"]) - 1
                    ]
                )
            ],
            "FrameDuration": self.nifti_json_data["FrameDuration"],
            "ReconMethodName": self.dicom_header_data.ReconstructionMethod,
            "ReconFilterType": self.dicom_header_data.ConvolutionKernel,
            "AttenuationCorrection": self.dicom_header_data.AttenuationCorrectionMethod,
            "DecayCorrectionFactor": self.nifti_json_data.get("DecayFactor", ""),
        }

        # initializing empty dictionaries to catch possible additional data from a metadata spreadsheet
        future_blood_json = {}
        future_blood_tsv = {}

        if self.metadata_translation_script_path:
            try:
                # this is where the goofiness happens, we allow the user to create their own custom script to manipulate
                # data from their particular spreadsheet wherever that file is located.
                spec = importlib.util.spec_from_file_location(
                    "metadata_translation_script", self.metadata_translation_script_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                text_file_data = module.translate_metadata(
                    self.metadata_dataframe, self.dicom_header_data
                )
            except AttributeError as err:
                print(f"Unable to locate metadata_translation_script")

            self.future_blood_tsv = text_file_data.get("blood_tsv", {})
            self.future_blood_json = text_file_data.get("blood_json", {})
            self.future_nifti_json = text_file_data.get("nifti_json", {})

        participants_tsv = {
            "sub_id": [self.subject_id],
            "weight": [self.dicom_header_data.PatientWeight],
            "sex": [self.dicom_header_data.PatientSex],
        }

        return {
            "future_nifti_json": future_nifti_json,
            "future_blood_json": future_blood_json,
            "future_blood_tsv": future_blood_tsv,
            "participants_info": participants_tsv,
        }

    def write_out_jsons(self, manual_path=None):
        """
        Writes out blood and modified `*_pet.json` file at destination path

        :param manual_path: user supplied path to write out jsons to, if None writes the json to the ouput directory supplied to Convert class object destination_path.

        :return: The name of the json file written to.

        """

        if manual_path is None:
            # dry
            identity_string = os.path.join(
                self.destination_path, self.subject_string + self.session_string
            )
        else:
            identity_string = os.path.join(
                manual_path, self.subject_string + self.session_string
            )

        with open(identity_string + "_pet.json", "w") as outfile:
            self.nifti_json_data.update(self.future_nifti_json)
            json.dump(self.nifti_json_data, outfile, indent=4)

        # write out better json
        with open(identity_string + "_recording-manual-blood.json", "w") as outfile:
            self.blood_json_data.update(self.future_blood_json)
            json.dump(self.blood_json_data, outfile, indent=4)

        return identity_string

    def write_out_blood_tsv(self, manual_path=None):
        """
        Creates a blood.tsv
        :param manual_path:  a folder path specified at function call by user, defaults none
        :return: The name of the tsv file written to.
        """
        if manual_path is None:
            # dry
            identity_string = os.path.join(
                self.destination_path, self.subject_string + self.session_string
            )
        else:
            identity_string = os.path.join(
                manual_path, self.subject_string + self.session_string
            )

        # make a pandas dataframe from blood data
        blood_data_df = pandas.DataFrame.from_dict(self.future_blood_tsv)
        blood_data_df.to_csv(
            identity_string + "_recording-manual_blood.tsv", sep="\t", index=False
        )

        # make a small dataframe for the participants
        # participants_df = pandas.DataFrame.from_dict(self.participant_info)
        # participants_df.to_csv(os.path.join(self.destination_path, 'participants.tsv'), sep='\t', index=False)

        return identity_string


# get around dark mode issues on OSX when viewing the Gooey generated gui on a darkmode enabled Mac, does not work well.
if platform.system() == "Darwin":
    item_default = {
        "error_color": "#ea7878",
        "label_color": "#000000",
        "text_field_color": "#ffffff",
        "text_color": "#000000",
        "help_color": "#363636",
        "full_width": False,
        "validator": {"type": "local", "test": "lambda x: True", "message": ""},
        "external_validator": {
            "cmd": "",
        },
    }
else:
    item_default = None


def cli():
    # simple converter takes command line arguments <folder path> <destination path> <subject-id> <session-id>
    parser = ArgumentParser(
        description="Converts PET imaging data from dicom to BIDS compliant nifti and metadata "
        "files"
    )
    parser.add_argument("folder", type=str, help="Folder path containing imaging data")
    parser.add_argument(
        "-m", "--metadata-path", type=str, help="Path to metadata file for scan"
    )
    parser.add_argument(
        "-t",
        "--translation-script-path",
        help="Path to a script written to extract and transform metadata from a spreadsheet to BIDS"
        + " compliant text files (tsv and json)",
    )
    parser.add_argument(
        "-d",
        "--destination-path",
        type=str,
        help="Destination path to send converted imaging and metadata files to. If "
        + "omitted defaults to using the path supplied to folder path. If destination path "
        + "doesn't exist an attempt to create it will be made.",
        required=False,
    )
    parser.add_argument(
        "-i",
        "--subject-id",
        type=str,
        help="user supplied subject id. If left blank will use PatientName from dicom header",
        required=False,
    )
    parser.add_argument(
        "-s",
        "--session_id",
        type=str,
        help="User supplied session id. If left blank defaults to "
        + "None/null and omits addition to output",
    )

    args = parser.parse_args()

    if not isdir(args.folder):
        raise FileNotFoundError(f"{args.folder} is not a valid path")

    converter = Convert(
        image_folder=args.folder,
        metadata_path=args.metadata_path,
        destination_path=args.destination_path,
        metadata_translation_script_path=args.translation_script_path,
        subject_id=args.subject_id,
        session_id=args.session_id,
    )

    # convert it all!
    converter.run_dcm2niix()
    if args.metadata_path and args.translation_script_path:
        converter.bespoke()
        converter.write_out_jsons()
        converter.write_out_blood_tsv()


if __name__ == "__main__":
    cli()

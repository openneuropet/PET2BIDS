from json_maj import main
import importlib.util
import subprocess
import pandas as pd
import sys
from os.path import isdir, isfile, join
from os import listdir, walk, makedirs
from pathlib import Path
import json
import pydicom
import re
import platform
from numpy import cumsum
from tempfile import TemporaryDirectory
import shutil
from dateutil import parser
from termcolor import colored


"""
This module acts as a simple wrapper around dcm2niix, it takes all of the same arguments as dcm2niix but does a little
bit of extra work to conform the output nifti and json from dcm2niix to the PET BIDS specification. Additionally, but
optionally, this module can collect blood or physiological data/metadata from spreadsheet files if the path of that
spreadsheet file as well as a python module/script written to interpret it are provided in addition to relevant dcm2niix
commands.
"""

# fields to check for
module_folder = Path(__file__).parent.resolve()
python_folder = module_folder.parent
pet2bids_folder = python_folder.parent
metadata_folder = join(pet2bids_folder, 'metadata')

# collect metadata jsons
metadata_jsons = [Path(join(metadata_folder, metadata_json)) for metadata_json in listdir(metadata_folder) if '.json' in metadata_json]

metadata_dictionaries = {}

for metadata_json in metadata_jsons:
    try:
        with open(metadata_json, 'r') as infile:
            dictionary = json.load(infile)

        metadata_dictionaries[metadata_json.name] = dictionary
    except FileNotFoundError as err:
        raise err(f"Missing pet metadata files in {metadata_folder}, unable to validate metadata.")


def check_json(path_to_json, items_to_check=metadata_dictionaries['PET_metadata.json']):
    """
    this method opens a json and checks to see if a set of mandatory values is present within that json, optionally it
    also checks for recommened key value pairs. If fields are not present a warning is raised to the user.
    :param path_to_json: path to a json file e.g. a BIDS sidecar file created after running dcm2niix
    :param items_to_check: a dictionary with items to check for within that json. Items to check should be structured
    such there are keys describing the pertinance of the required items corresponding with a list of fields of those
    items. See below:

    >>>items_to_check = {"mandatory": ["AttenuationCorrection"],
    >>>                  "recommended": ["SinglesRate"],
    >>>                  "optional": ["Anaesthesia"]}
    :return: None
    """
    # check if path exists
    path_to_json = Path(path_to_json)
    if not path_to_json.exists():
        raise FileNotFoundError(path_to_json)

    # open the json
    with open(path_to_json, 'r') as infile:
        json_to_check = json.load(infile)


    warning_color = {'mandatory': 'red',
                     'recommended': 'yellow',
                     'optional:': 'blue'}

    for requirement in items_to_check.keys():
        color = warning_color.get(requirement, 'yellow')
        for item in items_to_check[requirement]:
            if item in json_to_check.keys() and json_to_check.get(item, None):
                # this json has both the key and a non blank value
                pass
            elif item in json_to_check.keys() and not json_to_check.get(item, None):
                print(colored(f"WARNING {item} present but has null value.", "yellow"))
            else:
                print(colored(f"WARNING!!!! {item} is not present in {path_to_json}. This will have to be corrected "
                              f"post conversion.", color))


def dicom_datetime_to_dcm2niix_time(dicom=None, time_field='StudyTime', date_field='StudyDate', date='', time=''):
    """
    Dcm2niix provides the option of outputing the scan data and time into the .nii and .json filename at the time of
    conversion if '%t' is provided following the '-f' flag. The result is the addition of a date time string of the
    format:
    :param dicom: pydicom.dataset.FileDataset object or a path to a dicom
    :param time_field: 
    :param date_field: 
    :return: 
    """
    if dicom:
        if type(dicom) is pydicom.dataset.FileDataset:
            # do nothing
            pass
        elif type(dicom) is str:
            try:
                dicom_path = Path(dicom)
                dicom = pydicom.dcmread(dicom_path)
            except TypeError as err:
                raise err(f"dicom must be either a pydicom.dataset.FileDataSet object or a valid path to a dicom file")


        parsed_date = dicom.StudyDate
        parsed_time = str(round(float(dicom.StudyTime)))
    elif date and time:
        parsed_date = date
        parsed_time = str(round(float(time)))

    return parsed_date + parsed_time

def collect_date_time_from_file_name(file_name):
    date_time_string = re.search(r"(?!\_)[0-9]{14}(?=\_)", file_name)
    if date_time_string:
        date = date_time_string[0][0:8]
        time = date_time_string[0][8:]
    else:
        raise Exception(f"Unable to parse date_time string from filename: {file_name}")

    return date, time

class Dcm2niix4PET:
    def __init__(self, image_folder, destination_path, metadata_path=None,
                 metadata_translation_script=None, additional_arguments=None, file_format=''):
        """
        :param image_folder:
        :param destination_path:
        :param metadata_path:
        :param metadata_translation_script:
        :param file_format:
        :param additional_arguments:
        """

        self.image_folder = Path(image_folder)
        self.destination_path =  Path(destination_path)
        if metadata_path is not None and metadata_translation_path is not None:
            self.metadata_path =  Path(metadata_path)
            self.metadata_translation_script = Path(metadata_path)
        self.subject_id = None
        self.file_format = file_format
        self.dicom_headers = {}


    @staticmethod
    def check_for_dcm2niix():
        """
        Just checks for dcm2niix using the system shell, returns 0 if dcm2niix is present.
        :return: status code of the command dcm2niix
        """
        check = subprocess.run("dcm2niix -h", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if check.returncode != 0:
            pkged = "https://github.com/rordenlab/dcm2niix/releases"
            instructions = "https://github.com/rordenlab/dcm2niix#install"
            raise Exception(f"""Dcm2niix does not appear to be installed. Installation instructions can be found here 
                   {instructions} and packaged versions can be found at {pkged}""")

        return check.returncode

    def extract_dicom_headers(self, additional_fields=[], depth=1):
        """
        Opening up files till a dicom is located, then extracting any header information
        to be used during and after the conversion process. This includes patient/subject id,
        as well any additional frame or metadata that's required for conversion.
        :return: dicom header information to self.subject_id and/or self.dicom_header_data
        """
        n = 0
        for root, dirs, files in walk(self.image_folder):
            for f in files:
                if n >= depth:
                    break
                try:
                    dicom_path = Path(join(root, f))
                    dicom_header = pydicom.dcmread(dicom_path, stop_before_pixels=True)
                    # collect subject/patient id if none is supplied
                    if self.subject_id is None:
                        self.subject_id = dicom_header.PatientID

                    self.dicom_headers[dicom_path.name] = dicom_header

                except pydicom.errors.InvalidDicomError:
                    pass
                n += 1

    def run_dcm2niix(self):
        if self.file_format:
            file_format_args = f"-f {self.file_format}"
        else:
            file_format_args = ""
        with TemporaryDirectory() as tempdir:
            tempdir_pathlike = Path(tempdir)

            convert = subprocess.run(f"dcm2niix -w 1 -z y {file_format_args} -o {tempdir_pathlike} {self.image_folder}", shell=True,
                                     capture_output=True)

            if convert.returncode != 0 and bytes("Skipping existing file name", "utf-8") not in convert.stdout or convert.stderr:
                print(convert.stderr)
                raise Exception("Error during image conversion from dcm to nii!")

            # collect contents of the tempdir
            files_created_by_dcm2niix = [join(tempdir_pathlike, file) for file in listdir(tempdir_pathlike)]

            # make sure destination path exists if not try creating it.
            if self.destination_path.exists():
                pass
            else:
                makedirs(self.destination_path)

            for created in files_created_by_dcm2niix:
                created_path = Path(created)
                new_path = Path(join(self.destination_path, created_path.name))
                shutil.move(src=created, dst=new_path)




if __name__ == "__main__":
    print("hello")
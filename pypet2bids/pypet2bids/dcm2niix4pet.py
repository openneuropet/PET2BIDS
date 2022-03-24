from json_maj.main import JsonMAJ, load_json_or_dict
import importlib.util
import subprocess
import pandas as pd
import sys
from os.path import isdir, isfile, join, commonprefix
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
metadata_jsons = \
    [Path(join(metadata_folder, metadata_json)) for metadata_json in listdir(metadata_folder) if '.json' in metadata_json]

# create a dictionary to house the PET metadata files
metadata_dictionaries = {}

for metadata_json in metadata_jsons:
    try:
        with open(metadata_json, 'r') as infile:
            dictionary = json.load(infile)

        metadata_dictionaries[metadata_json.name] = dictionary
    except FileNotFoundError as err:
        raise err(f"Missing pet metadata files in {metadata_folder}, unable to validate metadata.")


def check_json(path_to_json, items_to_check=metadata_dictionaries['PET_metadata.json'], silent=False):
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
    :return: dictionary of items existence and value state, if key is True/False there exists/(does not exist) a
    corresponding entry in the json the same can be said of value.
    {
        'Units': {'key': False, 'value': False},
        'TracerName': {'key': False, 'value': False},
        'TracerRadionuclide': {'key': False, 'value': False},
        'InjectedRadioactivity': {'key': False, 'value': False}
    }
    """
    # check if path exists
    path_to_json = Path(path_to_json)
    if not path_to_json.exists():
        raise FileNotFoundError(path_to_json)

    # open the json
    with open(path_to_json, 'r') as infile:
        json_to_check = json.load(infile)

    # initalize warning colors and warning storage dictionary
    storage = {}
    warning_color = {'mandatory': 'red',
                     'recommended': 'yellow',
                     'optional:': 'blue'}

    for requirement in items_to_check.keys():
        color = warning_color.get(requirement, 'yellow')
        for item in items_to_check[requirement]:
            if item in json_to_check.keys() and json_to_check.get(item, None):
                # this json has both the key and a non blank value do nothing
                pass
            elif item in json_to_check.keys() and not json_to_check.get(item, None):
                if not silent:
                    print(colored(f"WARNING {item} present but has null value.", "yellow"))
                storage[item] = {'key': True, 'value': False}
            else:
                if not silent:
                    print(colored(f"WARNING!!!! {item} is not present in {path_to_json}. This will have to be corrected "
                                f"post conversion.", color))
                storage[item]  = {'key': False, 'value': False}

    return storage

def update_json_with_dicom_value(
        path_to_json,
        missing_values,
        dicom_header,
        dicom2bids_json=metadata_dictionaries['dicom2bids.json']):
    """
    We go through all of the missing values or keys that we find in the sidecar json and attempt to extract those
    missing entities from the dicom source. This function relies on many heuristics a.k.a. many unique conditionals and
    simply is what it is, hate the game not the player.
    :param path_to_json: path to the sidecar json to check
    :param missing_values: dictionary output from check_json indicating missing fields and/or values
    :param dicom: the dicom or dicoms that may contain information not picked up by dcm2niix
    :return: a dictionary of sucessfully updated (written to the json file) fields and values
    """
    # Units gets written as Unit in older versions of dcm2niix here we check for missing Units and present Unit entity
    units = missing_values.get('Units', None)
    if units:
        try:
            # Units is missing, check to see if Unit is present
            sidecar_json = load_json_or_dict(str(path_to_json))
            if sidecar_json.get('Unit', None):
                temp = JsonMAJ(path_to_json, {'Units': sidecar_json.get('Unit')})
                temp.remove('Unit')
            else: # we source the Units value from the dicom header and update the json
                JsonMAJ(path_to_json, {'Units': dicom_header.Units})
        except AttributeError:
            print(f"Dicom is missing Unit(s) field, are you sure this is a PET dicom?")
    # pair up dicom fields with bids sidecar json field, we do this in a separate json file
    # it's loaded when this script is run and stored in metadata dictionaries
    dcmfields = metadata_dictionaries['dicom2bids.json']['dcmfields']
    jsonfields = metadata_dictionaries['dicom2bids.json']['jsonfields']

    special_cases = ["ReconstructionMethod", "ConvolutionKernel"]

    # strip excess characters from dcmfields
    dcmfields = [re.sub('[^0-9a-zA-Z]+', '', field) for field in dcmfields]
    paired_fields = {}
    for index, field in enumerate(jsonfields):
        paired_fields[field] = dcmfields[index]

    print("Attempting to locate missing BIDS fields in dicom header")
    # go through missing fields and reach into dicom to pull out values
    for key, value in paired_fields.items():
        missing_bids_field = missing_values.get(key, None)
        # if field is missing look into dicom
        if missing_bids_field:
            # there are a few special cases that require regex splitting of the dicom entries
            # into several bids sidecar entities
            try:
                dicom_field = getattr(dicom_header, value)
                print(f"FOUND {value} corresponding to BIDS {key}: {dicom_field}")
            except AttributeError:
                dicom_field = None
                print(f"NOT FOUND {value} corresponding to BIDS {key} in dicom header.")

            if dicom_field and value in special_cases:
                    pass # do regex magic
            elif dicom_field:
                # update json
                temp = JsonMAJ(json_path=path_to_json, update_values={key: dicom_field})
                temp.update()


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
    """
    Collects the date and time from a nifti or a json produced by dcm2niix when dcm2niix is run with the options
    %p_%i_%t_%s. This datetime us used to match a dicom header object to the resultant file. E.G. if there are missing
    BIDS fields in the json produced by dcm2niix it's hopeful that the dicom header may contain the missing info.
    :param file_name: name of the file to extract the date time info from, this should be a json ouput file from
    dcm2niix
    :return: a date and time object
    """
    date_time_string = re.search(r"(?!\_)[0-9]{14}(?=\_)", file_name)
    if date_time_string:
        date = date_time_string[0][0:8]
        time = date_time_string[0][8:]
    else:
        raise Exception(f"Unable to parse date_time string from filename: {file_name}")

    return date, time


class Dcm2niix4PET:
    def __init__(self, image_folder, destination_path, metadata_path=None,
                 metadata_translation_script=None, additional_arguments=None, file_format='%p_%i_%t_%s',
                 silent=False):
        """
        This class is a simple wrapper for dcm2niix and contains methods to do the following in order:
            - Convert a set of dicoms into .nii and .json sidecar files
            - Inspect the .json sidecar files for any missing BIDS PET fields or values
            - If there are missing BIDS PET fields or values this class will attempt to extract them from the dicom
            header, a metadata file using a metadata translation script, and lastly from user supplied key pair
            arguments.

        # class is instantiated:
        converter = Dcm2niix4PET(...)
        # then conversion is run by calling run_dcm2niix
        converter.run_dcm2niix()

        Conversion is performed in a temporary directory to make matching dicom headers to dcm2niix output files easier
        (and to avoid leaving intermediary files persisting on disc). After which, these files are then moved the
        destination directory.

        :param image_folder: folder containing a single series/session of dicoms
        :param destination_path: destination path for dcm2niix output nii and json files
        :param metadata_path: path to excel, csv, or text file with PET metadata (radioligand, blood, etc etc)
        :param metadata_translation_script: python file to extract and transform data contained in the metadata_path
        :param file_format: the file format that we want dcm2niix to use, by default %p_%i_%t_%s
        %p ->
        %i ->
        %t ->
        %s ->
        :param additional_arguments: user supplied key value pairs, E.g. TimeZero=12:12:12, InjectedRadioactivity=1
        this key value pair will overwrite any fields in the dcm2niix produced nifti sidecar.json as it is assumed that
        the user knows more about converting their data than the heuristics within dcm2niix, this library, or even the
        dicom header
        :param silent: silence missing sidecar metadata messages, default is False and very verbose
        """

        # check to see if dcm2niix is installed
        self.check_for_dcm2niix()

        self.image_folder = Path(image_folder)
        self.destination_path =  Path(destination_path)
        if metadata_path is not None and metadata_translation_path is not None:
            self.metadata_path =  Path(metadata_path)
            self.metadata_translation_script = Path(metadata_path)
        self.subject_id = None
        self.file_format = file_format
        self.dicom_headers = {}
        # we may want to include additional information to the sidecar, tsv, or json files generated after conversion
        # this variable stores the mapping between output files and a single dicom header used to generate those files
        # to access the dicom header information use the key in self.headers_to_files to access that specific header
        # in self.dicom_headers
        self.headers_to_files = {}
        # if silent is set to True output warnings aren't displayed to stdout/stderr
        self.silent = silent


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

            if convert.returncode != 0:
                print("Check output .nii files, dcm2iix returned these errors during conversion:")
                if bytes("Skipping existing file name", "utf-8") not in convert.stdout or convert.stderr:
                    print(convert.stderr)
                elif convert.returncode != 0 and bytes("Error: Check sorted order", "utf-8") in convert.stdout or convert.stderr:
                    print("Possible error with frame order, is this a phillips dicom set?")
                    print(convert.stdout)
                    print(convert.sterr)

            # collect contents of the tempdir
            files_created_by_dcm2niix = [join(tempdir_pathlike, file) for file in listdir(tempdir_pathlike)]

            # make sure destination path exists if not try creating it.
            if self.destination_path.exists():
                pass
            else:
                makedirs(self.destination_path)

            # iterate through created files to supplement sidecar jsons
            for created in files_created_by_dcm2niix:
                created_path = Path(created)
                if created_path.suffix == '.json':
                    # we want to pair up the headers to the files created in the output directory in case
                    # dcm2niix has created files from multiple sessions
                    matched_dicoms_and_headers = self.match_dicom_header_to_file(destination_path=tempdir_pathlike)

                    # we check to see what's missing from our recommended and required jsons by gathering the
                    # output of check_json silently
                    check_for_missing = check_json(created_path, silent=True)

                    # we do our best to extrat information from the dicom header and insert theses values
                    # into the sidecar json

                    # first do a reverse lookup of the key the json corresponds to
                    lookup = [key for key, value in matched_dicoms_and_headers.items() if str(created_path) in value]
                    if lookup:
                        dicom_header = self.dicom_headers[lookup[0]]

                        update_json_with_dicom_value(
                            created_path,
                            check_for_missing,
                            dicom_header,
                            dicom2bids_json=metadata_dictionaries['dicom2bids.json'])

                    # next we check to see if any of the additional user supplied arguments (kwargs) correspond to
                    # any of the missing tags in our sidecars


                new_path = Path(join(self.destination_path, created_path.name))
                shutil.move(src=created, dst=new_path)


    def match_dicom_header_to_file(self, destination_path=None):
        if not destination_path:
            destination_path = self.destination_path
        # first collect all of the files in the output directory
        output_files = [join(destination_path, output_file) for output_file in listdir(destination_path)]

        # create empty dictionary to store pairings
        headers_to_files = {}

        # collect study date and time from header
        for each in self.dicom_headers:
            header_study_date = self.dicom_headers[each].StudyDate
            header_acquisition_time = self.dicom_headers[each].StudyTime

            header_date_time = dicom_datetime_to_dcm2niix_time(date=header_study_date, time=header_acquisition_time)

            for output_file in output_files:
                if header_date_time in output_file:
                    try:
                        headers_to_files[each].append(output_file)
                    except KeyError:
                        headers_to_files[each] = [output_file]
        return headers_to_files

if __name__ == "__main__":
    pass
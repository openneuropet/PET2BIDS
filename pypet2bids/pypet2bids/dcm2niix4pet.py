import os
import sys
import warnings

from json_maj.main import JsonMAJ, load_json_or_dict
from pypet2bids.helper_functions import ParseKwargs, get_version, translate_metadata, expand_path
import subprocess
import pandas as pd
from os.path import join
from os import listdir, walk, makedirs
from pathlib import Path
import json
import pydicom
import re
from tempfile import TemporaryDirectory
import shutil
from dateutil import parser
from termcolor import colored
import argparse
import importlib



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

try:
    # collect metadata jsons in dev mode
    metadata_jsons = \
        [Path(join(metadata_folder, metadata_json)) for metadata_json
         in listdir(metadata_folder) if '.json' in metadata_json]
except FileNotFoundError:
    metadata_jsons = \
        [Path(join(module_folder, 'metadata', metadata_json)) for metadata_json
         in listdir(join(module_folder, 'metadata')) if '.json' in metadata_json]

# create a dictionary to house the PET metadata files
metadata_dictionaries = {}

for metadata_json in metadata_jsons:
    try:
        with open(metadata_json, 'r') as infile:
            dictionary = json.load(infile)

        metadata_dictionaries[metadata_json.name] = dictionary
    except FileNotFoundError as err:
        raise Exception(f"Missing pet metadata file {metadata_json} in {metadata_folder}, unable to validate metadata.")
    except json.decoder.JSONDecodeError as err:
        raise IOError(f"Unable to read from {metadata_json}")


def check_json(path_to_json, items_to_check=None, silent=False):
    """
    This method opens a json and checks to see if a set of mandatory values is present within that json, optionally it
    also checks for recommended key value pairs. If fields are not present a warning is raised to the user.

    :param path_to_json: path to a json file e.g. a BIDS sidecar file created after running dcm2niix
    :param items_to_check: a dictionary with items to check for within that json. If None is supplied defaults to the
           PET_metadata.json contained in this repository
    :param silent: Raises warnings or errors to stdout if this flag is set to True
    :return: dictionary of items existence and value state, if key is True/False there exists/(does not exist) a
            corresponding entry in the json the same can be said of value
    """

    # check if path exists
    path_to_json = Path(path_to_json)
    if not path_to_json.exists():
        raise FileNotFoundError(path_to_json)

    # check for default argument for dictionary of items to check
    if items_to_check is None:
        items_to_check = metadata_dictionaries['PET_metadata.json']

    # open the json
    with open(path_to_json, 'r') as in_file:
        json_to_check = json.load(in_file)

    # initialize warning colors and warning storage dictionary
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
                    print(colored(f"WARNING!!!! {item} is not present in {path_to_json}. This will have to be "
                                  f"corrected post conversion.", color))
                storage[item] = {'key': False, 'value': False}

    return storage


def update_json_with_dicom_value(
        path_to_json,
        missing_values,
        dicom_header,
        dicom2bids_json=None
):
    """
    We go through all of the missing values or keys that we find in the sidecar json and attempt to extract those
    missing entities from the dicom source. This function relies on many heuristics a.k.a. many unique conditionals and
    simply is what it is, hate the game not the player.

    :param path_to_json: path to the sidecar json to check
    :param missing_values: dictionary output from check_json indicating missing fields and/or values
    :param dicom_header: the dicom or dicoms that may contain information not picked up by dcm2niix
    :param dicom2bids_json: a json file that maps dicom header entities to their corresponding BIDS entities
    :return: a dictionary of sucessfully updated (written to the json file) fields and values
    """

    # load the sidecar json
    sidecar_json = load_json_or_dict(str(path_to_json))

    # purely to clean up the generated read the docs page from sphinx, otherwise the entire json appears in the
    # read the docs page.
    if dicom2bids_json is None:
        dicom2bids_json = metadata_dictionaries['dicom2bids.json']

    # Units gets written as Unit in older versions of dcm2niix here we check for missing Units and present Unit entity
    units = missing_values.get('Units', None)
    if units:
        try:
            # Units is missing, check to see if Unit is present
            if sidecar_json.get('Unit', None):
                temp = JsonMAJ(path_to_json, {'Units': sidecar_json.get('Unit')})
                temp.remove('Unit')
            else:  # we source the Units value from the dicom header and update the json
                JsonMAJ(path_to_json, {'Units': dicom_header.Units})
        except AttributeError:
            print(f"Dicom is missing Unit(s) field, are you sure this is a PET dicom?")
    # pair up dicom fields with bids sidecar json field, we do this in a separate json file
    # it's loaded when this script is run and stored in metadata dictionaries
    dcmfields = dicom2bids_json['dcmfields']
    jsonfields = dicom2bids_json['jsonfields']

    regex_cases = ["ReconstructionMethod", "ConvolutionKernel"]

    # strip excess characters from dcmfields
    dcmfields = [re.sub('[^0-9a-zA-Z]+', '', field) for field in dcmfields]
    paired_fields = {}
    for index, field in enumerate(jsonfields):
        paired_fields[field] = dcmfields[index]

    print("Attempting to locate missing BIDS fields in dicom header")
    # go through missing fields and reach into dicom to pull out values
    json_updater = JsonMAJ(json_path=path_to_json)
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

            if dicom_field and value in regex_cases:
                # if it exists get rid of it, we don't want no part of it.
                if sidecar_json.get('ReconMethodName', None):
                    json_updater.remove('ReconstructionMethod')
                if dicom_header.get('ReconstructionMethod', None):
                    reconstruction_method = dicom_header.ReconstructionMethod
                    json_updater.remove('ReconstructionMethod')
                    reconstruction_method = get_recon_method(reconstruction_method)
                    json_updater.update(reconstruction_method)

                # TODO Convolution Kernel
            elif dicom_field:
                # update json
                json_updater.update({key: dicom_field})

    # Additional Heuristics are included below

    # See if time zero is missing in json
    if missing_values.get('TimeZero')['key'] is False or missing_values.get('TimeZero')['value'] is False:
        time_parser = parser
        acquisition_time = time_parser.parse(dicom_header['AcquisitionTime'].value).time().isoformat()
        json_updater.update({'TimeZero': acquisition_time})
        json_updater.remove('AcquisitionTime')
        json_updater.update({'ScanStart': 0})

    else:
        pass

    if missing_values.get('ScanStart')['key'] is False or missing_values.get('ScanStart')['value'] is False:
        json_updater.update({'ScanStart': 0})

    if missing_values.get('InjectionStart')['key'] is False or missing_values.get('InjectionStart')['value'] is False:
        json_updater.update({'InjectionTime': 0})

    # check to see if units are BQML
    json_updater = JsonMAJ(str(path_to_json))
    if json_updater.get('Units') == 'BQML':
        json_updater.update({'Units': 'Bq/mL'})

    # Add radionuclide to json
    Radionuclide = get_radionuclide(dicom_header)
    if Radionuclide:
        json_updater.update({'TracerRadionuclide': Radionuclide})
    print("PAUSE")


def dicom_datetime_to_dcm2niix_time(dicom=None, date='', time=''):
    """
    Dcm2niix provides the option of outputing the scan data and time into the .nii and .json filename at the time of
    conversion if '%t' is provided following the '-f' flag. The result is the addition of a date time string of the
    format. This function similarly generates the same datetime string from a dicom header.

    :param dicom: pydicom.dataset.FileDataset object or a path to a dicom
    :param date: a given date, used in conjunction with time to supply a date time
    :param time: a given time, used in conjunction with date

    :return: a datetime string that corresponds to the converted filenames from dcm2niix when used with the `-f %t` flag
    """
    if dicom:
        if type(dicom) is pydicom.dataset.FileDataset:
            # do nothing
            pass
        elif type(dicom) is str:
            try:
                dicom_path = Path(dicom)
                dicom = pydicom.dcmread(dicom_path)
            except TypeError:
                raise TypeError(f"dicom {dicom} must be either a pydicom.dataset.FileDataSet object or a "
                                f"valid path to a dicom file")

        parsed_date = dicom.StudyDate
        parsed_time = str(round(float(dicom.StudyTime)))
        if len(parsed_time) < 6:
            zeros_to_pad = 6 - len(parsed_time)
            parsed_time = zeros_to_pad * '0' + parsed_time

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
    date_time_string = re.search(r'(?!\_)[0-9]{14}(?=\_)', file_name)
    if date_time_string:
        date = date_time_string[0][0:8]
        time = date_time_string[0][8:]
    else:
        raise Exception(f"Unable to parse date_time string from filename: {file_name}")

    return date, time


class Dcm2niix4PET:
    def __init__(self, image_folder, destination_path=None, metadata_path=None,
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
        %p -> protocol
        %i -> ID of patient
        %t -> time
        %s -> series number
        :param additional_arguments: user supplied key value pairs, E.g. TimeZero=12:12:12, InjectedRadioactivity=1
        this key value pair will overwrite any fields in the dcm2niix produced nifti sidecar.json as it is assumed that
        the user knows more about converting their data than the heuristics within dcm2niix, this library, or even the
        dicom header
        :param silent: silence missing sidecar metadata messages, default is False and very verbose
        """

        # check to see if dcm2niix is installed
        self.blood_json = None
        self.blood_tsv = None
        self.check_for_dcm2niix()

        self.image_folder = Path(image_folder)
        if destination_path:
            self.destination_path = Path(destination_path)
        else:
            self.destination_path = self.image_folder

        self.subject_id = None
        self.dicom_headers = self.extract_dicom_headers()

        self.spreadsheet_metadata = {}
        # if there's a spreadsheet and if there's a provided python script use it to manipulate the data in the
        # spreadsheet
        if metadata_path and metadata_translation_script:
            self.metadata_path = Path(metadata_path)
            self.metadata_translation_script = Path(metadata_translation_script)

            if self.metadata_path.exists() and self.metadata_translation_script.exists():
                # load the spreadsheet into a dataframe
                self.extract_metadata()
                # next we use the loaded python script to extract the information we need
                self.load_spread_sheet_data()

        self.additional_arguments = additional_arguments
        self.file_format = file_format
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

        :return: status code of the command dcm2niix -h
        """
        check = subprocess.run("dcm2niix -h", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if check.returncode != 0:
            pkged = "https://github.com/rordenlab/dcm2niix/releases"
            instructions = "https://github.com/rordenlab/dcm2niix#install"
            raise Exception(f"""Dcm2niix does not appear to be installed. Installation instructions can be found here 
                   {instructions} and packaged versions can be found at {pkged}""")

        return check.returncode

    def extract_dicom_headers(self, depth=1):
        """
        Opening up files till a dicom is located, then extracting any header information
        to be used during and after the conversion process. This includes patient/subject id,
        as well any additional frame or metadata that's required for conversion.

        :param depth: the number of dicoms to collect per folder, defaults to 1 as it assumes a single sessions worth of
                     dicoms is included per folder.
        :return: dicom header information to self.subject_id and/or self.dicom_header_data
        """
        n = 0
        dicom_headers = {}
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

                    dicom_headers[dicom_path.name] = dicom_header

                except pydicom.errors.InvalidDicomError:
                    pass
                n += 1

        return dicom_headers

    def run_dcm2niix(self):
        """
        This runs dcm2niix and uses the other methods within this class to supplement the sidecar json's produced as
        dcm2niix output.

        :return: the path to the output of dcm2niix and the modified sidecar jsons
        """
        if self.file_format:
            file_format_args = f"-f {self.file_format}"
        else:
            file_format_args = ""
        with TemporaryDirectory() as tempdir:
            tempdir_pathlike = Path(tempdir)

            convert = subprocess.run(f"dcm2niix -w 1 -z y {file_format_args} -o {tempdir_pathlike} {self.image_folder}",
                                     shell=True,
                                     capture_output=True)

            if convert.returncode != 0:
                print("Check output .nii files, dcm2iix returned these errors during conversion:")
                if bytes("Skipping existing file name", "utf-8") not in convert.stdout or convert.stderr:
                    print(convert.stderr)
                elif convert.returncode != 0 and bytes("Error: Check sorted order",
                                                       "utf-8") in convert.stdout or convert.stderr:
                    print("Possible error with frame order, is this a phillips dicom set?")
                    print(convert.stdout)
                    print(convert.stderr)

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

                    # if we have entities in our metadata spreadsheet that we've used we update
                    if self.spreadsheet_metadata.get('nifti_json', None):
                        update_json = JsonMAJ(json_path=str(created),
                                              update_values=self.spreadsheet_metadata['nifti_json'])
                        update_json.update()

                    # next we check to see if any of the additional user supplied arguments (kwargs) correspond to
                    # any of the missing tags in our sidecars
                    if self.additional_arguments:
                        update_json = JsonMAJ(json_path=str(created),
                                              update_values=self.additional_arguments)
                        update_json.update()

                    # there are some additional updates that depend on some PET BIDS logic that we do next, since these
                    # updates depend on both information provided via the sidecar json and/or information provided via
                    # additional arguments we run this step after updating the sidecar with those additional user
                    # arguments

                    sidecar_json = JsonMAJ(json_path=str(created))  # load all supplied and now written sidecar data in

                    check_metadata_radio_inputs = check_meta_radio_inputs(sidecar_json.json_data)  # run logic

                    sidecar_json.update(check_metadata_radio_inputs)  # update sidecar json with results of logic

                    # tag json with additional conversion software
                    conversion_software = sidecar_json.get('ConversionSoftware')
                    conversion_software_version = sidecar_json.get('ConversionSoftwareVersion')

                    sidecar_json.update({'ConversionSoftware': [conversion_software, 'pypet2bids']})
                    sidecar_json.update({'ConversionSoftwareVersion': [conversion_software_version, get_version()]})

                new_path = Path(join(self.destination_path, created_path.name))
                shutil.move(src=created, dst=new_path)

            return self.destination_path

    def post_dcm2niix(self):
        with TemporaryDirectory() as temp_dir:
            tempdir_path = Path(temp_dir)
            if self.subject_id != list(self.dicom_headers.values())[0].PatientID:
                blood_file_name_w_out_extension = "sub-" + self.subject_id + "_blood"
            elif self.dicom_headers:
                # collect date and time and series number from dicom
                first_dicom = list(self.dicom_headers.values())[0]
                date_time = dicom_datetime_to_dcm2niix_time(first_dicom)
                series_number = str(first_dicom.SeriesNumber)
                protocol_name = str(first_dicom.SeriesDescription).replace(" ", "_")
                blood_file_name_w_out_extension = protocol_name + '_' + self.subject_id + '_' + date_time + '_' + \
                                                  series_number + "_blood"

            if self.spreadsheet_metadata.get('blood_tsv', None) is not None:
                blood_tsv_data = self.spreadsheet_metadata.get('blood_tsv')
                if type(blood_tsv_data) is pd.DataFrame:
                    # write out blood_tsv using pandas csv write
                        blood_tsv_data.to_csv(join(tempdir_path, blood_file_name_w_out_extension + ".tsv")
                                              , sep='\t',
                                              index=False)
                elif type(blood_tsv_data) is str:
                    # write out with write
                    with open(join(tempdir_path, blood_file_name_w_out_extension + ".tsv"), 'w') as outfile:
                        outfile.writelines(blood_tsv_data)
                else:
                    raise (f"blood_tsv dictionary is incorrect type {type(blood_tsv_data)}, must be type: "
                           f"pandas.DataFrame or str\nCheck return type of {translate_metadata} in "
                           f"{self.metadata_translation_script}")
            if self.spreadsheet_metadata.get('blood_json', {}) != {}:
                blood_json_data = self.spreadsheet_metadata.get('blood_json')
                if type(blood_json_data) is dict:
                    # write out to file with json dump
                    pass
                elif type(blood_json_data) is str:
                    # write out to file with json dumps
                    blood_json_data = json.loads(blood_json_data)
                else:
                    raise (f"blood_json dictionary is incorrect type {type(blood_json_data)}, must be type: dict or str"
                           f"pandas.DataFrame or str\nCheck return type of {translate_metadata} in "
                           f"{self.metadata_translation_script}")

                with open(join(tempdir_path, blood_file_name_w_out_extension + '.json'), 'w') as outfile:
                    json.dump(blood_json_data, outfile, indent=4)

            blood_files = [join(str(tempdir_path), blood_file) for blood_file in os.listdir(str(tempdir_path))]
            for blood_file in blood_files:
                shutil.move(blood_file, join(self.destination_path, os.path.basename(blood_file)))

    def convert(self):
        self.run_dcm2niix()
        self.post_dcm2niix()

    def match_dicom_header_to_file(self, destination_path=None):
        """
        Matches a dicom header to a nifti or json file produced by dcm2niix, this is run after dcm2niix converts the
        input dicoms into nifti's and json's.

        :param destination_path: the path dcm2niix generated files are placed at, collected during class instantiation

        :return: a dictionary of headers matched to nifti and json file names
        """
        if not destination_path:
            destination_path = self.destination_path
        # first collect all of the files in the output directory
        output_files = [join(destination_path, output_file) for output_file in listdir(destination_path)]

        # create empty dictionary to store pairings
        headers_to_files = {}

        # collect study date and time from header
        for each in self.dicom_headers:
            header_study_date = self.dicom_headers[each].StudyDate
            header_acquisition_time = str(round(float(self.dicom_headers[each].StudyTime)))
            if len(header_acquisition_time) < 6:
                header_acquisition_time = (6 - len(header_acquisition_time)) * "0" + header_acquisition_time

            header_date_time = dicom_datetime_to_dcm2niix_time(date=header_study_date, time=header_acquisition_time)

            for output_file in output_files:
                if header_date_time in output_file:
                    try:
                        headers_to_files[each].append(output_file)
                    except KeyError:
                        headers_to_files[each] = [output_file]
        return headers_to_files

    def extract_metadata(self):
        """
        Opens up a metadata file and reads it into a pandas dataframe
        :return: a pd dataframe object
        """
        # collect metadata from spreadsheet
        metadata_extension = Path(self.metadata_path).suffix
        self.open_meta_data(metadata_extension)

    def open_meta_data(self, extension):
        """
        Opens a text metadata file with the pandas method most appropriate for doing so based on the metadata
        file's extension.
        :param extension: The extension of the file
        :return: a pandas dataframe representation of the spreadsheet/metadatafile
        """
        methods = {
            'excel': pd.read_excel,
            'csv': pd.read_csv
        }

        if 'xls' in extension:
            proper_method = 'excel'
        else:
            proper_method = extension

        try:
            use_me_to_read = methods.get(proper_method, None)
            self.metadata_dataframe = use_me_to_read(self.metadata_path)
        except IOError as err:
            raise err(f"Problem opening {self.metadata_path}")

    def load_spread_sheet_data(self):
        text_file_data = {}
        if self.metadata_translation_script:
            try:
                # this is where the goofiness happens, we allow the user to create their own custom script to manipulate
                # data from their particular spreadsheet wherever that file is located.
                spec = importlib.util.spec_from_file_location("metadata_translation_script",
                                                              self.metadata_translation_script)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                text_file_data = module.translate_metadata(self.metadata_dataframe)
            except AttributeError as err:
                print(f"Unable to locate metadata_translation_script")

            self.spreadsheet_metadata['blood_tsv'] = text_file_data.get('blood_tsv', {})
            self.spreadsheet_metadata['blood_json'] = text_file_data.get('blood_json', {})
            self.spreadsheet_metadata['nifti_json'] = text_file_data.get('nifti_json', {})


# noinspection PyPep8Naming
def get_recon_method(ReconstructionMethodString: str) -> dict:
    """
    Given the reconstruction method from a dicom header this function does its best to determine the name of the
    reconstruction, the number of iterations used in the reconstruction, and the number of subsets in the
    reconstruction.

    :param ReconstructionMethodString:
    :return: dictionary containing PET BIDS fields ReconMethodName, ReconMethodParameterUnits,
        ReconMethodParameterLabels, and ReconMethodParameterValues

    """
    contents = ReconstructionMethodString
    subsets = None
    iterations = None
    ReconMethodParameterUnits = ["none", "none"]
    ReconMethodParameterLabels = ["subsets", "iterations"]

    # determine order of recon iterations and subsets, this is not  a surefire way to determine this...
    iter_sub_combos = {
        'iter_first': [r'\d\di\ds', r'\d\di\d\ds', r'\di\ds', r'\di\d\ds',
                       r'i\d\ds\d', r'i\d\ds\d\d', r'i\ds\d', r'i\ds\d\d'],
        'sub_first': [r'\d\ds\di', r'\d\ds\d\di', r'\ds\di', r'\ds\d\di',
                      r's\d\di\d', r's\d\di\d\d', r's\di\d', r's\di\d\d'],
    }

    iter_sub_combos['iter_first'] = [re.compile(regex) for regex in iter_sub_combos['iter_first']]
    iter_sub_combos['sub_first'] = [re.compile(regex) for regex in iter_sub_combos['sub_first']]
    order = None
    possible_iter_sub_strings = []
    iteration_subset_string = None
    # run through possible combinations of iteration substitution strings in iter_sub_combos
    for key, value in iter_sub_combos.items():
        for expression in value:
            iteration_subset_string = expression.search(contents)
            if iteration_subset_string:
                order = key
                iteration_subset_string = iteration_subset_string[0]
                possible_iter_sub_strings.append(iteration_subset_string)
    # if matches get ready to pick one
    if possible_iter_sub_strings:
        # sorting matches by string length as our method can return more than one match e.g. 3i21s will return
        # 3i21s and 3i1s or something similar
        possible_iter_sub_strings.sort(key=len)
        # picking the longest match as it's most likely the correct one
        iteration_subset_string = possible_iter_sub_strings[-1]

    # after we've captured the subsets and iterations we next need to separate them out from each other
    if iteration_subset_string and order:
        #  remove all chars replace with spaces
        just_digits = re.sub(r'[a-zA-Z]', " ", iteration_subset_string)
        just_digits = just_digits.strip()
        # split up subsets and iterations
        just_digits = just_digits.split(" ")
        # assign digits to either subsets or iterations based on order information obtained earlier
        if order == 'iter_first' and len(just_digits) == 2:
            iterations = int(just_digits[0])
            subsets = int(just_digits[1])
        elif len(just_digits) == 2:
            iterations = int(just_digits[1])
            subsets = int(just_digits[0])
        else:
            # if we don't have both we decide that we don't have either, flawed but works for the samples in
            # test_dcm2niix4pet.py may. Will be updated when non-conforming data is obtained
            pass  # do nothing, this case shouldn't fire.....

    if iteration_subset_string:
        ReconMethodName = re.sub(iteration_subset_string, "", contents)
    else:
        ReconMethodName = contents

    # cleaning up weird chars at end or start of name
    ReconMethodName = re.sub(r'[^a-zA-Z0-9]$', "", ReconMethodName)
    ReconMethodName = re.sub(r'^[^a-zA-Z0-9]', "", ReconMethodName)

    # get everything in front of \d\di or \di or \d\ds or \ds

    return {
        "ReconMethodName": ReconMethodName,
        "ReconMethodParameterUnits": ReconMethodParameterUnits,
        "ReconMethodParameterLabels": ReconMethodParameterLabels,
        "ReconMethodParameterValues": [subsets, iterations]
    }


def check_meta_radio_inputs(kwargs: dict) -> dict:
    InjectedRadioactivity = kwargs.get('InjectedRadioactivity', None)
    InjectedMass = kwargs.get("InjectedMass", None)
    SpecificRadioactivity = kwargs.get("SpecificRadioactivity", None)
    MolarActivity = kwargs.get("MolarActivity", None)
    MolecularWeight = kwargs.get("MolecularWeight", None)

    data_out = {}

    if InjectedRadioactivity and InjectedMass:
        data_out['InjectedRadioactivity'] = InjectedRadioactivity
        data_out['InjectedRadioactivityUnits'] = 'MBq'
        data_out['InjectedMass'] = InjectedMass
        data_out['InjectedMassUnits'] = 'ug'
        # check for strings where there shouldn't be strings
        numeric_check = [str(InjectedRadioactivity).isnumeric(), str(InjectedMass).isnumeric()]
        if False in numeric_check:
            data_out['InjectedMass'] = 'n/a'
            data_out['InjectedMassUnits'] = 'n/a'
        else:
            tmp = (InjectedRadioactivity*10**6)/(InjectedMass*10**6)
            if SpecificRadioactivity:
                if SpecificRadioactivity != tmp:
                    print(colored("WARNING inferred SpecificRadioactivity in Bq/g doesn't match InjectedRadioactivity "
                                  "and InjectedMass, could be a unit issue", "yellow"))
                data_out['SpecificRadioactivity'] = SpecificRadioactivity
                data_out['SpecificRadioactivityUnits'] = kwargs.get('SpecificRadioactivityUnityUnits', 'n/a')
            else:
                data_out['SpecificRadioactivity'] = tmp
                data_out['SpecificRadioactivityUnits'] = 'Bq/g'

    if InjectedRadioactivity and SpecificRadioactivity:
        data_out['InjectedRadioactivity'] = InjectedRadioactivity
        data_out['InjectedRadioactivityUnits'] = 'MBq'
        data_out['SpecificRadioactivity'] = SpecificRadioactivity
        data_out['SpecificRadioactivityUnits'] = 'Bq/g'
        numeric_check = [str(InjectedRadioactivity).isnumeric(), str(SpecificRadioactivity).isnumeric()]
        if False in numeric_check:
            data_out['InjectedMass'] = 'n/a'
            data_out['InjectedMassUnits'] = 'n/a'
        else:
            tmp = ((InjectedRadioactivity*10**6)/SpecificRadioactivity)*10**6
            if InjectedMass:
                if InjectedMass != tmp:
                    print(colored("WARNING Infered InjectedMass in ug doesn''t match InjectedRadioactivity and "
                                  "InjectedMass, could be a unit issue", "yellow"))
                data_out['InjectedMass'] = InjectedMass
                data_out['InjectedMassUnits'] = kwargs.get('InjectedMassUnits', 'n/a')
            else:
                data_out['InjectedMass'] = tmp
                data_out['InjectedMassUnits'] = 'ug'

    if InjectedMass and SpecificRadioactivity:
        data_out['InjectedMass'] = InjectedMass
        data_out['InjectedMassUnits'] = 'ug'
        data_out['SpecificRadioactivity'] = SpecificRadioactivity
        data_out['SpecificRadioactivityUnits'] = 'Bq/g'
        numeric_check = [str(SpecificRadioactivity).isnumeric(), str(InjectedMass).isnumeric()]
        if False in numeric_check:
            data_out['InjectedRadioactivity'] = 'n/a'
            data_out['InjectedRadioactivityUnits'] = 'n/a'
        else:
            tmp = ((InjectedMass / 10 ** 6) / SpecificRadioactivity) / 10 ** 6  # ((ug / 10 ^ 6) / Bq / g)/10 ^ 6 = MBq
            if InjectedRadioactivity:
                if InjectedRadioactivity != tmp:
                    print(colored("WARNING infered InjectedRadioactivity in MBq doesn't match SpecificRadioactivity "
                                  "and InjectedMass, could be a unit issue", "yellow"))
                data_out['InjectedRadioactivity'] = InjectedRadioactivity
                data_out['InjectedRadioactivityUnits'] = kwargs.get('InjectedRadioactivityUnits', 'n/a')
            else:
                data_out['InjectedRadioactivity'] = tmp
                data_out['InjectedRadioactivityUnits'] = 'MBq'

    if MolarActivity and MolecularWeight:
        data_out['MolarActivity'] = MolarActivity
        data_out['MolarActivityUnits'] = 'GBq/umol'
        data_out['MolecularWeight'] = MolecularWeight
        data_out['MolecularWeightUnits'] = 'g/mol'
        numeric_check = [str(MolarActivity).isnumeric(), str(MolecularWeight).isnumeric()]
        if False in numeric_check:
            data_out['SpecificRadioactivity'] = 'n/a'
            data_out['SpecificRadioactivityUnits'] = 'n/a'
        else:
            tmp = (MolarActivity * 10 ** 6) / (
                        MolecularWeight / 10 ** 6)  # (GBq / umol * 10 ^ 6) / (g / mol / * 10 ^ 6) = Bq / g
            if SpecificRadioactivity:
                if SpecificRadioactivity != tmp:
                    print(colored('infered SpecificRadioactivity in MBq/ug doesn''t match Molar Activity and Molecular '
                                  'Weight, could be a unit issue', 'yellow'))
                data_out['SpecificRadioactivity'] = SpecificRadioactivity
                data_out['SpecificRadioactivityUnits'] = kwargs.get('SpecificRadioactivityUnityUnits', 'n/a')
            else:
                data_out['SpecificRadioactivity'] = tmp
                data_out['SpecificRadioactivityUnits'] = 'Bq/g'

    if MolarActivity and SpecificRadioactivity:
        data_out['SpecificRadioactivity'] = SpecificRadioactivity
        data_out['SpecificRadioactivityUnits'] = 'MBq/ug'
        data_out['MolarActivity'] = MolarActivity
        data_out['MolarActivityUnits'] = 'GBq/umol'
        numeric_check = [str(SpecificRadioactivity).isnumeric(), str(MolarActivity).isnumeric()]
        if False in numeric_check:
            data_out['MolecularWeight'] = 'n/a'
            data_out['MolecularWeightUnits'] = 'n/a'
        else:
            tmp = (SpecificRadioactivity / 1000) / MolarActivity  # (MBq / ug / 1000) / (GBq / umol) = g / mol
            if MolecularWeight:
                if MolecularWeight != tmp:
                    print(colored("WARNING Infered MolecularWeight in MBq/ug doesn't match Molar Activity and "
                                  "Molecular Weight, could be a unit issue", 'yellow'))

                data_out['MolecularWeight'] = MolecularWeight
                data_out['MolecularWeightUnits'] = kwargs.get('MolecularWeightUnits', 'n/a')
            else:
                data_out.MolecularWeight = tmp
                data_out.MolecularWeightUnits = 'g/mol'

    if MolecularWeight and SpecificRadioactivity:
        data_out['SpecificRadioactivity'] = SpecificRadioactivity
        data_out['SpecificRadioactivityUnits'] = 'MBq/ug'
        data_out['MolecularWeight'] = MolarActivity
        data_out['MolecularWeightUnits'] = 'g/mol'
        numeric_check = [str(SpecificRadioactivity).isnumeric(), str(MolecularWeight).isnumeric()]
        if False in numeric_check:
            data_out['MolarActivity'] = 'n/a'
            data_out['MolarActivityUnits'] = 'n/a'
        else:
            tmp = MolecularWeight * (SpecificRadioactivity / 1000)  # g / mol * (MBq / ug / 1000) = GBq / umol
            if MolarActivity:
                if MolarActivity != tmp:
                    print(colored("WARNING infered MolarActivity in GBq/umol doesn''t match Specific Radioactivity and "
                                  "Molecular Weight, could be a unit issue", "yellow"))
                data_out['MolarActivity'] = MolarActivity
                data_out['MolarActivityUnits'] = kwargs.get('MolarActivityUnits', 'n/a')
            else:
                data_out['MolarActivity'] = tmp
                data_out['MolarActivityUnits'] = 'GBq/umol'

    return data_out


def get_radionuclide(pydicom_dicom):
    """
    Gets the radionuclide if given a pydicom_object if
    pydicom_object.RadiopharmaceuticalInformationSequence[0].RadionuclideCodeSequence exists

    :param pydicom_dicom: dicom object collected by pydicom.dcmread("dicom_file.img")
    :return: Labeled Radionuclide e.g. 11Carbon, 18Flourine
    """
    try:
        radiopharmaceutical_information_sequence = pydicom_dicom.RadiopharmaceuticalInformationSequence
        radionuclide_code_sequence = radiopharmaceutical_information_sequence[0].RadionuclideCodeSequence
        code_value = radionuclide_code_sequence[0].CodeValue
        code_meaning = radionuclide_code_sequence[0].CodeMeaning
        extraction_good = True
    except AttributeError:
        warnings.warn("Unable to extract RadioNuclideCodeSequence from RadiopharmaceuticalInformationSequence")
        radionuclide = ""
        extraction_good = False

    if extraction_good:
        # check to see if these nucleotides appear in our verified values
        verified_nucleotides = metadata_dictionaries['dicom2bids.json']['RadionuclideCodes']

        check_code_value = ""
        check_code_meaning = ""

        if code_value in verified_nucleotides.keys():
            check_code_value = code_value
        else:
            warnings.warn(f"Radionuclide Code {code_value} does not match any known codes in dcm2bids.json\n"
                          f"will attempt to infer from code meaning {code_meaning}")

        if code_meaning in verified_nucleotides.values():
            radionuclide = re.sub(r'\^', "", code_meaning)
            check_code_meaning = code_meaning
        else:
            warnings.warn(f"Radionuclide Meaning {code_meaning} not in known values in dcm2bids json")
            if code_value in verified_nucleotides.keys:
                radionuclide = re.sub(r'\^', "", verified_nucleotides[code_value])

        # final check
        if check_code_meaning and check_code_value:
            pass
        else:
            warnings.warn(f"Possible mismatch between nuclide code meaning {code_meaning} and {code_value} in dicom "
                          f"header")

    return radionuclide


def get_convolution_kernel(ConvolutionKernelString: str) -> dict:
    return {}


def cli():
    """
    Collects arguments used to initiate a Dcm2niix4PET class, collects the following arguments from the user.

    :param folder: folder containing imaging data, no flag required
    :param -m, --metadata-path: path to PET metadata spreadsheet
    :param -t, --translation-script-path: path to script used to extract information from metadata spreadsheet
    :param -d, --destination-path: path to place outputfiles post conversion from dicom to nifti + json
    :return: arguments collected from argument parser
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('folder', type=str, default=os.getcwd(),
                        help="Folder path containing imaging data")
    parser.add_argument('--metadata-path', '-m', type=str, default=None,
                        help="Path to metadata file for scan")
    parser.add_argument('--translation-script-path', '-t', default=None,
                        help="Path to a script written to extract and transform metadata from a spreadsheet to BIDS" +
                             " compliant text files (tsv and json)")
    parser.add_argument('--destination-path', '-d', type=str, default=None,
                        help="Destination path to send converted imaging and metadata files to. If " +
                             "omitted defaults to using the path supplied to folder path. If destination path " +
                             "doesn't exist an attempt to create it will be made.", required=False)
    parser.add_argument('--kwargs', '-k', nargs='*', action=ParseKwargs, default={},
                        help="Include additional values int the nifti sidecar json or override values extracted from "
                             "the supplied nifti. e.g. including `--kwargs TimeZero='12:12:12'` would override the "
                             "calculated TimeZero. Any number of additional arguments can be supplied after --kwargs "
                             "e.g. `--kwargs BidsVariable1=1 BidsVariable2=2` etc etc.")
    parser.add_argument('--silent', '-s', type=bool, default=False, help="Display missing metadata warnings and errors"
                                                                         "to stdout/stderr")

    args = parser.parse_args()

    return args


def main():
    """
    Executes cli() and uses Dcm2niix4PET class to convert a folder containing dicoms into nifti + json.

    :return: None
    """

    # collect args
    cli_args = cli()

    # instantiate class
    converter = Dcm2niix4PET(
        image_folder=expand_path(cli_args.folder),
        destination_path=expand_path(cli_args.destination_path),
        metadata_path=expand_path(cli_args.metadata_path),
        metadata_translation_script=expand_path(cli_args.translation_script_path),
        additional_arguments=cli_args.kwargs,
        silent=cli_args.silent)

    converter.convert()


if __name__ == '__main__':
    main()

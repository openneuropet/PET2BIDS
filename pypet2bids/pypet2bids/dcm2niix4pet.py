"""
This module acts as a simple wrapper around dcm2niix, it takes all of the same arguments as dcm2niix but does a little
bit of extra work to conform the output nifti and json from dcm2niix to the PET BIDS specification. Additionally, but
optionally, this module can collect blood or physiological data/metadata from spreadsheet files if the path of that
spreadsheet file as well as a python module/script written to interpret it are provided in addition to relevant dcm2niix
commands.

For more details see the CLI portion of this module or the documentation for the main class Dcm2niix4PET


| *Authors: Anthony Galassi*
| *Copyright OpenNeuroPET team*
"""
import pathlib
import sys
import textwrap
from json_maj.main import JsonMAJ
from platform import system
import subprocess
import pandas as pd
from os.path import join
from os import listdir, walk
from pathlib import Path
import json
import pydicom
import re
from tempfile import TemporaryDirectory
import shutil
import argparse
import importlib

try:
    import helper_functions
    import is_pet
    from update_json_pet_file import (check_json, update_json_with_dicom_value, update_json_with_dicom_value_cli,
                                      get_radionuclide, check_meta_radio_inputs, metadata_dictionaries,
                                      get_metadata_from_spreadsheet)
except ModuleNotFoundError:
    import pypet2bids.helper_functions as helper_functions
    import pypet2bids.is_pet as is_pet
    from pypet2bids.update_json_pet_file import (check_json, update_json_with_dicom_value,
                                                 update_json_with_dicom_value_cli, get_radionuclide,
                                                 check_meta_radio_inputs, metadata_dictionaries,
                                                 get_metadata_from_spreadsheet)

logger = helper_functions.logger("pypet2bids")

module_folder = Path(__file__).parent.resolve()
python_folder = module_folder.parent
pet2bids_folder = python_folder.parent
metadata_folder = join(pet2bids_folder, 'metadata')

# check to see if config file exists
home_dir = Path.home()
pypet2bids_config = home_dir / '.pet2bidsconfig'
if pypet2bids_config.exists():
    # check to see if the template json var is set and valid
    default_metadata_json = helper_functions.check_pet2bids_config('DEFAULT_METADATA_JSON')
    if default_metadata_json and Path(default_metadata_json).exists():
        # do nothing
        pass
    else:
        try:
            shutil.copy(Path(metadata_folder) / 'template_json.json', default_metadata_json)
        except FileNotFoundError:
            shutil.copy(module_folder / 'template_json.json', default_metadata_json)
else:
    # if it doesn't exist use the default one included in this library
    helper_functions.modify_config_file('DEFAULT_METADATA_JSON', module_folder / 'template_json.json')


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
    parsed_time = ''
    parsed_date = ''
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

    elif date and time:
        parsed_date = date
        parsed_time = str(round(float(time)))

    if len(parsed_time) < 6:
        zeros_to_pad = 6 - len(parsed_time)
        parsed_time = zeros_to_pad * '0' + parsed_time

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
                 metadata_translation_script=None, additional_arguments={}, file_format='%p_%i_%t_%s',
                 silent=False, tempdir_location=None):
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
        :param additional_arguments: user supplied key value pairs, E.g. TimeZero=\"12:12:12\", InjectedRadioactivity=1
        this key value pair will overwrite any fields in the dcm2niix produced nifti sidecar.json as it is assumed that
        the user knows more about converting their data than the heuristics within dcm2niix, this library, or even the
        dicom header
        :param tempdir_location: user supplied base location for temporary directory (override system default)
        :param silent: silence missing sidecar metadata messages, default is False and very verbose
        :param tempdir_location: location to create the temporary directory, for use on constrained systems
        """

        # check to see if dcm2niix is installed
        self.blood_json = None
        self.blood_tsv = None

        self.dcm2niix_path = self.check_for_dcm2niix()
        if not self.dcm2niix_path:
            raise FileNotFoundError("dcm2niix not found, this module depends on it for conversions, exiting.")

        # check for the version of dcm2niix
        minimum_version = 'v1.0.20220720'
        version_string = subprocess.run([self.dcm2niix_path, '-v'], capture_output=True)
        version = re.search(r"v[0-9].[0-9].{8}[0-9]", str(version_string.stdout))

        if version:
            # compare with minimum version
            if version[0] < minimum_version:
                logger.warning(f"Minimum version {minimum_version} of dcm2niix is recommended, found "
                               f"installed version {version[0]} at {self.dcm2niix_path}.")

        # check if user provided a custom tempdir location
        self.tempdir_location = tempdir_location
        self.image_folder = Path(image_folder)
        self.destination_folder = None

        # if we're provided an entire file path just us that no matter what, we're assuming the user knows what they
        # are doing in that case
        self.full_file_path_given = False

        for part in Path(destination_path).parts:
            if '.nii' in part or '.nii.gz' in part:
                self.full_file_path_given = True
                self.destination_folder = Path(destination_path).parent
                # replace .nii and .nii.gz
                self.destination_path = Path(str(destination_path).replace('.nii', '').replace('.gz', ''))
                break

        # replace the suffix in the destination path with '' if a non-nifti full file path is give
        if Path(destination_path).suffix:
            self.full_file_path_given = True
            self.destination_folder = destination_path.parent
            self.destination_path = Path(destination_path).with_suffix('')

        if not self.full_file_path_given:
            if not destination_path:
                self.destination_path = self.image_folder
                self.destination_folder = self.image_folder
            else:
                self.destination_folder = Path(destination_path)
                self.destination_path = self.destination_folder

        # extract PET filename parts from destination path if given
        self.subject_id = helper_functions.collect_bids_part('sub', str(self.destination_path))
        self.session_id = helper_functions.collect_bids_part('ses', str(self.destination_path))
        self.task = helper_functions.collect_bids_part('task', str(self.destination_path))
        self.tracer = helper_functions.collect_bids_part('trc', str(self.destination_path))
        self.reconstruction_method = helper_functions.collect_bids_part('rec', str(self.destination_path))
        self.run_id = helper_functions.collect_bids_part('run', str(self.destination_path))

        self.file_name_slug = None

        # we keep track of PET metadata in this spreadsheet metadata_dict, that includes nifti, _blood.json, and
        # _blood.tsv data
        self.spreadsheet_metadata = {'nifti_json': {}, 'blood_json': {}, 'blood_tsv': {}}
        self.dicom_headers = self.extract_dicom_headers()
        # we consider values stored in a default JSON file to be additional arguments, we load those
        # values first and then overwrite them with any user supplied values

        # load config file
        default_json_path = helper_functions.check_pet2bids_config('DEFAULT_METADATA_JSON')
        if default_json_path and Path(default_json_path).exists():
            with open(default_json_path, 'r') as json_file:
                try:
                    self.spreadsheet_metadata.update(json.load(json_file))
                except json.decoder.JSONDecodeError:
                    logger.warning(f"Unable to load default metadata json file at {default_json_path}, skipping.")

        self.additional_arguments = additional_arguments

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
        elif metadata_path and not metadata_translation_script or metadata_path == "":
            if not self.spreadsheet_metadata.get('nifti_json', None):
                self.spreadsheet_metadata['nifti_json'] = {}

            load_spreadsheet_data = get_metadata_from_spreadsheet(metadata_path=metadata_path,
                                                                  image_folder=self.image_folder,
                                                                  image_header_dict=self.dicom_headers[
                                                                    next(iter(self.dicom_headers))],
                                                                  **self.additional_arguments)

            self.spreadsheet_metadata['nifti_json'].update(load_spreadsheet_data['nifti_json'])
            self.spreadsheet_metadata['blood_tsv'].update(load_spreadsheet_data['blood_tsv'])
            self.spreadsheet_metadata['blood_json'].update(load_spreadsheet_data['blood_json'])

        self.file_format = file_format
        # we may want to include additional information to the sidecar, tsv, or json files generated after conversion
        # this variable stores the mapping between output files and a single dicom header used to generate those files
        # to access the dicom header information use the key in self.headers_to_files to access that specific header
        # in self.dicom_headers
        self.headers_to_files = {}
        # if silent is set to True output warnings aren't displayed to stdout/stderr
        self.silent = silent

    @staticmethod
    def check_posix():
        check = subprocess.run("dcm2niix -h", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if check.returncode == 0:
            dcm2niix_path = subprocess.run('which dcm2niix',
                                           shell=True,
                                           capture_output=True).stdout.decode('utf-8').strip()
        else:
            pkged = "https://github.com/rordenlab/dcm2niix/releases"
            instructions = "https://github.com/rordenlab/dcm2niix#install"
            no_dcm2niix = f"""Dcm2niix does not appear to be installed. Installation instructions can be found here 
                       {instructions} and packaged versions can be found at {pkged}"""
            logger.error(no_dcm2niix)
            dcm2niix_path = None

        return dcm2niix_path

    def check_for_dcm2niix(self):
        """
        Just checks for dcm2niix using the system shell, returns 0 if dcm2niix is present.

        :return: status code of the command dcm2niix -h
        """

        if system().lower() != 'windows':
            dcm2niix_path = self.check_posix()
            # fall back and check the config file if it's not on the path
            if not dcm2niix_path:
                dcm2niix_path = helper_functions.check_pet2bids_config('DCM2NIIX_PATH')
        elif system().lower() == 'windows':
            dcm2niix_path = helper_functions.check_pet2bids_config('DCM2NIIX_PATH')
        else:
            dcm2niix_path = None

        return dcm2niix_path

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
                    n += 1

                except pydicom.errors.InvalidDicomError:
                    pass

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
        with TemporaryDirectory(dir=self.tempdir_location) as tempdir:
            tempdir_pathlike = Path(tempdir)
            # people use screwy paths, we do this before running dcm2niix to account for that
            image_folder = helper_functions.sanitize_bad_path(self.image_folder)
            cmd = f"{self.dcm2niix_path} -b y -w 1 -z y {file_format_args} -o {tempdir_pathlike} {image_folder}"
            convert = subprocess.run(cmd, shell=True, capture_output=True)

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
            try:
                if self.destination_path.exists():
                    pass
                elif not self.destination_path.exists() and self.full_file_path_given:
                    self.destination_path.parent.mkdir(parents=True, exist_ok=True)
                else:
                    self.destination_path.mkdir(parents=True, exist_ok=True)
            except FileExistsError:
                pass

            # iterate through created files to supplement sidecar jsons
            for created in files_created_by_dcm2niix:
                created_path = Path(created)
                if created_path.suffix == '.json':
                    # we want to pair up the headers to the files created in the output directory in case
                    # dcm2niix has created files from multiple sessions
                    matched_dicoms_and_headers = self.match_dicom_header_to_file(destination_path=tempdir_pathlike)

                    # we check to see what's missing from our recommended and required jsons by gathering the
                    # output of check_json silently
                    if self.additional_arguments:
                        check_for_missing = check_json(created_path,
                                                       silent=True,
                                                       spreadsheet_metadata=self.spreadsheet_metadata,
                                                       **self.additional_arguments)
                    else:
                        check_for_missing = check_json(created_path,
                                                       silent=True,
                                                       spreadsheet_metadata=self.spreadsheet_metadata)

                    # we do our best to extra information from the dicom header and insert these values
                    # into the sidecar json

                    # first do a reverse lookup of the key the json corresponds to
                    lookup = [key for key, value in matched_dicoms_and_headers.items() if str(created_path) in value]
                    if lookup:
                        dicom_header = self.dicom_headers[lookup[0]]

                        update_json_with_dicom_value(
                            created_path,
                            check_for_missing,
                            dicom_header,
                            dicom2bids_json=metadata_dictionaries['dicom2bids.json'],
                            **self.additional_arguments)

                    # if we have entities in our metadata spreadsheet that we've used we update
                    if self.spreadsheet_metadata.get('nifti_json', None):
                        update_json = JsonMAJ(json_path=str(created),
                                              update_values=self.spreadsheet_metadata['nifti_json'],
                                              bids_null=True)
                        update_json.update()

                    # check to see if frame duration is a single value, if so convert it to list
                    update_json = JsonMAJ(json_path=str(created), bids_null=True)

                    # there are some additional updates that depend on some PET BIDS logic that we do next, since these
                    # updates depend on both information provided via the sidecar json and/or information provided via
                    # additional arguments we run this step after updating the sidecar with those additional user
                    # arguments

                    sidecar_json = JsonMAJ(json_path=str(created),
                                           bids_null=True,
                                           update_values=self.additional_arguments)  # load all supplied and now written sidecar data in

                    sidecar_json.update()

                    check_metadata_radio_inputs = check_meta_radio_inputs(sidecar_json.json_data)  # run logic

                    sidecar_json.update(check_metadata_radio_inputs)  # update sidecar json with results of logic

                    # should be list/array types in the json
                    should_be_array = [
                        'FrameDuration',
                        'ScatterFraction',
                        'FrameTimesStart',
                        'DecayCorrectionFactor',
                        'ReconFilterSize'
                    ]

                    for should in should_be_array:
                        should_value = update_json.get(should)
                        if should_value and type(should_value) is not list:
                            update_json.update({should: [should_value]})

                    # next we check to see if any of the additional user supplied arguments (kwargs) correspond to
                    # any of the missing tags in our sidecars
                    if self.additional_arguments:
                        update_json = JsonMAJ(json_path=str(created),
                                              update_values=self.additional_arguments,
                                              bids_null=True)
                        update_json.update()

                    # check to see if convolution kernel is present
                    sidecar_json = JsonMAJ(json_path=str(created), bids_null=True)
                    if sidecar_json.get('ConvolutionKernel'):
                        if sidecar_json.get('ReconFilterType') and sidecar_json.get('ReconFilterSize'):
                            sidecar_json.remove('ConvolutionKernel')
                        else:
                            # collect filter size
                            recon_filter_size = ''
                            if re.search(r'\d+.\d+', sidecar_json.get('ConvolutionKernel')):
                                recon_filter_size = re.search(r'\d+.\d*', sidecar_json.get('ConvolutionKernel'))[0]
                                recon_filter_size = float(recon_filter_size)
                                sidecar_json.update({'ReconFilterSize': float(recon_filter_size)})
                            # collect just the filter type by popping out the filter size if it exists
                            recon_filter_type = re.sub(str(recon_filter_size), '',
                                                       sidecar_json.get('ConvolutionKernel'))
                            # further sanitize the recon filter type string
                            recon_filter_type = re.sub(r'[^a-zA-Z0-9]', ' ', recon_filter_type)
                            recon_filter_type = re.sub(r' +', ' ', recon_filter_type)

                            # update the json
                            sidecar_json.update({'ReconFilterType': recon_filter_type})
                            # remove non bids field
                            sidecar_json.remove('ConvolutionKernel')

                    # check the input args again as our logic is applied after parsing user inputs
                    if self.additional_arguments:
                        recon_filter_user_input = {
                            'ReconFilterSize': self.additional_arguments.get('ReconFilterSize', None),
                            'ReconFilterType': self.additional_arguments.get('ReconFilterType', None)
                        }
                        for key, value in recon_filter_user_input.items():
                            if value:
                                sidecar_json.update({key: value})
                    else:
                        pass

                    # tag json with additional conversion software
                    conversion_software = sidecar_json.get('ConversionSoftware')
                    conversion_software_version = sidecar_json.get('ConversionSoftwareVersion')

                    sidecar_json.update({'ConversionSoftware': [conversion_software, 'pypet2bids']})
                    sidecar_json.update(
                        {
                            'ConversionSoftwareVersion': [conversion_software_version, helper_functions.get_version()]
                        })

                    # if this looks familiar, that's because it is, we re-run this to override any changes
                    # made by this software as the input provided by the user is "the correct input"
                    sidecar_json.update(self.spreadsheet_metadata.get('nifti_json', {}))
                    sidecar_json.update(self.additional_arguments)

                # if there's a subject id rename the output file to use it
                if self.subject_id:
                    if 'nii.gz' in created_path.name:
                        suffix = '.nii.gz'
                    else:
                        suffix = created_path.suffix
                    if self.session_id:
                        session_id = '_' + self.session_id
                    else:
                        session_id = ''

                    if self.task:
                        task = '_' + self.task
                    else:
                        task = ''

                    if self.tracer:
                        trc = '_' + self.tracer
                    else:
                        trc = ''

                    if self.reconstruction_method:
                        rec = '_' + self.reconstruction_method
                    else:
                        rec = ''

                    if self.run_id:
                        run = '_' + self.run_id
                    else:
                        run = ''

                    if self.full_file_path_given:
                        new_path = self.destination_path.with_suffix(suffix)
                        self.destination_folder = self.destination_path.parent
                    else:
                        new_path = self.destination_path / Path(self.subject_id + session_id + task + trc + rec +
                                                                run + '_pet' + suffix)

                    try:
                        new_path.parent.mkdir(parents=True, exist_ok=True)
                    except FileExistsError:
                        pass

                elif not self.subject_id:
                    new_path = Path(join(self.destination_path, created_path.name))

                self.new_file_name_with_entities = new_path

                shutil.move(src=created, dst=new_path)

            return self.destination_path

    def post_dcm2niix(self):
        # TODO add logic to handle blood tsv recording manual vs automatic
        # for now we will just assume that if the user supplied a blood tsv then it is manual
        recording_entity = "_recording-manual"

        if '_pet' in self.new_file_name_with_entities.name:
            if self.new_file_name_with_entities.suffix == '.gz' and len(self.new_file_name_with_entities.suffixes) > 1:
                self.new_file_name_with_entities = self.new_file_name_with_entities.with_suffix('').with_suffix('')

            blood_file_name = self.new_file_name_with_entities.stem.replace('_pet', recording_entity + '_blood')
        else:
            blood_file_name = self.new_file_name_with_entities.stem + recording_entity + '_blood'

        if self.spreadsheet_metadata.get('blood_tsv', {}) != {}:
            blood_tsv_data = self.spreadsheet_metadata.get('blood_tsv')
            if type(blood_tsv_data) is pd.DataFrame or type(blood_tsv_data) is dict:
                if type(blood_tsv_data) is dict:
                    blood_tsv_data = pd.DataFrame(blood_tsv_data)
                # write out blood_tsv using pandas csv write
                blood_tsv_data.to_csv(join(self.destination_folder, blood_file_name + ".tsv")
                                      , sep='\t',
                                      index=False)

            elif type(blood_tsv_data) is str:
                # write out with write
                with open(join(self.destination_folder, blood_file_name + ".tsv"), 'w') as outfile:
                    outfile.writelines(blood_tsv_data)
            else:
                raise (f"blood_tsv dictionary is incorrect type {type(blood_tsv_data)}, must be type: "
                       f"pandas.DataFrame or str\nCheck return type of translate_metadata in "
                       f"{self.metadata_translation_script}")

        # if there's blood data in the tsv then write out the sidecar file too
        if self.spreadsheet_metadata.get('blood_json', {}) != {} \
                and self.spreadsheet_metadata.get('blood_tsv', {}) != {}:
            blood_json_data = self.spreadsheet_metadata.get('blood_json')
            if type(blood_json_data) is dict:
                # write out to file with json dump
                pass
            elif type(blood_json_data) is str:
                # write out to file with json dumps
                blood_json_data = json.loads(blood_json_data)
            else:
                raise (f"blood_json dictionary is incorrect type {type(blood_json_data)}, must be type: dict or str"
                       f"pandas.DataFrame or str\nCheck return type of translate_metadata in "
                       f"{self.metadata_translation_script}")

            with open(join(self.destination_folder, blood_file_name + '.json'), 'w') as outfile:
                json.dump(blood_json_data, outfile, indent=4)

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
        # first collect all the files in the output directory
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


epilog = textwrap.dedent('''
    
    example usage:
    
    dcm2niix4pet folder_with_pet_dicoms/ --destinationp-path sub-ValidBidSSubject/pet # the simplest conversion
    dcm2niix4pet folder_with_pet_dicoms/ --destination-path sub-ValidBidsSubject/pet --metadata-path metadata.xlsx \
    # use with an input spreadsheet
    
''')


def cli():
    """
    Collects arguments used to initiate a Dcm2niix4PET class, collects the following arguments from the user.

    :param folder: folder containing imaging data, no flag required
    :param -m, --metadata-path: path to PET metadata spreadsheet
    :param -t, --translation-script-path: path to script used to extract information from metadata spreadsheet
    :param -d, --destination-path: path to place outputfiles post conversion from dicom to nifti + json
    :return: arguments collected from argument parser
    """
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, epilog=epilog)
    parser.add_argument('folder', nargs='?', type=str,
                        help="Folder path containing imaging data")
    parser.add_argument('--metadata-path', '-m', type=str, default=None, const='', nargs='?',
                        help="Path to metadata file for scan")
    parser.add_argument('--translation-script-path', '-t', default=None,
                        help="Path to a script written to extract and transform metadata from a spreadsheet to BIDS" +
                             " compliant text files (tsv and json)")
    parser.add_argument('--destination-path', '-d', type=str, default=None,
                        help="Destination path to send converted imaging and metadata files to. If subject id and "
                             "session id is included in the path files created by dcm2niix4pet will be named as such. "
                             "e.g. sub-NDAR123/ses-ABCD/pet will yield fields named sub-NDAR123_ses-ABCD_*. If " +
                             "omitted defaults to using the path supplied to folder path. If destination path " +
                             "doesn't exist an attempt to create it will be made.", required=False)
    parser.add_argument('--tempdir', type=str, default=None,
                        help="User-specified tempdir location (overrides default system tempfile default)",
                        required=False)
    parser.add_argument('--kwargs', '-k', nargs='*', action=helper_functions.ParseKwargs, default={},
                        help="Include additional values in the nifti sidecar json or override values extracted from "
                             "the supplied nifti. e.g. including `--kwargs TimeZero=\"12:12:12\"` would override the "
                             "calculated TimeZero. Any number of additional arguments can be supplied after --kwargs "
                             "e.g. `--kwargs BidsVariable1=1 BidsVariable2=2` etc etc."
                             "Note: the value portion of the argument (right side of the equal's sign) should always"
                             "be surrounded by double quotes BidsVarQuoted=\"[0, 1 , 3]\"")
    parser.add_argument('--silent', '-s', action="store_true", default=False,
                        help="Hide missing metadata warnings and errors to stdout/stderr")
    parser.add_argument('--show-examples', '-E', '--HELP', '-H', help="Shows example usage of this cli.",
                        action='store_true')

    parser.add_argument('--set-dcm2niix-path', help="Provide a path to a dcm2niix install/exe, writes path to config "
                                                    f"file {Path.home()}/.pet2bidsconfig under the variable "
                                                    f"DCM2NIIX_PATH", type=pathlib.Path)
    parser.add_argument('--set-default-metadata-json', help="Provide a path to a default metadata file json file."
                                                            "This file will be used to fill in missing metadata not"
                                                            "contained within dicom headers or spreadsheet metadata."
                                                            "Sets given path to DEFAULT_METADATA_JSON var in "
                                                            f"{Path.home()}/.pet2bidsconfig")
    parser.add_argument('--trc', '--tracer', type=str, default='',
                        help="Provide a tracer name to be used in the output file name")
    parser.add_argument('--run', type=str, default='',
                        help="Provide a run id to be used in the output file name")
    parser.add_argument('--rec', type=str, default='',
                        help="Provide a reconstruction method to be used in the output file name")

    return parser


example1 = textwrap.dedent('''

Usage examples are below, the first being the most brutish way of making dcm2niix4pet to pass through the
BIDS validator (with no errors, removing all warnings is left to the user as an exercise) see:

example 1 (Passing PET metadata via the --kwargs argument): 
    
    # Note `#` denotes a comment
    # dcm2niix4pet is called with the following arguments
    
    # folder -> GeneralElectricSignaPETMR-NIMH/
    # destination-path -> sub-GeneralElectricSignaPETMRINIMH/pet
    # kwargs -> a bunch of key pair arguments spaced 1 space apart with the values surrounded by double quotes

    dcm2niix4pet GeneralElectricSignaPETMR-NIMH/ --destination-path sub-GeneralElectricSignaPETMRNIMH/pet 
    --kwargs TimeZero="14:08:45" Manufacturer="GE MEDICAL SYSTEMS" ManufacturersModelName="SIGNA PET/MR" 
    InstitutionName="NIH Clinical Center, USA" BodyPart="Phantom" Units="Bq/mL" TracerName="Gallium citrate" 
    TracerRadionuclide="Germanium68" InjectedRadioactivity=1 SpecificRadioactivity=23423.75 
    ModeOfAdministration="infusion" FrameTimesStart=0 
    AcquisitionMode="list mode" ImageDecayCorrected="False" FrameTimesStart="[0]" ImageDecayCorrectionTime=0 
    ReconMethodParameterValues="[1, 1]" ReconFilterType="n/a" ReconFilterSize=1

    # The output of the above command (given some GE phantoms from the NIMH) can be seen below with tree
    
    tree sub-GeneralElectricSignaPETMRNIMH 
    sub-GeneralElectricSignaPETMRNIMH
    └── pet
        ├── sub-GeneralElectricSignaPETMRNIMH_pet.json
        └── sub-GeneralElectricSignaPETMRNIMH_pet.nii.gz

    # Further, when we examine the json output file we can see that all of our metadata supplied via kwargs was written
    # into the sidecar json 
    
    cat sub-GeneralElectricSignalPETMRNIMH/pet/sub-GeneralElectricSignaPETMRNIMH_pet.json
    {
        "Modality": "PT",
        "Manufacturer": "GE MEDICAL SYSTEMS",
        "ManufacturersModelName": "SIGNA PET/MR",
        "InstitutionName": "NIH Clinical Center, USA",
        "StationName": "PETMR",
        "PatientPosition": "HFS",
        "SoftwareVersions": "61.00",
        "SeriesDescription": "PET Scan for VQC Verification",
        "ProtocolName": "PET Scan for VQC Verification",
        "ImageType": [
            "ORIGINAL",
            "PRIMARY"
        ],
        "SeriesNumber": 2,
        "Radiopharmaceutical": "Germanium",
        "RadionuclidePositronFraction": 0.891,
        "RadionuclideHalfLife": 23410100.0,
        "Units": "Bq/mL",
        "DecayCorrection": "NONE",
        "AttenuationCorrectionMethod": "NONE, 0.000000 cm-1,",
        "SliceThickness": 2.78,
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
            "v1.0.20220720",
            "1.0.2"
        ],
        "FrameDuration": [
            98000
        ],
        "ReconMethodName": "VPFX",
        "ReconMethodParameterUnits": [
            "none",
            "none"
        ],
        "ReconMethodParameterLabels": [
            "subsets",
            "iterations"
        ],
        "ReconMethodParameterValues": [
            1,
            1
        ],
        "AttenuationCorrection": "NONE, 0.000000 cm-1,",
        "TimeZero": "14:08:45",
        "ScanStart": 0,
        "InjectionStart": 0,
        "TracerRadionuclide": "Germanium68",
        "BodyPart": "Phantom",
        "TracerName": "Gallium citrate",
        "InjectedRadioactivity": 1,
        "SpecificRadioactivity": 23423.75,
        "ModeOfAdministration": "infusion",
        "FrameTimesStart": [
            0
        ],
        "AcquisitionMode": "list mode",
        "ImageDecayCorrected": false,
        "ImageDecayCorrectionTime": 0,
        "ReconFilterType": "n/a",
        "ReconFilterSize": 1,
        "InjectedRadioactivityUnits": "MBq",
        "SpecificRadioactivityUnits": "Bq/g",
        "InjectedMass": "n/a",
        "InjectedMassUnits": "n/a"
        }''')


def main():
    """
    Executes cli() and uses Dcm2niix4PET class to convert a folder containing dicoms into nifti + json.

    :return: None
    """

    # collect args
    cli_parser = cli()

    if len(sys.argv) == 1:
        cli_parser.print_usage()
        print(f"version: {helper_functions.get_version()}")
        sys.exit(1)
    else:
        cli_args = cli_parser.parse_args()

    if cli_args.silent:
        logger.disabled = True

    if cli_args.show_examples:
        print(example1)
        sys.exit(0)

    if cli_args.set_dcm2niix_path:
        helper_functions.modify_config_file('DCM2NIIX_PATH', cli_args.set_dcm2niix_path)
        sys.exit(0)

    if cli_args.set_default_metadata_json:
        helper_functions.modify_config_file('DEFAULT_METADATA_JSON', cli_args.set_default_metadata_json)
        sys.exit(0)

    elif cli_args.folder:
        # instantiate class
        converter = Dcm2niix4PET(
            image_folder=helper_functions.expand_path(cli_args.folder),
            destination_path=helper_functions.expand_path(cli_args.destination_path),
            metadata_path=helper_functions.expand_path(cli_args.metadata_path),
            metadata_translation_script=helper_functions.expand_path(cli_args.translation_script_path),
            additional_arguments=cli_args.kwargs,
            tempdir_location=cli_args.tempdir,
            silent=cli_args.silent)

        if cli_args.trc:
            converter.tracer = "trc-" + cli_args.trc
        if cli_args.run:
            converter.run_id = "run-" + cli_args.run
        if cli_args.rec:
            converter.reconstruction_method = "rec-" + cli_args.rec

        converter.convert()
    else:
        print("folder is a required argument for running dcm2niix, see -h for more detailed usage.")
        sys.exit(1)


if __name__ == '__main__':
    main()

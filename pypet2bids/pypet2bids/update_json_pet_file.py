from pathlib import Path
from os.path import join
from os import listdir
import json
from json_maj.main import JsonMAJ, load_json_or_dict
import re
from dateutil import parser
import argparse
import pydicom
from typing import Union

try:
    import helper_functions
    import is_pet
except ModuleNotFoundError:
    import pypet2bids.helper_functions as helper_functions
    import pypet2bids.is_pet as is_pet

# import logging
logger = helper_functions.logger("pypet2bids")

# load module and metadata_json paths from helper_functions
module_folder, metadata_folder = helper_functions.module_folder, helper_functions.metadata_folder

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


def check_json(path_to_json, items_to_check=None, silent=False, spreadsheet_metadata={}, mandatory=True,
               recommended=True, logger_name='pypet2bids', **additional_arguments):
    """
    This method opens a json and checks to see if a set of mandatory values is present within that json, optionally it
    also checks for recommended key value pairs. If fields are not present a warning is raised to the user.

    :param spreadsheet_metadata:
    :type spreadsheet_metadata:
    :param path_to_json: path to a json file e.g. a BIDS sidecar file created after running dcm2niix
    :param items_to_check: a dictionary with items to check for within that json. If None is supplied defaults to the
           PET_metadata.json contained in this repository
    :param silent: Raises warnings or errors to stdout if this flag is set to True
    :return: dictionary of items existence and value state, if key is True/False there exists/(does not exist) a
            corresponding entry in the json the same can be said of value
    """

    logger = helper_functions.logger(logger_name)

    if silent:
        logger.disabled = True
    else:
        logger.disabled = False

    # check if path exists
    path_to_json = Path(path_to_json)
    if not path_to_json.exists():
        raise FileNotFoundError(path_to_json)

    # check for default argument for dictionary of items to check
    if items_to_check is None:
        items_to_check = metadata_dictionaries['PET_metadata.json']
        # remove blood tsv data from items to check
        if items_to_check.get('blood_recording_fields', None):
            items_to_check.pop('blood_recording_fields')

    # open the json
    with open(path_to_json, 'r') as in_file:
        json_to_check = json.load(in_file)

    # initialize warning colors and warning storage dictionary
    storage = {}
    flattened_spreadsheet_metadata = {}
    flattened_spreadsheet_metadata.update(spreadsheet_metadata.get('nifti_json', {}))
    flattened_spreadsheet_metadata.update(spreadsheet_metadata.get('blood_json', {}))
    flattened_spreadsheet_metadata.update(spreadsheet_metadata.get('blood_tsv', {}))

    if mandatory:
        for item in items_to_check['mandatory']:
            all_good = False
            if (item in json_to_check.keys() and
                    (json_to_check.get(item, None) is not None or json_to_check.get(item) != '')
                    or item in additional_arguments or item in flattened_spreadsheet_metadata.keys()):
                # this json has both the key and a non-blank value do nothing
                all_good = True
                pass
            elif (item in json_to_check.keys()
                  and (json_to_check.get(item, None) is None or json_to_check.get(item, None) == '')):
                logger.error(f"{item} present but has null value.")
                storage[item] = {'key': True, 'value': False}
            elif not all_good:
                logger.error(f"{item} is not present in {path_to_json}. This will have to be "
                               f"corrected post conversion.")
                storage[item] = {'key': False, 'value': False}

    if recommended:
        for item in items_to_check['recommended']:
            all_good = False
            if (item in json_to_check.keys() and
                    (json_to_check.get(item, None) is not None or json_to_check.get(item) != '')
                    or item in additional_arguments or item in flattened_spreadsheet_metadata.keys()):
                # this json has both the key and a non-blank value do nothing
                all_good = True
                pass
            elif (item in json_to_check.keys()
                  and (json_to_check.get(item, None) is None or json_to_check.get(item, None) == '')):
                logger.info(f"{item} present but has null value.")
                storage[item] = {'key': True, 'value': False}
            elif not all_good:
                logger.info(f"{item} is recommended but not present in {path_to_json}")
                storage[item] = {'key': False, 'value': False}

    return storage


def update_json_with_dicom_value(
        path_to_json,
        missing_values,
        dicom_header,
        dicom2bids_json=None,
        silent=True,
        **additional_arguments
):
    """
    We go through all the missing values or keys that we find in the sidecar json and attempt to extract those
    missing entities from the dicom source. This function relies on many heuristics a.k.a. many unique conditionals and
    simply is what it is, hate the game not the player.

    :param path_to_json: path to the sidecar json to check
    :param missing_values: dictionary output from check_json indicating missing fields and/or values
    :param dicom_header: the dicom or dicoms that may contain information not picked up by dcm2niix
    :param dicom2bids_json: a json file that maps dicom header entities to their corresponding BIDS entities
    :return: a dictionary of sucessfully updated (written to the json file) fields and values
    """

    if silent:
        logger.disabled = True

    json_sidecar_path = Path(path_to_json)
    if not json_sidecar_path.exists():
        with open(path_to_json, 'w') as outfile:
            json.dump({}, outfile)

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
                temp = JsonMAJ(path_to_json, {'Units': sidecar_json.get('Unit')}, bids_null=True)
                temp.remove('Unit')
            else:  # we source the Units value from the dicom header and update the json
                JsonMAJ(path_to_json, {'Units': dicom_header.Units}, bids_null=True)
        except AttributeError:
            logger.error(f"Dicom is missing Unit(s) field, are you sure this is a PET dicom?")
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

    logger.info("Attempting to locate missing BIDS fields in dicom header")
    # go through missing fields and reach into dicom to pull out values
    json_updater = JsonMAJ(json_path=path_to_json, bids_null=True)
    for key, value in paired_fields.items():
        missing_bids_field = missing_values.get(key, None)
        # if field is missing look into dicom
        if missing_bids_field and key not in additional_arguments:
            # there are a few special cases that require regex splitting of the dicom entries
            # into several bids sidecar entities
            try:
                dicom_field = getattr(dicom_header, value)
                logger.info(f"FOUND {value} corresponding to BIDS {key}: {dicom_field}")
            except AttributeError:
                dicom_field = None
                logger.info(f"NOT FOUND {value} corresponding to BIDS {key} in dicom header.")

            if dicom_field and value in regex_cases:
                # if it exists get rid of it, we don't want no part of it.
                if sidecar_json.get('ReconMethodName', None):
                    json_updater.remove('ReconstructionMethod')
                if dicom_header.get('ReconstructionMethod', None):
                    reconstruction_method = dicom_header.ReconstructionMethod
                    json_updater.remove('ReconstructionMethod')
                    reconstruction_method = helper_functions.get_recon_method(reconstruction_method)

                    json_updater.update(reconstruction_method)

            elif dicom_field:
                # update json
                json_updater.update({key: dicom_field})

    # Additional Heuristics are included below

    # See if time zero is missing in json or additional args
    if missing_values.get('TimeZero', None):
        if missing_values.get('TimeZero')['key'] is False or missing_values.get('TimeZero')['value'] is False:
            time_parser = parser
            if sidecar_json.get('AcquisitionTime', None):
                acquisition_time = time_parser.parse(sidecar_json.get('AcquisitionTime')).time().strftime("%H:%M:%S")
            else:
                acquisition_time = time_parser.parse(dicom_header['SeriesTime'].value).time().strftime("%H:%M:%S")

            json_updater.update({'TimeZero': acquisition_time})
            json_updater.remove('AcquisitionTime')
            json_updater.update({'ScanStart': 0})
        else:
            pass

    if missing_values.get('ScanStart', None):
        if missing_values.get('ScanStart')['key'] is False or missing_values.get('ScanStart')['value'] is False:
            json_updater.update({'ScanStart': 0})
    if missing_values.get('InjectionStart', None):
        if missing_values.get('InjectionStart')['key'] is False \
                or missing_values.get('InjectionStart')['value'] is False:
            json_updater.update({'InjectionStart': 0})

    # check to see if units are BQML
    json_updater = JsonMAJ(str(path_to_json), bids_null=True)
    if json_updater.get('Units') == 'BQML':
        json_updater.update({'Units': 'Bq/mL'})

    # Add radionuclide to json
    Radionuclide = get_radionuclide(dicom_header)
    if Radionuclide:
        json_updater.update({'TracerRadionuclide': Radionuclide})

    # remove scandate if it exists
    json_updater.remove('ScanDate')

    # after updating raise warnings to user if values in json don't match values in dicom headers, only warn!
    updated_values = json.load(open(path_to_json, 'r'))
    for key, value in paired_fields.items():
        try:
            json_field = updated_values.get(key)
            dicom_field = dicom_header.__getattr__(key)
            if json_field != dicom_field:
                logger.info(f"WARNING!!!! JSON Field {key} with value {json_field} does not match dicom value "
                            f"of {dicom_field}")
        except AttributeError:
            pass


def update_json_with_dicom_value_cli():
    """
    Command line interface for update_json_with_dicom_value, updates a PET json with values from a dicom header,
    optionally can update with values from a spreadsheet or via values passed in as additional arguments with the -k
    --additional_arguments flag. This command be accessed after installation of pypet2bids via
    `updatepetjsonfromdicom`.
    """
    dicom_update_parser = argparse.ArgumentParser()
    dicom_update_parser.add_argument('-j', '--json', help='path to json to update', required=True)
    dicom_update_parser.add_argument('-d', '--dicom', help='path to dicom to extract values from', required=True)
    dicom_update_parser.add_argument('-m', '--metadata-path', help='path to metadata json', default=None)
    dicom_update_parser.add_argument('-k', '--additional_arguments',
                                     help='additional key value pairs to update json with', nargs='*',
                                     action=helper_functions.ParseKwargs, default={})

    args = dicom_update_parser.parse_args()

    try:
        # get missing values
        missing_values = check_json(args.json, silent=True)
    except FileNotFoundError:
        with open(args.json, 'w') as outfile:
            json.dump({}, outfile)
        missing_values = check_json(args.json, silent=True)

    # load dicom header
    dicom_header = pydicom.dcmread(args.dicom, stop_before_pixels=True)

    if args.metadata_path:
        spreadsheet_metadata = get_metadata_from_spreadsheet(args.metadata_path, args.dicom, dicom_header,
                                                             **args.additional_arguments)
        # update json
        update_json_with_dicom_value(args.json, missing_values, dicom_header, silent=True,
                                     spreadsheet_metadata=spreadsheet_metadata['nifti_json'],
                                     **args.additional_arguments)

        JsonMAJ(args.json, update_values=spreadsheet_metadata['nifti_json']).update()
    else:
        update_json_with_dicom_value(args.json, missing_values, dicom_header, silent=True, **args.additional_arguments)

    JsonMAJ(args.json, update_values=args.additional_arguments).update()

    # check json again after updating
    check_json(args.json, required=True, recommended=True, silent=False, logger_name='check_json')


def update_json_cli():
    """
    Updates a json file with user supplied values or values from a spreadsheet. This command can be accessed after
    conversion via `updatepetjson` if so required.
    """
    update_json_parser = argparse.ArgumentParser()
    update_json_parser.add_argument('-j', '--json', help='path to json to update', required=True)
    update_json_parser.add_argument('-k', '--additional_arguments',
                        help='additional key value pairs to update json with', nargs='*',
                        action=helper_functions.ParseKwargs, default={})
    update_json_parser.add_argument('-m', '--metadata-path', help='path to metadata json', default=None)

    update_json_args = update_json_parser.parse_args()

    if update_json_args.metadata_path:
        nifti_sidecar_metadata = (
            get_metadata_from_spreadsheet(update_json_args.metadata_path, update_json_args.json))['nifti_json']
    else:
        nifti_sidecar_metadata = {}

    j = JsonMAJ(update_json_args.json, update_values=nifti_sidecar_metadata)
    j.update()
    j.update(update_json_args.additional_arguments)

    # check meta radio inputs
    j.update(check_meta_radio_inputs(j.json_data))

    # check json again after updating
    check_json(update_json_args.json, required=True, recommended=True, silent=False, logger_name='check_json')

def get_radionuclide(pydicom_dicom):
    """
    Gets the radionuclide if given a pydicom_object if
    pydicom_object.RadiopharmaceuticalInformationSequence[0].RadionuclideCodeSequence exists

    :param pydicom_dicom: dicom object collected by pydicom.dcmread("dicom_file.img")
    :return: Labeled Radionuclide e.g. 11Carbon, 18Flourine
    """
    radionuclide = ""
    try:
        radiopharmaceutical_information_sequence = pydicom_dicom.RadiopharmaceuticalInformationSequence
        radionuclide_code_sequence = radiopharmaceutical_information_sequence[0].RadionuclideCodeSequence
        code_value = radionuclide_code_sequence[0].CodeValue
        code_meaning = radionuclide_code_sequence[0].CodeMeaning
        extraction_good = True
    except AttributeError:
        logger.info("Unable to extract RadioNuclideCodeSequence from RadiopharmaceuticalInformationSequence")
        extraction_good = False

    if extraction_good:
        # check to see if these nucleotides appear in our verified values
        verified_nucleotides = metadata_dictionaries['dicom2bids.json']['RadionuclideCodes']

        check_code_value = ""
        check_code_meaning = ""

        if code_value in verified_nucleotides.keys():
            check_code_value = code_value
        else:
            logger.warning(f"Radionuclide Code {code_value} does not match any known codes in dcm2bids.json\n"
                           f"will attempt to infer from code meaning {code_meaning}")

        if code_meaning in verified_nucleotides.values():
            radionuclide = re.sub(r'\^', "", code_meaning)
            check_code_meaning = code_meaning
        else:
            logger.warning(f"Radionuclide Meaning {code_meaning} not in known values in dcm2bids json")
            if code_value in verified_nucleotides.keys():
                radionuclide = re.sub(r'\^', "", verified_nucleotides[code_value])

        # final check
        if check_code_meaning and check_code_value:
            pass
        else:
            logger.warning(
                f"WARNING!!!! Possible mismatch between nuclide code meaning {code_meaning} and {code_value} in dicom "
                f"header")

    return radionuclide


def check_meta_radio_inputs(kwargs: dict, logger='pypet2bids') -> dict:
    """
    Executes very specific PET logic, author does not recall everything it does.
    :param kwargs: metadata key pair's to examine
    :type kwargs: dict
    :return: fitted/massaged metadata corresponding to logic steps below, return type is an update on input `kwargs`
    :rtype: dict
    """

    logger = helper_functions.logger(logger)

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
        numeric_check = [helper_functions.is_numeric(str(InjectedRadioactivity)),
                         helper_functions.is_numeric(str(InjectedMass))]
        if False in numeric_check:
            data_out['InjectedMass'] = 'n/a'
            data_out['InjectedMassUnits'] = 'n/a'
        else:
            tmp = (InjectedRadioactivity * 10 ** 6) / (InjectedMass * 10 ** 6)
            if SpecificRadioactivity:
                if SpecificRadioactivity != tmp:
                    logger.warning("Inferred SpecificRadioactivity in Bq/g doesn't match InjectedRadioactivity "
                                   "and InjectedMass, could be a unit issue")
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
        numeric_check = [helper_functions.is_numeric(str(InjectedRadioactivity)),
                         helper_functions.is_numeric(str(SpecificRadioactivity))]
        if False in numeric_check:
            data_out['InjectedMass'] = 'n/a'
            data_out['InjectedMassUnits'] = 'n/a'
        else:
            tmp = ((InjectedRadioactivity * (10 ** 6) / SpecificRadioactivity) * (10 ** 6))
            if InjectedMass:
                if InjectedMass != tmp:
                    logger.warning("Inferred InjectedMass in ug doesn't match InjectedRadioactivity and "
                                   "InjectedMass, could be a unit issue")
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
        numeric_check = [helper_functions.is_numeric(str(SpecificRadioactivity)),
                         helper_functions.is_numeric(str(InjectedMass))]
        if False in numeric_check:
            data_out['InjectedRadioactivity'] = 'n/a'
            data_out['InjectedRadioactivityUnits'] = 'n/a'
        else:
            tmp = ((InjectedMass / (10 ** 6)) * SpecificRadioactivity) / (
                    10 ** 6)  # ((ug / 10 ^ 6) / Bq / g)/10 ^ 6 = MBq
            if InjectedRadioactivity:
                if InjectedRadioactivity != tmp:
                    logger.warning("Inferred InjectedRadioactivity in MBq doesn't match SpecificRadioactivity "
                                   "and InjectedMass, could be a unit issue")
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
        numeric_check = [helper_functions.is_numeric(str(MolarActivity)),
                         helper_functions.is_numeric(str(MolecularWeight))]
        if False in numeric_check:
            data_out['SpecificRadioactivity'] = 'n/a'
            data_out['SpecificRadioactivityUnits'] = 'n/a'
        else:
            tmp = (MolarActivity * (10 ** 3)) / MolecularWeight  # (GBq / umol * 10 ^ 6) / (g / mol / * 10 ^ 6) = Bq / g
            if SpecificRadioactivity:
                if SpecificRadioactivity != tmp:
                    logger.warning(
                        "Inferred SpecificRadioactivity in MBq/ug doesn't match Molar Activity and Molecular "
                        "Weight, could be a unit issue")
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
        numeric_check = [helper_functions.is_numeric(str(SpecificRadioactivity)),
                         helper_functions.is_numeric(str(MolarActivity))]
        if False in numeric_check:
            data_out['MolecularWeight'] = 'n/a'
            data_out['MolecularWeightUnits'] = 'n/a'
        else:
            tmp = (MolarActivity * 1000) / SpecificRadioactivity  # (MBq / ug / 1000) / (GBq / umol) = g / mol
            if MolecularWeight:
                if MolecularWeight != tmp:
                    logger.warning("Inferred MolecularWeight in MBq/ug doesn't match Molar Activity and "
                                   "Molecular Weight, could be a unit issue")

                data_out['MolecularWeight'] = tmp
                data_out['MolecularWeightUnits'] = kwargs.get('MolecularWeightUnits', 'n/a')
            else:
                data_out['MolecularWeight'] = tmp
                data_out['MolecularWeightUnits'] = 'g/mol'

    if MolecularWeight and SpecificRadioactivity:
        data_out['SpecificRadioactivity'] = SpecificRadioactivity
        data_out['SpecificRadioactivityUnits'] = 'MBq/ug'
        data_out['MolecularWeight'] = MolarActivity
        data_out['MolecularWeightUnits'] = 'g/mol'
        numeric_check = [helper_functions.is_numeric(str(SpecificRadioactivity)),
                         helper_functions.is_numeric(str(MolecularWeight))]
        if False in numeric_check:
            data_out['MolarActivity'] = 'n/a'
            data_out['MolarActivityUnits'] = 'n/a'
        else:
            tmp = MolecularWeight * (SpecificRadioactivity / 1000)  # g / mol * (MBq / ug / 1000) = GBq / umol
            if MolarActivity:
                if MolarActivity != tmp:
                    logger.warning("Inferred MolarActivity in GBq/umol doesn't match Specific Radioactivity and "
                                   "Molecular Weight, could be a unit issue")
                data_out['MolarActivity'] = MolarActivity
                data_out['MolarActivityUnits'] = kwargs.get('MolarActivityUnits', 'n/a')
            else:
                data_out['MolarActivity'] = tmp
                data_out['MolarActivityUnits'] = 'GBq/umol'

    return data_out


def get_metadata_from_spreadsheet(metadata_path: Union[str, Path], image_folder,
                                  image_header_dict={}, **additional_arguments) -> dict:
    """
    Extracts metadata from a spreadsheet and returns a dictionary of metadata organized under
    three main keys: nifti_json, blood_json, and blood_tsv

    :param metadata_path: path to a spreadsheet
    :type metadata_path: [str, pathlib.Path]
    :param image_folder: path to image folder
    :type image_folder: [str, pathlib.Path]
    :param image_header_dict: dictionary of image header values
    :type image_header_dict: dict
    :param additional_arguments: additional arguments to pass on, typically user sourced key value pairs
    :type additional_arguments: dict
    :return: dictionary of metadata
    :rtype: dict
    """
    spreadsheet_metadata = {'nifti_json': {}, 'blood_json': {}, 'blood_tsv': {}}
    spreadsheet_values = {}
    if Path(metadata_path).is_file():
        spreadsheet_values = helper_functions.single_spreadsheet_reader(
            path_to_spreadsheet=metadata_path,
            dicom_metadata=image_header_dict,
            **additional_arguments)

    if Path(metadata_path).is_dir() or metadata_path == "":
        # we accept folder input as well as no input, in the
        # event of no input we search for spreadsheets in the
        # image folder
        if metadata_path == "":
            metadata_path = image_folder

        spreadsheets = helper_functions.collect_spreadsheets(metadata_path)
        pet_spreadsheets = [spreadsheet for spreadsheet in spreadsheets if is_pet.pet_file(spreadsheet)]
        spread_sheet_values = {}

        for pet_spreadsheet in pet_spreadsheets:
            spreadsheet_values.update(
                helper_functions.single_spreadsheet_reader(
                    path_to_spreadsheet=pet_spreadsheet,
                    dicom_metadata=image_header_dict,
                    **additional_arguments))

    # check for any blood (tsv) data or otherwise in the given spreadsheet values
    blood_tsv_columns = ['time', 'plasma_radioactivity', 'metabolite_parent_fraction',
                         'whole_blood_radioactivity']
    blood_json_columns = ['PlasmaAvail', 'WholeBloodAvail', 'MetaboliteAvail', 'MetaboliteMethod',
                          'MetaboliteRecoveryCorrectionApplied', 'DispersionCorrected']

    # check for existing tsv columns
    for column in blood_tsv_columns:
        try:
            values = spreadsheet_values[column]
            spreadsheet_metadata['blood_tsv'][column] = values
            # pop found data from spreadsheet values after it's been found
            spreadsheet_values.pop(column)
        except KeyError:
            pass

    # check for existing blood json values
    for column in blood_json_columns:
        try:
            values = spreadsheet_values[column]
            spreadsheet_metadata['blood_json'][column] = values
            # pop found data from spreadsheet values after it's been found
            spreadsheet_values.pop(column)
        except KeyError:
            pass

    if not spreadsheet_metadata.get('nifti_json', None):
        spreadsheet_metadata['nifti_json'] = {}
    spreadsheet_metadata['nifti_json'].update(spreadsheet_values)

    return spreadsheet_metadata


if __name__ == '__main__':
    update_json_cli()

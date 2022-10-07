import typing
import os
import pathlib
import argparse
import logging
from json_maj.main import JsonMAJ

try:
    import helper_functions
except ModuleNotFoundError:
    import pypet2bids.helper_functions as helper_functions

#from pypet2bids.helper_functions import single_spreadsheet_reader, \
#    collect_bids_part, open_meta_data, load_pet_bids_requirements_json, ParseKwargs


def read_single_subject_spreadsheets(
        general_metadata_spreadsheet: pathlib.Path,
        **kwargs) -> dict:
    """
    Reads in spreadsheet as formatted in PET2BIDS/spreadsheet_conversion/single_subject_sheet,
    extra arguments are supplied in key pair form via kwargs as is convention.

    :format:
    :param general_metadata_spreadsheet: path to a metadatspread sheet containing bids fields as columns
    with values below
    :type general_metadata_spreadsheet: file path
    :param kwargs: additional key pair arguments to pass on, these get applied generally
    just like the first spreadsheet. e.g. TimeZero=12:12:12, SpecificRadioactivity=3
    :type kwargs: string or dict
    :return: dictionary of subject data extracted from each spreadsheet along with any additional
    kwargs supplied
    :rtype: dict
    
    Anthony Galassi
    -----------------------------
    Copyright Open NeuroPET team
    """

    required_fields = helper_functions.load_pet_bids_requirements_json()

    subject_id = kwargs.get('subject_id', None)
    session_id = kwargs.get('session_id', None)

    if general_metadata_spreadsheet.is_file():
        general_metadata = helper_functions.single_spreadsheet_reader(general_metadata_spreadsheet)
        if not subject_id:
            subject_id = helper_functions.collect_bids_part('sub', str(general_metadata_spreadsheet))
            if subject_id:
                general_metadata['subject_id'] = subject_id
        else:
            general_metadata['subject_id'] = subject_id

        if not session_id:
            session_id = helper_functions.collect_bids_part('ses', str(general_metadata_spreadsheet))
            if session_id:
                general_metadata['session_id'] = session_id
        else:
            general_metadata['session_id'] = session_id

        column_set = list(general_metadata.keys())
        # assert required columns are in input spreadsheets
        for k in required_fields.keys():
            for field in required_fields[k]:
                field_exists = field in column_set
                if k == 'mandatory' and not field_exists:
                    logging.warning(f"Input spreadsheet {general_metadata_spreadsheet} is missing required "
                                    f"column {field}")
                elif k == 'recommended' and not field_exists:
                    logging.info(f"Input spreadsheet(s) {general_metadata_spreadsheet} and is missing "
                                 f"recommended column {field}")
                elif k == 'optional':
                    logging.info(f"Input spreadsheet(s) {general_metadata_spreadsheet} is missing "
                                 f"optional column {field}")

        # check to see if there's a subject column in the multi subject data
        accepted_column_names = ['participant_id', 'participant', 'subject', 'subject_id']
        columns = helper_functions.open_meta_data(metadata_path=general_metadata_spreadsheet).columns
        found_column_names = []
        for acceptable in accepted_column_names:
            if acceptable in columns:
                found_column_names.append(acceptable)

        if len(found_column_names) > 1:
            error_message = f"single_subject_spreadsheet: {general_metadata_spreadsheet} must contain only one column " \
                            f"of the following names: "
            for name in accepted_column_names:
                error_message += name + " "
            error_message += f"\nContains these instead {found_column_names}."
            raise Exception(error_message)
        elif len(found_column_names) >= 0 and subject_id:
            if len(found_column_names) > 0:
                logging.warning(f"Found subject id in filepath {general_metadata_spreadsheet} and column(s) "
                                f"{found_column_names}. Defaulting to the value {subject_id} found in the file path "
                                f"{general_metadata_spreadsheet}.")
        elif len(found_column_names) == 1 and not subject_id:
            subject_id_column = found_column_names[0]
            subject_id = general_metadata.pop(subject_id_column)
            general_metadata['subject_id'] = subject_id

        return general_metadata

    else:
        raise FileNotFoundError(general_metadata_spreadsheet)


def write_single_subject_spreadsheets(subject_metadata: dict, output_path: typing.Union[str, pathlib.Path],
                                      create_bids_tree: bool = False) -> str:
    """
    Writes out a dictionary of subjects to a series of json files, if files exist updates
    them with new values obtained from spreadsheets.
    :param subject_metadata: dictionary primary keys and all bids fields as values
    :type subject_metadata: dict
    :param output_path: path to write out files to, very much required
    :type output_path: str or pathlib.Path object
    :param create_bids_tree: boolean flag to create a bids tree, function will do it's best
        to create subject folders and session folders along w/ pet modality folder if this option is
        specified. Works on existing bids if session and subject id can be parsed from
        subject_metadata.
    :type create_bids_tree: bool
    :return: path to written json file
    :rtype: str
    """

    subject_id = subject_metadata.get('subject_id', None)
    if subject_id:
        subject_metadata.pop('subject_id')
    else:
        subject_id = helper_functions.collect_bids_part('sub', output_path)

    session_id = subject_metadata.get('session_id', None)
    if session_id:
        subject_metadata.pop('session_id')
    else:
        session_id = helper_functions.collect_bids_part('ses', output_path)

    if create_bids_tree:
        if subject_id not in output_path.parts:
            output_path = output_path / subject_id
        if session_id:
            json_out_file_name = subject_id + "_" + f"{session_id}_pet.json"
            if session_id not in output_path.parts:
                output_path = output_path / session_id
        else:
            json_out_file_name = subject_id + "_pet.json"

        if output_path.parts[-1] != 'pet':
            output_path = output_path / 'pet'

        output_path.mkdir(parents=True, exist_ok=True)

        JsonMAJ(json_path=os.path.join(output_path, json_out_file_name), update_values=subject_metadata).update()
    else:
        output_path.expanduser().mkdir(exist_ok=True, parents=True)
        json_out_path = os.path.join(output_path, f"{subject_id}")
        if session_id:
            json_out_path += f"_{session_id}_pet.json"
        else:
            json_out_path += '_pet.json'

        JsonMAJ(json_path=json_out_path, update_values=subject_metadata).update()

    return None


def cli():
    """
    Instantiates a command line interface with which allows reading and writing of
    a spreadsheet following the format specified in PET2BIDS/spreadsheet_conversion/single_subject_sheet/ to a json
    :return: a dictionary version of the subject sidecar json's that get written out
    :rtype: dict
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("spreadsheet", type=pathlib.Path,
                        help="Path to a spreadsheet with data applicable to mulitiple subjects")
    parser.add_argument("--output-path", "-o", type=pathlib.Path)
    parser.add_argument("--bids-tree", "-b", action='store_true')
    parser.add_argument("--kwargs", "-k", nargs="*", action=helper_functions.ParseKwargs, default={})
    args = parser.parse_args()
    subject = read_single_subject_spreadsheets(
        general_metadata_spreadsheet=args.spreadsheet,
        **args.kwargs)
    if args.output_path:
        output_path = args.output_path.expanduser()
    else:
        output_path = pathlib.Path(os.getcwd())

    write_single_subject_spreadsheets(output_path=output_path.expanduser(),
                                      subject_metadata=subject,
                                      create_bids_tree=args.bids_tree)

    return subject


if __name__ == '__main__':
    x = cli()

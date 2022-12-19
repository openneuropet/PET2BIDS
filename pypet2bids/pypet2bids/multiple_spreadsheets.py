from json_maj.main import JsonMAJ

try:
    from pypet2bids.helper_functions import *
except ModuleNotFoundError:
    from helper_functions import *


def read_multi_subject_spreadsheets(
        general_metadata_spreadsheet: pathlib.Path,
        multiple_subject_spreadsheet: pathlib.Path,
        **kwargs) -> dict:
    """
    Reads in two spreadsheets as formatted in PET2BIDS/spreadsheet_conversion/many_subject_sheets,
    generic (scanner or subject independent data is supplied via the first argument and subject
    specific data is supplied via the second argument.

    :param general_metadata_spreadsheet: path to a metadata spreadsheet containing bids fields as columns
    with values below
    :type general_metadata_spreadsheet: file path
    :param multiple_subject_spreadsheet: path to multi subject spreadsheet containing a subject id, participant id,
    subject, or participant column consisting of paths to subject folders/files.
    :type multiple_subject_spreadsheet: file path
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

    required_fields = load_pet_bids_requirements_json()

    if general_metadata_spreadsheet.is_file() and multiple_subject_spreadsheet.is_file():
        general_metadata = single_spreadsheet_reader(general_metadata_spreadsheet)
        multiple_subject_metadata = open_meta_data(multiple_subject_spreadsheet)
        multiple_subject_metadata

        column_set = set(list(general_metadata.keys()) + list(multiple_subject_metadata.columns))

        column_set = list(column_set)

        # assert required columns are in input spreadsheets
        for k in required_fields.keys():
            for field in required_fields[k]:
                field_exists = field in column_set
                if k == 'mandatory' and not field_exists:
                    logging.warning(f"Input spreadsheet(s) {general_metadata_spreadsheet} and "
                                    f"{multiple_subject_spreadsheet} are missing required column {field}")
                elif k == 'recommended' and not field_exists:
                    logging.info(f"Input spreadsheet(s) {general_metadata_spreadsheet} and "
                                 f"{multiple_subject_spreadsheet} are missing recommended column {field}")
                elif k == 'optional':
                    logging.info(f"Input spreadsheet(s) {general_metadata_spreadsheet} and "
                                 f"{multiple_subject_spreadsheet} are missing optional column {field}")

        # check to see if there's a subject column in the multi subject data
        accepted_column_names = ['participant_id', 'participant', 'subject', 'subject_id']
        found_column_names = []
        for acceptable in accepted_column_names:
            if acceptable in multiple_subject_metadata.columns:
                found_column_names.append(acceptable)

        if len(found_column_names) != 1:
            error_message = f"multi-subject_spreadsheet: {multiple_subject_spreadsheet} must contain only one column " \
                            f"of the following names: "
            for name in accepted_column_names:
                error_message += name + " "
            error_message += f"\nContains these instead {found_column_names}."
            raise Exception(error_message)
        else:
            subject_column = found_column_names[0]

        # collect all subject id's
        subject_metadata = {}
        for subject in multiple_subject_metadata.get(subject_column, None):
            subject_row = get_coordinates_containing(subject, multiple_subject_metadata, single=True)[0]
            subject_id = collect_bids_part('sub', subject)
            session_id = collect_bids_part('ses', subject)
            if subject_id:
                subject_metadata[subject_id] = general_metadata
                if session_id:
                    subject_metadata[subject_id]['session_id'] = session_id
                if kwargs:
                    subject_metadata[subject_id].update(**kwargs)

                subject_data_from_row = transform_row_to_dict(subject_row, multiple_subject_metadata)
                for k, v in subject_data_from_row.items():
                    if v and k != subject_column and v is not numpy.nan:
                        subject_metadata[subject_id][k] = v

        return subject_metadata

    else:
        missing_files = \
            [missing for missing in (general_metadata_spreadsheet, multiple_subject_spreadsheet)
             if not missing.is_file()]
        error_message = f"Missing "
        for m in missing_files:
            error_message += f'{m=}'.split('=')[0]
            error_message += f' {m}'
        raise Exception(error_message)


def write_multi_subject_spreadsheets(subjects: dict, output_path: typing.Union[str, pathlib.Path],
                                     create_bids_tree: bool = False) -> None:
    """
    Writes out a dictionary of subjects to a series of json files, if files exist updates
    them with new values obtained from spreadsheets.

    :param subjects: subject dictionary with subject id as primary keys and all bids fields as values
    :type subjects: dict
    :param output_path: path to write out files to, very much required
    :type output_path: str or pathlib.Path object
    :param create_bids_tree: boolean flag to create a bids tree, function will do it's best
        to create subject folders and session folders along w/ pet modality folder if this option is
        specified. Works on existing bids trees so long as session and subject id can be parsed from
        multi subject input sheet.
    :type create_bids_tree: bool
    :return: None
    :rtype: None
    """
    if create_bids_tree:
        for subject, fields in subjects.items():
            json_out_path = os.path.join(output_path, f"{subject}")
            if fields.get('session_id', None):
                json_out_file_name = subject + "_" + f"{fields.get('session_id')}_pet.json"
                json_out_path = os.path.join(json_out_path, fields.get('session_id'), 'pet')
            else:
                json_out_file_name = subject + "_pet.json"
                json_out_path = os.path.join(json_out_path, 'pet')
            pathlib.Path(json_out_path).mkdir(parents=True, exist_ok=True)
            json_out_file_name = os.path.join(json_out_path, json_out_file_name)
            json_out = JsonMAJ(json_path=json_out_file_name, update_values=fields).update()
    else:
        for subject, fields in subjects.items():
            json_out_path = os.path.join(output_path, f"{subject}")
            if fields.get('session_id', None):
                json_out_path += f"{fields.get('session_id')}_pet.json"
            else:
                json_out_path += '_pet.json'

            json_out = JsonMAJ(json_path=json_out_path, update_values=fields).update()


def cli():
    """
    Instantiates a command line interface with which allows reading and writing of
    2 spreadsheets following the format specified in PET2BIDS/spreadsheet_conversion/many_subjects_sheet
    :return: a dictionary version of the subject sidecar json's that get written out
    :rtype: dict
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--general-spreadsheet", '-g', type=pathlib.Path,
                        help="Path to a spreadsheet with data applicable to mulitiple subjects")
    parser.add_argument("--many-subjects-spreadsheet", '-m', type=pathlib.Path,
                        help="Path to spreadsheet containing multiple subjects")
    parser.add_argument("--output-path", "-o", type=pathlib.Path)
    parser.add_argument("--bids-tree", "-b", action='store_true')
    args = parser.parse_args()
    subjects = read_multi_subject_spreadsheets(
        general_metadata_spreadsheet=args.general_spreadsheet,
        multiple_subject_spreadsheet=args.many_subjects_spreadsheet)
    if args.output_path:
        output_path = args.output_path
    else:
        output_path = os.getcwd()

    write_multi_subject_spreadsheets(output_path=output_path, subjects=subjects, create_bids_tree=args.bids_tree)

    return subjects


if __name__ == '__main__':
    x = cli()

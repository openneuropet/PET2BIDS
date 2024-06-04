try:
    import ecat
    import write_ecat
    import read_ecat
    import helper_functions
except ImportError:
    from pypet2bids.ecat import ecat
    from pypet2bids.write_ecat import write_ecat
    from pypet2bids.read_ecat import read_ecat
    from pypet2bids import helper_functions

# collect ecat header jsons
ecat_headers = read_ecat.ecat_header_maps.get("ecat_headers")


def update_ecat_header(ecat_file: str, new_values: dict):
    """
    Update the header of an ECAT file with new values
    :param ecat_file: path to the ECAT file
    :param new_values: dictionary of new values to update
    :param ecat_header: dictionary of the ECAT header
    :return: None
    """

    # read ecat and determine version of ecat file
    print(f"Reading ECAT file {ecat_file}")
    infile = ecat.Ecat(ecat_file)

    # collect the appropriate header schema
    sw_version = str(infile.ecat_header.get("SW_VERSION", 73))

    infile_header_map = ecat_headers[sw_version]["mainheader"]

    # iterate through new values and update the header
    for name, value in new_values.items():
        if infile.ecat_header.get(name):
            if type(infile.ecat_header[name]) == type(value):
                infile.ecat_header[name] = value
            else:
                print(
                    f"WARNING: {name} has type {type(infile.ecat_header[name])} "
                    f"and new value {value} has type {type(value)}"
                )
        else:
            print(
                f"WARNING: {name} not found in header schema for ECAT {ecat_headers.ecat_header.get('SW_VERSION', 73)} "
                f"not updating with value {value}"
            )

    # update the header of the ecat file in question
    with open(infile.ecat_file, "r+b") as outfile:
        write_ecat.write_header(
            ecat_file=outfile, schema=infile_header_map, values=infile.ecat_header
        )


def cli():
    import argparse

    parser = argparse.ArgumentParser(description="Update the header of an ECAT file.")
    parser.add_argument("ecat_file", type=str, help="path to the ECAT file")
    parser.add_argument(
        "new_values",
        nargs="*",
        action=helper_functions.ParseKwargs,
        default={},
        help="new values to update the MAINHEADER of the ecat file, e.g. NUM_FRAMES=71 "
        "or CALIBRATION_FACTOR=0.5. "
        'or STUDY_DESCRIPTION="very important work"'
        "If the value is a string, it must be in quotes.",
    )
    args = parser.parse_args()
    update_ecat_header(ecat_file=args.ecat_file, new_values=args.new_values)


if __name__ == "__main__":
    cli()

from thisbytes import *


if __name__ == "__main__":
    """
    Verifying that the byte positions and widths correspond to their datatype size as 
    stated in ecat_headers.json (this is mostly a sanity check).
    """
    check_header_json = False

    if check_header_json:
        for header, header_values in ecat_header_maps['ecat_headers'].items():

            print(header)
            byte_position = 0

            for each in header_values:
                print(each.get('byte'), each.get('variable_name'), each.get('type'), get_buffer_size(each.get('type'), each.get('variable_name')), byte_position)
                if byte_position != each.get('byte'):
                    print(f"Mismatch in {header} between byte position {each.get('byte')} and calculated position {byte_position}.")
                    try:
                        paren_error = re.findall(r'^.*?\([^\d]*(\d+)[^\d]*\).*$', each.get('variable_name'))
                    except TypeError:
                        pass
                byte_position = get_buffer_size(each['type'], each['variable_name']) + byte_position

    check_byte_reading = True
    if check_byte_reading:
        from dotenv import load_dotenv, find_dotenv

        # load a test ecat file (this really should live at a url somewhere)
        load_dotenv(find_dotenv())
        ecat_test_file = os.environ.get("TEST_ECAT_PATH")

        test_ecat = read_ecat_7(ecat_file=ecat_test_file)
        print("READ IT")
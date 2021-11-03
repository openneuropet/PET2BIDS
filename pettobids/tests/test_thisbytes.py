from pettobids.read_ecat import *
from dotenv import load_dotenv

parent_dir = pathlib.Path(__file__).parent.resolve()
env_path = parent_dir.parent.resolve().joinpath('.env')

if __name__ == "__main__":
    """
    Verifying that the byte positions and widths correspond to their datatype size as 
    stated in ecat_headers.json (this is mostly a sanity check). The most likely error to
    occur is from the user during json/schema creation. This test does some simple math 
    to verify the byte width between, say byte 4 and 8 corresponds to the length of an 
    integer2. This script is run at the command line and simply grepped to determine if 
    a mismatch occurs. 
    
    usage:
    > python test_thisbytes.py | grep Mismatch
    
    Manual test, but still fairly useful.
    
    """
    check_header_json = True

    if check_header_json:

        for header, header_values in ecat_header_maps['ecat_headers'].items():
            for header_name, header_map in header_values.items():
                byte_position = 0
                print(header + " " + header_name)
                for each in header_map:
                    print(each.get('byte'), each.get('variable_name'), each.get('type'), get_buffer_size(each.get('type'), each.get('variable_name')), byte_position)
                    if byte_position != each.get('byte'):
                        print(f"Mismatch in {header} between byte position {each.get('byte')} and calculated position {byte_position}.")
                        try:
                            paren_error = re.findall(r'^.*?\([^\d]*(\d+)[^\d]*\).*$', each.get('variable_name'))
                        except TypeError:
                            pass
                    byte_position = get_buffer_size(each['type'], each['variable_name']) + byte_position

    """
    Checking reading of ECAT header and subheader, only works if there exists a  ../.env w/ TEST_ECAT_PATH=<pathtoecat>
    or if the environment variable TEST_ECAT_PATH is set to a valid ecat
    """
    check_byte_reading = False
    if check_byte_reading:

        load_dotenv(env_path)
        ecat_test_file = os.environ.get("TEST_ECAT_PATH")

        test_main_header, test_subheaders, test_data = read_ecat(ecat_file=ecat_test_file)
        print(f"Main header info:")
        for k, v in test_main_header.items():
            print(f"{k}: {v}")
        print(f"Sub-header info:")

        for subheader in test_subheaders:
            for k, v in subheader.items():
                print(f"{k}: {v}")
        print(f"Image Data, Dimensions {test_data.shape}, Datatype {test_data.dtype}")
        print(test_data)
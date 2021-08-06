from ecat import Ecat
import dotenv
import os
from datetime import datetime

# collect path to test ecat file
dotenv.load_dotenv(dotenv.find_dotenv())  # load path from .env file into env
ecat_path = os.environ['TEST_ECAT_PATH']
nifti_path = os.environ['OUTPUT_NIFTI_PATH']

if __name__ == '__main__':
    """
    More manual testing of nifti writing functions works for now as there is no public or frozen dataset to test on
    that is accessible by CI. Requires a .env file with the following fields:
    
    TEST_ECAT_PATH=<path to a valid ecat>
    OUTPUT_NIFTI_PATH=<desired output path>
    
    usage:
    > python test_nifti_write.py
    
    or more likely this gets run w/ a debugger in an IDE such as pycharm or vs code.
    
    """
    read_and_write = Ecat(ecat_file=ecat_path, nifti_file=nifti_path)
    time_zero = datetime.fromtimestamp(read_and_write.ecat_header['DOSE_START_TIME']).strftime('%I:%M:%S')
    nifti_path = read_and_write.make_nifti()
    read_and_write.populate_sidecar()
    read_and_write.prune_sidecar()

    read_and_write.show_sidecar(os.path.join(os.path.dirname(nifti_path),
                                             os.path.basename(nifti_path),) + '.json')

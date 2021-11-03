import pickle

from pettobids.ecat import Ecat
import dotenv
import os
from datetime import datetime
from pettobids.ecat2nii import ecat2nii
from nibabel import load
import numpy

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
    read_and_write.populate_sidecar()
    read_and_write.prune_sidecar()

    read_and_write.show_sidecar(os.path.join(os.path.dirname(nifti_path),
                                             os.path.basename(nifti_path),) + '.json')

    # testing how much this image gets mangled w/ nifti conversion
    # write nifti and save binary of nibabel.Nifti1 object
    read_from_ecat_but_not_written = ecat2nii(ecat_file=ecat_path, nifti_file=nifti_path, save_binary=True, sif_out=True)

    # load pickled object why not?
    pickled_nifti = pickle.load(open(nifti_path + ".pickle", 'rb'))

    # collect nifti from written out file
    written_nifti = load(nifti_path)

    # compare what write does
    difference = read_from_ecat_but_not_written.dataobj - written_nifti.dataobj

    # compare pickle vs written
    pickle_difference = pickled_nifti.dataobj - read_from_ecat_but_not_written.dataobj

    # are these the same?
    all_zero = numpy.all(difference == 0.0)
    if all_zero:
        print("They the same")
    else:
        raise Exception("Something is happening.")

    pickle_zero = numpy.all(pickle_difference == 0.0)

    if pickle_zero:
        print("Pickle difference zero.")
    else:
        raise Exception("Pickle differs from returned nifti from ecat2nii function.")









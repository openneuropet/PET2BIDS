import scipy.io.matlab.miobase
from pettobids.read_ecat import read_ecat
from scipy.io import savemat
import dotenv
import os
import nibabel

"""
This script reads in an ecat file from .env/environment variable 'TEST_ECAT_PATH' and saves the pixel data into a 
.mat file located at the variable found in the .env/environment variable 'READ_ECAT_SAVE_AS_MATLAB' and attempts to 
repeat this operation using nibabel's ecat.load and storing the output at 'NIBABEL_READ_ECAT_SAVE_AS_MATLAB'.

The error handling for the nibabel write to matlab demonstrate that saving the larger nibabel generated array can fail
with a sufficiently large ecat file.
"""


# collect path to test ecat file
dotenv.load_dotenv(dotenv.find_dotenv())  # load path from .env file into env
ecat_path = os.environ['TEST_ECAT_PATH']
read_ecat_save_as_matlab = os.environ['READ_ECAT_SAVE_AS_MATLAB']
nibabel_read_ecat_save_as_matlab = os.environ['NIBABEL_READ_ECAT_SAVE_AS_MATLAB']

# read in the ecat
ecat_main_header, ecat_subheaders, ecat_image = read_ecat(ecat_file=ecat_path)

# read in the ecat with nibabel
nibabel_ecat = nibabel.ecat.load(ecat_path)
# extract the image data from nibabel
nibabel_data = nibabel_ecat.get_fdata()

# save the read ecat pixel object as a matlab object for comparison
matlab_dictionary = {'data': ecat_image}
savemat(read_ecat_save_as_matlab, matlab_dictionary)
print(f"Saved read ecat datastructure as matlab matrix at:\n{read_ecat_save_as_matlab}")

# save the nibabel ecat read as matlab object for comparison
matlab_dictionary = {'nibabel_data': nibabel_data}
try:
    savemat(nibabel_read_ecat_save_as_matlab, matlab_dictionary, do_compression=True)
    print(f"Saved read ecat datastructure as matlab matrix at:\n{nibabel_read_ecat_save_as_matlab}")
except scipy.io.matlab.miobase.MatWriteError as err:
    print(f"Unable to write nibabel array of size {nibabel_data.shape} and "
          f"datatype {nibabel_data.dtype} to matlab .mat file")
    print(err)



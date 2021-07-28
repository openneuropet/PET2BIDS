import unittest
from ecat_dump import EcatDump
import dotenv
import os
from datetime import datetime
from ecat2nii import ecat2nii
from dateutil import parser
# collect path to test ecat file
dotenv.load_dotenv(dotenv.find_dotenv())  # load path from .env file into env
ecat_path = os.environ['ECAT_PATH']

if __name__ == '__main__':
    read_and_write = EcatDump(ecat_path)
    time_zero = datetime.fromtimestamp(read_and_write.ecat_header['dose_start_time']).strftime('%I:%M:%S')
    img_data = read_and_write.ecat.get_fdata()
    read_and_write.make_nifti()

    # now test ecat2nii
    ecat2nii(ecat_path)
    print('done')

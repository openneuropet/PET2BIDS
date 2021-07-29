import unittest
from ecat_dump import EcatDump
import dotenv
import os
from datetime import datetime
from ecat2nii import ecat2nii

# collect path to test ecat file
dotenv.load_dotenv(dotenv.find_dotenv())  # load path from .env file into env
ecat_path = os.environ['ECAT_PATH']

if __name__ == '__main__':
    new_fields = {'FakeField1': 1, 'FakeField2': 'two'}
    read_and_write = EcatDump(ecat_path, **new_fields)
    time_zero = datetime.fromtimestamp(read_and_write.ecat_header['DOSE_START_TIME']).strftime('%I:%M:%S')
    read_and_write.populate_sidecar()
    read_and_write.make_nifti()
    read_and_write.prune_sidecar()

    # now test ecat2nii
    ecat2nii(ecat_path)
    print('done')

import unittest
from ecat_dump import EcatDump
import dotenv
import os
from datetime import datetime
from dateutil import parser
# collect path to test ecat file
dotenv.load_dotenv(dotenv.find_dotenv())  # load path from .env file into env
ecat_path = os.environ['ECAT_PATH']


#class MyTestCase(unittest.TestCase):
#    def test_something(self):
#        self.assertEqual(True, False)


if __name__ == '__main__':
    #unittest.main()
    read_and_write = EcatDump(ecat_path)
    time_zero = datetime.fromtimestamp(read_and_write.ecat_header['dose_start_time']).strftime('%I:%M:%S')
    img_data = read_and_write.ecat.get_fdata()
    read_and_write.make_nifti()

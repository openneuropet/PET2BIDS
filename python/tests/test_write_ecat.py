import os
import unittest
from write_ecat import create_directory_table, write_header, write_directory_table, write_pixel_data
from read_ecat import read_ecat, get_directory_data, read_bytes, ecat_header_maps
import numpy
import dotenv

dotenv.load_dotenv(dotenv.load_dotenv())


class TestECATWrite(unittest.TestCase):
    @classmethod
    def setUp(cls) -> None:
        cls.known_main_header, cls.known_subheaders, cls.known_pixel_data = read_ecat(os.environ['TEST_ECAT_PATH'],
                                                                                      collect_pixel_data=False)
        # collect directory table from ecat
        directory_block = read_bytes(path_to_bytes=os.environ['TEST_ECAT_PATH'],
                                     byte_start=512,
                                     byte_stop=1024)
        cls.known_directory_table = get_directory_data(directory_block, os.environ['TEST_ECAT_PATH'])
        cls.pixel_byte_size_int = 2

    def test_create_directory_table(self):

        pixel_dimensions = {
            'x': self.known_subheaders[0]['X_DIMENSION'],
            'y': self.known_subheaders[0]['Y_DIMENSION'],
            'z': self.known_subheaders[0]['Z_DIMENSION']
        }

        generated_directory_table = create_directory_table(self.known_main_header['NUM_FRAMES'],
                                                           pixel_dimensions,
                                                           pixel_byte_size=self.pixel_byte_size_int)

        # dimensions of directory should be 4 x 64
        self.assertEqual(generated_directory_table[0].shape, (4, 64))
        # data type should be int 32
        self.assertTrue(generated_directory_table[0].dtype == numpy.dtype('>i4'))
        # assert spacing between dimensions is correct
        width = (generated_directory_table[0][2,1] - generated_directory_table[0][1,1]) * 512
        calculated_width = \
            pixel_dimensions['x'] * pixel_dimensions['y'] * pixel_dimensions['z'] * self.pixel_byte_size_int
        self.assertEqual(width, calculated_width)
        self.assertTrue(generated_directory_table[0][2, 0] == 0)
        self.assertTrue(generated_directory_table[1][2, 0] == 2)

    def test_write_header(self):
        tempfile = 'test_write_header.b'
        import shutil
        shutil.copy(os.environ['TEST_ECAT_PATH'], tempfile)
        with open(tempfile, 'r+b') as outfile:
            schema = ecat_header_maps['ecat_headers']['73']['mainheader']
            write_header(
                ecat_file=outfile,
                schema=schema,
                values=self.known_main_header)

        # now read the file w ecat read to see if it's changed.
        check_header, check_subheaders, check_pixel_data = read_ecat(tempfile, collect_pixel_data=False)

        os.remove(tempfile)
        for key, value in self.known_main_header.items():
            if 'fill' not in str.lower(key):
                self.assertEqual(self.known_main_header[key], check_header[key])

    def test_write_pixel_data(self):
        pass


if __name__ == '__main__':
    unittest.main()

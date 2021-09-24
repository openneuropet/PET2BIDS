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
                                     byte_stop=512)
        cls.known_directory_table = get_directory_data(directory_block, os.environ['TEST_ECAT_PATH'])
        cls.known_directory_table_raw = get_directory_data(directory_block, os.environ['TEST_ECAT_PATH'], return_raw=True)
        cls.pixel_byte_size_int = 2
        cls.temp_file = 'test_tempfile.v'
        cls.pixel_dimensions = {
            'x': cls.known_subheaders[0]['X_DIMENSION'],
            'y': cls.known_subheaders[0]['Y_DIMENSION'],
            'z': cls.known_subheaders[0]['Z_DIMENSION']
        }

    def test_create_directory_table(self):

        generated_directory_table = create_directory_table(self.known_main_header['NUM_FRAMES'],
                                                           self.pixel_dimensions,
                                                           pixel_byte_size=self.pixel_byte_size_int)

        # dimensions of directory should be 4 x 64
        self.assertEqual(generated_directory_table[0].shape, (4, 32))
        # data type should be int 32
        self.assertTrue(generated_directory_table[0].dtype == numpy.dtype('>i4'))
        # assert spacing between dimensions is correct
        width = (generated_directory_table[0][2, 1] - generated_directory_table[0][1, 1]) * 512
        calculated_width = \
            self.pixel_dimensions['x'] * self.pixel_dimensions['y'] * self.pixel_dimensions['z'] * self.pixel_byte_size_int
        self.assertEqual(width, calculated_width)
        self.assertTrue(generated_directory_table[0][2, 0] == 0)
        self.assertTrue(generated_directory_table[1][2, 0] == 2)

    def test_write_header(self):
        temp_file = self.temp_file
        import shutil
        shutil.copy(os.environ['TEST_ECAT_PATH'], temp_file)
        with open(temp_file, 'r+b') as outfile:
            schema = ecat_header_maps['ecat_headers']['73']['mainheader']
            write_header(
                ecat_file=outfile,
                schema=schema,
                values=self.known_main_header)

        # now read the file w ecat read to see if it's changed.
        check_header, check_subheaders, check_pixel_data = read_ecat(temp_file, collect_pixel_data=False)

        os.remove(temp_file)
        for key, value in self.known_main_header.items():
            self.assertEqual(self.known_main_header[key], check_header[key])

    def test_write_directory_table(self):
        import shutil
        shutil.copy(os.environ['TEST_ECAT_PATH'], self.temp_file)
        with open(self.temp_file, 'r+b') as outfile:
            # write header
            schema = ecat_header_maps['ecat_headers']['73']['mainheader']
            write_header(ecat_file=outfile,
                         schema=schema,
                         values=self.known_main_header)

            directory_table = create_directory_table(self.known_main_header['NUM_FRAMES'],
                                                     pixel_dimensions=self.pixel_dimensions,
                                                     pixel_byte_size=self.pixel_byte_size_int
                                                     )
            write_directory_table(outfile, directory_table)

        # collect newly written directory table from temp file

        directory_block = read_bytes(path_to_bytes=self.temp_file,
                                     byte_start=512,
                                     byte_stop=512)
        just_written_directory_table = get_directory_data(directory_block, self.temp_file, return_raw=True)
        # dimensions of directory should be 4 x 64
        self.assertEqual(just_written_directory_table[0].shape, (4, 32))
        # data type should be int 32
        self.assertTrue(just_written_directory_table[0].dtype == numpy.dtype('>i4'))
        # assert spacing between dimensions is correct
        width = (just_written_directory_table[0][2, 1] - just_written_directory_table[0][1, 1]) * 512
        calculated_width = \
            self.pixel_dimensions['x'] * self.pixel_dimensions['y'] * self.pixel_dimensions[
                'z'] * self.pixel_byte_size_int
        self.assertEqual(width, calculated_width)
        self.assertTrue(just_written_directory_table[0][2, 0] == 0)
        self.assertTrue(just_written_directory_table[1][2, 0] == 2)

        # assert additional directory table was created at correct byte position
        if len(directory_table) > 1:
            directory_block = read_bytes(path_to_bytes=self.temp_file,
                                         byte_start=(just_written_directory_table[0][1, 0] -1) * 512,
                                         byte_stop=512)
            additional_directory_table = numpy.frombuffer(directory_block, dtype=numpy.dtype('>i4'), count=-1)
            additional_directory_table = numpy.transpose(numpy.reshape(additional_directory_table, (-1, 4)))
            numpy.testing.assert_array_equal(additional_directory_table, directory_table[1])


if __name__ == '__main__':
    unittest.main()

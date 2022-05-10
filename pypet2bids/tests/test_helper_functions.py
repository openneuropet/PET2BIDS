import collections
import tempfile
import unittest
import pypet2bids.helper_functions as helper_functions
from os import remove
import pandas
from pathlib import Path
from os.path import join

# collect config files
# fields to check for
module_folder = Path(__file__).parent.resolve()
python_folder = module_folder.parent
pet2bids_folder = python_folder.parent
metadata_folder = join(pet2bids_folder, 'spreadsheet_conversion')
single_subject_metadata_file = join(metadata_folder, 'single_subject_sheet', 'subject_metadata_example.xlsx')

class TestHelperFunctions(unittest.TestCase):
    @classmethod
    def setUp(cls) -> None:
        test_config_string = '''
        test_int=0
        test_int_list=[1,2,3,4]
        test_float=99.9
        test_float_list=[1.0,2.0,3.0,4.0]
        test_string=CharlieWorks
        test_string_list=['entry1', 'entry2', 'entry3', 'entry4']
        test_mixed_list=['a', 1, 2.0, 'longstring']
        '''
        cls.test_env_file_path = '.test_env'
        with open(cls.test_env_file_path, 'w') as outfile:
            outfile.write(test_config_string)

        cls.test_load = helper_functions.load_vars_from_config(cls.test_env_file_path)

    def test_load_vars_from_config(self):
        self.test_load = helper_functions.load_vars_from_config(self.test_env_file_path)
        self.assertEqual(type(self.test_load), collections.OrderedDict)  # add assertion here

    def test_int(self):
        self.assertEqual(self.test_load['test_int'], 0)

    def test_float(self):
        self.assertEqual(self.test_load['test_float'], 99.9)

    def test_int_list(self):
        self.assertEqual(self.test_load['test_int_list'], [1, 2, 3, 4])

    def test_float_list(self):
        self.assertEqual(self.test_load['test_float_list'], [1.0, 2.0, 3.0, 4.0])

    def test_string(self):
        self.assertEqual(self.test_load['test_string'], 'CharlieWorks')

    def test_string_list(self):
        self.assertEqual(self.test_load['test_string_list'],
                         ['entry1', 'entry2', 'entry3', 'entry4'])

    def test_mixed_list(self):
        self.assertEqual(self.test_load['test_mixed_list'],
                         ['a', 1, 2.0, 'longstring'])

    @classmethod
    def tearDown(cls) -> None:
        remove(cls.test_env_file_path)

def test_open_metadata():
    # read in a known metadata spreadsheet
    test_dataframe = pandas.read_excel(single_subject_metadata_file)

    # read in the the same dataframe using the helper function
    metadata_dataframe = helper_functions.open_meta_data(single_subject_metadata_file)

    # assert that open metadata opens an excel spreadsheet
    pandas.testing.assert_frame_equal(test_dataframe, metadata_dataframe)

    # write the excel spreadsheet data to a csv and make sure the open_meta_data function
    # still works on that
    with tempfile.TemporaryDirectory():
        pass

def test_translate_metadata():
    test_translate_script_path = join(module_folder, 'metadata_excel_example_reader.py')

    test_output = helper_functions.translate_metadata(single_subject_metadata_file,test_translate_script_path)

    # values below manually parsed out of the file 'subject_metadata_example.xlsx'
    assert test_output['nifti_json']['ImageDecayCorrectionTime'] == 0
    assert test_output['nifti_json']['ReconMethodName'] == '3D-OSEM-PSF'
    assert test_output['nifti_json']['ReconMethodParameterLabels'] == ['subsets', 'iterations']
    assert test_output['nifti_json']['ReconMethodParameterUnits'] == ['none', 'none']
    assert test_output['nifti_json']['ReconMethodParameterValues'] == [16, 10]
    assert test_output['nifti_json']['ReconFilterType'] == 'none'

if __name__ == '__main__':
    unittest.main()

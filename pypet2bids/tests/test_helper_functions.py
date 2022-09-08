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
multi_subject_metadata_file = join(metadata_folder, 'many_subjects_sheet', 'subjects_metadata_example.xlsx')
scanner_metadata_file = join(metadata_folder, 'many_subjects_sheet', 'scanner_metadata_example.xlsx')

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


def test_collect_bids_parts():
    bids_like_path = '/home/users/user/bids_data/sub-NDAR123/ses-firstsession'
    windows_bids_like_path = 'D:\BIDS\ONP\sub-NDAR123\ses-firstsession\pet'
    subject_id = helper_functions.collect_bids_part('sub', bids_like_path)
    assert subject_id == 'sub-NDAR123'
    assert helper_functions.collect_bids_part('sub', windows_bids_like_path) == 'sub-NDAR123'

    session_id = helper_functions.collect_bids_part('ses', bids_like_path)
    assert session_id == 'ses-firstsession'
    assert helper_functions.collect_bids_part('ses', windows_bids_like_path) == 'ses-firstsession'

    not_bids_like_path = '/home/users/user/no/bids/here'
    nope_sub = helper_functions.collect_bids_part('sub', not_bids_like_path)
    assert nope_sub == ''

    nope_ses = helper_functions.collect_bids_part('ses', not_bids_like_path)
    assert nope_ses == ''


def test_transform_row_to_dict():
    # load real test data from many subject sheet
    many_subjects_dataframe = pandas.read_excel(multi_subject_metadata_file)
    subject_with_frames_time_start_input = many_subjects_dataframe.iloc[0]

    # transform a row
    transformed_row = helper_functions.transform_row_to_dict(subject_with_frames_time_start_input)

    frame_times_start = subject_with_frames_time_start_input['FrameTimesStart'].split(',')
    frame_times_start = [int(entry) for entry in frame_times_start]

    assert frame_times_start == transformed_row['FrameTimesStart']

    # test whole dataframe transform
    transform_row_from_dataframe = helper_functions.transform_row_to_dict(0, many_subjects_dataframe)

    assert frame_times_start == transform_row_from_dataframe['FrameTimesStart']

    # a simpler test
    key = 'FrameTimesStart'
    values = '0,1,2,3,4,5,6'
    simpler_df = pandas.DataFrame({key: [values]})

    assert [int(v) for v in values.split(',')] == helper_functions.transform_row_to_dict(0, simpler_df)['FrameTimesStart']


def test_get_coordinates_containing():
    given_data = {
        'columnA': ['string1', 'string2', 'string3', 'muchlongerstringVALUE'],
        'columnB': [0, 1, 2, 3],
        'columnC': [pandas.NA, 1.2, 3.1, pandas.NA]
    }

    given_dataframe = pandas.DataFrame(given_data)
    get_coords = helper_functions.get_coordinates_containing
    assert get_coords('string3', given_dataframe) == [(2, 'columnA')]
    assert get_coords('string3', given_dataframe, single=True) == (2, 'columnA')
    assert get_coords('notthere', given_dataframe) == []
    assert get_coords('string', given_dataframe) == [(0, 'columnA'), (1, 'columnA'), (2, 'columnA'), (3, 'columnA')]
    assert get_coords(0, given_dataframe, exact=True, single=True) == (0, 'columnB')
    assert get_coords(0, given_dataframe, exact=True) == [(0, 'columnB')]


if __name__ == '__main__':
    unittest.main()

import collections
import unittest
import pypet2bids.helper_functions as helper_functions
from os import remove


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


if __name__ == '__main__':
    unittest.main()

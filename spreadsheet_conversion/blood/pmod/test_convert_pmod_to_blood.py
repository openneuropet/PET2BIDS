import pytest
import pathlib
import os
from convert_pmod_to_blood import PmodToBlood, type_cast_cli_input


def test_type_cast_cli_input():
    assert True == type_cast_cli_input('true')
    assert True == type_cast_cli_input('t')
    assert True == type_cast_cli_input('True')
    assert False == type_cast_cli_input('f')
    assert False == type_cast_cli_input('false')
    assert False == type_cast_cli_input('False')
    assert [1, 2, 3] == type_cast_cli_input('[1, 2, 3]')
    assert [1.0, 2, 3] == type_cast_cli_input('[1.0, 2, 3]')
    assert [1.0, 2.0, 3.0] == type_cast_cli_input('[1.0, 2.0, 3.0]')
    assert ['a', 'b'] == type_cast_cli_input("['a', 'b']")
    assert {'a': 'b'} == type_cast_cli_input("{'a': 'b'}")
    assert 1 == type_cast_cli_input('1')
    assert 1.0 == type_cast_cli_input('1.0')
    assert 'string' == type_cast_cli_input('string')

@pytest.fixture()
def good_blood_files():
    this_files_parent_dir = os.path.dirname(os.path.abspath(__file__))
    bld_files = [os.path.join(this_files_parent_dir, bld) for bld in os.listdir(this_files_parent_dir) if pathlib.Path(bld).suffix == '.bld']
    good_blood_files = {'parent': [], 'plasma': [], 'whole': []}
    for index, bld_file in enumerate(bld_files):
        for key in good_blood_files.keys():
            if key in bld_file:
                good_blood_files[key].append(bld_file)   
        
    yield good_blood_files

class TestPmodToBlood:

    def test_load_files(self, good_blood_files):
        print(good_blood_files)
        assert len(good_blood_files) > 1
        pmod_to_blood = PmodToBlood(
            whole_blood_activity=pathlib.Path(good_blood_files['whole'][0]),
            parent_fraction=pathlib.Path(good_blood_files['parent'][0]),
            plasma_activity = pathlib.Path(good_blood_files['plasma'][0])
        )

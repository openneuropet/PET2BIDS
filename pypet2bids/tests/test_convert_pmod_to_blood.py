import tempfile

import pytest
import pathlib
import os
from unittest.mock import Mock, patch

from pypet2bids.convert_pmod_to_blood import PmodToBlood, type_cast_cli_input


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
def Ex_bld_whole_blood_only_files():
    """
    Only collects blood and plasma files from the folder Ex_bld_whole_blood_only_files as they are all that exist there.
    :return: two files
    :rtype: dict
    """
    this_files_parent_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = pathlib.Path(this_files_parent_dir).parent.parent
    pmod_blood_dir = os.path.join(
        project_dir,
        'spreadsheet_conversion',
        'blood',
        'pmod',
        'Ex_bld_wholeblood_and_plasma_only')
    bld_files = \
        [os.path.join(pmod_blood_dir, bld) for bld in os.listdir(pmod_blood_dir) if pathlib.Path(bld).suffix == '.bld']
    blood_files = {'plasma': [], 'whole': []}
    for index, bld_file in enumerate(bld_files):
        for key in blood_files.keys():
            if key in pathlib.Path(bld_file).name:
                blood_files[key].append(bld_file)
        
    yield blood_files


class TestPmodToBlood:
    # requires manual input, don't run in actions

    def test_load_files(self, Ex_bld_whole_blood_only_files):
        print(Ex_bld_whole_blood_only_files)
        kwargs_input = {
            'whole_blood_activity_collection_method': 'automatic',
            'parent_fraction_collection_method': 'automatic',
            'plasma_activity_collection_method': 'automatic'
            }
        with tempfile.TemporaryDirectory() as tempdir:
            pmod_to_blood = PmodToBlood(
                whole_blood_activity=pathlib.Path(Ex_bld_whole_blood_only_files['whole'][0]),
                plasma_activity=pathlib.Path(Ex_bld_whole_blood_only_files['plasma'][0]),
                output_path=pathlib.Path(tempdir),
                **kwargs_input
            )

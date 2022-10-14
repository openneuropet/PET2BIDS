import tempfile

import pandas
import pytest
import pathlib
import os
from unittest.mock import Mock, patch
from pypet2bids.convert_pmod_to_blood import PmodToBlood, type_cast_cli_input
from pypet2bids.helper_functions import open_meta_data

# resolving paths for the opening of test data, for this module test data is contained in the spreadsheet_conversion
# folder at the top level of the project repository
this_files_parent_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = pathlib.Path(this_files_parent_dir).parent.parent


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


@pytest.fixture()
def Ex_bld_manual_and_autosampled_mixed():
    """
    Collects parent fraction, plasma activity, and whole blood activity from folder Ex_bld_manual_and_autosampled_mixed
    :return: three bld files
    :rtype: dict
    """
    pmod_blood_dir = os.path.join(
        project_dir,
        'spreadsheet_conversion',
        'blood',
        'pmod',
        'Ex_bld_manual_and_autosampled_mixed')
    bld_files = \
        [os.path.join(pmod_blood_dir, bld) for bld in os.listdir(pmod_blood_dir) if pathlib.Path(bld).suffix == '.bld']

    pop_indexes = []
    for f in bld_files:
        if 'ratio' in str(f).lower():
            pop_indexes.append(f)

    for pop in pop_indexes:
        bld_files.remove(pop)

    blood_files = {'plasma': [], 'whole': [], 'parent': []}
    for index, bld_file in enumerate(bld_files):
        for key in blood_files.keys():
            if key in str(pathlib.Path(bld_file).name).lower():
                blood_files[key].append(bld_file)

    yield blood_files


@pytest.fixture()
def Ex_txt_manual_and_autosampled_mixed():
    """
    Collects parent fraction, plasma activity, and whole blood activity from folder Ex_bld_manual_and_autosampled_mixed
    :return: three bld files
    :rtype: dict
    """
    pmod_blood_dir = os.path.join(
        project_dir,
        'spreadsheet_conversion',
        'blood',
        'pmod',
        'Ex_txt_manual_and_autosampled_mixed')

    bld_files = \
        [os.path.join(pmod_blood_dir, bld) for bld in os.listdir(pmod_blood_dir) if pathlib.Path(bld).suffix == '.txt']

    blood_files = {'plasma': [], 'whole': [], 'parent': []}
    for index, bld_file in enumerate(bld_files):
        for key in blood_files.keys():
            if key in str(pathlib.Path(bld_file).name).lower():
                blood_files[key].append(bld_file)

    yield blood_files


class TestPmodToBlood:
    def test_load_bld_files_blood_only(self, Ex_bld_whole_blood_only_files):
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

    def test_load_bld_files_mixed(self, Ex_bld_manual_and_autosampled_mixed):
        kwargs_input = {
            'whole_blood_activity_collection_method': 'automatic',
            'parent_fraction_collection_method': 'manual',
            'plasma_activity_collection_method': 'automatic'
        }

        with tempfile.TemporaryDirectory() as tempdir:
            pmod_to_blood = PmodToBlood(
                whole_blood_activity=pathlib.Path(Ex_bld_manual_and_autosampled_mixed['whole'][0]),
                plasma_activity=pathlib.Path(Ex_bld_manual_and_autosampled_mixed['plasma'][0]),
                parent_fraction=pathlib.Path(Ex_bld_manual_and_autosampled_mixed['parent'][0]),
                output_path=tempdir,
                **kwargs_input
            )

    def test_bld_output_manual_popped_values(self, Ex_bld_manual_and_autosampled_mixed):
        kwargs_input = {
            'whole_blood_activity_collection_method': 'automatic',
            'parent_fraction_collection_method': 'manual',
            'plasma_activity_collection_method': 'automatic'
        }

        # test bld (pmod files first)
        with tempfile.TemporaryDirectory() as tempdir:
            pmod_to_blood = PmodToBlood(
                whole_blood_activity=pathlib.Path(Ex_bld_manual_and_autosampled_mixed['whole'][0]),
                plasma_activity=pathlib.Path(Ex_bld_manual_and_autosampled_mixed['plasma'][0]),
                parent_fraction=pathlib.Path(Ex_bld_manual_and_autosampled_mixed['parent'][0]),
                output_path=tempdir,
                **kwargs_input
            )

            created_files = [pathlib.Path(os.path.join(tempdir, created)) for created in  os.listdir(pathlib.Path(tempdir))]
            assert len([created for created in created_files if 'automatic' in created.name]) >= 1
            assert len([created for created in created_files if 'manual' in created.name]) >= 1

            for f in created_files:
                if 'manual' in f.name and f.suffix == '.tsv':
                    manual_df = pandas.read_csv(f, sep='\t')

                    assert 'plasma_radioactivity' in manual_df.columns
                    assert 'whole_blood_radioactivity' in manual_df.columns

    def test_load_txt_files_mixed(self, Ex_txt_manual_and_autosampled_mixed):
        kwargs_input = {
            'whole_blood_activity_collection_method': 'automatic',
            'parent_fraction_collection_method': 'manual',
            'plasma_activity_collection_method': 'manual'
        }
        with tempfile.TemporaryDirectory() as tempdir:
            pmod_to_blood = PmodToBlood(
                whole_blood_activity=pathlib.Path(Ex_txt_manual_and_autosampled_mixed['whole'][0]),
                plasma_activity=pathlib.Path(Ex_txt_manual_and_autosampled_mixed['plasma'][0]),
                parent_fraction=pathlib.Path(Ex_txt_manual_and_autosampled_mixed['parent'][0]),
                output_path=tempdir,
                **kwargs_input
            )

    def test_txt_output_manual_popped_values(self, Ex_txt_manual_and_autosampled_mixed):
        kwargs_input = {
            'whole_blood_activity_collection_method': 'automatic',
            'parent_fraction_collection_method': 'manual',
            'plasma_activity_collection_method': 'manual'
        }
        # next test txt files
        with tempfile.TemporaryDirectory() as tempdir:
            pmod_to_blood = PmodToBlood(
                whole_blood_activity=pathlib.Path(Ex_txt_manual_and_autosampled_mixed['whole'][0]),
                plasma_activity=pathlib.Path(Ex_txt_manual_and_autosampled_mixed['plasma'][0]),
                parent_fraction=pathlib.Path(Ex_txt_manual_and_autosampled_mixed['parent'][0]),
                output_path=tempdir,
                **kwargs_input
            )

            created_files = [pathlib.Path(os.path.join(tempdir, created)) for created in  os.listdir(pathlib.Path(tempdir))]
            assert len([created for created in created_files if 'automatic' in created.name]) >= 1
            assert len([created for created in created_files if 'manual' in created.name]) >= 1

            for f in created_files:
                if 'manual' in f.name and f.suffix == '.tsv':
                    manual_df = pandas.read_csv(f, sep='\t')

                    # we want to calculate plasma radioactivity if we have whole blood and parent fraction, for the
                    # manual blood file at least
                    assert 'plasma_radioactivity' in manual_df.columns
                    assert 'whole_blood_radioactivity' in manual_df.columns
                    assert 'metabolite_parent_fraction' in manual_df.columns
                    assert len(manual_df['plasma_radioactivity']) == len(manual_df['metabolite_parent_fraction'])

                if 'auto' in f.name and f.suffix == '.tsv':
                    automatic_df = pandas.read_csv(f, sep='\t')
                    original_whole_blood = open_meta_data(Ex_txt_manual_and_autosampled_mixed['whole'][0])
                    assert 'whole_blood_radioactivity' in automatic_df.columns
                    assert len(automatic_df) + len(manual_df) == len(original_whole_blood)
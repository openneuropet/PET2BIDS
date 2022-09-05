import gzip
import os
import re
import shutil
import typing

import dotenv
import ast
import argparse
import pathlib

import pandas
import toml
import pathlib
from pandas import read_csv, read_excel
from numpy import where
import importlib
import sys
import argparse


def compress(file_like_object, output_path: str = None):
    """
    Compresses a file using gzip.

    :param file_like_object: a file path to an uncompressed file
    :param output_path: an output path to compress the file to, if omitted simply appends .gz to
        file_like_object path
    :return: output_path on successful completion of compression
    """
    if os.path.isfile(file_like_object) and not output_path:
        output_path = os.path.join(file_like_object, '.gz')
    elif not os.path.isfile(file_like_object):
        raise Exception(f"{file_like_object} is not a valid file to compress.")
    else:
        pass

    with open(file_like_object, 'rb') as infile:
        input_data = infile.read()

    output = gzip.GzipFile(output_path, 'wb')
    output.write(input_data)
    output.close()

    return output_path


def decompress(file_like_object, output_path: str = None):
    """
    Decompresses a gzip file.

    :param file_like_object: a compressed gzip file
    :param output_path: optional output path, if not supplied this function simply trims '.gz' off of
        the input file and writes to that amended path
    :return: output_path on successful decompression
    """
    if not output_path and '.gz' in file_like_object:
        output_path = re.sub('.gz', '', file_like_object)

    compressed_file = gzip.GzipFile(file_like_object)
    compressed_input = compressed_file.read()
    compressed_file.close()

    with open(output_path, 'wb') as outfile:
        outfile.write(compressed_input)
    return output_path


def load_vars_from_config(path_to_config: str):
    """
    Loads values from a .env file given a path to said .env file.

    :param path_to_config: path to .env file
    :return: a dictionary containing the values stored in .env
    """
    if os.path.isfile(path_to_config):
        parameters = dotenv.main.dotenv_values(path_to_config)
    else:
        raise FileNotFoundError(path_to_config)

    for parameter, value in parameters.items():
        try:
            parameters[parameter] = ast.literal_eval(value)
        except ValueError:
            parameters[parameter] = str(value)

    return parameters


def get_version():
    """
    Gets the version of this software from the toml file
    :return: version number from pyproject.toml
    """
    # this scripts directory path
    scripts_dir = pathlib.Path(os.path.dirname(__file__))

    try:
        # if this is bundled as a package look next to this file for the pyproject.toml
        toml_path = os.path.join(scripts_dir, 'pyproject.toml')
        with open(toml_path, 'r') as infile:
            tomlfile = toml.load(infile)
    except FileNotFoundError:
        # when in development the toml file with the version is 2 directories above (e.g. where it should actually live)
        toml_dir = scripts_dir.parent
        toml_path = os.path.join(toml_dir, 'pyproject.toml')
        with open(toml_path, 'r') as infile:
            tomlfile = toml.load(infile)

    attrs = tomlfile.get('tool', {})
    poetry = attrs.get('poetry', {})
    version = poetry.get('version', '')

    return version


class ParseKwargs(argparse.Action):
    """
    Class that is used to extract key pair arguments passed to an argparse.ArgumentParser objet via the command line.
    Accepts key value pairs in the form of 'key=value' and then passes these arguments onto the arg parser as kwargs.
    This class is used during the construction of the ArgumentParser class via the add_argument method. e.g.:\n
    `ArgumentParser.add_argument('--kwargs', '-k', nargs='*', action=ParseKwargs, default={})`
    """

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, dict())
        for value in values:
            key, value = value.split('=')
            getattr(namespace, self.dest)[key] = value


def open_meta_data(metadata_path):
    """
    Opens a text metadata file with the pandas method most appropriate for doing so based on the metadata
    file's extension.
    :param extension: The extension of the file
    :return: a pandas dataframe representation of the spreadsheet/metadatafile
    """

    metadata_path = pathlib.Path(metadata_path)

    if metadata_path.exists():
        pass
    else:
        raise FileExistsError(metadata_path)

    # collect suffix from metadata an use the approriate pandas method to read the data
    extension = metadata_path.suffix

    methods = {
        'excel': read_excel,
        'csv': read_csv
    }

    if 'xls' in extension:
        proper_method = 'excel'
    else:
        proper_method = extension

    try:
        use_me_to_read = methods.get(proper_method, None)
        metadata_dataframe = use_me_to_read(metadata_path)
    except IOError as err:
        raise err(f"Problem opening {metadata_path}")

    return metadata_dataframe


def translate_metadata(metadata_path, metadata_translation_script_path, **kwargs):
    # load metadata
    metadata_dataframe = open_meta_data(metadata_path)

    if metadata_dataframe is not None:
        try:
            # this is where the goofiness happens, we allow the user to create their own custom script to manipulate
            # data from their particular spreadsheet wherever that file is located.
            spec = importlib.util.spec_from_file_location("metadata_translation_script_path",
                                                          metadata_translation_script_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            # note the translation must have a method named translate metadata in order to work
            text_file_data = module.translate_metadata(metadata_dataframe, **kwargs)
        except AttributeError as err:
            print(f"Unable to locate metadata_translation_script\n{err}")
    else:
        print(f"No metadata found at {metadata_path}")
        text_file_data = None

    return text_file_data


def import_and_write_out_module(module: str, destination: str):
    """
    Writes an imported module file to a destination
    :param module: an imported python module
    :param destination: the destination to write the source/script of the module to file

    :return: the destination path of the copied module file if successful
    """
    imported_module = importlib.import_module(module)
    path_to_module = os.path.abspath(imported_module.__file__)
    shutil.copy(path_to_module, destination)
    if os.path.isfile(destination):
        return destination
    elif os.path.isdir(destination):
        return os.path.join(destination, os.path.basename(path_to_module))


def write_out_module(module: str = 'pypet2bids.metadata_spreadsheet_example_reader'):
    parser = argparse.ArgumentParser()
    parser.add_argument('template_path', type=str, help="Path to write out template for a translation script.")
    args = parser.parse_args()

    import_and_write_out_module(module=module, destination=args.template_path)


def expand_path(path_like: str) -> str:
    """
    Expands relative ~ paths to full paths
    :param path_like: path like string
    :type path_like: string
    :return: full path string
    :rtype: string
    """
    if path_like:
        if path_like[0] == '~':
            return str(os.path.expanduser(path_like))
        else:
            return (os.path.abspath(path_like))
    else:
        return ''


def collect_bids_part(bids_part: str, path_like: str) -> str:
    """
    Regex is hard, this finds a bids key if it's present in path or pathlink string

    >>> bids_like_path = '/home/users/user/bids_data/sub-NDAR123/ses-firstsession'
    >>> subject_id = collect_bids_part('sub', bids_like_path)
    >>> subject_id
    >>> "sub-NDAR123"

    :param bids_part: the bids part to find in the path e.g. subject id, session id, recording, etc etc
    :type bids_part: string
    :param path_like: a pathlike input, this is strictly for parsing file paths or file like strings
    :type path_like: string
    :return: the collected bids part
    :rtype: string
    """
    # break up path into parts
    parts = pathlib.PurePath(path_like).parts

    # create search string
    search_string = bids_part + '-(.*)'
    # collect bids_part
    for part in parts:
        found_part = re.search(search_string, part)
        if found_part:
            collected_part = found_part[0]
            break
        else:
            collected_part = ''

    return collected_part


def get_coordinates_containing(
        containing: typing.Union[str, int, float],
        dataframe: pandas.DataFrame,
        exact: bool = False,
        single=False) -> typing.Union[list, tuple]:
    """
    Collects the co-ordinates (row and column) containing an input value, that value could be a string, integer, or
    float. When searching for integers or floats it is most likely best to use set the exact argument to True; the same
    goes for finding the exact match of a string. This method is primarily meant to find the row corresponding to a
    subject ID, e.g.
    # if your dataframe is given as

        subject_id    some_values    more_values
        sub-NDAR1     1              2
        sub-NDAR2     3              3

    And you provided the arguments: `containing='sub-NDAR', exact=False` you would return a set of the following
    co-ordinates

        [(0, 'subject_id'), (1, 'subject_id')]

    If you are confident in your input data you would most likely call this method this way:


    >>> coordinates = get_coordinates_containing(
    >>>     'sub-NDAR1',
    >>>     pandas.DataFrame({'subject_id': ['sub-NDAR1', 'sub-NDAR2'], 'some_values': [1, 2]}),
    >>>     single=True)
    >>> coordinates
    >>> (0, 1)

    :param containing: value you wish to search a dataframe for
    :type containing: string, integer, or float
    :param dataframe: A pandas dataframe read in from a spreadsheet
    :type dataframe: pandas.datafarame
    :param exact: Boolean proscribing an exact match to containing; default is to locate a string or value that holds the
    input containing
    :type exact: bool
    :param single: return only the first co-ordinate, use only if the string/contains your searching for is unique and
    you have high confidence in your data
    :type single: bool
    :return: A co-ordinate in the form of (row, column) or a list containing a set of co-ordinates [(row, column), ...]
    :rtype: tuple or list of tuples
    """

    coordinates = []
    for row_index, row in dataframe.iterrows():
        for column_index, value in row.items():
            if value is not pandas.NA:
                if exact:
                    if value == containing:
                        coordinates.append((row_index, column_index))
                elif not exact and type(value) is str:
                    if str(containing) in value:
                        coordinates.append((row_index, column_index))
    if single and coordinates:
        return coordinates[0]
    else:
        return coordinates


def transform_row_to_dict(row: typing.Union[int, str, pandas.Series], dataframe: pandas.DataFrame = None) -> dict:
    """
    Parses a row of a dataframe (or a series from a dataframe) into a dictionary, special care is taken to transform
    array like data contained in a single cell to a list of numbers or strings.
    :param row: either the row index as an integer or a pandas.Series object
    :type row: int, pandas.Series
    :param dataframe: Provided if only an int is given to this method, will be queried at the row by the given integer
    :type dataframe: pandas.DataFrame
    :return: a dictionary corresponding a row from a (most likely multi-subject input sheet) spreadsheet
    :rtype: dict
    """
    if type(row) is pandas.Series:
        row = row
    elif type(row) is str or type(row) is int and dataframe is not None:
        if type(row) is int:
            row = dataframe.iloc[row]
        else:
            row = dataframe.loc[row]

    transformed = {}
    for key, value in row.items():
        try:
            evaluated = ast.literal_eval(str(value))
            if type(evaluated) is tuple:
                evaluated = list(evaluated)
        except (SyntaxError, ValueError):
            evaluated = value
        transformed[key] = evaluated

    return transformed

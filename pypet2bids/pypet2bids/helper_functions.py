import gzip
import os
import re
import dotenv
import ast
import argparse
import pathlib
import toml


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
    # the toml file with the version is 2 directories above
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



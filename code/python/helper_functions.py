import gzip
import os
import re


def compress(file_like_object, output_path=None):
    """
    Compresses a file using gzip
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


def decompress(file_like_object, output_path=None):
    """
    Decompresses a gzip file
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

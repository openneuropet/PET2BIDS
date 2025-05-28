import os
import pydicom
import argparse
import nibabel
import re
from typing import Union
from pathlib import Path
import contextlib
import sys
import json
from joblib import Parallel, delayed


try:
    import helper_functions
    import ecat
    import dcm2niix4pet
    import pet_metadata
except ModuleNotFoundError:
    import pypet2bids.helper_functions as helper_functions
    import pypet2bids.ecat as ecat
    import pypet2bids.dcm2niix4pet as dcm2niix4pet
    import pypet2bids.pet_metadata as pet_metadata


def spread_sheet_check_for_pet(sourcefile: Union[str, Path], **kwargs):
    # load data from spreadsheet
    data = helper_functions.open_meta_data(sourcefile)

    try:
        pet_field_requirements = pet_metadata.PET_metadata
    except:
        pet_field_requirements = {}

    mandatory_fields = pet_field_requirements.get("mandatory", [])
    recommended_fields = pet_field_requirements.get("recommended", [])
    optional_fields = pet_field_requirements.get("optional", [])
    blood_recording_fields = pet_field_requirements.get("blood_recording_fields", [])

    intersection = set(
        mandatory_fields + recommended_fields + optional_fields + blood_recording_fields
    ) & set(data.keys())

    if len(intersection) > 0:
        return True
    else:
        return False


def read_files_in_parallel(file_paths: list, function, n_jobs=-2, **kwargs):
    """
    Read files in parallel using joblib (note this should be refactored to use the threading module)
    :param file_paths: list of file paths to read
    :param function: function to apply to each file
    :param n_jobs: number of jobs to run in parallel
    :param kwargs: keyword arguments to pass to function
    :return: list of results
    """
    # TODO replace dependency on joblib with threading module
    results = Parallel(n_jobs=n_jobs)(
        delayed(function)(file_path, **kwargs) for file_path in file_paths
    )
    return results


class DummyFile(object):
    def write(self, x):
        pass


@contextlib.contextmanager
def nostdout():
    save_stdout = sys.stdout
    sys.stdout = DummyFile()
    yield
    sys.stdout = save_stdout


def pet_file(file_path: Path, return_only_path=False) -> Union[bool, str]:
    """
    Given a file path determine if the file is a pet imaging or pet spreadsheet type of file.
    Returns a tuple with the 'PET' status of the file followed by the type of PET file, one of
    the following -> 'DICOM', 'ECAT', 'SPREADSHEET', ''

    True value and DICOM returned if a dicom file is found
    >>> status, type_of_pet_file = pet_file('PETDICOM001.img')
    >>> assert status == True
    >>> assert type_of_pet_file == 'DICOM'

    False value and empty string are returned if not a pet file e.g.:
    >>> status, type_of_pet_file = pet_file('is_pet.py')
    >>> assert status == False
    >>> assert type_of_pet_file == ''

    :param file_path: path to file to check
    :type file_path: pathlib.Path object
    :return: (status, file type)
    :rtype: tuple(bool, str)
    """
    if not file_path.exists():
        raise FileNotFoundError(file_path)

    file_type = ""
    # get suffix of file
    suffix = file_path.suffix

    # if there are suffixes, join them together
    if len(file_path.suffixes) > 1:
        suffix = "".join(file_path.suffixes)

    # suppress all stdout from other functions
    with nostdout():
        if not file_type and (
            suffix.lower() in [".dcm", ".ima", ".img", ""]
            or "mr" in str(file_path.name).lower()
            or bool(re.search(r"\d", suffix.lower()))
        ):
            try:
                read_file = pydicom.dcmread(file_path)
                if read_file.Modality == "PT":
                    file_type = "DICOM"
                else:
                    # do nothing, we only want dicoms with the correct modality
                    pass
            except (pydicom.errors.InvalidDicomError, AttributeError):
                pass

        if not file_type and suffix.lower() in [".v", ".v.gz"]:
            try:
                read_file = ecat.Ecat(str(file_path))
                file_type = "ECAT"
            except nibabel.filebasedimages.ImageFileError:
                pass

        if not file_type and suffix.lower() in [".xlsx", ".tsv", ".csv", ".xls"]:
            try:
                read_file = spread_sheet_check_for_pet(file_path)
                if read_file:
                    # if it looks like a pet file
                    file_type = "SPREADSHEET"
            except (IOError, ValueError):
                pass

    if file_type:
        if return_only_path:
            return Path(file_path)
        else:
            return True, file_type
    else:
        if return_only_path:
            pass
        else:
            return False, file_type


def pet_folder(folder_path: Path, skim=False, njobs=2) -> Union[str, list, bool]:
    if not folder_path.exists():
        raise FileNotFoundError(folder_path)
    if not folder_path.is_dir():
        raise FileNotFoundError(folder_path)

    all_files = []
    # collect list of all files
    for root, folders, files in os.walk(folder_path):
        for f in files:
            f_path = Path(os.path.join(root, f))
            if f_path.exists():
                all_files.append(Path(os.path.join(root, f)))

    # we aren't going to want to inspect every single file, instead we're going skim through the list of files
    # by first selecting only the first file of each folder that has a given suffix (especially for dicom files)
    if skim:
        from pprint import pprint

        # collect all the dicom images
        dicoms, spreadsheets, ecats = {}, {}, {}
        for f in all_files:
            if f.suffix.lower() in [".dcm", ".ima", ".img", ""]:
                parent = dicoms.get(str(f.parent), {str(f.parent): {f.suffix: f}})
                dicoms[str(f.parent)] = parent
            if f.suffix.lower() in [".xlsx", ".tsv", ".csv", ".xls"]:
                parent = spreadsheets.get(str(f.parent), {str(f.parent): {f.suffix: f}})
                spreadsheets[str(f.parent)] = parent
            if f.suffix.lower() in [".v"] or f.suffixes == [".v", ".gz"]:
                parent = ecats.get(
                    str(f.parent), {str(f.parent): {"".join(f.suffixes): f}}
                )
                ecats[str(f.parent)] = parent
        # now flatten all the dictionaries to only include the file parts
        smaller_list = []
        for file_dict in [dicoms, spreadsheets, ecats]:
            for k, v in file_dict.items():
                for k2, v2 in v.items():
                    for k3, v3 in v2.items():
                        smaller_list.append(v3)

        all_files = smaller_list

    # check if any files are pet files
    files = read_files_in_parallel(
        all_files, pet_file, n_jobs=njobs, return_only_path=True
    )
    files = [Path(f) for f in files if f is not None]
    # check through list of pet files and statuses for True values in parallel
    folders = set([f.parent for f in files])

    return folders


def main():
    """
    This command line utility exists almost entirely for ezBIDS. It's use there is to ensure that dcm2niix is not run
    on folders containing PET images. Instead, the PET images are converted using the dcm2niix4pet from this library.
    :return: Path to PET folder or file
    :rtype: str
    """

    parser = argparse.ArgumentParser(
        description="Check if a file is a PET image or bloodfile. If a folder is given, "
        "all files in the folder will be checked and any folders "
        "containing PET files will be returned."
    )
    parser.add_argument(
        "filepath",
        type=Path,
        help="File path to check whether file is PET image or bloodfile. "
        "If a folder is given, all files in the folder will be checked and "
        "any folders containing PET files will be returned.",
    )
    parser.add_argument(
        "-p",
        "--path-only",
        action="store_true",
        default=False,
        help="Omit type of pet file; only return file path if file is PET file",
    )
    parser.add_argument(
        "-s",
        "--skim",
        action="store_true",
        default=False,
        help="Only check files that "
        "are suspected to be PET files. Defaults to checking every file found in a folder."
        "When selected checks only a single file in folder ending in an extension that may be a PET FILE.",
    )
    parser.add_argument(
        "-n",
        "--njobs",
        type=int,
        default=2,
        help="Number of jobs to run in parallel when examining folders, defaults to 2.",
    )
    args = parser.parse_args()

    if args.filepath.is_file():
        status, pet_files = pet_file(args.filepath.resolve())
        if status:
            if args.path_only:
                print(f"{args.filepath}")
            else:
                print(f"{args.filepath} {pet_files}")
        else:
            sys.exit(1)

    elif args.filepath.is_dir():
        pet_folders = pet_folder(
            args.filepath.resolve(), skim=args.skim, njobs=args.njobs
        )
        if len(pet_folders) > 0:
            for f in pet_folders:
                print(f"{f}")
        else:
            sys.exit(1)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

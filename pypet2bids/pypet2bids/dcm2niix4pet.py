from json_maj import main
import importlib.util
import subprocess
import pandas as pd
import sys
from os.path import isdir, isfile, join
from os import listdir, walk, makedirs
from pathlib import Path
import json
import pydicom
import re
import platform
from numpy import cumsum
from tempfile import TemporaryDirectory
import shutil

"""
This module acts as a simple wrapper around dcm2niix, it takes all of the same arguments as dcm2niix but does a little
bit of extra work to conform the output nifti and json from dcm2niix to the PET BIDS specification. Additionally, but
optionally, this module can collect blood or physiological data/metadata from spreadsheet files if the path of that
spreadsheet file as well as a python module/script written to interpret it are provided in addition to relevant dcm2niix
commands.
"""

class Dcm2niix4PET:
    def __init__(self, image_folder, destination_path, metadata_path=None,
                 metadata_translation_script=None, additional_arguments=None):
        """
        :param image_folder:
        :param destination_path:
        :param metadata_path:
        :param metadata_translation_script:
        :param file_format:
        :param additional_arguments:
        """

        self.image_folder = Path(image_folder)
        self.destination_path =  Path(destination_path)
        if metadata_path is not None and metadata_translation_path is not None:
            self.metadata_path =  Path(metadata_path)
            self.metadata_translation_script = Path(metadata_path)


    @staticmethod
    def check_for_dcm2niix():
        """
        Just checks for dcm2niix using the system shell, returns 0 if dcm2niix is present.
        :return: status code of the command dcm2niix
        """
        check = subprocess.run("dcm2niix -h", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if check.returncode != 0:
            pkged = "https://github.com/rordenlab/dcm2niix/releases"
            instructions = "https://github.com/rordenlab/dcm2niix#install"
            raise Exception(f"""Dcm2niix does not appear to be installed. Installation instructions can be found here 
                   {instructions} and packaged versions can be found at {pkged}""")

        return check.returncode

    def extract_dicom_header(self, additional_fields=[]):
        """
        Opening up files till a dicom is located, then extracting any header information
        to be used during and after the conversion process. This includes patient/subject id,
        as well any additional frame or metadata that's required for conversion.
        :return: dicom header information to self.subject_id and/or self.dicom_header_data
        """
        for root, dirs, files in os.walk(self.image_folder):
            for f in files:
                try:
                    dicom_header = pydicom.dcmread(os.path.join(root, f))
                    # collect subject/patient id if none is supplied
                    if self.subject_id is None:
                        self.subject_id = dicom_header.PatientID

                    self.dicom_header_data = dicom_header
                    break

                except pydicom.errors.InvalidDicomError:
                    pass

    def run_dcm2niix(self):
        with TemporaryDirectory() as tempdir:
            tempdir_pathlike = Path(tempdir)

            convert = subprocess.run(f"dcm2niix -w 1 -z y -o {tempdir_pathlike} {self.image_folder}", shell=True,
                                     capture_output=True)

            if convert.returncode != 0 and bytes("Skipping existing file name", "utf-8") not in convert.stdout or convert.stderr:
                print(convert.stderr)
                raise Exception("Error during image conversion from dcm to nii!")

            # collect contents of the tempdir
            files_created_by_dcm2niix = [join(tempdir_pathlike, file) for file in listdir(tempdir_pathlike)]

            # make sure destination path exists if not try creating it.
            if self.destination_path.exists():
                pass
            else:
                makedirs(self.destination_path)

            for created in files_created_by_dcm2niix:
                created_path = Path(created)
                new_path = Path(join(self.destination_path, created_path.name))
                shutil.move(src=created, dst=new_path)





import requests
import os
import pathlib
import subprocess
from dotenv import load_dotenv
from typing import Union


# collect pet2bids version
from pypet2bids.helper_functions import get_version


def telemetry_enabled(config_path=None):
    # load dcm2niix file
    if not config_path:
        config_file = pathlib.Path.home() / ".pet2bidsconfig"
    else:
        config_file = pathlib.Path(config_path)

    if config_file.exists():
        load_dotenv(dotenv_path=config_file)

    # check to see if telemetry is disabled
    if os.getenv("PET2BIDS_TELEMETRY_ENABLED", "").lower() == "false":
        return False
    else:
        return True


def send_telemetry(json_data: dict, url: str = "http://52.87.154.236/telemetry/"):
    if telemetry_enabled():
        # update data with version of pet2bids
        json_data["pypet2bids_version"] = get_version()
        # check if it's one of the dev's running this
        running_from_cloned_repository = subprocess.run(
            ["git", "status"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        if running_from_cloned_repository.returncode == 0:
            json_data["running_from_cloned_repository"] = True

        json_data["description"] = "pet2bids_python_telemetry"

        # Send a POST request to the telemetry server
        requests.post(url, json=json_data)
    else:
        pass


def count_input_files(input_file_path: Union[str, pathlib.Path]):
    # Count the number of input files in the input file path
    if isinstance(input_file_path, str):
        input_file_path = pathlib.Path(input_file_path)

    if input_file_path.is_dir():
        # collect all files in the input dir
        all_files = [f for f in input_file_path.iterdir()]
        # count the number of dicom files
        num_dicom_files = 0
        dicom_files_size = 0
        total_files = 0
        total_files_size = 0
        for file in all_files:
            if file.is_file():
                total_files += 1
                total_files_size += file.stat().st_size
    return {
        "TotalInputFiles": total_files,
        "TotalInputFilesSize": total_files_size,
    }


def count_output_files(output_file_path: Union[str, pathlib.Path]):
    if isinstance(output_file_path, str):
        output_file_path = pathlib.Path(output_file_path)

    if output_file_path.is_file():
        output_file_path = output_file_path.parent

    if output_file_path.is_dir():
        # collect all files in the output dir
        all_files = [f for f in output_file_path.iterdir()]
        # count the number nifti files
        num_nifti_files = 0
        nifti_files_size = 0
        total_files = 0
        total_files_size = 0
        for f in all_files:
            if f.is_file():
                total_files += 1
                total_files_size += f.stat().st_size
                if str(f).endswith(".nii") or str(f).endswith(".nii.gz"):
                    num_nifti_files += 1
                    nifti_files_size += f.stat().st_size
    return {
        "TotalOutputFiles": total_files,
        "TotalOutputFilesSize": total_files_size,
        "NiftiFiles": num_nifti_files,
        "NiftiFilesSize": nifti_files_size,
    }

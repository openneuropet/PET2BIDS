import requests
import os
import pathlib
import subprocess
import time
import sys
import select
from dotenv import load_dotenv
from typing import Union


try:
    from helper_functions import get_version, load_vars_from_config, modify_config_file
except ModuleNotFoundError:
    # collect pet2bids version
    from pypet2bids.helper_functions import get_version, load_vars_from_config, modify_config_file

pet2bids_config = load_vars_from_config()
telemetry_default_url = pet2bids_config.get("TELEMETRY_URL", "http://52.87.154.236/telemetry/")
telemetry_enabled = pet2bids_config.get("TELEMETRY_ENABLED", True)
telemetry_notify_user = pet2bids_config.get("NOTIFY_USER_OF_TELEMETRY", False)


def ask_user_to_opt_out(timeout=10):
    """Waits for user input for a specified number of seconds.

    Args:
        timeout: Number of seconds to wait for input.

    Returns:
        The user input if provided within the timeout, otherwise None.
    """

    print("Do you want to opt out of telemetry? (yes/no): ".format(timeout), end="", flush=True)
    sys.stdout.flush()

    ready, _, _ = select.select([sys.stdin], [], [], timeout)
    if ready:
        response = sys.stdin.readline().rstrip('\n')
        if response.lower() == "yes":
            return True
    else:
        return False


if telemetry_notify_user is False:
    opt_out = ask_user_to_opt_out()
    if opt_out:
        # update the config file
        modify_config_file("TELEMETRY_ENABLED", False)

    modify_config_file("NOTIFY_USER_OF_TELEMETRY", True)


def telemetry_enabled(config_path=None):
    """
    Check if telemetry is enabled, if it isn't disabled in the .pet2bidsconfig file
    it will be considered enabled. One must opt out of tracking usage manually.
    :param config_path: The path to the config file
    :type config_path: Union[str, pathlib.Path]
    :return: Whether telemetry is enabled or not
    :rtype: bool
    """
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


def send_telemetry(json_data: dict, url: str = telemetry_default_url):
    """
    Send telemetry data to the telemetry server, by default this will first try
    to load the telemetry server url from the config file, if it's not found it will
    default to the hardcoded value in this module. This will always send, unless a user
    has disabled the pet2bids telemetry in the .pet2bidsconfig file.
    :param json_data: The dat to be sent to the telemetry server
    :type json_data: dict
    :param url: The url of the telemetry server
    :type url: str
    """
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
    """
    Count the number of input files in the input file path
    :param input_file_path: location of the input files
    :type input_file_path: Union[str, pathlib.Path]
    :return: The number of input files and their size
    :rtype: dict
    """
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
    """
    Count the number of output files in the output file path. This can be usefull
    in determining whether any additional files were created during the conversion process.
    However, this is only useful if the conversion process initially takes place from within
    a temporary directory.

    # TODO check the last modified date of the files to determine if they were created during
    # TODO the conversion process. That should make this usefull in all cases.
    :param output_file_path: location of the output files
    :type output_file_path: Union[str, pathlib.Path]
    :return: The number of output files and their size and spefically the number of nifti files and
    their size
    :rtype: dict
    """
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



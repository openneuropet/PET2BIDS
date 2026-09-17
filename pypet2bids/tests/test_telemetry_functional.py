import os
import shutil
from pathlib import Path

import pytest
import requests

import pypet2bids.dcm2niix4pet as dcm2niix4pet_module
import pypet2bids.ecat as ecat_module
from pypet2bids import telemetry
from pypet2bids.dcm2niix4pet import Dcm2niix4PET
from pypet2bids.ecat import Ecat


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DICOM_SOURCE = (
    REPOSITORY_ROOT
    / "OpenNeuroPET-Phantoms"
    / "sourcedata"
    / "SiemensBiographPETMR-NIMH"
    / "AC_TOF"
)
ECAT_PHANTOM_ROOT = REPOSITORY_ROOT / "OpenNeuroPET-Phantoms" / "sourcedata"
ECAT_PHANTOM_SOURCES = tuple(sorted(ECAT_PHANTOM_ROOT.rglob("*.v"))) + tuple(
    sorted(ECAT_PHANTOM_ROOT.rglob("*.v.gz"))
)
ECAT_VALIDATION_SOURCE = REPOSITORY_ROOT / "ecat_validation" / "ECAT7_multiframe.v.gz"
ECAT_SOURCE = (
    ECAT_PHANTOM_SOURCES[0] if ECAT_PHANTOM_SOURCES else ECAT_VALIDATION_SOURCE
)
MIGAS_ROOT_URL = "https://migas.openneuropet.org"
MIGAS_URL = f"{MIGAS_ROOT_URL}/api/breadcrumb?wait=true"
MIGAS_TEST_PROJECT = "openneuropet/testing_endpoint"
MISSING_PHANTOMS = (
    "OpenNeuroPET phantom data not found. Run "
    "`make collectphantoms decompressphantoms` from the repository root."
)

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_TELEMETRY_FUNCTIONAL") != "1",
    reason="set RUN_TELEMETRY_FUNCTIONAL=1 to run live Migas tests",
)


def require_registered_test_project():
    token = os.getenv("MIGAS_TEST_TOKEN")
    if not token:
        return

    response = requests.get(
        f"{MIGAS_ROOT_URL}/api/auth/projects",
        headers={"Authorization": f"Bearer {token}"},
        timeout=5,
    )
    assert response.status_code == 200, response.text
    assert MIGAS_TEST_PROJECT in response.json()["projects"], (
        f"Migas project {MIGAS_TEST_PROJECT!r} is not registered or the test "
        "token cannot access it."
    )


def test_dicom_conversion_reaches_migas_testing_endpoint(monkeypatch, tmp_path):
    if not DICOM_SOURCE.is_dir():
        pytest.fail(MISSING_PHANTOMS)
    require_registered_test_project()

    responses = []

    def send_to_testing_endpoint(data):
        responses.append(
            telemetry.send_telemetry(
                data,
                url=MIGAS_URL,
                project=MIGAS_TEST_PROJECT,
            )
        )

    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("PET2BIDS_TELEMETRY_ENABLED", raising=False)
    monkeypatch.setattr(dcm2niix4pet_module, "telemetry_enabled", lambda: True)
    monkeypatch.setattr(
        dcm2niix4pet_module,
        "send_telemetry",
        send_to_testing_endpoint,
    )

    converter = Dcm2niix4PET(DICOM_SOURCE, destination_path=tmp_path)
    converter.convert()

    assert list(tmp_path.glob("*.nii*"))
    assert len(responses) == 1
    response = responses[0]
    assert response is not None, "Migas request failed before receiving a response"
    assert response.status_code == 200, response.text
    assert response.json()["success"] is True


def test_ecat_conversion_reaches_migas_testing_endpoint(monkeypatch, tmp_path):
    if not ECAT_SOURCE.is_file():
        pytest.fail(MISSING_PHANTOMS)
    require_registered_test_project()

    responses = []

    def send_to_testing_endpoint(data):
        responses.append(
            telemetry.send_telemetry(
                data,
                url=MIGAS_URL,
                project=MIGAS_TEST_PROJECT,
            )
        )

    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("PET2BIDS_TELEMETRY_ENABLED", raising=False)
    monkeypatch.setattr(ecat_module, "telemetry_enabled", lambda: True)
    monkeypatch.setattr(ecat_module, "send_telemetry", send_to_testing_endpoint)

    ecat_input = tmp_path / ECAT_SOURCE.name
    shutil.copy2(ECAT_SOURCE, ecat_input)
    nifti_output = tmp_path / "phantom.nii.gz"
    converter = Ecat(
        ecat_file=ecat_input,
        nifti_file=nifti_output,
        collect_pixel_data=True,
    )
    converter.convert()

    assert nifti_output.is_file()
    assert converter.telemetry_data["InputType"].startswith("ECAT")
    assert len(responses) == 1
    response = responses[0]
    assert response is not None, "Migas request failed before receiving a response"
    assert response.status_code == 200, response.text
    assert response.json()["success"] is True

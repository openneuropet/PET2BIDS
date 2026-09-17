import shutil
from types import SimpleNamespace
from unittest.mock import Mock
from pathlib import Path

import pytest

import pypet2bids.dcm2niix4pet as dcm2niix4pet_module
import pypet2bids.ecat as ecat_module
from pypet2bids import telemetry
from pypet2bids.dcm2niix4pet import Dcm2niix4PET
from pypet2bids.ecat import Ecat


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PHANTOM_SOURCE = REPOSITORY_ROOT / "OpenNeuroPET-Phantoms" / "sourcedata"
DICOM_SOURCE = PHANTOM_SOURCE / "SiemensBiographPETMR-NIMH" / "AC_TOF"
ECAT_SOURCES = tuple(sorted(PHANTOM_SOURCE.rglob("*.v"))) + tuple(
    sorted(PHANTOM_SOURCE.rglob("*.v.gz"))
)
ECAT_VALIDATION_SOURCE = REPOSITORY_ROOT / "ecat_validation" / "ECAT7_multiframe.v.gz"
ECAT_SOURCE = ECAT_SOURCES[0] if ECAT_SOURCES else None
if ECAT_SOURCE is None and ECAT_VALIDATION_SOURCE.is_file():
    ECAT_SOURCE = ECAT_VALIDATION_SOURCE


def test_default_telemetry_url():
    assert (
        telemetry.telemetry_default_url
        == "https://migas.openneuropet.org/api/breadcrumb"
    )


@pytest.mark.parametrize(
    ("returncode", "expected_status"),
    [
        (0, "C"),
        (1, "F"),
    ],
)
def test_send_telemetry_posts_migas_breadcrumb(
    monkeypatch, returncode, expected_status
):
    post = Mock()
    monkeypatch.setattr(telemetry, "telemetry_enabled", lambda: True)
    monkeypatch.setattr(telemetry, "get_version", lambda: "1.5.1")
    monkeypatch.setattr(telemetry.sys, "version_info", (3, 12, 7))
    monkeypatch.setattr(telemetry.sys, "platform", "linux")
    monkeypatch.setattr(
        telemetry.uuid,
        "uuid4",
        lambda: "12345678-1234-4234-8234-123456789abc",
    )
    monkeypatch.setattr(
        telemetry.subprocess,
        "run",
        Mock(return_value=SimpleNamespace(returncode=0)),
    )
    monkeypatch.setattr(telemetry.requests, "post", post)
    monkeypatch.delenv("CI", raising=False)

    telemetry_data = {
        "returncode": returncode,
        "InputType": "DICOM",
        "TotalInputFiles": 120,
        "TotalInputFilesSize": 123456789,
        "dcm2niix": {"returncode": 0},
    }

    telemetry.send_telemetry(telemetry_data)

    post.assert_called_once_with(
        "https://migas.openneuropet.org/api/breadcrumb",
        json={
            "project": "openneuropet/PET2BIDS",
            "project_version": "1.5.1",
            "language": "python",
            "language_version": "3.12.7",
            "ctx": {
                "session_id": "12345678-1234-4234-8234-123456789abc",
                "platform": "linux",
                "is_ci": False,
            },
            "proc": {
                "status": expected_status,
                "params": {
                    "returncode": returncode,
                    "InputType": "DICOM",
                    "TotalInputFiles": 120,
                    "TotalInputFilesSize": 123456789,
                    "dcm2niix": {"returncode": 0},
                    "version": "1.5.1",
                    "running_from_cloned_repository": True,
                    "description": "pet2bids_python_telemetry",
                },
            },
        },
        timeout=5,
    )


def test_send_telemetry_does_not_post_when_disabled(monkeypatch):
    post = Mock()
    monkeypatch.setattr(telemetry, "telemetry_enabled", lambda: False)
    monkeypatch.setattr(telemetry.requests, "post", post)

    telemetry.send_telemetry({"returncode": 0})

    post.assert_not_called()


def _assert_completed_conversion_crumb(post, expected_input_type):
    post.assert_called_once()
    args, kwargs = post.call_args
    assert args == ("https://migas.openneuropet.org/api/breadcrumb",)
    assert kwargs["timeout"] == 5

    crumb = kwargs["json"]
    assert set(crumb) == {
        "project",
        "project_version",
        "language",
        "language_version",
        "ctx",
        "proc",
    }
    assert crumb["project"] == "openneuropet/PET2BIDS"
    assert crumb["language"] == "python"
    assert crumb["proc"]["status"] == "C"
    assert crumb["proc"]["params"]["returncode"] == 0
    assert crumb["proc"]["params"]["InputType"] == expected_input_type


@pytest.mark.skipif(
    not DICOM_SOURCE.is_dir(),
    reason="OpenNeuroPET DICOM phantom source is not available",
)
def test_dcm2niix4pet_conversion_posts_migas_breadcrumb(monkeypatch, tmp_path):
    post = Mock()
    monkeypatch.setattr(telemetry, "telemetry_enabled", lambda: True)
    monkeypatch.setattr(dcm2niix4pet_module, "telemetry_enabled", lambda: True)
    monkeypatch.setattr(telemetry.requests, "post", post)
    monkeypatch.delenv("CI", raising=False)

    converter = Dcm2niix4PET(DICOM_SOURCE, destination_path=tmp_path)
    converter.convert()

    assert list(tmp_path.glob("*.nii*"))
    _assert_completed_conversion_crumb(post, "DICOM")
    params = post.call_args.kwargs["json"]["proc"]["params"]
    assert params["TotalInputFiles"] == sum(
        path.is_file() for path in DICOM_SOURCE.iterdir()
    )
    assert params["dcm2niix"]["returncode"] == 0


@pytest.mark.skipif(
    ECAT_SOURCE is None,
    reason="OpenNeuroPET ECAT phantom source is not available",
)
def test_ecat2bids_conversion_posts_migas_breadcrumb(monkeypatch, tmp_path):
    post = Mock()
    monkeypatch.setattr(telemetry, "telemetry_enabled", lambda: True)
    monkeypatch.setattr(ecat_module, "telemetry_enabled", lambda: True)
    monkeypatch.setattr(telemetry.requests, "post", post)
    monkeypatch.delenv("CI", raising=False)

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
    _assert_completed_conversion_crumb(post, converter.telemetry_data["InputType"])
    params = post.call_args.kwargs["json"]["proc"]["params"]
    assert params["metadata_spreadsheet_used"] is False
    assert params["blood_tsv"] is False


@pytest.mark.parametrize(
    ("conversion_error", "expected_returncode"),
    [(None, 0), (RuntimeError("conversion failed"), 1)],
)
def test_ecat_conversion_reports_outcome(
    monkeypatch, tmp_path, conversion_error, expected_returncode
):
    converter = Ecat.__new__(Ecat)
    converter.telemetry_data = {
        "InputType": "ECAT72",
        "blood_tsv": True,
        "metadata_spreadsheet_used": True,
    }
    converter.spreadsheet_metadata = {
        "blood_tsv": {"time": [0]},
        "blood_json": {},
    }
    converter.metadata_path = None
    converter.kwargs = {}

    if conversion_error:
        converter.make_nifti = Mock(side_effect=conversion_error)
    else:
        converter.make_nifti = Mock(return_value=tmp_path / "output.nii.gz")
    converter.populate_sidecar = Mock()
    converter.prune_sidecar = Mock()
    converter.show_sidecar = Mock()
    converter.write_out_blood_files = Mock()

    send = Mock()
    monkeypatch.setattr(ecat_module, "telemetry_enabled", lambda: True)
    monkeypatch.setattr(ecat_module, "send_telemetry", send)

    if conversion_error:
        with pytest.raises(RuntimeError, match="conversion failed"):
            converter.convert()
    else:
        converter.convert()

    assert converter.telemetry_data["returncode"] == expected_returncode
    assert converter.telemetry_data["blood_tsv"] is True
    assert converter.telemetry_data["metadata_spreadsheet_used"] is True
    send.assert_called_once_with(converter.telemetry_data)

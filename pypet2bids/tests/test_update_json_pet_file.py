import json

import pytest
from pydicom.dataset import Dataset

from pypet2bids import update_json_pet_file
from pypet2bids.update_json_pet_file import (
    get_metadata_from_spreadsheet,
    update_json_with_dicom_value,
)


MISSING_TIME_ZERO = {"TimeZero": {"key": False, "value": False}}


def test_missing_time_zero_prefers_series_time(tmp_path):
    sidecar_path = tmp_path / "sidecar.json"
    sidecar_path.write_text(
        json.dumps(
            {
                "SeriesTime": "12:34:56.500000",
                "AcquisitionTime": "12:35:07.000000",
                "ScanStart": 4.5,
            }
        )
    )

    update_json_with_dicom_value(sidecar_path, MISSING_TIME_ZERO, Dataset())

    sidecar = json.loads(sidecar_path.read_text())
    assert sidecar["TimeZero"] == "12:34:56"
    assert sidecar["ScanStart"] == 4.5
    assert "AcquisitionTime" not in sidecar


def test_missing_time_zero_requires_series_time(tmp_path):
    sidecar_path = tmp_path / "sidecar.json"
    sidecar_path.write_text(json.dumps({"AcquisitionTime": "12:35:07.000000"}))

    with pytest.raises(ValueError, match="SeriesTime is missing"):
        update_json_with_dicom_value(sidecar_path, MISSING_TIME_ZERO, Dataset())


def test_missing_time_zero_uses_dicom_series_time(tmp_path):
    sidecar_path = tmp_path / "sidecar.json"
    sidecar_path.write_text(json.dumps({"AcquisitionTime": "12:35:07.000000"}))
    dicom_header = Dataset()
    dicom_header.SeriesTime = "112233.000000"

    update_json_with_dicom_value(
        sidecar_path,
        MISSING_TIME_ZERO,
        dicom_header,
    )

    sidecar = json.loads(sidecar_path.read_text())
    assert sidecar["TimeZero"] == "11:22:33"


def test_missing_time_zero_parses_compact_dicom_time(tmp_path):
    sidecar_path = tmp_path / "sidecar.json"
    sidecar_path.write_text(json.dumps({"AcquisitionTime": "13:51:00"}))
    dicom_header = Dataset()
    dicom_header.SeriesTime = "135026"

    update_json_with_dicom_value(
        sidecar_path,
        MISSING_TIME_ZERO,
        dicom_header,
    )

    sidecar = json.loads(sidecar_path.read_text())
    assert sidecar["TimeZero"] == "13:50:26"


def test_ezbids_parses_compact_dicom_acquisition_time(tmp_path):
    sidecar_path = tmp_path / "sidecar.json"
    sidecar_path.write_text("{}")
    dicom_header = Dataset()
    dicom_header.AcquisitionDate = "20260102"
    dicom_header.AcquisitionTime = "090625"

    update_json_with_dicom_value(sidecar_path, {}, dicom_header, ezbids=True)

    sidecar = json.loads(sidecar_path.read_text())
    assert sidecar["AcquisitionDate"] == "2026-01-02"
    assert sidecar["AcquisitionTime"] == "09:06:25"
    assert sidecar["AcquisitionDateTime"] == "2026-01-02T09:06:25"


def test_ezbids_missing_acquisition_tags_uses_datetime_sentinel(tmp_path):
    sidecar_path = tmp_path / "sidecar.json"
    sidecar_path.write_text("{}")

    update_json_with_dicom_value(sidecar_path, {}, Dataset(), ezbids=True)

    sidecar = json.loads(sidecar_path.read_text())
    assert sidecar["AcquisitionDateTime"] == "0000-00-00T00:00:00"
    assert "AcquisitionDate" not in sidecar
    assert "AcquisitionTime" not in sidecar


def test_spreadsheet_compact_time_is_not_parsed_as_a_date(tmp_path, monkeypatch):
    spreadsheet = tmp_path / "metadata.xlsx"
    spreadsheet.touch()
    monkeypatch.setattr(
        update_json_pet_file.helper_functions,
        "single_spreadsheet_reader",
        lambda **kwargs: {"InjectionTime": "090625"},
    )

    metadata = get_metadata_from_spreadsheet(spreadsheet, tmp_path)

    assert metadata["nifti_json"]["InjectionTime"] == "09:06:25"


def test_reconstruction_fallback_accepts_path(tmp_path):
    sidecar_path = tmp_path / "sidecar.json"
    sidecar_path.write_text(
        json.dumps(
            {
                "ReconstructionMethod": "PSF+TOF 3i21s",
                "ReconMethodName": "incomplete native result",
            }
        )
    )
    dicom_header = Dataset()
    dicom_header.ReconstructionMethod = "PSF+TOF 3i21s"

    update_json_with_dicom_value(
        sidecar_path,
        {"ReconMethodParameterLabels": {"key": False, "value": False}},
        dicom_header,
    )

    sidecar = json.loads(sidecar_path.read_text())
    assert sidecar["ReconMethodName"] == (
        "Point-Spread Function modelling Time Of Flight"
    )
    assert sidecar["ReconMethodParameterLabels"] == ["subsets", "iterations"]

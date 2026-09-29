import json

import pytest
from pydicom.dataset import Dataset

from pypet2bids.update_json_pet_file import update_json_with_dicom_value


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

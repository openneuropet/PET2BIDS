import json

import pytest
from pydicom.dataset import Dataset

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


@pytest.mark.parametrize("series_time", ["090625", "135026"])
def test_missing_time_zero_uses_six_digit_dicom_series_time(tmp_path, series_time):
    sidecar_path = tmp_path / "sidecar.json"
    sidecar_path.write_text(json.dumps({"AcquisitionTime": "12:35:07.000000"}))
    dicom_header = Dataset()
    dicom_header.SeriesTime = series_time

    update_json_with_dicom_value(sidecar_path, MISSING_TIME_ZERO, dicom_header)

    sidecar = json.loads(sidecar_path.read_text())
    assert sidecar["TimeZero"] == (
        f"{series_time[:2]}:{series_time[2:4]}:{series_time[4:]}"
    )


@pytest.mark.parametrize(
    ("acquisition_time", "expected_time"),
    [
        ("090625", "09:06:25"),
        ("135026", "13:50:26"),
        ("135026.123456", "13:50:26.123456"),
    ],
)
def test_ezbids_uses_dicom_acquisition_date_and_time(
    tmp_path, acquisition_time, expected_time
):
    sidecar_path = tmp_path / "sidecar.json"
    sidecar_path.write_text("{}")
    dicom_header = Dataset()
    dicom_header.AcquisitionDate = "20261009"
    dicom_header.AcquisitionTime = acquisition_time

    update_json_with_dicom_value(sidecar_path, {}, dicom_header, ezbids=True)

    sidecar = json.loads(sidecar_path.read_text())
    assert sidecar["AcquisitionDate"] == "2026-10-09"
    assert sidecar["AcquisitionTime"] == expected_time
    assert sidecar["AcquisitionDateTime"] == f"2026-10-09T{expected_time}"


@pytest.mark.parametrize("present_tag", [None, "AcquisitionDate", "AcquisitionTime"])
def test_ezbids_handles_missing_acquisition_tags(tmp_path, present_tag):
    sidecar_path = tmp_path / "sidecar.json"
    sidecar_path.write_text("{}")
    dicom_header = Dataset()
    if present_tag == "AcquisitionDate":
        dicom_header.AcquisitionDate = "20261009"
    elif present_tag == "AcquisitionTime":
        dicom_header.AcquisitionTime = "135026"

    update_json_with_dicom_value(sidecar_path, {}, dicom_header, ezbids=True)

    sidecar = json.loads(sidecar_path.read_text())
    assert sidecar["AcquisitionDate"] == "0000-00-00"
    assert sidecar["AcquisitionTime"] == "00:00:00"
    assert sidecar["AcquisitionDateTime"] == "0000-00-00T00:00:00"


@pytest.mark.parametrize(
    ("spreadsheet_time", "expected"),
    [("090625", "09:06:25"), ("135026", "13:50:26")],
)
def test_csv_compact_clock_times(tmp_path, spreadsheet_time, expected):
    metadata_path = tmp_path / "metadata.csv"
    metadata_path.write_text(f"TimeZero\n{spreadsheet_time}\n")

    metadata = get_metadata_from_spreadsheet(
        metadata_path,
        image_folder=tmp_path,
        warn_missing=False,
    )

    assert metadata["nifti_json"]["TimeZero"] == expected


def test_spreadsheet_numeric_timing_field_is_not_parsed_as_clock_time(tmp_path):
    metadata_path = tmp_path / "metadata.csv"
    metadata_path.write_text("ImageDecayCorrectionTime\n135026\n")

    metadata = get_metadata_from_spreadsheet(
        metadata_path,
        image_folder=tmp_path,
        warn_missing=False,
    )

    assert metadata["nifti_json"]["ImageDecayCorrectionTime"] == 135026


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

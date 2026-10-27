"""Synthetic sorter regressions; no converter, phantom data, or PET imports."""

import importlib.util
import subprocess
import sys
import warnings
from datetime import date, time
from pathlib import Path

import pydicom
import pytest
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import (
    ExplicitVRLittleEndian,
    SecondaryCaptureImageStorage,
    generate_uid,
)

# Load the file independently to exercise its standalone use and avoid importing
# the package's unrelated converter dependencies and configuration machinery.
MODULE_PATH = Path(__file__).parents[1] / "pypet2bids" / "sort_dcm.py"
SPEC = importlib.util.spec_from_file_location("standalone_sort_dcm", MODULE_PATH)
sorter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sorter)


def names_fixture(folder, names):
    folder.mkdir(exist_ok=True)
    for name in names:
        (folder / name).touch()
    return folder


def dicom_fixture(folder, names, times, dates=None):
    folder.mkdir(exist_ok=True)
    dates = dates if dates is not None else ["20260929"] * len(names)
    for name, acquisition_time, acquisition_date in zip(names, times, dates):
        meta = FileMetaDataset()
        meta.MediaStorageSOPClassUID = SecondaryCaptureImageStorage
        meta.MediaStorageSOPInstanceUID = generate_uid()
        meta.TransferSyntaxUID = ExplicitVRLittleEndian
        dataset = FileDataset(
            str(folder / name), {}, file_meta=meta, preamble=b"\0" * 128
        )
        dataset.SOPClassUID = meta.MediaStorageSOPClassUID
        dataset.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
        if acquisition_time is not None:
            dataset.AcquisitionTime = acquisition_time
        if acquisition_date is not None:
            dataset.AcquisitionDate = acquisition_date
        dataset.save_as(folder / name)
    return folder


def test_numeric_names_without_header_reads_or_renaming(tmp_path, monkeypatch):
    names = ["10.dcm", "2.dcm", "1.dcm", "001.dcm", "100.dcm"]
    names_fixture(tmp_path, names)

    def fail(*args, **kwargs):
        pytest.fail("Name mode must not read DICOM headers")

    monkeypatch.setattr(pydicom, "dcmread", fail)
    assert sorter.sort_dcm(tmp_path) == [
        "001.dcm",
        "1.dcm",
        "2.dcm",
        "10.dcm",
        "100.dcm",
    ]
    assert sorted(path.name for path in tmp_path.iterdir()) == sorted(names)
    assert all(path.stat().st_size == 0 for path in tmp_path.iterdir())


def test_extensions_and_no_recursion(tmp_path):
    names_fixture(
        tmp_path,
        [
            "1001.dcm",
            "10.IMA",
            "1000.dcm",
            "1",
            "100.dcm",
            "2.DCM",
            "20.img",
            "notes.txt",
        ],
    )
    nested = tmp_path / "3.dcm"
    nested.mkdir()
    (nested / "4.dcm").touch()
    assert sorter.sort_dcm(str(tmp_path)) == [
        "1",
        "2.DCM",
        "10.IMA",
        "20.img",
        "100.dcm",
        "1000.dcm",
        "1001.dcm",
    ]


def test_natural_names_whitespace_and_ties(tmp_path):
    names_fixture(
        tmp_path,
        [
            "subject name 10.dcm",
            "subject name  3.dcm",
            "subject name 2.dcm",
            "subject name 02.dcm",
        ],
    )
    assert sorter.sort_dcm(tmp_path) == [
        "subject name 02.dcm",
        "subject name 2.dcm",
        "subject name  3.dcm",
        "subject name 10.dcm",
    ]


def test_exact_long_integers(tmp_path):
    large = "9" * 5000
    # Explicit paths need not exist in name mode; this also covers integers
    # beyond Python's integer-string conversion limit without filesystem limits.
    files = sorter.sort_dicom_files(
        [large + ".dcm", "2.dcm", "9007199254740993.dcm", "9007199254740992.dcm"]
    )
    assert [path.name for path in files] == [
        "2.dcm",
        "9007199254740992.dcm",
        "9007199254740993.dcm",
        large + ".dcm",
    ]


@pytest.mark.parametrize(
    "pattern",
    [
        r"^slice(?P<slice>\d+)_frame(?P<frame>\d+)$",
        r"^slice\d+_frame(?P<frame>\d+)$",
    ],
)
def test_frame_pattern(tmp_path, pattern):
    names_fixture(
        tmp_path, ["slice2_frame10.dcm", "slice10_frame2.dcm", "slice2_frame2.dcm"]
    )
    assert sorter.sort_dcm(tmp_path, pattern=pattern) == [
        "slice2_frame2.dcm",
        "slice10_frame2.dcm",
        "slice2_frame10.dcm",
    ]


@pytest.mark.parametrize(
    "pattern",
    [
        42,
        "[z-a]",
        r"^slice(?P<slice>\d+)_frame\d+$",
        r"^(?P<frame>\d+)$",
        r"^slice(?P<slice>.*)_frame(?P<frame>\d+)$",
    ],
)
def test_invalid_patterns(tmp_path, pattern):
    names_fixture(tmp_path, ["sliceX_frame2.dcm"])
    with pytest.raises(ValueError):
        sorter.sort_dcm(tmp_path, pattern=pattern)


def test_auto_keeps_chronological_names(tmp_path):
    dicom_fixture(
        tmp_path, ["10.dcm", "2.dcm", "1.dcm"], ["120003", "120002", "120001"]
    )
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert sorter.sort_dcm(tmp_path, "auto") == ["1.dcm", "2.dcm", "10.dcm"]


def test_auto_repairs_interleaved_times_and_reads_once(tmp_path, monkeypatch):
    dicom_fixture(
        tmp_path,
        ["1.dcm", "2.dcm", "3.dcm", "4.dcm"],
        ["120002", "120001", "120002", "120001"],
    )
    read = pydicom.dcmread
    calls = []

    def record(path, **kwargs):
        calls.append(path)
        assert kwargs == {
            "stop_before_pixels": True,
            "specific_tags": ["AcquisitionDate", "AcquisitionTime"],
        }
        return read(path, **kwargs)

    monkeypatch.setattr(pydicom, "dcmread", record)
    with pytest.warns(sorter.DicomOrderWarning):
        assert sorter.sort_dcm(tmp_path, "auto") == ["2.dcm", "4.dcm", "1.dcm", "3.dcm"]
    assert len(calls) == len(set(calls)) == 4


@pytest.mark.parametrize("method", ["auto", "acquisition_time"])
def test_midnight_and_year_boundary(tmp_path, method):
    dicom_fixture(
        tmp_path,
        ["1.dcm", "2.dcm", "3.dcm"],
        ["235959.999999", "000000", "000000.000001"],
        ["20261231", "20270101", "20270101"],
    )
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert sorter.sort_dcm(tmp_path, method) == ["1.dcm", "2.dcm", "3.dcm"]


def test_dates_take_priority_over_times(tmp_path):
    dicom_fixture(
        tmp_path, ["1.dcm", "2.dcm"], ["000001", "235959"], ["20270101", "20261231"]
    )
    with pytest.warns(sorter.DicomOrderWarning):
        assert sorter.sort_dcm(tmp_path, "auto") == ["2.dcm", "1.dcm"]


def test_equal_times_on_different_dates(tmp_path):
    dicom_fixture(
        tmp_path, ["1.dcm", "2.dcm"], ["120000", "120000"], ["20261001", "20260930"]
    )
    assert sorter.sort_dcm(tmp_path, "acquisition_time") == ["2.dcm", "1.dcm"]


@pytest.mark.parametrize("method", ["auto", "acquisition_time"])
def test_pattern_breaks_datetime_ties(tmp_path, method):
    dicom_fixture(
        tmp_path,
        ["slice2_frame10.dcm", "slice10_frame2.dcm", "slice2_frame2.dcm"],
        ["120001"] * 3,
    )
    assert sorter.sort_dcm(
        tmp_path, method, r"^slice(?P<slice>\d+)_frame(?P<frame>\d+)$"
    ) == ["slice2_frame2.dcm", "slice10_frame2.dcm", "slice2_frame10.dcm"]


@pytest.mark.parametrize("tag", ["AcquisitionDate", "AcquisitionTime"])
@pytest.mark.parametrize("method", ["auto", "acquisition_time"])
def test_missing_tags(tmp_path, tag, method):
    times = [None] if tag == "AcquisitionTime" else ["120000"]
    dates = [None] if tag == "AcquisitionDate" else ["20260929"]
    dicom_fixture(tmp_path, ["1.dcm"], times, dates)
    with pytest.raises(ValueError, match="Missing " + tag):
        sorter.sort_dcm(tmp_path, method)


@pytest.mark.parametrize(
    "tag,value",
    [
        ("AcquisitionDate", "20230229"),
        ("AcquisitionDate", "20260431"),
        ("AcquisitionDate", "20261301"),
        ("AcquisitionDate", "00000101"),
        ("AcquisitionDate", "2026-10-01"),
        ("AcquisitionDate", 20261001),
        ("AcquisitionTime", "240000"),
        ("AcquisitionTime", "126000"),
        ("AcquisitionTime", "120061"),
        ("AcquisitionTime", "12:00:00"),
        ("AcquisitionTime", "120000.1234567"),
        ("AcquisitionTime", 120000),
    ],
)
def test_invalid_tags(tmp_path, monkeypatch, tag, value):
    names_fixture(tmp_path, ["1.dcm"])
    header = {"AcquisitionDate": "20260929", "AcquisitionTime": "120000", tag: value}
    monkeypatch.setattr(pydicom, "dcmread", lambda *args, **kwargs: header)
    with pytest.raises(ValueError, match="Invalid " + tag):
        sorter.sort_dcm(tmp_path, "auto")


@pytest.mark.parametrize(
    "times",
    [
        ["12", "1201", "120100.000001"],
        ["120059.5", "120100", "120100.25"],
        ["235959", "235960", "235960.5"],
    ],
)
def test_time_formats_fractional_precision_and_leap_seconds(tmp_path, times):
    dicom_fixture(tmp_path, ["3.dcm", "2.dcm", "1.dcm"], times, ["20240229"] * 3)
    assert sorter.sort_dcm(tmp_path, "acquisition_time") == ["3.dcm", "2.dcm", "1.dcm"]


def test_pydicom_datetime_conversion(tmp_path, monkeypatch):
    dicom_fixture(
        tmp_path,
        ["1.dcm", "2.dcm"],
        ["235959.999999", "000000.000001"],
        ["20261231", "20270101"],
    )
    monkeypatch.setattr(pydicom.config, "datetime_conversion", True)
    assert sorter.sort_dcm(tmp_path, "auto") == ["1.dcm", "2.dcm"]


def test_converted_leap_seconds_preserve_original_time(tmp_path, monkeypatch):
    dicom_fixture(tmp_path, ["1.dcm", "2.dcm"], ["235960", "235959"])
    monkeypatch.setattr(pydicom.config, "datetime_conversion", True)
    with warnings.catch_warnings():
        # pydicom warns when converting the permitted leap second to time.
        warnings.simplefilter("ignore", UserWarning)
        assert sorter.sort_dcm(tmp_path, "acquisition_time") == ["2.dcm", "1.dcm"]


def test_native_date_and_time_values(tmp_path, monkeypatch):
    names_fixture(tmp_path, ["1.dcm", "2.dcm"])
    headers = {
        "1.dcm": {
            "AcquisitionDate": date(2026, 12, 31),
            "AcquisitionTime": time(23, 59, 59, 999999),
        },
        "2.dcm": {
            "AcquisitionDate": date(2027, 1, 1),
            "AcquisitionTime": time(0, 0, 0, 1),
        },
    }
    monkeypatch.setattr(pydicom, "dcmread", lambda path, **kwargs: headers[path.name])
    assert sorter.sort_dcm(tmp_path, "auto") == ["1.dcm", "2.dcm"]


def test_explicit_subset_preserves_paths(tmp_path):
    folder = names_fixture(tmp_path, ["1.dcm", "2.dcm", "10.dcm"])
    assert sorter.sort_dicom_files([folder / "10.dcm", folder / "2.dcm"]) == [
        folder / "2.dcm",
        folder / "10.dcm",
    ]


def test_empty_invalid_folder_and_method(tmp_path):
    assert sorter.sort_dcm(tmp_path) == []
    with pytest.raises(NotADirectoryError):
        sorter.sort_dcm(tmp_path / "missing")
    for method in [None, 42, "other"]:
        with pytest.raises(ValueError):
            sorter.sort_dcm(tmp_path, method)


def test_invalid_dicom_is_not_silently_skipped(tmp_path):
    names_fixture(tmp_path, ["1.dcm"])
    with pytest.raises(pydicom.errors.InvalidDicomError):
        sorter.sort_dcm(tmp_path, "auto")


def test_standalone_cli(tmp_path):
    names_fixture(tmp_path, ["10.dcm", "2.dcm", "1.dcm"])
    result = subprocess.run(
        # Isolated mode without site packages proves name sorting depends only
        # on the standard library, even when launched outside the package.
        [sys.executable, "-I", "-S", str(MODULE_PATH), str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["1.dcm", "2.dcm", "10.dcm"]

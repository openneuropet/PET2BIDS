"""Concurrent DICOM header reading and temporal-frame grouping."""

import concurrent.futures
import math
import os
from pathlib import Path

import pydicom

__all__ = [
    "default_worker_count",
    "group_dicom_headers_by_frame",
    "read_dicom_frames",
    "read_dicom_headers",
    "reduce_dicom_frames",
]


def default_worker_count(cpu_count=None):
    """Return one quarter of available CPUs, rounded up to an even number."""
    available = cpu_count if cpu_count is not None else (os.cpu_count() or 1)
    quarter = available / 4
    return 2 * math.ceil(quarter / 2)


def _read_header(path):
    try:
        dataset = pydicom.dcmread(path, stop_before_pixels=True)
        sop_class_uid = getattr(dataset, "SOPClassUID", None)
        if not sop_class_uid:
            file_meta = getattr(dataset, "file_meta", None)
            sop_class_uid = getattr(file_meta, "MediaStorageSOPClassUID", None)
        return dataset if sop_class_uid else None
    except MemoryError:
        raise
    # Directory scans are untrusted input; one malformed file must not stop them.
    except Exception:
        return None


def _as_text(value):
    if value is None:
        return ""
    return str(value).strip()


def _as_number(value):
    if value is None or value == "":
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _scalar_keyword(dataset, keyword):
    values = []
    for element in dataset.iterall():
        if element.keyword == keyword and element.VR != "SQ":
            value = element.value
            if isinstance(value, (list, tuple)):
                values.extend(value)
            else:
                values.append(value)
    if not values:
        return None
    return values[0] if len({_as_text(value) for value in values}) == 1 else None


def _frame_identity(dataset):
    temporal = _scalar_keyword(dataset, "TemporalPositionIdentifier")
    if temporal is not None:
        return "TemporalPositionIdentifier", _as_text(temporal)

    reference = _scalar_keyword(dataset, "FrameReferenceTime")
    if reference is not None:
        return "FrameReferenceTime", _as_text(reference)

    acquisition_datetime = _scalar_keyword(dataset, "AcquisitionDateTime")
    if acquisition_datetime is not None:
        return "AcquisitionDateTime", _as_text(acquisition_datetime)

    date = _as_text(_scalar_keyword(dataset, "AcquisitionDate"))
    time = _as_text(_scalar_keyword(dataset, "AcquisitionTime"))
    if date or time:
        return "AcquisitionDate+AcquisitionTime", f"{date}T{time}"

    return "UnidentifiedFrame", "1"


def _frame_order(frame):
    ranks = {
        "TemporalPositionIdentifier": 0,
        "FrameReferenceTime": 1,
        "AcquisitionDateTime": 2,
        "AcquisitionDate+AcquisitionTime": 3,
        "UnidentifiedFrame": 4,
    }
    kind = frame["frame_key_kind"]
    value = frame["frame_key"]
    rank = ranks.get(kind, 5)
    number = None
    if kind in ("TemporalPositionIdentifier", "FrameReferenceTime"):
        number = _as_number(value)
    sortable = (0, number) if number is not None else (1, value)
    return frame["series_uid"], rank, sortable, value


def read_dicom_headers(paths, workers=None):
    """Read DICOM headers concurrently, preserving the supplied path order.

    Returns ``(headers, skipped)``. Each header is paired with its input path;
    unreadable and non-DICOM files contribute to the skipped count.
    """
    paths = [Path(path) for path in paths]
    if workers is None:
        workers = default_worker_count()
    if workers < 1:
        raise ValueError("workers must be at least 1")

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        datasets = executor.map(_read_header, paths)
        headers = [
            (path, dataset)
            for path, dataset in zip(paths, datasets)
            if dataset is not None
        ]
    return headers, len(paths) - len(headers)


def group_dicom_headers_by_frame(headers):
    """Group ``(path, dataset)`` pairs by series and temporal-frame metadata.

    Frames are returned in chronological order within each series. Headers
    within frames retain input order. Enhanced multi-frame DICOMs are rejected
    because their frames require per-frame sequence parsing.
    """
    frames = {}
    for path, dataset in headers:
        number_of_frames = _as_number(getattr(dataset, "NumberOfFrames", None))
        if number_of_frames is not None and number_of_frames > 1:
            raise ValueError(
                f"Enhanced multi-frame DICOM is not supported yet: {path} has "
                f"{int(number_of_frames)} frames."
            )

        series_uid = _as_text(getattr(dataset, "SeriesInstanceUID", None))
        if not series_uid:
            series_uid = f"missing-series-uid:{Path(path).parent}"
        frame_key_kind, frame_key = _frame_identity(dataset)
        identity = (series_uid, frame_key_kind, frame_key)
        if identity not in frames:
            frames[identity] = {
                "series_uid": series_uid,
                "frame_key_kind": frame_key_kind,
                "frame_key": frame_key,
                "headers": [],
            }
        frames[identity]["headers"].append((Path(path), dataset))
    return sorted(frames.values(), key=_frame_order)


def read_dicom_frames(paths, workers=None):
    """Read headers concurrently and return chronologically ordered frames."""
    headers, skipped = read_dicom_headers(paths, workers=workers)
    return group_dicom_headers_by_frame(headers), skipped


def reduce_dicom_frames(frames):
    """Return the first DICOM dataset from each frame."""
    reduced = []
    for frame in frames:
        if not frame["headers"]:
            raise ValueError("cannot reduce a frame without DICOM headers")
        reduced.append(frame["headers"][0][1])
    return reduced

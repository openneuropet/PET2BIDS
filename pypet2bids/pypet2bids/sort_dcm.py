"""Reusable DICOM filename ordering, independent of PET/BIDS conversion.

Name ordering needs only the Python standard library. Checked ordering imports
pydicom lazily and reads only AcquisitionDate/Time, never pixel data. Files are
never renamed. This module can also be copied and imported as ``sort_dcm``.
"""

from __future__ import annotations

import argparse
import re
import warnings
from datetime import date, time
from decimal import Decimal
from os import PathLike
from pathlib import Path
from typing import Iterable, Union

__all__ = ["DicomOrderWarning", "sort_dcm", "sort_dicom_files"]
PathType = Union[str, PathLike]


class DicomOrderWarning(UserWarning):
    """Filename order disagrees with acquisition date/time."""


def _integer_key(value):
    significant = value.lstrip("0") or "0"
    return len(significant), significant


def _natural_keys(names):
    normalized = [re.sub(r"\s+", " ", name) for name in names]
    width = max(
        (len(number) for name in normalized for number in re.findall(r"[0-9]+", name)),
        default=0,
    )
    return [
        re.sub(
            r"[0-9]+",
            lambda match: (match[0].lstrip("0") or "0").zfill(width),
            name,
        )
        for name in normalized
    ]


def _acquisition_datetime(path):
    import pydicom

    header = pydicom.dcmread(
        path,
        stop_before_pixels=True,
        specific_tags=["AcquisitionDate", "AcquisitionTime"],
    )
    value = header.get("AcquisitionTime")
    if value is None:
        raise ValueError(f"Missing AcquisitionTime in {path}.")
    # pydicom's TM conversion clamps leap seconds to 59; its original string
    # retains the actual value and must take priority when present.
    if isinstance(value, time) and hasattr(value, "original_string"):
        value = value.original_string
    if isinstance(value, time):
        seconds = Decimal(value.hour * 3600 + value.minute * 60 + value.second)
        seconds += Decimal(value.microsecond) / 1_000_000
    else:
        if not isinstance(value, str) or not re.fullmatch(
            r"([0-9]{2}|[0-9]{4}|[0-9]{6}(\.[0-9]{1,6})?)", value.strip()
        ):
            raise ValueError(f"Invalid AcquisitionTime in {path}.")
        value = value.strip()
        hours = int(value[:2])
        minutes = int(value[2:4]) if len(value) >= 4 else 0
        seconds = Decimal(value[4:]) if len(value) >= 6 else Decimal(0)
        # Preserve the permitted leap-second value of 60.
        if hours > 23 or minutes > 59 or seconds >= 61:
            raise ValueError(f"Invalid AcquisitionTime in {path}.")
        seconds += hours * 3600 + minutes * 60

    value = header.get("AcquisitionDate")
    if value is None or value == "":
        raise ValueError(f"Missing AcquisitionDate in {path}.")
    if not isinstance(value, date):
        if not isinstance(value, str) or not re.fullmatch(r"[0-9]{8}", value.strip()):
            raise ValueError(f"Invalid AcquisitionDate in {path}.")
        value = value.strip()
        try:
            value = date(int(value[:4]), int(value[4:6]), int(value[6:8]))
        except ValueError as exc:
            raise ValueError(f"Invalid AcquisitionDate in {path}.") from exc
    # Separate keys avoid rounding fractional seconds against a large epoch.
    return value.toordinal(), seconds


def sort_dicom_files(
    paths: Iterable[PathType], method: str = "name", pattern: str | None = None
) -> list[Path]:
    r"""Order explicit DICOM paths, including a subset selected by another tool.

    ``name`` orders numeric stems by value and mixed names naturally, without
    reading headers. ``acquisition_time`` orders by AcquisitionDate, then
    AcquisitionTime. ``auto`` checks name/pattern order, warning and reordering
    when it is not chronological. Checked modes require both valid tags.

    ``pattern`` is a Python regex searched against each filename stem, with a
    named ``frame`` integer group and optional ``slice`` integer group, e.g.
    ``r'^slice(?P<slice>\d+)_frame(?P<frame>\d+)$'``. Every path must match.
    Equal frame/slice keys retain natural filename order; equal dates/times
    retain name/pattern order. Whitespace is normalized only in sorting keys.
    Alphabetical order breaks equivalent numeric keys. Integers of any length
    are compared as text without converting to floating point.

    Returns unchanged paths as Path objects. The explicit list is not filtered
    by extension. Unreadable DICOMs and invalid tags raise errors; files on disk
    are never changed. AcquisitionDate is used, with no StudyDate substitution.
    """
    if not isinstance(method, str) or method.lower() not in (
        "name",
        "acquisition_time",
        "auto",
    ):
        raise ValueError("method must be 'name', 'acquisition_time' or 'auto'.")
    method = method.lower()
    expression = None
    if pattern is not None and not isinstance(pattern, str):
        raise ValueError("pattern must be a string or None.")
    if pattern:
        try:
            expression = re.compile(pattern)
        except re.error as exc:
            raise ValueError("pattern must be a valid regular expression.") from exc
        if "frame" not in expression.groupindex:
            raise ValueError("pattern must contain a named integer frame group.")

    files = sorted(
        (Path(path) for path in paths), key=lambda path: (path.name, str(path))
    )
    stems = [re.sub(r"(?i)\.(dcm|ima|img)$", "", path.name) for path in files]
    if not expression and all(re.fullmatch(r"[0-9]+", stem) for stem in stems):
        files = [
            path
            for _, path in sorted(
                zip(stems, files), key=lambda pair: _integer_key(pair[0])
            )
        ]
    else:
        keys = _natural_keys([path.name for path in files])
        files = [path for _, path in sorted(zip(keys, files), key=lambda pair: pair[0])]
    if expression:
        keys = []
        for path in files:
            stem = re.sub(r"(?i)\.(dcm|ima|img)$", "", path.name)
            match = expression.search(stem)
            groups = ["frame"] + (["slice"] if "slice" in expression.groupindex else [])
            key = []
            for group in groups:
                value = match.group(group) if match else None
                if value is None or not re.fullmatch(r"[0-9]+", value):
                    raise ValueError(
                        f"Pattern must match an integer {group} in {path}."
                    )
                key.append(_integer_key(value))
            keys.append(tuple(key))
        files = [path for _, path in sorted(zip(keys, files), key=lambda pair: pair[0])]

    if method != "name":
        timestamps = [_acquisition_datetime(path) for path in files]
        chronological = all(a <= b for a, b in zip(timestamps, timestamps[1:]))
        if method == "auto" and chronological:
            return files
        if method == "auto":
            warnings.warn(
                "Filename order does not follow acquisition date/time; "
                "returning acquisition-time order.",
                DicomOrderWarning,
                stacklevel=2,
            )
        files = [
            path for _, path in sorted(zip(timestamps, files), key=lambda pair: pair[0])
        ]
    return files


def sort_dcm(
    folder: PathType, method: str = "name", pattern: str | None = None
) -> list[str]:
    """Return DICOM filenames in a folder using ``sort_dicom_files`` ordering.

    Includes .dcm/.ima/.img extensions (case insensitive) and extensionless files.
    Extensionless files are assumed to be DICOM. Subfolders are not searched.
    Returns unchanged filenames without folder paths, matching MATLAB sort_dcm.
    """
    folder = Path(folder)
    if not folder.is_dir():
        raise NotADirectoryError(f"folder must be an existing directory: {folder}")
    paths = [
        path
        for path in folder.iterdir()
        if path.is_file()
        and (path.suffix.lower() in (".dcm", ".ima", ".img") or "." not in path.name)
    ]
    return [path.name for path in sort_dicom_files(paths, method, pattern)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", help="Folder containing DICOM files")
    parser.add_argument(
        "--method", choices=("name", "acquisition_time", "auto"), default="name"
    )
    parser.add_argument(
        "--pattern",
        help="Filename-stem regex with named frame and optional slice groups",
    )
    args = parser.parse_args()
    for name in sort_dcm(args.folder, args.method, args.pattern):
        print(name)


if __name__ == "__main__":
    main()

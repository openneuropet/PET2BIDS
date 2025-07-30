import sys
import json
import re
import requests
from pathlib import Path
from typing import Dict, Any, Optional, Union
from types import SimpleNamespace


def get_bids_schema(schema_version: str = "latest") -> Dict[str, Any]:
    """
    Get the BIDS schema, with fallback to online version.

    Args:
        schema_version: BIDS schema version (default: "latest")

    Returns:
        Dictionary containing the BIDS schema

    Raises:
        FileNotFoundError: If schema cannot be found locally or online
    """

    # Try local packaged schema first (static version)
    schema_path = Path(__file__).parent / "bids_schema.json"

    if schema_path.exists():
        try:
            with open(schema_path, "r") as f:
                return json.load(f)
        except Exception:
            pass

    # Fallback to online schema
    try:
        url = (
            f"https://bids-specification.readthedocs.io/en/{schema_version}/schema.json"
        )
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        pass

    raise FileNotFoundError(
        f"BIDS schema not found. Tried local at {schema_path} and online at {url}"
    )


def get_schema_path() -> Path:
    """Get the path to the packaged schema file."""
    return Path(__file__).parent / "bids_schema.json"


def load_schema_as_namedtuple(name: str, data: Union[dict, list, Any]) -> Any:
    """
    Convert a dictionary to a SimpleNamespace for dot notation access.

    Args:
        name: Name for the namespace (unused but kept for compatibility)
        data: Dictionary, list, or other data to convert

    Returns:
        SimpleNamespace object with dot notation access
    """
    if isinstance(data, dict):
        from types import SimpleNamespace

        return SimpleNamespace(
            **{k: load_schema_as_namedtuple(k, v) for k, v in data.items()}
        )
    elif isinstance(data, list):
        return [load_schema_as_namedtuple(name, v) for v in data]
    else:
        return data


def get_bids_schema_object(schema_version: str = "latest") -> Any:
    """
    Get the BIDS schema as a namedtuple object with dot notation access.

    Args:
        schema_version: BIDS schema version (default: "latest")

    Returns:
        Namedtuple object with dot notation access to schema
    """
    schema_dict = get_bids_schema(schema_version)
    return load_schema_as_namedtuple("BIDSSchema", schema_dict)


# Convenience function for MATLAB access
def get_schema_as_string() -> str:
    """Get the schema as a JSON string for MATLAB."""
    schema = get_bids_schema()
    return json.dumps(schema, indent=2)


# Backward compatibility functions (for existing code)
def collect_schema(schema_version: str = "latest") -> Dict[str, Any]:
    """
    Backward compatibility function for existing code.
    Use get_bids_schema() instead.
    """
    return get_bids_schema(schema_version)


def load_schema(name: str, data: Union[Dict, list, Any]) -> Any:
    """
    Backward compatibility function for existing code.
    Use load_schema_as_namedtuple() instead.
    """
    return load_schema_as_namedtuple(name, data)


schema = get_bids_schema()

blood_metadata = {
    "mandatory": [
        k
        for k, v in schema["rules"]["sidecars"]["pet"]["BloodRecording"][
            "fields"
        ].items()
        if v == "required"
    ],
    "recommended": [
        k
        for k, v in schema["rules"]["sidecars"]["pet"]["BloodRecording"][
            "fields"
        ].items()
        if v == "recommended"
    ],
}

dicom2bids = {
    "dcmfields": [
        "Manufacturer",
        "ManufacturerModelName",
        "Units",
        "InstitutionName",
        "InstitutionAddress",
        "InstitutionalDepartmentName",
        "BodyPartExamined",
        "MappingResource",
        "MappingResourceName",
        "CodeMeaning",
        "RadionuclideTotalDose",
        "RadiopharmaceuticalSpecificActivity",
        "RadiopharmaceuticalVolume",
        "InterventionDrugName",
        "InterventionDrugDose",
        "RadiopharmaceuticalStartTime",
        "ActualFrameDuration",
        "AcquisitionDate",
        "RadiopharmaceuticalStopTime",
        "ReconstructionMethod",
        "ReconstructionMethod",
        "ReconstructionMethod",
        "ReconstructionMethod",
        "ConvolutionKernel",
        "ConvolutionKernel",
        "AttenuationCorrectionMethod",
        "ScatterFractionFactor",
        "DoseCalibrationFactor",
        "DecayFactor",
    ],
    "jsonfields": [
        "Manufacturer",
        "ManufacturersModelName",
        "Units",
        "InstitutionName",
        "InstitutionAddress",
        "InstitutionalDepartmentName",
        "BodyPart",
        "TracerName",
        "TracerName",
        "TracerRadionuclide",
        "InjectedRadioactivity",
        "MolarActivity",
        "InjectedVolume",
        "PharmaceuticalName",
        "PharmaceuticalDoseAmount",
        "InjectionStart",
        "FrameDuration",
        "ScanDate",
        "InjectionEnd",
        "ReconMethodName",
        "ReconMethodParameterLabels",
        "ReconMethodParameterUnits",
        "ReconMethodParameterValues",
        "ReconFilterType",
        "ReconFilterSize",
        "AttenuationCorrection",
        "ScatterFraction",
        "DoseCalibrationFactor",
        "DecayCorrectionFactor",
    ],
    "RadionuclideCodes": {
        "C-105A": "^11^Carbon",
        "C-107A1": "^13^Nitrogen",
        "C-1018C": "^14^Oxygen",
        "C-B1038": "^15^Oxygen",
        "C-111A1": "^18^Fluorine",
        "C-155A1": "^22^Sodium",
        "C-135A4": "^38^Potassium",
        "126605": "^43^Scandium",
        "126600": "^44^Scandium",
        "C-166A2": "^45^Titanium",
        "126601": "^51^Manganese",
        "C-130A1": "^52^Iron",
        "C-149A1": "^52^Manganese",
        "126607": "^52m^Manganese",
        "C-127A4": "^60^Copper",
        "C-127A1": "^61^Copper",
        "C-127A5": "^62^Copper",
        "C-141A1": "^62^Zinc",
        "C-127A": "^64^Copper ",
        "C-131A1": "^66^Gallium",
        "C-131A3": "^68^Gallium",
        "C-128A2": "^68^Germanium",
        "126602": "^70^Arsenic",
        "C-115A2": "^72^Arsenic",
        "C-116A2": "^73^Selenium",
        "C-113A1": "^75^Bromine",
        "C-113A2": "^76^Bromine",
        "C-113A3": "^77^Bromine",
        "C-159A2": "^82^Rubidium",
        "C-162A3": "^86^Yttrium",
        "C-168A4": "^89^Zirconium",
        "126603": "^90^Niobium",
        "C-162A7": "^90^Yttrium",
        "C-163AA": "^94m^Technetium",
        "C-114A5": "^124^Iodine",
        "126606": "^152^Terbium",
    },
}
PET_reconstruction_filters = {
    "dicom_values": [
        {
            "value": "XYZGAUSSIAN3.00",
            "ReconFilterSize": 3,
            "ReconFilterType": "GAUSSIAN",
        }
    ]
}


PET_reconstruction_methods = {
    "reconstruction_method": [
        {
            "contents": "PSF+TOF3i21s",
            "subsets": 21,
            "iterations": 3,
            "ReconMethodName": "Point-Spread Function + Time Of Flight",
            "ReconMethodParameterUnits": [None, None],
            "ReconMethodParameterLabels": ["subsets", "iterations"],
            "ReconMethodParameterValues": [21, 3],
        },
        {
            "contents": "OP-OSEM3i21s",
            "subsets": 21,
            "iterations": 3,
            "ReconMethodName": "Ordinary Poisson - Ordered Subset Expectation Maximization",
            "ReconMethodParameterUnits": [None, None],
            "ReconMethodParameterLabels": ["subsets", "iterations"],
            "ReconMethodParameterValues": [21, 3],
        },
        {
            "contents": "OSEM3D-OP-PSFi10s16",
            "subsets": 16,
            "iterations": 10,
            "ReconMethodName": "Ordinary Poisson 3D Ordered Subset Expectation Maximization + Point-Spread Function",
            "ReconMethodParameterUnits": [None, None],
            "ReconMethodParameterLabels": ["subsets", "iterations"],
            "ReconMethodParameterValues": [16, 10],
        },
        {
            "contents": "OP_OSEM3D",
            "ReconMethodName": "Ordinary Poisson 3D Ordered Subset Expectation Maximization",
            "ReconMethodParameterUnits": [None, None],
            "ReconMethodParameterLabels": ["subsets", "iterations"],
            "ReconMethodParameterValues": [None, None],
        },
        {
            "contents": "LOR-RAMLA",
            "subsets": None,
            "iterations": None,
            "ReconMethodName": "Line Of Response - Row Action Maximum Likelihood",
            "ReconMethodParameterUnits": ["none", "none"],
            "ReconMethodParameterLabels": ["subsets", "iterations"],
            "ReconMethodParameterValues": [None, None],
        },
        {
            "contents": "3D-RAMLA",
            "subsets": None,
            "iterations": None,
            "ReconMethodName": "3D Row Action Maximum Likelihood",
            "ReconMethodParameterUnits": [None, None],
            "ReconMethodParameterLabels": ["subsets", "iterations"],
            "ReconMethodParameterValues": [None, None],
        },
        {
            "contents": "3DKinahan-Rogers",
            "subsets": None,
            "iterations": None,
            "ReconMethodName": "3D Reprojection",
            "ReconMethodParameterLabels": [],
            "ReconMethodParameterValues": [],
            "ReconMethodParameterUnits": [],
        },
    ],
    "reconstruction_names": [
        {"value": "OS", "name": "Ordered Subset"},
        {"value": "OSEM", "name": "Ordered Subset Expectation Maximization"},
        {"value": "LOR", "name": "Line Of Response"},
        {"value": "RAMLA", "name": "Row Action Maximum Likelihood"},
        {"value": "OP", "name": "Ordinary Poisson"},
        {"value": "PSF", "name": "Point-Spread Function modelling"},
        {"value": "TOF", "name": "Time Of Flight"},
        {"value": "TF", "name": "Time Of Flight"},
        {"value": "VPHD", "name": "VUE Point HD"},
        {
            "value": "VPHD-S",
            "name": "3D Ordered Subset Expectation Maximization with Point-Spread Function modelling",
        },
        {"value": "VPFX", "name": "VUE Point HD using Time Of Flight"},
        {
            "value": "VPFXS",
            "name": "VUE Point HD using Time Of Flight with Point-Spread Function modelling",
        },
        {"value": "Q.Clear", "name": "VUE Point HD with regularization (smoothing)"},
        {"value": "BLOB", "name": "3D spherically symmetric basis function"},
        {"value": "FilteredBackProjection", "name": "Filtered Back Projection"},
        {"value": "Kinahan-Rogers", "name": "Reprojection"},
    ],
}

# create a sidecar metadata schema
PET_metadata= {"required": [], "recommended": [], "optional": []}
for category in [
    "PETHardware",
    "PETInstitutionInformation",
    "PETSample",
    "PETRadioChemistry",
    "PETPharmaceuticals",
    "PETTime",
    "PETReconstruction",
]:
    for r in PET_metadata.keys():
        for k, v in schema["rules"]["sidecars"]["pet"][category]["fields"].items():
            if v == r or (type(v) == dict and v.get("level", "")) == r:
                PET_metadata[r].append(k)

PET_metadata["blood_recording_fields"] = schema["rules"]["sidecars"]["pet"]["BloodRecording"]["fields"].keys() + \
    schema["rules"]["sidecars"]["pet"]["BloodPlasmaFreeFraction"]["fields"].keys() + \
    schema["rules"]["sidecars"]["pet"]["BloodMetaboliteMethod"]["fields"].keys()

sys.modules[__name__] = SimpleNamespace(
    blood_metadata=blood_metadata,
    dicom2bids=dicom2bids,
    PET_reconstruction_filters=PET_reconstruction_filters,
    PET_reconstruction_methods=PET_reconstruction_methods,
    schema=schema,
    PET_metadata=PET_metadata,
)

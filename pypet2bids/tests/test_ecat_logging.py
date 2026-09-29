import json

import pytest

import pypet2bids.ecat as ecat_module
from pypet2bids.ecat import Ecat
from pypet2bids.ecat_cli import cli


def test_ecat_output_flags():
    parser = cli()

    defaults = parser.parse_args(["scan.v"])
    assert defaults.silent is False
    assert defaults.verbose is False

    verbose = parser.parse_args(["scan.v", "--verbose"])
    assert verbose.verbose is True
    assert verbose.silent is False

    with pytest.raises(SystemExit):
        parser.parse_args(["scan.v", "--silent", "--verbose"])


def test_ecat_conversion_checks_final_sidecar(tmp_path, monkeypatch):
    converter = Ecat.__new__(Ecat)
    converter.silent = False
    converter.verbose = True
    converter.nifti_file = tmp_path / "sub-01_pet.nii"
    converter.kwargs = {}
    converter.spreadsheet_metadata = {"blood_tsv": {}, "blood_json": {}}
    converter.telemetry_data = {}

    monkeypatch.setattr(converter, "make_nifti", lambda: converter.nifti_file)
    monkeypatch.setattr(converter, "populate_sidecar", lambda **kwargs: None)
    monkeypatch.setattr(converter, "prune_sidecar", lambda: None)
    monkeypatch.setattr(converter, "write_out_blood_files", lambda: None)
    monkeypatch.setattr(
        converter,
        "show_sidecar",
        lambda output_path: output_path.write_text(json.dumps({})),
    )
    monkeypatch.setattr(ecat_module, "telemetry_enabled", lambda: False)

    validation_calls = []
    monkeypatch.setattr(
        ecat_module,
        "check_json",
        lambda path, **kwargs: validation_calls.append((path, kwargs)),
    )

    converter.convert()

    assert validation_calls == [
        (
            tmp_path / "sub-01_pet.json",
            {
                "silent": False,
                "recommended": True,
                "logger_name": "pypet2bids",
            },
        )
    ]

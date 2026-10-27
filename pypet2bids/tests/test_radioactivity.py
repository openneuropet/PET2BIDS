"""Radiotracer regression tests, independent of scanner files and environment."""

import logging
from copy import deepcopy

import numpy as np
import pytest

from pypet2bids.update_json_pet_file import check_meta_radio_inputs
from pypet2bids.sidecar import sidecar_template_full


@pytest.fixture(autouse=True)
def capture_warnings(monkeypatch):
    # Use a plain logger so these unit tests do not depend on console formatting.
    monkeypatch.setattr(
        "pypet2bids.update_json_pet_file.helper_functions.logger",
        lambda name: logging.getLogger("tests.radioactivity"),
    )


REFERENCE = {
    "InjectedRadioactivity": 100,
    "InjectedMass": 2,
    "SpecificRadioactivity": 5e13,
    "MolarActivity": 15,
    "TracerMolecularWeight": 300,
}


@pytest.mark.parametrize(
    "target,first,second",
    [
        ("SpecificRadioactivity", "InjectedRadioactivity", "InjectedMass"),
        ("InjectedMass", "InjectedRadioactivity", "SpecificRadioactivity"),
        ("InjectedRadioactivity", "InjectedMass", "SpecificRadioactivity"),
        ("SpecificRadioactivity", "MolarActivity", "TracerMolecularWeight"),
        ("TracerMolecularWeight", "MolarActivity", "SpecificRadioactivity"),
        ("MolarActivity", "TracerMolecularWeight", "SpecificRadioactivity"),
    ],
)
def test_six_physical_relations(target, first, second):
    # Independent physical example: 100 MBq, 2 ug, 50 MBq/ug,
    # 15 GBq/umol and molecular weight 300 g/mol.
    result = check_meta_radio_inputs({key: REFERENCE[key] for key in (first, second)})
    assert result[target] == pytest.approx(REFERENCE[target])


@pytest.mark.parametrize(
    "unit,specific",
    [
        ("Bq/g", 5e13),
        ("MBq/ug", 50),
        ("kBq/mg", 5e7),
        ("GBq/g", 5e4),
        ("MBq/µg", 50),
        ("MBq/μg", 50),
    ],
)
@pytest.mark.parametrize(
    "source,target",
    [
        ("InjectedRadioactivity", "InjectedMass"),
        ("InjectedMass", "InjectedRadioactivity"),
        ("MolarActivity", "TracerMolecularWeight"),
        ("TracerMolecularWeight", "MolarActivity"),
    ],
)
def test_commensurate_specific_activity_units(unit, specific, source, target):
    result = check_meta_radio_inputs(
        {
            source: REFERENCE[source],
            "SpecificRadioactivity": specific,
            "SpecificRadioactivityUnits": unit,
        }
    )
    assert result[target] == pytest.approx(REFERENCE[target])
    assert result["SpecificRadioactivity"] == specific
    assert result["SpecificRadioactivityUnits"] == unit


def test_issue_400_activity_to_mass_conversion():
    result = check_meta_radio_inputs({"InjectedRadioactivity": 10, "InjectedMass": 10})
    assert result["SpecificRadioactivity"] == pytest.approx(1e12)
    assert result["SpecificRadioactivityUnits"] == "Bq/g"
    result = check_meta_radio_inputs(
        {
            "InjectedRadioactivity": 10,
            "InjectedMass": 10,
            "SpecificRadioactivityUnits": "MBq/ug",
        }
    )
    assert result["SpecificRadioactivity"] == pytest.approx(1)
    assert result["SpecificRadioactivityUnits"] == "MBq/ug"


def test_explicit_units_are_used_in_injected_quantity_relations():
    result = check_meta_radio_inputs(
        {
            "InjectedRadioactivity": 10,
            "InjectedRadioactivityUnits": "Bq",
            "InjectedMass": 10,
            "InjectedMassUnits": "g",
        }
    )
    assert result["SpecificRadioactivity"] == pytest.approx(1)
    assert result["SpecificRadioactivityUnits"] == "Bq/g"

    result = check_meta_radio_inputs(
        {
            "InjectedRadioactivity": 10,
            "InjectedRadioactivityUnits": "MBq",
            "SpecificRadioactivity": 1,
            "SpecificRadioactivityUnits": "MBq/ug",
        }
    )
    assert result["InjectedMass"] == pytest.approx(10)
    assert result["InjectedMassUnits"] == "ug"


def test_injected_amount_units_use_molar_activity_relations():
    result = check_meta_radio_inputs(
        {
            "InjectedRadioactivity": 100,
            "InjectedRadioactivityUnits": "MBq",
            "InjectedMass": 2,
            "InjectedMassUnits": "nmol",
        }
    )
    assert result["MolarActivity"] == pytest.approx(50)
    assert result["MolarActivityUnits"] == "GBq/umol"
    assert "SpecificRadioactivity" not in result

    result = check_meta_radio_inputs(
        {
            "InjectedRadioactivity": 100,
            "InjectedRadioactivityUnits": "MBq",
            "InjectedMassUnits": "nmol",
            "MolarActivity": 50,
            "MolarActivityUnits": "GBq/umol",
        }
    )
    assert result["InjectedMass"] == pytest.approx(2)
    assert result["InjectedMassUnits"] == "nmol"

    result = check_meta_radio_inputs(
        {
            "InjectedMass": 2,
            "InjectedMassUnits": "nmol",
            "MolarActivity": 50,
            "MolarActivityUnits": "GBq/umol",
        }
    )
    assert result["InjectedRadioactivity"] == pytest.approx(100)
    assert result["InjectedRadioactivityUnits"] == "MBq"


@pytest.mark.parametrize("molar", [None, 30])
def test_issue_400_accepts_legacy_molecular_weight(molar):
    inputs = {
        "MolecularWeight": 300,
        "MolecularWeightUnits": "g/mol",
        "SpecificRadioactivity": 100,
        "SpecificRadioactivityUnits": "MBq/ug",
    }
    if molar is not None:
        inputs["MolarActivity"] = molar
    result = check_meta_radio_inputs(inputs)
    assert result["TracerMolecularWeight"] == 300
    assert result["TracerMolecularWeightUnits"] == "g/mol"
    assert "MolecularWeight" not in result
    assert "MolecularWeightUnits" not in result
    assert result["MolarActivity"] == pytest.approx(30)
    assert result["MolarActivityUnits"] == "GBq/umol"


def test_standard_molecular_weight_takes_precedence(caplog):
    result = check_meta_radio_inputs(
        {
            "TracerMolecularWeight": 300,
            "TracerMolecularWeightUnits": "g/mol",
            "MolecularWeight": 600,
            "MolecularWeightUnits": "kg/mol",
            "SpecificRadioactivity": 100,
            "SpecificRadioactivityUnits": "MBq/ug",
        }
    )

    assert result["TracerMolecularWeight"] == 300
    assert result["TracerMolecularWeightUnits"] == "g/mol"
    assert result["MolarActivity"] == pytest.approx(30)
    assert "using TracerMolecularWeight" in caplog.text
    assert "using TracerMolecularWeightUnits or its default" in caplog.text


def test_standard_molecular_weight_does_not_inherit_legacy_units(caplog):
    result = check_meta_radio_inputs(
        {
            "TracerMolecularWeight": 300,
            "MolecularWeight": 0.3,
            "MolecularWeightUnits": "kg/mol",
            "SpecificRadioactivity": 100,
            "SpecificRadioactivityUnits": "MBq/ug",
        }
    )

    assert result["TracerMolecularWeight"] == 300
    assert result["TracerMolecularWeightUnits"] == "g/mol"
    assert result["MolarActivity"] == pytest.approx(30)
    assert "using TracerMolecularWeight" in caplog.text
    assert "using TracerMolecularWeightUnits or its default" in caplog.text


def test_conflicting_invalid_molecular_weight_aliases_do_not_crash(caplog):
    standard = np.array([1, 2])
    result = check_meta_radio_inputs(
        {
            "TracerMolecularWeight": standard,
            "MolecularWeight": np.array([3, 4]),
        }
    )

    assert np.array_equal(result["TracerMolecularWeight"], standard)
    assert "using TracerMolecularWeight" in caplog.text


@pytest.mark.parametrize("placeholder", ["", "  ", None, [], np.array([]), "none"])
def test_empty_standard_fields_fall_back_to_legacy_molecular_weight(placeholder):
    result = check_meta_radio_inputs(
        {
            "TracerMolecularWeight": placeholder,
            "TracerMolecularWeightUnits": placeholder,
            "MolecularWeight": 0.3,
            "MolecularWeightUnits": "kg/mol",
            "SpecificRadioactivity": 50,
            "SpecificRadioactivityUnits": "MBq/ug",
        }
    )

    assert result["TracerMolecularWeight"] == 0.3
    assert result["TracerMolecularWeightUnits"] == "kg/mol"
    assert result["MolarActivity"] == pytest.approx(15)


def test_explicit_standard_na_takes_precedence_over_legacy_molecular_weight():
    result = check_meta_radio_inputs(
        {
            "TracerMolecularWeight": "n/a",
            "TracerMolecularWeightUnits": "n/a",
            "MolecularWeight": 0.3,
            "MolecularWeightUnits": "kg/mol",
        }
    )

    assert result["TracerMolecularWeight"] == "n/a"
    assert result["TracerMolecularWeightUnits"] == "n/a"


def test_non_molecular_empty_container_remains_an_explicit_input():
    result = check_meta_radio_inputs({"InjectedRadioactivity": [], "InjectedMass": 2})

    assert result["InjectedRadioactivity"] == []
    assert result["SpecificRadioactivity"] == "n/a"


def test_legacy_molecular_weight_units_are_preserved_without_a_value():
    result = check_meta_radio_inputs({"MolecularWeightUnits": "kg/mol"})

    assert result == {"TracerMolecularWeightUnits": "kg/mol"}


def test_inferred_molecular_weight_uses_standard_field_names():
    result = check_meta_radio_inputs(
        {
            "MolarActivity": 15,
            "SpecificRadioactivity": 50,
            "SpecificRadioactivityUnits": "MBq/ug",
        }
    )

    assert result["TracerMolecularWeight"] == pytest.approx(300)
    assert result["TracerMolecularWeightUnits"] == "g/mol"
    assert "MolecularWeight" not in result
    assert "MolecularWeightUnits" not in result


def test_sidecar_template_uses_standard_molecular_weight_units_field():
    assert "TracerMolecularWeightUnits" in sidecar_template_full
    assert "TracerMolecularUnits" not in sidecar_template_full


def test_preserves_all_inputs_and_units_without_warning(caplog):
    inputs = dict(
        REFERENCE, SpecificRadioactivity=50, SpecificRadioactivityUnits="MBq/ug"
    )
    original = deepcopy(inputs)
    result = check_meta_radio_inputs(inputs)
    for key, value in inputs.items():
        assert result[key] == value
    assert inputs == original
    assert not caplog.records


def test_molar_conversion_and_requested_units():
    inputs = {"MolarActivity": 30, "TracerMolecularWeight": 300}
    result = check_meta_radio_inputs(inputs)
    assert result["SpecificRadioactivity"] == pytest.approx(1e14)
    assert result["SpecificRadioactivityUnits"] == "Bq/g"
    inputs["SpecificRadioactivityUnits"] = "MBq/ug"
    result = check_meta_radio_inputs(inputs)
    assert result["SpecificRadioactivity"] == pytest.approx(100)


def test_other_units():
    result = check_meta_radio_inputs(
        {
            "InjectedRadioactivity": 1e8,
            "InjectedRadioactivityUnits": "Bq",
            "InjectedMass": 0.002,
            "InjectedMassUnits": "mg",
            "SpecificRadioactivityUnits": "MBq/ug",
        }
    )
    assert result["SpecificRadioactivity"] == pytest.approx(50)
    assert result["InjectedMass"] == 0.002
    assert result["InjectedMassUnits"] == "mg"
    result = check_meta_radio_inputs(
        {
            "MolarActivity": 15e6,
            "MolarActivityUnits": "MBq/mol",
            "TracerMolecularWeight": 0.3,
            "TracerMolecularWeightUnits": "kg/mol",
        }
    )
    assert result["SpecificRadioactivity"] == pytest.approx(5e10)
    result = check_meta_radio_inputs(
        {
            "InjectedRadioactivity": 1,
            "InjectedRadioactivityUnits": "mCi",
            "InjectedMass": 1,
        }
    )
    assert result["SpecificRadioactivity"] == pytest.approx(3.7e13)


def test_consistency_tolerance_and_warning(caplog):
    check_meta_radio_inputs(
        {
            "InjectedRadioactivity": 44.4,
            "InjectedMass": 6240,
            "SpecificRadioactivity": 7.1154e9,
        }
    )
    assert not caplog.records
    result = check_meta_radio_inputs(dict(REFERENCE, SpecificRadioactivity=8e13))
    assert result["SpecificRadioactivity"] == 8e13
    assert "does not match" in caplog.text


@pytest.mark.parametrize(
    "value", ["n/a", float("nan"), float("inf"), -1, True, [1, 2], complex(1, 2)]
)
def test_invalid_values_do_not_overwrite_measurements(value):
    result = check_meta_radio_inputs(
        {"InjectedRadioactivity": value, "InjectedMass": 2}
    )
    assert result["InjectedMass"] == 2
    assert result["InjectedMassUnits"] == "ug"
    assert result["SpecificRadioactivity"] == "n/a"


def test_zero_numerator_and_denominator(caplog):
    result = check_meta_radio_inputs({"InjectedRadioactivity": 0, "InjectedMass": 2})
    assert result["SpecificRadioactivity"] == 0
    result = check_meta_radio_inputs({"InjectedRadioactivity": 100, "InjectedMass": 0})
    assert result["SpecificRadioactivity"] == "n/a"
    assert "zero InjectedMass" in caplog.text
    assert result["InjectedMass"] == 0


def test_numeric_strings_and_numpy_scalars():
    result = check_meta_radio_inputs(
        {"InjectedRadioactivity": "100", "InjectedMass": "2"}
    )
    assert result["SpecificRadioactivity"] == pytest.approx(5e13)
    result = check_meta_radio_inputs(
        {"InjectedRadioactivity": np.float64(100), "InjectedMass": np.int64(2)}
    )
    assert result["SpecificRadioactivity"] == pytest.approx(5e13)


@pytest.mark.parametrize("unit", ["Bq/mol", "Bq/mL", "not-a-unit", "n/a"])
def test_incompatible_units_preserved_and_excluded(unit, caplog):
    result = check_meta_radio_inputs(
        {
            "SpecificRadioactivity": 50,
            "SpecificRadioactivityUnits": unit,
            "InjectedRadioactivity": 100,
        }
    )
    assert result["SpecificRadioactivity"] == 50
    assert result["SpecificRadioactivityUnits"] == unit
    assert result["InjectedMass"] == "n/a"
    assert "Unsupported or incompatible" in caplog.text


@pytest.mark.parametrize("missing", [None, ""])
def test_missing_values(missing):
    result = check_meta_radio_inputs(
        {"InjectedRadioactivity": missing, "InjectedMass": 2}
    )
    assert result == {"InjectedMass": 2, "InjectedMassUnits": "ug"}
    assert check_meta_radio_inputs({}) == {}


def test_independent_estimates_keep_first_and_warn(caplog):
    result = check_meta_radio_inputs(
        {
            "InjectedRadioactivity": 100,
            "InjectedMass": 2,
            "MolarActivity": 30,
            "TracerMolecularWeight": 300,
        }
    )
    assert result["SpecificRadioactivity"] == pytest.approx(5e13)
    assert "does not match" in caplog.text


def test_valid_estimate_replaces_failed_estimate():
    result = check_meta_radio_inputs(
        {
            "InjectedRadioactivity": "n/a",
            "InjectedMass": 2,
            "MolarActivity": 15,
            "TracerMolecularWeight": 300,
        }
    )
    assert result["SpecificRadioactivity"] == pytest.approx(5e13)


def test_round_trip():
    specific = check_meta_radio_inputs(
        {
            "InjectedRadioactivity": 100,
            "InjectedMass": 2,
            "SpecificRadioactivityUnits": "MBq/ug",
        }
    )
    mass = check_meta_radio_inputs(
        {
            "InjectedRadioactivity": 100,
            "SpecificRadioactivity": specific["SpecificRadioactivity"],
            "SpecificRadioactivityUnits": specific["SpecificRadioactivityUnits"],
        }
    )
    assert mass["InjectedMass"] == pytest.approx(2)


def test_update_json_cli_writes_consistent_values_and_units(tmp_path, monkeypatch):
    import json
    from pypet2bids.update_json_pet_file import update_json_cli

    path = tmp_path / "sub-01_pet.json"
    path.write_text(
        json.dumps(
            {
                "InjectedRadioactivity": 100,
                "InjectedRadioactivityUnits": "MBq",
                "InjectedMass": 2,
                "InjectedMassUnits": "ug",
                "SpecificRadioactivityUnits": "MBq/ug",
                "MolecularWeight": 300,
                "MolecularWeightUnits": "g/mol",
            }
        )
    )
    monkeypatch.setattr("sys.argv", ["updatepetjson", "-j", str(path)])
    update_json_cli()
    result = json.loads(path.read_text())
    assert result["SpecificRadioactivity"] == pytest.approx(50)
    assert result["SpecificRadioactivityUnits"] == "MBq/ug"
    assert result["TracerMolecularWeight"] == 300
    assert result["TracerMolecularWeightUnits"] == "g/mol"
    assert "MolecularWeight" not in result
    assert "MolecularWeightUnits" not in result


def test_update_json_cli_does_not_restore_blank_legacy_alias(tmp_path, monkeypatch):
    import json
    from pypet2bids.update_json_pet_file import update_json_cli

    path = tmp_path / "sub-01_pet.json"
    path.write_text("{}")
    monkeypatch.setattr(
        "pypet2bids.update_json_pet_file.get_metadata_from_spreadsheet",
        lambda *args, **kwargs: {
            "nifti_json": {"MolecularWeight": ""},
        },
    )
    monkeypatch.setattr(
        "pypet2bids.update_json_pet_file.check_json", lambda *args, **kwargs: {}
    )
    monkeypatch.setattr(
        "sys.argv",
        ["updatepetjson", "-j", str(path), "-m", "metadata.xlsx"],
    )

    update_json_cli()

    result = json.loads(path.read_text())
    assert "MolecularWeight" not in result
    assert "MolecularWeightUnits" not in result


def test_dicom_update_cli_migrates_legacy_molecular_weight(tmp_path, monkeypatch):
    import json
    from pypet2bids.update_json_pet_file import update_json_with_dicom_value_cli

    path = tmp_path / "sub-01_pet.json"
    path.write_text("{}")
    monkeypatch.setattr(
        "sys.argv",
        [
            "updatepetjsonfromdicom",
            "-j",
            str(path),
            "-d",
            "representative.dcm",
            "-k",
            "MolecularWeight=0.3",
            "MolecularWeightUnits=kg/mol",
            "SpecificRadioactivity=50",
            "SpecificRadioactivityUnits=MBq/ug",
        ],
    )
    monkeypatch.setattr(
        "pypet2bids.update_json_pet_file.pydicom.dcmread",
        lambda *args, **kwargs: object(),
    )
    monkeypatch.setattr(
        "pypet2bids.update_json_pet_file.check_json",
        lambda *args, **kwargs: {},
    )
    monkeypatch.setattr(
        "pypet2bids.update_json_pet_file.update_json_with_dicom_value",
        lambda *args, **kwargs: None,
    )

    update_json_with_dicom_value_cli()

    result = json.loads(path.read_text())
    assert result["TracerMolecularWeight"] == pytest.approx(0.3)
    assert result["TracerMolecularWeightUnits"] == "kg/mol"
    assert result["MolarActivity"] == pytest.approx(15)
    assert "MolecularWeight" not in result
    assert "MolecularWeightUnits" not in result

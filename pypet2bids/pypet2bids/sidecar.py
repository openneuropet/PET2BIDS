"""
This is a lazy way to avoid opening a json, simply import this file to collect your BIDS sidecar templates instead. This
is not a function or a true module. This is just two python dictionaries with keys and empty value pairs.

**Parameters**

* sidecar_template_full: a dict containing every PET BIDS field
* sidecar_template_short: a dict containing only required PET BIDS fields

**Returns**     sidecar_template_full, sidecar_template_short

*Anthony Galassi*
*Copyright OpenNeuroPET team*

"""


sidecar_template_full = {
    "Manufacturer": "",
    "ManufacturersModelName": "",
    "Units": "",
    "InstitutionName": "",
    "InstitutionAddress": "",
    "InstitutionalDepartmentName": "",
    "BodyPart": "",
    "TracerName": "",
    "TracerRadionuclide": "",
    "InjectedRadioactivity": "",
    "InjectedRadioactivityUnits": "",
    "InjectedMass": "",
    "InjectedMassUnits": "",
    "SpecificRadioactivity": "",
    "SpecificRadioactivityUnits": "",
    "ModeOfAdministration": "",
    "TracerRadLex": "",
    "TracerSNOMED": "",
    "TracerMolecularWeight": "",
    "TracerMolecularUnits": "",
    "InjectedMassPerWeight": "",
    "InjectedMassPerWeightUnits": "",
    "SpecificRadioactivityMeasTime": "",
    "MolarActivity": "",
    "MolarActivityUnits": "",
    "MolarActivityMeasTime": "",
    "InfusionRadioActivity": "",
    "InfusionStart": "",
    "InfusionSpeed": "",
    "InfusionSpeedUnits": "",
    "InjectedVolume": "",
    "Purity": "",
    "PharamceuticalName": "",
    "PharmaceuticalDoseAmount": [],
    "PharmaceuticalDoseUnits": "",
    "PharmaceuticalDoseRegimen": "",
    "PharmaceuticalDoseTime": [],
    "Anaesthesia": "",
    "TimeZero": "",
    "ScanStart": "",
    "InjectionStart": "",
    "FrameTimesStart": [],
    "FrameDuration": [],
    "ScanDate": "",
    "InjectionEnd": "",
    "AcquisitionMode": "",
    "ImageDecayCorrected": "",
    "ImageDecayCorrectionTime": "",
    "ReconMethodName": "",
    "ReconMethodParameterLabels": [],
    "ReconMethodParameterUnits": [],
    "ReconMethodParameterValues": [],
    "ReconFilterType": [],
    "ReconFilterSize": [],
    "AttenuationCorrection": "",
    "ReconMethodImplementationVersion": "",
    "AttenuationCorrectionMethodReference": "",
    "ScaleFactor": [],
    "ScatterFraction": [],
    "DecayCorrectionFactor": [],
    "PromptRate": [],
    "RandomRate": [],
    "SinglesRate": []
}

sidecar_template_short = {
    "Manufacturer": "",
    "ManufacturersModelName": "",
    "Units": "",
    "TracerName": "",
    "TracerRadionuclide": "",
    "InjectedRadioactivity": "",
    "InjectedRadioactivityUnits": "",
    "InjectedMass": "",
    "InjectedMassUnits": "",
    "SpecificRadioactivity": "",
    "SpecificRadioactivityUnits": "",
    "ModeOfAdministration": "",
    "TimeZero": "",
    "ScanStart": "",
    "InjectionStart": "",
    "FrameTimesStart": [],
    "FrameDuration": [],
    "AcquisitionMode": "",
    "ImageDecayCorrected": "",
    "ImageDecayCorrectionTime": "",
    "ReconMethodName": "",
    "ReconMethodParameterLabels": [],
    "ReconMethodParameterUnits": [],
    "ReconMethodParameterValues": [],
    "ReconFilterType": [],
    "ReconFilterSize": [],
    "AttenuationCorrection": ""
}

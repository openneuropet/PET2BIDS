"""
This is a lazy way to avoid opening a json, simply import this file to collect your BIDS sidecar templates instead. This
is not a function or a `true` module. It's just two python dictionaries with keys and empty value pairs.

:param sidecar_template_full: a dictionary containing every field specified in the BIDS standard for PET imaging data
:param sidecar_template_short: a dictionary containing only the required fields in the BIDS standard for PET
    imaging data
:return: sidecar_template_full, sidecar_template_short

|*Anthony Galassi*
|*Copyright OpenNeuroPET team*
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

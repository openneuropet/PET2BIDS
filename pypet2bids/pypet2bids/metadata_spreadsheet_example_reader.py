import pandas
import warnings


def flatten_series(series):
    """
    This function retrieves either a list or a single value from a pandas series object thus converting a complex
    data type to a simple datatype or list of simple types. If the length of the series is one or less this returns that
    single value, else this object returns all values within the series that are not Null/nan in the form of a list
    :param series: input series of type pandas.Series object, typically extracted as a column/row from a
    pandas.Dataframe object
    :return: a simplified single value or list of values
    """
    simplified_series_object = series.dropna().to_list()
    if len(simplified_series_object) > 1:
        pass
    elif len(simplified_series_object) == 1:
        simplified_series_object = simplified_series_object[0]
    else:
        raise(f"Invalid Series: {series}")
    return simplified_series_object


def translate_metadata(metadata_dataframe, image_path=NotImplemented):
    """
    This method exists as an example/template for an individual to customize and use on their own PET metadata contained
    within a spreadsheet. It is important to note that everything but the method name `translate_metadata` and the
    dictionary structure it returns can be modified to extract, transform, and load data from a user's spreadsheet.
    That is to say keep this method named `translate_metadata` and return a dictionary of the form:
    {
        'nifti_json: {},
        'blood_json: {},
        'blood_tsv: <pandas.DataFrame> or a <str>,
    }

    :param metadata_dataframe:
    :param image_path:
    :return:
    """
    nifti_json = {
        'Manufacturer': '',
        'ManufacturersModelName': '',
        'Units': '',
        'TracerName': '',
        'TracerRadionuclide': '',
        'InjectedRadioactivity': 0,
        'InjectedRadioactivityUnits': '',
        'InjectedMass': 0,
        'InjectedMassUnits': '',
        'SpecificRadioactivity': 0,
        'SpecificRadioactivityUnits': '',
        'ModeOfAdministration': '',
        'TimeZero': 0,
        'ScanStart': 0,
        'InjectionStart': 0,
        'FrameTimesStart': [],
        'FrameDuration': [],
        'AcquisitionMode': '',
        'ImageDecayCorrected': '',
        'ImageDecayCorrectionTime': 0,
        'ReconMethodName': '',
        'ReconMethodParameterLabels': [],
        'ReconMethodParameterUnits': [],
        'ReconMethodParameterValues': [],
        'ReconFilterType': '',
        'ReconFilterSize': 0,
        'AttenuationCorrection': '',
        'InstitutionName': '',
        'InstitutionalDepartmentName': ''
    }

    for key in nifti_json.keys():
        try:
            nifti_json[key] = flatten_series(metadata_dataframe[key])
        except KeyError:
            warnings.warn(f"{key} not found in metadata extracted from spreadsheet")

    blood_json = {
        "PlasmaAvail": True,
        "WholeBloodAvail": True,
        "MetaboliteAvail": False,
        "DispersionCorrected": False,
        "time": {
            "Description": "Time in relation to time zero defined in _pet.json",
            "Units": "s"
        },
        "plasma_radioactivity": {
            "Description": "Radioactivity in plasma samples, measured by eye balling it.",
            "Units": "kBq/mL"
        },
        "whole_blood_radioactivity": {
            "Description": "Radioactivity in whole blood samples, measured by divining rod.",
            "Units": "kBq/mL"
        }
    }

    blood_tsv = {
        "time": [],
        "plasma_radioactivity": [],
        "whole_blood_radioactivity": []
    }

    for key in blood_tsv.keys():
        try:
            blood_tsv[key] = flatten_series(metadata_dataframe[key])
        except KeyError:
            warnings.warn(f"{key} not found in metadata extracted from spreadsheet")

    # now transform the key value pairs in blood_tsv into a pandas dataframe object.
    blood_tsv = pandas.DataFrame.from_dict(blood_tsv)

    return {'nifti_json': nifti_json, 'blood_json': blood_json, 'blood_tsv': blood_tsv}

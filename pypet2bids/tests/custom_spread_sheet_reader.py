import re


def translate_metadata(metadata_dataframe, dicom_header_data):
    nifti_json = {

        'InjectedMass': metadata_dataframe.iloc[35, 10] * metadata_dataframe.iloc[38, 6],
        # nmol/kg * weight
        'InjectedMassUnits': 'nmol',
        'MolarActivity': metadata_dataframe.iloc[0, 35] * 0.000037,  # uCi to GBq
        'MolarActivityUnits': 'GBq/nmol',
        'SpecificRadioactivity': 'n/a',
        'SpecificRadioactivityUnits': 'n/a',
        'ModeOfAdministration': 'bolus',
        'TimeZero': '10:15:14',
        'ScanStart': 61,
        'InjectionStart': 0,
        'AcquisitionMode': 'list mode',
        'ImageDecayCorrected': True,
        'ImageDecayCorrectionTime': -61,
        'ReconMethodParameterLabels': ['iterations',
                                       'subsets',
                                       'lower energy threshold',
                                       'upper energy threshold'],
        'ReconMethodParameterUnits': ['none',
                                      'none',
                                      'keV',
                                      'keV'],
        'ReconMethodParameterValues': [
            3,
            21,
            float(min(re.findall('\d+\.\d+', dicom_header_data.EnergyWindowRangeSequence).lower())),
            float(max(re.findall('\d+\.\d+', dicom_header_data.EnergyWindowRangeSequence).lower())),
        ],
        'ReconFilterSize': 0,
    }

    blood_json = {
    }

    blood_tsv = {
        'time': metadata_dataframe.iloc[2:7, 6] * 60,  # convert minutes to seconds,
        'PlasmaRadioactivity': metadata_dataframe.iloc[2:7, 7] / 60,
        'WholeBloodRadioactivity': metadata_dataframe.iloc[2:7, 9] / 60,
        'MetaboliteParentFraction': metadata_dataframe.iloc[2:7, 8] / 60
    }

    return {'nifti_json': nifti_json, 'blood_json': blood_json, 'blood_tsv': blood_tsv}
# Pypet2bids

This library contains several tools and many methods to aid in the conversion of PET imaging and blood data into 
[BIDS]() formatted data. For more detailed documentation refer to the pages at our 
[readthedocs.io site](https://pet2bids.readthedocs.io/en/latest/).

# Python DICOM PET converter

This converter is a simple wrapper around Chris Rorden's [Dcm2niix](https://github.com/rordenlab/dcm2niix) that provides
additional functionality to convert and deliver more BIDS PET friendly output (supplemented sidecar jsons, tsvs, etc)
following image conversion from dicom to nifti.

# Python ECAT PET converter

This converter takes an ecat file, reads it in and then with the help of nibabel spits out a Nifti w/ a BIDS compliant
json replete with any relevant fields parsed from the ecat headers. Required fields that cannot be filled from data
present in the ecat image are still included in the bids json but as empty string values e.g. `RequiredField: ''`.

## Installation and Nifti Generation/Conversion

### Installation

Use pip to install the library via:
```bash
pip install pypet2bids
```

*Additional Windows setup*
For a windows installation you will have to manually point pypet2bids to the location of dcm2niix via
a configuration file at `$Home\.pet2bidsconfig`

```powershell
# using powershell create a file name .pet2bidsconfig at the users home directory
'DCM2NIIX_PATH="C:\<path to dcm2niix.exe>"' | Out-File $Home\.pet2bidsconfig
```


## A brief note about kwargs

It's desirable for the user to be able to quickly provide additional metadata at the time of conversion to make the output of
the conversion BIDS compliant. PET data is often strewn across multiple files and formats; the `--kwargs` flag allows 
the user to input any metadata that may not be present in a spreadsheet, text, or imaging type of file. We use the 
word `kwargs` is it corresponds directly to the default argument place-holder in Python used for dictionary based 
arguments (key pair sets of values), see 
[kwargs](https://docs.python.org/3/tutorial/controlflow.html#unpacking-argument-lists).

`--kwargs` can be used to *force* (or guide) an image or set of images into BIDS compliance by supplying missing info.
or overwriting errant info recorded or used elsewhere. In the example below the following arguments are supplied to 
`kwargs`:

```bash
# full example below; input is wrapped with \ for readability on screen
dcm2niix4pet $SOURCE_FOLDER/GeneralElectricAdvance-NIMH/long_trans \ 
--destination-path $DESTINATION/sub-GeneralElectricAdvanceNIMH/pet \
--kwargs \
TimeZero="13:39:41" \
Manufacturer="GE MEDICAL SYSTEMS" \
ManufacturersModelName="GE Advance" \
InstitutionName="NIH Clinical Center, USA" \
BodyPart="Phantom" \
Units="Bq/mL" \
TracerName="FDG" \
TracerRadionuclide="F18" \
InjectedRadioactivity=75.8500 \
InjectionStart=0 \
SpecificRadioactivity=418713.8 \
ModeOfAdministration="infusion" \
FrameTimesStart="[0]" \
ReconMethodParameterValues="[1, 1]" \
ImageDecayCorrected='false' \
AttenuationCorrection='n/a' \
AcquisitionMode='list mode' \
ImageDecayCorrectionTime="0" \
ScatterCorrectionMethod="Gaussian Fit" \
ScanStart="0"
```

And when calling directly from python:

```python
kwargs = {
    "TimeZero": "13:39:41",
    "Manufacturer": "GE MEDICAL SYSTEMS",
    "ManufacturersModelName": "GE Advance",
    "InstitutionName": "NIH Clinical Center, USA",
    "BodyPart": "Phantom",
    "Units": "Bq/mL",
    "TracerName": "FDG", 
    "TracerRadionuclide": "F18",
    "InjectedRadioactivity": 75.8500,
    "InjectionStart": 0,
    "SpecificRadioactivity": 418713.8,
    "ModeOfAdministration": "infusion",
    "FrameTimesStart": [0],
    "ReconMethodParameterValues":[1, 1],
    "ImageDecayCorrected": False,
    "AttenuationCorrection": "n/a",
    "AcquisitionMode": "list mode",
    "ImageDecayCorrectionTime": 0,
    "ScatterCorrectionMethod": "Gaussian Fit",
    "ScanStart": 0
    }

dcm2niix4pet = Dcm2niix4PET(
    image_folder='SOURCE_FOLDER/GeneralElectricAdvance-NIMH/long_trans', 
    destination_path='DESTINATION/sub-GeneralElectricAdvanceNIMH/pet',
    additional_arguments=kwargs)

```

Arguments supplied to kwargs should correspond directly to the following datatypes (which as chance would have it are 
all acceptable BIDS types, json serializable too!):
- [int](https://docs.python.org/3/library/functions.html?highlight=int#int)
- [float](https://docs.python.org/3/library/functions.html?highlight=float#float)
- [list](https://docs.python.org/3/library/stdtypes.html#list)
- [string](https://docs.python.org/3/library/stdtypes.html#str)

Any argument supplied that falls outside of scope of the above types will be parsed as a string if possible or it will
return an error if the syntax of the argument pair is expressed incorrectly e.g. `KeyPair = 3` or `KeyPairList=[1,`



### Converting Dicoms to Nifti

```bash
dcm2niix4pet /path/to/folder/with/dicoms
```

### Converting ECAT to Nifti

```bash
# for ecat to Nii use the cli to create a nifti from the ecat via:
ecatpet2bids /path/to/ecat/image.v --convert
```

If you wish to generate the converted image(s) and json somewhere other than the current directory of your ecat image(s)
include the `--nifti` argument and specify a filename w/ a full path included e.g.:

```bash
ecatpet2bids /path/to/ecat/image.v --convert --nifti /path/to/new/nifti
```

### Additional Usage

This converter was written originally as a method to extract ecat header/subheader data into stdout key: value format
and/or json.

For more information about those arguments see `python main.py --help` or read below:

```bash
ecatpet2bids --help
usage: ecatpet2bids [-h] [--affine] [--convert] [--dump] [--json] [--nifti file_name]
       [--subheader] [--sidecar] [--kwargs [KWARGS ...]]
       [--scannerparams [SCANNERPARAMS ...]] ecat_file

positional arguments:
  ecat_file             Ecat image to collect info from.

optional arguments:
  -h, --help            show this help message and exit
  --affine, -a          Show affine matrix
  --convert, -c         If supplied will attempt conversion.
  --dump, -d            Dump information in Header
  --json, -j            Output header and subheader info as JSON to stdout,
                        overrides all other options
  --nifti file_name, -n file_name
                        Name of nifti output file
  --subheader, -s       Display subheaders
  --sidecar             Output a bids formatted sidecar for pairing witha nifti.
  --kwargs [KWARGS ...], -k [KWARGS ...]
                        Include additional values int the nifti sidecar json or
                        override values extracted from the supplied nifti. e.g.
                        including `--kwargs TimeZero='12:12:12'` would override
                        the calculated TimeZero. Any number of additional
                        arguments can be supplied after --kwargs e.g. `--kwargs
                        BidsVariable1=1 BidsVariable2=2` etc etc.
  --scannerparams [SCANNERPARAMS ...]
                        Loads saved scanner params from a configuration file
                        following --scanner-params/-s if this option is used
                        without an argument this cli will look for any scanner
                        parameters file in the directory with the name
                        *parameters.txt from which this cli is called.
```

### Configuring a default scanner parameters file

When converting a files from ECAT to Nifti originating from the same scanner or institution it
may be desirable to include these same values in your BIDS sidecar.json across all files/scans/subjects.

This can be done by populating a txt or .env file with the common BIDS scanner parameters and
specifying to the command line to use this file with `--scannerparams`.

Note: Values included in the scanneparameter file will be overridden with any corresponding
values supplied via the `--kwargs` argument. e.g. `--kwargs Manufacturer=GE` would override

```bash
# scannerparameters.txt file
Manufacturer=Siemens
```

### File Formatting

Scannerparam files are configured as simply as environment variables, that is to say:
```bash
# Number signs can be used for comments
# String variables such as institution name are entered after the equals sign
InstitutionName='Your Prestigous Institution'
# a list of strings would be entered as a bracketed list of comma separated quoted strings
ReconMethodParameterUnits=['None','None', 'keV', 'keV']
# A list of real numbers
ReconMethodParameterValues=[0.0, 1.2, 3.0, 42.1]
# Similarly, a list of integers
ValidBidsTerm=[1,2,3,4]
# Single numerical values are entered directly without quotes
BidsFloat=3.2
BidsInt=7

```

### Usage

- Pointing directly at a scannerparams file `--scannerparams /path/to/scannerparams.txt`
- **NOTE**: `--scannerparams` usage by itself with no file path requires a parameter file exist in the directory
that the CLI is being called from. `$ecat_dir: ecatpet2bids ecatfile.v --scannerparms` assumes that `ls ecat_dir` will
reveal a file containing `*parameters.txt`

## Testing

To run the tests in `tests/` first copy the `template.env` file to `.env` with in this folder and then populate it with
paths to read ecats from as well as paths to write test niftis to.

```bash
cp template.env .env
cat .env
TEST_ECAT_PATH=
OUTPUT_NIFTI_PATH=
READ_ECAT_SAVE_AS_MATLAB=
NIBABEL_READ_ECAT_SAVE_AS_MATLAB=
```

And after you've filled in you .env file it should resemble the following:

```bash
cat .env
TEST_ECAT_PATH=/Users/user/ecat_file.v
OUTPUT_NIFTI_PATH=/Users/user/test_nifti.nii
READ_ECAT_SAVE_AS_MATLAB=/Users/user/python_ecat_read_object.mat
NIBABEL_READ_ECAT_SAVE_AS_MATLAB=/Users/user/nibabel_ecat_read_object.mat
```

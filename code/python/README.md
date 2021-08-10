# Python ECAT converter

This converter takes an ecat file, reads it in and then with the help of nibabel spits out a Nifti w/ a BIDS compliant 
json  replete with any relevant fields parsed from the ecat headers. Required fields that cannot be filled from data 
present in the ecat image are still included in the bids json but as empty string values e.g. `RequiredField: ''`.

## Installation and Nifti Generation/Conversion

```bash
# install the requirements with pip
pip3 install -r requirements.txt
# then use the cli to create a nifti from the ecat via:
python3 main.py /path/to/ecat/image.v --convert
```

If you wish to generate the converted image(s) and json somewhere other than the current directory of your ecat image(s)
include the `--nifti` argument and specify a filename w/ a full path included e.g.:

```bash
python3 main.py /path/to/ecat/image.v --convert --nifti /path/to/new/nifti
```

## Additional Usage

This converter was written originally as a method to extract ecat header/subheader data into stdout key: value format 
and/or json.

For more information about those arguments see `python main.py --help` or read below:

```bash
(python) mycomputer:python me$ python main.py --help
usage: main.py [-h] [--affine] [--convert] [--dump] [--json]
              [--nifti file_name] [--subheader] [--sidecar]
              ecat_file

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
  --sidecar             Output a bids formatted sidecar for pairing with a
                        nifti.
```

## Testing

To run the tests in `tests/` first copy the `template.env` file to `.env` with in this folder and then populate it 
with paths to read ecats from as well as paths to write test niftis to.

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

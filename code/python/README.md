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
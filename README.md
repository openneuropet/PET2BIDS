# PET2BIDS is a code library to convert source Brain PET data to BIDS 

[![python](https://github.com/openneuropet/PET2BIDS/actions/workflows/python.yaml/badge.svg)](https://github.com/openneuropet/PET2BIDS/actions/workflows/python.yaml)
[![Matlab PET2BIDS Tests](https://github.com/openneuropet/PET2BIDS/actions/workflows/matlab.yaml/badge.svg)](https://github.com/openneuropet/PET2BIDS/actions/workflows/matlab.yaml) 
[![Documentation Status](https://readthedocs.org/projects/pet2bids/badge/?version=latest)](https://pet2bids.readthedocs.io/en/latest/?badge=latest)
[![phantoms](https://github.com/openneuropet/PET2BIDS/actions/workflows/phantoms.yaml/badge.svg?event=push)](https://github.com/openneuropet/PET2BIDS/actions/workflows/phantoms.yaml)

This repository is hosting tools to curate PET brain data using the [Brain Imaging Data Structure Specification](https://bids-specification.readthedocs.io/en/stable/04-modality-specific-files/09-positron-emission-tomography.html). The work to create these tools is funded by [Novo Nordisk Foundation](https://novonordiskfonden.dk/en/) (NNF20OC0063277) and the [BRAIN initiative](https://braininitiative.nih.gov/) (MH002977-01).

For DICOM image conversion, we rely on [dcm2niix](https://www.nitrc.org/plugins/mwiki/index.php/dcm2nii:MainPage), 
collaborating with Prof. Chris Rorden without whom we could not convert your data! For more information on dcm2niix 
and nifti please see [The first step for neuroimaging data analysis: DICOM to NIfTI conversion](https://www.ncbi.nlm.nih.gov/pubmed/26945974) paper.


# Documentation

For **more detailed** (and most likely helpful) documentation visit the Read the Docs site for this project at:

[https://pet2bids.readthedocs.io](https://pet2bids.readthedocs.io/en/latest/index.html#)

## Installation

Simply download the repository - follow the specific Matlab or Python explanations. Matlab and Python codes provide the same functionalities.

### matlab

[![asciicast](https://asciinema.org/a/RPxiHW6afISPmWYFBOGKWNem1.svg)](https://asciinema.org/a/RPxiHW6afISPmWYFBOGKWNem1)

1) remember to set the path to the PET2BIDS/matlab folder, you will find the source code to use here.
2) if converting DICOM files, make sure you have dcm2niix (for windows users, edit dcm2niix4pet.m to set the right paths to the .exe)
3) start using the code! more info [here](https://github.com/openneuropet/PET2BIDS/tree/main/matlab#readme)

### pypet2bids

Use pip:

[![asciicast](https://asciinema.org/a/TZJg5BglDMFM2fEEX9dSpnJEy.svg)](https://asciinema.org/a/TZJg5BglDMFM2fEEX9dSpnJEy)

For advance users clone this repository and run from the python source under the `PET2BIDS/pypet2bids` folder. If you 
wish to build and install via pip locally we recommend you do so using [poetry](https://python-poetry.org/) build or
using the make commands below.

```bash
cd PET2BIDS
make installpoetry buildpackage installpackage
```

**Note:**
*We recommend using dcm2niix v1.0.20220720 or newer; we rely on metadata included in these later releases. It's best to 
collect releases from the [rorden lab/dcm2niix/releases](https://github.com/rordenlab/dcm2niix/releases) page. We have
observed that package managers such as yum or apt or apt-get often install much older versions of dcm2niix e.g. 
v1.0.2017XXXX, v1.0.2020XXXXX. You may run into invalid-BIDS or errors with this software with older versions.* 


### spreadsheet_conversion (custom and pmod)

This folder contains spreadsheets templates and examples of metadata and matlab and python code to convert them to json files. Often, metadata such as Frame durations, InjectedRadioactivity, etc are stored in spreadsheets and we have made those function to create json files automatically for 1 or many subjects at once to go with the nifti imaging data. Note, we also have conversion for pmod files (also spreadsheets) allowing to export to blood.tsv files.

### metadata

A small collection of json files for our metadata information. 

### user metadata 

No matter the way you prefer inputting metadata (passing all arguments, using txt or env file, using spreadsheets), you are always right! DICOM values will be ignored - BUT they are checked and the code tells you if there is inconsistency between your inputs and what DICOM says.

### ecat_validation

This folder contains code generating Siemens HRRT scanner data using ecat file format and validating the matlab and python conversion tools (i.e. giving the data generated as ecat, do our nifti images reflect acurately the data).

## Citation 

Please [cite us](CITATION.cff) when using PET2BIDS.

## Contribute

Anyone is welcome to contribute ! check here [how you can get involved](contributing.md), the [code of conduct](code_of_conduct.md). Contributors are listed [here](contributors.md)

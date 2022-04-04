# PET to BIDS is a set of BIDS converter for your Brain PET data

[![Python PET2BIDS Tests](https://github.com/openneuropet/PET2BIDS/actions/workflows/setup_and_cli_test_posix.yaml/badge.svg)](https://github.com/openneuropet/PET2BIDS/actions/workflows/setup_and_cli_test_posix.yaml) [![Matlab PET2BIDS Tests](https://github.com/openneuropet/PET2BIDS/actions/workflows/matlab.yaml/badge.svg)](https://github.com/openneuropet/PET2BIDS/actions/workflows/matlab.yaml) [![Documentation Status](https://readthedocs.org/projects/pet2bids/badge/?version=latest)](https://pet2bids.readthedocs.io/en/latest/?badge=latest)

This repository is hosting tools to curate PET brain data using the [Brain Imaging Data Structure Specification](https://bids-specification.readthedocs.io/en/stable/04-modality-specific-files/09-positron-emission-tomography.html). The work to create these tools is funded by [Novo Nordisk fonden](https://novonordiskfonden.dk/en/) (NNF20OC0063277) and the [BRAIN initiative](https://braininitiative.nih.gov/) (MH002977-01).

For DICOM conversion, we rely on [dcm2niix](https://www.nitrc.org/plugins/mwiki/index.php/dcm2nii:MainPage), loosely collaborating with Prof. Chris Rorden without whom we could not convert your data! For more information on dcm2niix and nifti please see [The first step for neuroimaging data analysis: DICOM to NIfTI conversion](https://www.ncbi.nlm.nih.gov/pubmed/26945974) paper.

## Installation

Simply download the repository - follow the specific Matlab or Python explanations. Matlab and Python codes provide the same functionalities.

### matlab

This is where the matlab code lives - simply add the folder your Matlab path to start using the different functions.

### pypet2bids

This is where the python library lives.

### spreadsheet_conversion

This folder contains spreadsheets templates and examples of metedata and matlab and python code to convert tehm to json files.

### metadata

A small collection of json files for our metadata information. 

### ecat_validation

This folder contains exemple of Siemens HRRT scanner data using ecat file format.

## Citation 

Please [cite us](CITATION.cff) when using PET2BIDS

## Contribute

Anyone is welcome to contribute ! check here [how you can get involved](contributing.md), the [code of conduct](code_of_conduct.md). Contributors are listed [here](contributors.md)

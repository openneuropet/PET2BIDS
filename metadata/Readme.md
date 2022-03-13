# metadata

This folder contains metadata informations for PET, some of them being loaded by our Matlab and Python code (ensuring both use the same info).

## [definitions](https://github.com/openneuropet/PET2BIDS/blob/main/metadata/definitions.json)

List of terms, just making sure we agree on what we are talking about.  

## [PET_metadata](https://github.com/openneuropet/PET2BIDS/blob/main/metadata/PET_metadata.json)

Lists the mandatory, recommended and optional keys of the [*_pet.json file](https://bids-specification.readthedocs.io/en/stable/04-modality-specific-files/09-positron-emission-tomography.html#pet-metadata) 
 of the BIDS specification.  

## [dicom2bids_heuristics](https://github.com/openneuropet/PET2BIDS/blob/main/metadata/dicom2bids_heuristics.json)

List of matched keys between dicom tags and json keys, by using this we can:
- check values of the json match the dicom information  
- add missing information to the json  

## [blood_metadata](https://github.com/openneuropet/PET2BIDS/blob/main/metadata/blood_metadata.json)

Lists the mandatory and recommended keys of the [*_blood.json and *blood.tsv files](https://bids-specification.readthedocs.io/en/stable/04-modality-specific-files/09-positron-emission-tomography.html#blood-recording-data)
 of the BIDS specification.  

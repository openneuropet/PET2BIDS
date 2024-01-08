---
title: 'PET2BIDS: a library for converting Positron Emission Tomography data to BIDS'
tags:
  - Matlab
  - Python
  - brain imaging
  - positron emission tomography (PET)
  - brain imaging data structure (BIDS)
authors:
- name: Anthony Galassi
  orcid: 0000-0001-6550-4574
  affiliation: 1
- name: Cyrus Eierud
  orcid: 0000-0002-9942-676X
  affiliation: 2
- name: Martin Norgaard
  orcid: 0000-0003-2131-5688
  affiliation: "3, 4, 5"
- name: Adam G. Thomas
  orcid: 0000-0002-2850-1419
  affiliation: 1
- name: Gabriel Gonzalez-Escamilla
  orcid: 0000-0002-7209-1736
  affiliation: 6
- name: Claus Svarer
  orcid: 0000-0001-7811-1825
  affiliation: 3
- name: Chris Rorden
  orcid: 0000-0002-7554-6142
  affiliation: 7
- name: Granville J. Matheson
  orcid: 0000-0002-5646-4547
  affiliation: "8, 9"
- name: Gitte M. Knudsen
  orcid: 0000-0003-1508-6866
  affiliation: 3
- name: Robert B. Innis
  orcid: 0000-0003-1238-7209
  affiliation: 1 
- name: Melanie Ganz-Benjaminsen
  orcid: 0000-0002-9120-8098
  affiliation: "3, 4"
- name: Cyril Pernet
  orcid: 0000-0003-4010-4632
  affiliation: 3
affiliations:
 - name: National Institutes of Health, Bethesda, MD, USA
   index: 1
 - name: TReNDS Center, Georgia State University, Atlanta, GA, USA
   index: 2
 - name: Neurobiology Research Unit, Rigshospitalet, Copenhagen, Denmark
   index: 3
 - name: Department of Computer Science, University of Copenhagen, Copenhagen, Denmark
   index: 4
 - name: Department of Psychology, Stanford University, CA, USA
   index: 5
 - name: University Medical Center of the Johannes Gutenberg University Mainz, Mainz, Germany
   index: 6
 - name: Department of Psychology, University of South Carolina, Columbia, SC, USA
   index: 7
 - name: Mailman school of Public Health, Columbia University, New York, NY, USA
   index: 8
 - name: Department of Clinical Neuroscience, Karolinska Institutet and Stockholm County Council, Stockholm, Sweden
   index: 9
date: 22 August 2023
bibliography: paper.bib

---

# Summary

The Brain Imaging Data Structure [@gorgolewski_brain_2016] is a standard for organizing and naming neuroimaging data which has quickly become successful and popular in the community with adoption by major brain imaging repositories (e.g. OpenNeuro [@noauthor_openneuro], PublicnEUro [@noauthor_public], CONP [@noauthor_canadian]) and data management tools (e.g. COINS [@landis_coins_2016], XNAT [@marcus_extensible_2007], Loris [@das_loris_2012]). This not only allows data to be shared much more easily, but also enables the development of automated data analysis pipelines, and together improves reproducibility.  

The BIDS extension for Positron Emission Tomography (PET-BIDS) [@norgaard_pet-bids_2022] provides a structured data and metadata nomenclature, including all the necessary information to share and report on PET blood and metabolite [@knudsen_guidelines_2020]. Here we present a new code library, developed in both Matlab and Python, allowing the conversion of PET imaging data (ECAT and DICOM format) and metadata (e.g., time or blood measurements) into the BIDS specification.

# Statement of need

`PET2BIDS` was designed as a library code, allowing conversion of PET data to BIDS using the command line. Thanks to its modular structure, it can be integrated into software (with a graphical user interface) that aim at more general BIDS conversion, and current efforts are underway integrating PET2BIDS with ezBIDS [@noauthor_ezbids] and BIDSCoins [@zwiers_bidscoin_2022].

_File conversion_: The conversion for PET data stored in DICOM format to NIfTI is performed using the dcm2niix4pet (.m and .py) functions which are wrapper functions around dcm2niix [@rorden_dcm2nii; @li_first_2016] that extend the JSON file with details that are not included in the source images but are required for BIDS. Those information are given by the user. The conversion of PET data stored in ECAT format is performed using the newly created ecat2nii (.m .py) functions. The Matlab code relies on the readECAT7.m function from BT Christian (1998) and revised by RF Muzic (2002) to read the data, while writting relies on nii_tool [@Li_2016] while producing the correct JSON sidecar file, and optionally a (non-BIDS compliant) SIF file (Scan Information File - used by different pharmacokinetic modelling software for model weighting). The Python code was developed to mirror the Matlab code, with further testing of data reading (i.e., which parts are read according to the PET data frames) and writing, relying here on Nibabel [@brett_nipynibabel_2023]. 

_PET Metadata_: JSON files created from reading PET scanner data are always missing some of the
radiotracer and pharmaceutical information. To accommodate this, a dedicated PET JSON updater was
created. The PET JSON updater function takes the original JSON file and new metadata to add as input,
checks that the full BIDS specification is respected (correct metadata but also consistency of metadata
values for the different metadata keys) and updates the JSON file.  

_Spreadsheet conversion_: tabular data formats (xls, xlsx, csv, tsv, bld) are ubiquitous in the PET
community in particular to (a) keep track of radiotracer information injected per participant and (b)
recording of time and radiotracer concentration from the blood sampling. To facilitate conversion to BIDS, three dedicated functions were created to (i) convert pre-formatted tabular data to JSON files, or(ii) use pre-formatted tabular data to update JSON files, or (iii) convert a tabular PMOD file to a blood.tsv file (PMOD being a popular commercial pharmacokinetic modelling software [@Burger1997]).

# Acknowledgements

This work was supported by Novo Nordisk fonden (NNF20OC0063277) and the BRAIN initiative (MH002977-01).

# References


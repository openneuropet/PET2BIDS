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
  affiliation: "3, 4"
- name: Adam G. Thomas
  orcid: 0000-0002-2850-1419
  affiliation: 1
- name: Gabriel Gonzalez-Escamilla
  orcid: 0000-0002-7209-1736
  affiliation: 5
- name: Claus Svarer
  orcid: 0000-0001-7811-1825
  affiliation: 3
- name: Chris Rorden
  orcid: 0000-0002-7554-6142
  affiliation: 6
- name: Grandville Matheson
  orcid: 0000-0002-5646-4547
  affiliation: 7
- name: Gite Knudsen
  orcid: 0000-0003-1508-6866
  affiliation: 3
- name: Robert Innis
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
 - name: University Medical Center of the Johannes Gutenberg University Mainz, Mainz, Germany
   index: 5
 - name: Department of Psychology, University of South Carolina, Columbia, SC, USA
   index: 6
 - name: Mailman school of public health, Columbia University, New York, NY, USA
   index: 7
date: 22 August 2023
bibliography: paper.bib

---

# Summary

The Brain Imaging Data Structure [@gorgolewski_brain_2016] is a strandard for organizing and naming neuroimaging data which has quickly become successful and popular in the community with adoption by major brain imaging repositories (e.g. Open Neuro [@noauthor_openneuro], PublicnEUro [@noauthor_public], CONP [@noauthor_canadian]) and data management tools (e.g. COINS [@landis_coins_2016], XNAT [@marcus_extensible_2007], Loris [@das_loris_2012]). This not only allows data to be shared much more easily, but also enables the development of automated data analysis pipelines, and together improves reproducibility.  

The PET-BIDS extension [@norgaard_pet-bids_2022] provides a structured data and metadata nomenclature, including all the necessary information to share and report on PET blood and metabolite [@knudsen_guidelines_2020]. Here we present a new code library, developed in both Matlab and Python, allowing the conversion of PET imaging data (ecat and dicom format data) and metadata (e.g. time or blood measurements) into the brain imaging data structure specification.

# Statement of need

`PET2BIDS` was designed as a library code, allowing converting Positron Emission Tomography data to BIDS using command line. Thanks to it's modular structure, it can be integrated into software (with graphical user interface) that aim at more general BIDS conversion, and current efforts are integrating PET2BIDS with ezBIDS [@noauthor_ezbids] and BIDSCoins [@zwiers_bidscoin_2022].

_File conversion_: The conversion for PET data stored in DICOM files is performed using a wrapper
around dcm2niix [@rorden_dcm2nii] [@li_first_2016] and then updating the corresponding JSON file. For ECAT files, dedicated functions were written to support this conversion. The Matlab code relies on the readECAT7.m
function from BT Christian (1998) and revised by RF Muzic (2002) to read the data, while new ecat2nii
(.m .py) functions were written to convert into NIfTI and produce a JSON sidecar file, and optionally a
(non-BIDS compliant) SIF file (Scan Information File - used by different pharmacokinetic modelling software for model weighting). The Python code was subsequently developed in line with the Matlab code, further testing
data reading (i.e. which bits are read according to the PET data frames) and writing, relying here on
Nibabel [@brett_nipynibabel_2023].  

_PET Metadata_: JSON files created from reading PET scanner data are always missing some of the
radiotracer and pharmaceutical information. To accommodate this, a dedicated PET JSON updater was
created. The PET JSON updater function takes the original JSON file and new metadata to add as input,
checks that the full BIDS specification is respected (correct metadata but also consistency of metadata
values for the different metadata keys) and updates the JSON file.  

_Spreadsheet conversion_: tabular data formats (excel, csv, tsv, bld) are ubiquitous in the PET
community in particular to (a) keep track of radiotracer information injected per participants and (b)
record time and radiotracer concentration from the blood sampling. To facilitate conversion to BIDS,
dedicated functions were created to (i) convert pre-formatted tabular data to JSON files, (ii) use preformatted tabular data to update JSON files, and (iii) convert a tabular pmod file to a blood.tsv file
(pmod being a popular commercial pharmacokinetic modelling software [@]).

# Acknowledgements

This work was supported by Novo Nordisk fonden (NNF20OC0063277) and the BRAIN initiative (MH002977-01).

# References


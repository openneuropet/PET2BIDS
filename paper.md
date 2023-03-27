---
title: 'PET2BIDS: a library for converting Positron Emission Tomography data to BIDS'
tags:
  - Matlab
  - Python
  - brain imaging
  - positron emission tomography (PET)
  - brain imaging data structure (BIDS)
authors:
  - name: Adrian M. Price-Whelan
    orcid: 0000-0000-0000-0000
    equal-contrib: true
    affiliation: "1, 2" # (Multiple affiliations must be quoted)
  - name: Author Without ORCID
    equal-contrib: true # (This is how you can denote equal contributions between multiple authors)
    affiliation: 2
  - name: Author with no affiliation
    corresponding: true # (This is how to denote the corresponding author)
    affiliation: 3
affiliations:
 - name: Lyman Spitzer, Jr. Fellow, Princeton University, USA
   index: 1
 - name: Institution Name, Country
   index: 2
 - name: Independent Researcher, Country
   index: 3
date: 13 August 2017
bibliography: paper.bib

---

# Summary

The Brain Imaging Data Structure (BIDS) (1) has quickly become successful and popular in the
neuroimaging community with adoption by major brain imaging repositories (e.g. CONP, OpenNeuro,
WeBrain) and data management tools (e.g. COINS, XNAT, Loris). This not only allows data to be shared
much more easily, but also enables the development of automated data analysis pipelines (2), and
together improves reproducibility.  

The PET-BIDS extension (3) has recently been merged into the BIDS specification, providing a
structured data and metadata nomenclature, including all the necessary information to share and
report on PET blood and metabolite (4). Here we present a new code library, developed in both Matlab
and Python, allowing the conversion of PET imaging data (ecat and dicom) and metadata (e.g. time or
blood measurements) into the brain imaging data structure specification.

# Statement of need

File conversion: The conversion for PET data stored in DICOM files is performed using a wrapper
around dcm2niix (5) and then updating the corresponding JSON file. For ECAT files, dedicated
functions were written to support this conversion. The Matlab code relies on the readECAT7.m
function from BT Christian (1998) and revised by RF Muzic (2002) to read the data, while new ecat2nii
(.m .py) functions were written to convert into NIfTI and produce a JSON sidecar file, and optionally a
SIF file (Scan Information File - used by different pharmacokinetic modelling software for model
weighting). The Python code was subsequently developed in line with the Matlab code, further testing
data reading (i.e. which bits are read according to the PET data frames) and writing, relying here on
Nibabel (6).  

Metadata: JSON files created from reading PET scanner data are always missing some of the
radiotracer and pharmaceutical information. To accommodate this, a dedicated PET JSON updater was
created. The PET JSON updater function takes the original JSON file and new metadata to add as input,
checks that the full BIDS specification is respected (correct metadata but also consistency of metadata
values for the different metadata keys) and updates the JSON file.  

Spreadsheet conversion: tabular data formats (excel, csv, tsv, bld) are ubiquitous in the PET
community in particular to (a) keep track of radiotracer information injected per participants and (b)
record time and radiotracer concentration from the blood sampling. To facilitate conversion to BIDS,
dedicated functions were created to (i) convert pre-formatted tabular data to JSON files, (ii) use preformatted tabular data to update JSON files, and (iii) convert a tabular pmod file to a blood.tsv file
(pmod being a popular commercial pharmacokinetic modelling software -
https://www.pmod.com/web/).

# Citations

Citations to entries in paper.bib should be in
[rMarkdown](http://rmarkdown.rstudio.com/authoring_bibliographies_and_citations.html)
format.

If you want to cite a software repository URL (e.g. something on GitHub without a preferred
citation) then you can do it with the example BibTeX entry below for @fidgit.

For a quick reference, the following citation commands can be used:
- `@author:2001`  ->  "Author et al. (2001)"
- `[@author:2001]` -> "(Author et al., 2001)"
- `[@author1:2001; @author2:2001]` -> "(Author1 et al., 2001; Author2 et al., 2002)"

# Figures

Figures can be included like this:
![Caption for example figure.\label{fig:example}](figure.png)
and referenced from text using \autoref{fig:example}.

Figure sizes can be customized by adding an optional second parameter:
![Caption for example figure.](figure.png){ width=20% }

# Acknowledgements

We acknowledge contributions from Brigitta Sipocz, Syrtis Major, and Semyeong
Oh, and support from Kathryn Johnston during the genesis of this project.

# References

## Siemens - ECAT7

## ecat_info

During our effort to create a converter to BIDS, we came across some documentation that might be useful to others - so we stored it here.

## Validation

Synthetic ecat data of size 16*16*16*4 were created using golden_ecat.py (synthetic_ecat_integer_16x16x16x4.v.gz), and the values of each voxel also saved directly as .mat (synthetic_ecat_integer_16x16x16x4.mat). The validation ecat2nii_test.m then read the .v, convert to .nii, and reread the .nii. It then compare the reread values to expected ones (from the .mat). Ideally we would have the same values but (1) we have different dymamic range (here only 1 out of 16bits ~0.0003) because ecat2nii rescale your data to 16bits and (2) precisions around 0 differs as well, some small changes are expected. This can be seen in the figure below. Reread vs Orignal show a perfect correlation, but with an average difference of -0.000001 with min -05 and max 0.5 (to put this in perspective, it means for PET images, differences are equivalent of 1 photon detection - we can live with that).

![](https://github.com/openneuropet/PET2BIDS/blob/main/ecat_validation/synthetic_ecat_integer_16x16x16x4.v.jpg)

## Conversion

The ecat file ECAT7_multiframe.v was converted here as a test, with ecat2nii.m as follow

```matlab
file          = fullfile(pwd,'ECAT7_multiframe.v.gz'); % edit with the right path
meta.TimeZero = datestr(now,'hh:mm:ss'); % that metadata cannnot be skipped
ecat2nii(file,meta)
```

```python
```

This illustrates [what metadata are extracted from the ecat file](https://github.com/openneuropet/BIDS-converter/blob/main/PETdata_in/Siemens_ecat/ECAT7_multiframe.json) - which does not comform with BIDS because radiochemistry and pharmaceutical metadata are missing.

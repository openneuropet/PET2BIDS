## Siemens - ECAT7

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

## ecat_info

During our effort to create a converter to BIDS, we came across some documentation that might be useful to others - so we stored it here.

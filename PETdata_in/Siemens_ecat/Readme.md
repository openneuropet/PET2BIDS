## Siemens - ECAT7

## Conversion

the ecat file ECAT7_multiframe.v was converted here as a test, with ecat2nii.m as folow
```matlab
file          = fullfile(pathtofile,'ECAT7_multiframe.v'); % edit with the right path
meta.info     = 'just running a test';
meta.TimeZero = datestr(now,'hh:mm:ss');
ecat2nii(file,meta)
```
This illustrates what metadata are extracted from the ecat file - which does not comform with BIDS because radiochemistry and pharmaceutical metadata are missing.

## ecat_info

During our effort to create a converter to BIDS, we came across some documentation that might be useful to others - so we stored it here.

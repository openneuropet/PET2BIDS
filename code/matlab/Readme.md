# Read and write ecat files as nifti + json

BIDS requires nifti files and json. While json can be writen be hand, this is more convenient to populate them as one reads data. One issue is that some information is not encoded in ecat headers and thus needs to be created overwise.

## dependencies

we use the jsonwrite function available with the BIDS matlab tools and-or json.io

## usage

```matlab
metadata = get_SiemensHRRT_metadata(varargin)
ecat2nii({full_file_name},{metadata})
```


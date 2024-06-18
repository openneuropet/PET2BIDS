# Convert ecat file to nii+json

Siemens ecat (.v) files version 7+ can be converted to nifti (.nii) and accompanying json (.json) file in a [BIDS](https://bids-specification.readthedocs.io/en/stable/04-modality-specific-files/09-positron-emission-tomography.html) compliant fashion.

### nifti

We read the ecat file, rescale the data to 16 bits, round, multiply by the scanner calibration factor, and use the Matlab nifti write function (little endian).

## Testing

### 'Rounding' errors

`niftiwrite_test.m` is a simple test, creating random data, that are rescaled and saved as nifti - reread and the difference between the generated data and reread data plotted. This shows that the rescaling method used, creates small errors (up to 0.0008 for a simulated data range of 256, i.e. 0.0003125%).

![small_error](https://github.com/openneuropet/PET2BIDS/blob/main/matlab/unit_tests/error.jpg)

### Precision

`ecat2nii_test.m` test our groundtruth data and any other nifti file. Because acquired data are already scaled by the manufacturer (for instance in the 12 bits range) and then we rescaled in 16 bits, round and multiply by the dose calibration factor, many small [quantization errors](https://en.wikipedia.org/wiki/Quantization_(signal_processing)) occur. In addition, because the [representation of floating points is the densest around zero](https://docs.oracle.com/cd/E19957-01/806-3568/ncg_goldberg.html) it also means that most errors are concentrated around zero. When testing against the unsigned ground data (just type ecat) , we can see all errors above 0 with the largest error of 0.000000000002. With real data, we observed most errors around 0 because data be signed (which makes so sense for PET by the way) staying relarively constant across all data frames.

![small_error](https://github.com/openneuropet/PET2BIDS/blob/main/matlab/unit_tests/ECAT7_multiframe.v.jpg)



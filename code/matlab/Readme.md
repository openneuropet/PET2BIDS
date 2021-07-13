# Read and write raw scanner files as nifti + json

BIDS requires nifti files and json. While json can be writen be hand, this is more convenient to populate them as one reads data. One issue is that some information is not encoded in ecat headers and thus needs to be created overwise.

## Dependencies

We use the [niftiwrite](https://se.mathworks.com/help/images/ref/niftiwrite.html) from the Matlab image processing toolbox.  
The jsonwrite function is distributed here, taken from [json.io](https://github.com/gllmflndn/JSONio). 

## Configuration

Defaults parameters should be set in the .txt files to generate metadata easily (i.e. avoiding to pass all arguments in). 

## Usage

### for ecat files (HRRT)
```matlab
metadata = get_SiemensHRRT_metadata('TimeZero','XXX','tracer','DASB','Radionuclide','C11', ...
                        'Radioactivity', 605.3220,'InjectedMass', 1.5934,'MolarActivity', 107.66)
ecat2nii({full_file_name},{metadata})
```  
See the [documentation](https://github.com/openneuropet/BIDS-converter/blob/main/code/matlab/doc.mkd) for further details.


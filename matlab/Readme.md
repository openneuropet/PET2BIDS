# Read and write raw scanner files as nifti + json

BIDS requires nifti files and json. While json can be writen be hand, this is more convenient to populate them as one reads data. One issue is that some information is not encoded in ecat headers and thus needs to be created overwise.

## Dependencies

We use the [niftiwrite](https://se.mathworks.com/help/images/ref/niftiwrite.html) from the Matlab image processing toolbox, which is only need to convert ecat files. The jsonwrite function is distributed here, taken from [json.io](https://github.com/gllmflndn/JSONio). There are no other dependencies.

## Configuration

The entire repository or only the matlab subfolder (your choice) should be in your matlab path.  
Defaults parameters should be set in the .txt files to generate metadata easily (i.e. avoiding to pass all arguments in). At the moment, those parameters files are SiemensHRRTparameters.txt, SiemensBiograph.txt and GEAdvanceparameters.txt (only make what you need).

### Get metadata

To simplify the curation of json files, there are serveal get_XXX_metadata.m functions. Those are routines specific to each scanner and typically also need some manual input related to tracers (while defauts as txt file can be pulled for scanner info). We have dedicated functions for the [Siemens HRRT](https://github.com/openneuropet/PET2BIDS/blob/main/matlab/get_SiemensHRRT_metadata.m), [Siemens Biograph](https://github.com/openneuropet/PET2BIDS/blob/main/matlab/get_SiemensBiograph_metadata.m) and [GE Advance](https://github.com/openneuropet/PET2BIDS/blob/main/matlab/get_GEAdvance_metadata.m). _Feel free to reach out if you want to create such function for your scanner, we can help_.

## Usage

### converting dicom files

The simplest way is to call [dcm2niix4pet.m](https://github.com/openneuropet/PET2BIDS/blob/main/matlab/dcm2niix4pet.m) which wraps around dcm2niix. Assuming dcm2niix is present in your environment, Matlab will call it to convert your data to nifti and json - and the wrapper function will additionally edit the json file. Arguments in are the dcm folder(s) in, the metadata as a structure (using a get_XXX_metadata.m function for instance) and possibly options as per dcm2nixx.   

```matlab
meta = get_SiemensBiograph_metadata('TimeZero','ScanStart','tracer','CB36','Radionuclide','C11', ...
                'Radioactivity', 605.3220,'InjectedMass', 1.5934,'MolarActivity', 107.66);
fileout = dcm2niix4pet(folder1,meta,'gz',9,'o','mynewfolder','v',1); % change dcm2niix default
```  

Alternatively, you could have data already converted to nifti and json, and you need to update the json file. This can be done 2 ways:

1. Use the [updatejsonpetfile.m](https://github.com/openneuropet/PET2BIDS/blob/main/matlab/updatejsonpetfile.m) function. Arguments in are the json file to update and metadata to add as a structure (using a get_XXX_metadata.m function for instance) and possibly a dicom file to check additional fields. This is show below for data from the biograph.

```matlab
jsonfilename = fullfile(pwd,'DBS_Gris_13_FullCT_DBS_Az_2mm_PRR_AC_Images_20151109090448_48.json')
metadata = get_SiemensBiograph_metadata('TimeZero','ScanStart','tracer','AZ10416936','Radionuclide','C11', ...
                        'ModeOfAdministration','bolus','Radioactivity', 605.3220,'InjectedMass', 1.5934,'MolarActivity', 107.66)
dcminfo = dicominfo('DBSGRIS13.PT.PETMR_NRU.48.13.2015.11.11.14.03.16.226.61519201.dcm')
status = updatejsonpetfile(jsonfilename,metadata,dcminfo)
```  

2. Add the metadata 'manually' to the json file, show below for GE Advance data. 
```matlab
metadata1 = jsondecode(textread(myjsonfile.json)); % or use jsonread from the matlab BIDS library
metadata2 = get_GEAdvance_metadata('TimeZero','XXX','tracer','DASB','Radionuclide','C11', ...
                        'Radioactivity', 605.3220,'InjectedMass', 1.5934,'MolarActivity', 107.66)
metadata  = [metadata2;metadata1];                        
jsonwrite('mynewjsonfile.json'],metadata)                        
```  


### converting ecat files

If you have ecat (.v) instead of dicom (.dcm), we have build a dedicated converter. Arguments in are the file to convert and some metadata as a structure (using a get_XXX_metadata.m function for instance). This is shown below for HRRT data.

```matlab
metadata = get_SiemensHRRT_metadata('TimeZero','XXX','tracer','DASB','Radionuclide','C11', ...
                        'Radioactivity', 605.3220,'InjectedMass', 1.5934,'MolarActivity', 107.66)
ecat2nii({full_file_name},{metadata})
```  
See the [documentation](https://github.com/openneuropet/BIDS-converter/blob/main/code/matlab/doc.mkd) for further details on ecat conversion.  


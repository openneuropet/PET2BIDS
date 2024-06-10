# Read and write raw scanner files as nifti + json

BIDS requires nifti files and json. While json can be written be hand, this is more convenient to populate them as one reads data. One issue is that some information is not encoded in ecat/dicom headers and thus needs to be created otherwise.

## Dependencies

_To convert DICOM files_, [dcm2niix](https://www.nitrc.org/plugins/mwiki/index.php/dcm2nii:MainPage) (Chris Rorden) must be installed. Windows users must, in addition, indicate its full path in [dcm2niix4pet.m](https://github.com/openneuropet/PET2BIDS/blob/main/matlab/dcm2niix4pet.m#L42).

## Redistributed functions

 _To convert ECAT files_, [ecat2nii.m](https://github.com/openneuropet/PET2BIDS/blob/main/matlab/ecat2nii.m) uses [readECAT7](https://github.com/openneuropet/PET2BIDS/blob/main/matlab/readECAT7.m) (Raymond Muzic, 2002) and [nii_tool](https://github.com/xiangruili/dicm2nii) (Xiangrui Li, 2016), who are included and redistributed in the repository. _To write the JSON sidecar files_, one uses jsonwrite.m (Guillaume Flandin, 2020) taken from [json.io](https://github.com/gllmflndn/JSONio). 

## Configuration

The entire repository or only the matlab subfolder (your choice) should be in your matlab path.  

Defaults parameters should be set in (scannername).txt files to generate metadata easily (i.e. avoiding to pass all arguments in although this is also possible). You can find templates of such parameter file under /template_txt (SiemensHRRTparameters.txt, SiemensBiographparameters.txt, GEAdvanceparameters.txt,  PhilipsVereosparameters.txt).

### Get metadata

To simplify the curation of json files, one uses the [get_pet_metadata.m](https://github.com/openneuropet/PET2BIDS/blob/main/matlab/get_pet_metadata.m) function. This function takes as arguments the scanner info (thus loading the relevant *parameters.txt file) and also need some manual input related to the injected tracer.  
  
_Feel free to reach out if you have an issue with your scanner files, we can help_.

## Usage

### converting dicom files

The simplest way is to call [dcm2niix4pet.m](https://github.com/openneuropet/PET2BIDS/blob/main/matlab/dcm2niix4pet.m) which wraps around dcm2niix. Assuming dcm2niix is present in your environment, Matlab will call it to convert your data to nifti and json - and the wrapper function will additionally edit the json file. Arguments in are the dcm folder(s) in, the metadata as a structure (using the get_pet_metadata.m function for instance) and possibly options as per dcm2nixx.  

_Note for windows user_: edit the dcm2niix4pet.m line 51 to indicate where is the .exe function located

Now in order to convert a PET dataset on disk to PET BIDS,  just create a structure containing all the meta information and then point the function to the folder where your data resides *dcmfolder* and the folder where you want to output the PET BIDS formatted dataset *mynewfolder*:

```matlab
meta = get_pet_metadata('Scanner','SiemensBiograph','TimeZero','ScanStart',...
    'TracerName','CB36','TracerRadionuclide','C11', 'ModeOfAdministration',...
    'infusion','SpecificRadioactivity', 605.3220,'InjectedMass', 1.5934,...
    'MolarActivity', 107.66, 'InstitutionName','Rigshospitalet, NRU, DK',...
    'AcquisitionMode','list mode','ImageDecayCorrected','true',...
    'ImageDecayCorrectionTime' ,0,'ReconMethodName','OP-OSEM',...
    'ReconMethodParameterLabels',{'subsets','iterations'},...
    'ReconMethodParameterUnits',{'none','none'}, ...
    'ReconMethodParameterValues',[21 3], 'ReconFilterType','XYZGAUSSIAN',...
    'ReconFilterSize',2, 'AttenuationCorrection','CT-based attenuation correction');
dcm2niix4pet(dcmfolder,meta,'o',mynewfolder);
```  
_Note that get_pet_metadata can be called in a much simpler way if you have a `*parameters.txt` seating on disk next to this function. The call would then looks like:_

```matlab
% your SiemensBiographparameters.txt file is stored next to get_pet_metadata.m
meta = get_pet_metadata('Scanner','SiemensBiograph','TimeZero','ScanStart','TracerName','CB36',...
    'TracerRadionuclide','C11', 'ModeOfAdministration','infusion','SpecificRadioactivity', ...
    605.3220, 'InjectedMass', 1.5934,'MolarActivity', 107.66);
dcm2niix4pet(dcmfolder,meta,'o',mynewfolder);
```  

**Alternatively**, you could have data already converted to nifti and json, and you need to update the json file. This can be done 2 ways:

1. Use the [updatejsonpetfile.m](https://github.com/openneuropet/PET2BIDS/blob/main/matlab/updatejsonpetfile.m) function. Arguments in are the json file to update and metadata to add as a structure (using a get_metadata.m function for instance) and possibly a dicom file to check additional fields. This is show below for data from the biograph.

```matlab
jsonfilename = fullfile(pwd,'DBS_Gris_13_FullCT_DBS_Az_2mm_PRR_AC_Images_20151109090448_48.json')
% your SiemensBiographparameters.txt file is stored next to get_pet_metadata.m
metadata = get_pet_metadata('Scanner','SiemensBiograph','TimeZero','ScanStart','TracerName','AZ10416936','TracerRadionuclide','C11', ...
                        'ModeOfAdministration','bolus','InjectedRadioactivity', 605.3220,'InjectedMass', 1.5934,'MolarActivity', 107.66)
dcminfo = dicominfo('DBSGRIS13.PT.PETMR_NRU.48.13.2015.11.11.14.03.16.226.61519201.dcm')
status = updatejsonpetfile(jsonfilename,metadata,dcminfo)
```  

2. Add the metadata 'manually' to the json file, shown below for GE Advance data. 

```matlab
metadata1 = jsondecode(textread(myjsonfile.json)); % or use jsonread from the matlab BIDS library
% your GEAdvance.txt file is stored next to get_pet_metadata.m
metadata2 = get_pet_metadata('Scanner', 'GEAdvance','TimeZero','XXX','TracerName','DASB','TracerRadionuclide','C11', ...
                        'ModeOfAdministration','bolus', 'InjectedRadioactivity', 605.3220,'InjectedMass', 1.5934,'MolarActivity', 107.66)
metadata  = [metadata2;metadata1];                        
jsonwrite('mynewjsonfile.json'],metadata)                        
```  


### converting ecat files

If you have ecat (.v) instead of dicom (.dcm), we have build a dedicated converter. Arguments in are the file to convert and some metadata as a structure (using the get_pet_metadata.m function for instance). This is shown below for HRRT data.

```matlab
% your SiemensHRRT.txt file is stored next to get_pet_metadata.m
metadata = get_pet_metadata('Scanner','SiemensHRRT','TimeZero','XXX','TracerName','DASB','TracerRadionuclide','C11', ...
    'ModeOfAdministration','bolus', 'InjectedRadioactivity', 605.3220,'InjectedMass', 1.5934,'MolarActivity', 107.66)
ecat2nii({full_file_name},{metadata})
```  
See the [documentation](https://github.com/openneuropet/PET2BIDS/blob/main/matlab/unit_tests/Readme.md) for further details on ecat conversion.  


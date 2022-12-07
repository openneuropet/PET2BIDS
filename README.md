# This is the matlab4compile branch
A stripped down version of PET2BIDS with matlab code and metadata only.  
This branch is used to compile pet2bids.m (include the matlab kernel so nothing else needs to be downloaded).

## Notes
- No MATLAB license needed to install and use end product
- _dcm2niix.exe_, your default scanner parameter file (e.g., SiemensBiographparameters.txt), your startup script (e.g., pet2bids_example_dcm.m) must be located in the same directory as the executable (e.g., "C:\Program Files\pet2bids_exe_script.exe")
- The default scanner parameter file uses .txt files to pass generic metadata.

## A short demo may be downloaded and run the following way:
- First you need raw data to convert to dcm and you may download raw demo DICOM data using the following link: [https://drive.google.com/file/d/10S0H7HAnMmxHNpZLlifR14ykIuiXcBAD/view](https://drive.google.com/file/d/10S0H7HAnMmxHNpZLlifR14ykIuiXcBAD/view)
- Unzip the raw data and remember what folder you have the raw dcm files in (*)
- Download installation file from <DOWNLOAD LINK WILL SOON COME>
- From your Windows explorer, double click the exe-file you downloaded and follow instructions (to install the  compiled PET2BIDS)
- Open a DOS command window (cmd.exe)
- cd to the directory you chose as Destination folder during the installation above and choose the directory containing pet2bids_exe_script.exe (e.g., cd "C:\Program Files\pet2bids_exe_script\application")
- Edit the file pet2bids_example_dcm.m to point to your raw data in accordance with row containing asterisk (*) above
- In the command window type pet2bids_exe_script.exe pet2bids_example_dcm.m
- After command window writes several lines that DICOM files are converted and you may get some warnings about the conversion, you will see the command prompt again and you are done!

## Example of default scanner parameter file

A _SiemensHRRTparameters.txt_ file located next to the executable. The content looks like this:  
```
InstitutionName            = 'Rigshospitalet, NRU, DK';
BodyPart                   = 'Phantom';
AcquisitionMode            = 'list mode';
ImageDecayCorrected        = 'true';
ImageDecayCorrectionTime   = 0;
ReconFilterType            = 'none';
ReconFilterSize            = 0;
AttenuationCorrection      = '10-min transmission scan';
FrameDuration              = 1200;
FrameTimesStart            = 0;
```

## Example of startup script to import ECAT format (e.g., pet2bids_example_ecat.m)  
```matlab
source = 'D:\BIDS\ONP\OpenNeuroPET-Phantoms\sourcedata\';
```

``` matlab
pet2bids(fullfile(source,['SiemensHRRT-NRU' filesep 'XCal-Hrrt-2022.04.21.15.43.05_EM_3D.v']),...
    'Scanner','SiemensHRRT','TimeZero','ScanStart','TracerName',...
    'FDG','TracerRadionuclide','F18','SpecificRadioactivity',1.3019e+04,...
    'InjectedRadioactivity', 81.24,'ModeOfAdministration','infusion')
```


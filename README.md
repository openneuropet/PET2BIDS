# matlab4complit branch

A stripped down version of PET2BIDS with matlab code and metadata only.  
This branch is used to compile pet2bids.m (include the matlab kernel so nothing else needs to be downloaded).

## notes
- _dcm2niix.exe_ must be located in directory above the executable (e.g., `D:\PET2BIDS\pet2bids_exe_script.exe` and dcm2niix.exe should be in `D:\`)
- similarly use .txt files to pass generic metadata and place them next to the executable 

## example

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

Then for data located in  
```matlab
source = 'D:\BIDS\ONP\OpenNeuroPET-Phantoms\sourcedata\';
```

Call the code as
``` matlab
pet2bids(fullfile(source,['SiemensHRRT-NRU' filesep 'XCal-Hrrt-2022.04.21.15.43.05_EM_3D.v']),...
    'Scanner','SiemensHRRT','TimeZero','ScanStart','TracerName',...
    'FDG','TracerRadionuclide','F18','SpecificRadioactivity',1.3019e+04,...
    'InjectedRadioactivity', 81.24,'ModeOfAdministration','infusion')
```


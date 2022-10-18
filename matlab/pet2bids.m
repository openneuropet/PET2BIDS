function pet2bids(datain,varargin)

% FORMAT fileout = pet2bids(datain,varargin)
%
% wrapper function calling ecat2nii.m or dcm2niix4pet to convert files
% and calling get_pet_metadata to create needed metadata
% 
% datain is either an ecatfile (*.v) or the folder of dicom files
% additional arguments in the the necessary metadata for bids:
% 'TimeZero','TracerName','TracerRadionuclide','ModeOfAdministration',
% 'InjectedRadioactivity', 'InjectedMass', 'MolarActivity' 
% Since get_pet_metadata is used, a txt file of parameter can seat next to
% the compiled code allowing common parameters to be used
%
% examples usage 
%
% a SiemensHRRTparameters.txt file located next to the executable
%       InstitutionName            = 'Rigshospitalet, NRU, DK';
%       BodyPart                   = 'Phantom';
%       AcquisitionMode            = 'list mode';
%       ImageDecayCorrected        = 'true';
%       ImageDecayCorrectionTime   = 0;
%       ReconFilterType            = 'none';
%       ReconFilterSize            = 0;
%       AttenuationCorrection      = '10-min transmission scan';
%       FrameDuration              = 1200;
%       FrameTimesStart            = 0;
% data in 
% source      = 'D:\BIDS\ONP\OpenNeuroPET-Phantoms\sourcedata\';
% call the code as
% pet2bids(fullfile(source,['SiemensHRRT-NRU' filesep 'XCal-Hrrt-2022.04.21.15.43.05_EM_3D.v']),...
%    'Scanner','SiemensHRRT','TimeZero','ScanStart','TracerName',...
%    'FDG','TracerRadionuclide','F18','SpecificRadioactivity',1.3019e+04,...
%    'InjectedRadioactivity', 81.24,'ModeOfAdministration','infusion')
%
% a SiemensBiographparameters.txt file located next to the executable
%       InstitutionName            = 'Rigshospitalet, NRU, DK';
%       BodyPart                   = 'Phantom';
%       FrameTimesStart            = 0;
%       AcquisitionMode            = 'list mode';
%       ImageDecayCorrected        = 'true';
%       ImageDecayCorrectionTime   = 0;
%       AttenuationCorrection      = 'MR-corrected';
%       FrameDuration              = 300;
%       FrameTimesStart            = 0;
% data in 
% source      = 'D:\BIDS\ONP\OpenNeuroPET-Phantoms\sourcedata\';
% call the code as
% pet2bids(fullfile(source,'SiemensBiographPETMR-NRU' ),...
%    'Scanner','SiemensBiograph','TimeZero','ScanStart','TracerName',...
%    'FDG','TracerRadionuclide','F18','SpecificRadioactivity',1.3019e+04,...
%    'InjectedRadioactivity', 81.24,'ModeOfAdministration','infusion')


%% datain
if isfile(datain)
    [~,~,ext] = fileparts(datain);
    if ~strcmpi(ext,'.v')
        error('not an ecat file, for dicom indicate folder name')
    end
elseif isfolder(datain)
    checkecat = dir([datain '*.v']);
    if ~isempty(checkecat)
        datain = fullfile(checkecat.dir,checkecat.name);
    end
end

%% metadata
meta = get_pet_metadata(varargin{:});

%% convert
if isfile(datain)
    ecat2nii(datain,meta)
else
    dcm2niix4pet(datain,meta)
end



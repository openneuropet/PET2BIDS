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
% example usage 
% source      = 'D:\BIDS\ONP\OpenNeuroPET-Phantoms\sourcedata\';
% pet2bids(fullfile(source,['SiemensHRRT-NRU' filesep 'XCal-Hrrt-2022.04.21.15.43.05_EM_3D.v']),...
%    'Scanner','SiemensHRRT','TimeZero','ScanStart','TracerName',...
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
meta = get_pet_metadata(varargin);

%% convert
if isfile(datain)
    ecat2nii(datain,meta)
else
    dcm2niix4pet(datain,meta)
end



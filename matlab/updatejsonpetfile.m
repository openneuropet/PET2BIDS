function status = updatejsonpetfile(varargin)

% generic function that updates PET json file with missing PET-BIDS
% information
%
% FORMAT status = updatejsonpetfile(jsonfilename,newfields,dcminfo)
%
% INPUT - jsonfilename: jspon file to check or update update
%       optional
%       - newfields: a structure with the newfields to go into the json file
%       - dcminfo:   a dcmfile or the dicominfo structure from a representative
%                    dicom file- This information is used to also update the json
%                    file, and if a comflict exists, it returns warning messages,
%                    assumnimg the newfield provided is correct (i.e. as a user you
%                    know better than default dicom, presumably)
%
% OUTPUT status returns the state of the updating (includes warning messages
%               returned if any)
%
% Cyril Pernet Nov 2021
% ----------------------------------------------
% Copyright Open NeuroPET team

status = struct('state',[],'messages',{''});
status_index = 1;

%% check data in
jsonfilename = varargin{1};
if nargin >= 2
    newfileds = varargin{2};
    if nargin == 3
        dcminfo = varargin{3};
    end
end

% current file metadata
if exist(jsonfilename,'file')
    filemetadata = jsondecode(fileread(jsonfilename));
    filemetadatafields = fieldnames(filemetadata);
else
    error('looking for %s, but the file is missing',jsonfilename)
end

% expected metadata from the BIDS specification
jsontoload = fullfile(fileparts(fileparts(which('updatejsonpetfile.m'))),...
    ['metadata' filesep 'PET_metadata.json']);
if exist(jsontoload,'file')
    petmetadata = jsondecode(fileread(jsontoload));
else
    error('looking for %s, but the file is missing',jsontoload)
end

%% check metadata and update them
if nargin == 1
    % -------------- only check ---------------
    for m=length(petmetadata.mandatory):-1:1
        test(m) = isfield(filemetadata,petmetadata.mandatory{m});
    end
    
    if sum(test)~=length(petmetadata.mandatory)
        status.state    = 0;
        status.messages = sprints('missing mandatory field %s\n',petmetadata.mandatory{test==0});
    else
        status.state    = 1;
    end
    
else % -------------- update ---------------

    % proposed metadata
    if ~all(cellfun(@exist, newfileds))
        error('One or more mandatory name/value pairs are missing')
    end
    
    %% possible dcm fields to recover
    % - this part is truly empirical, going over different dcm files and
    % figuring out fields
    
    if exist('dcminfo','var')
        if ischar(dcminfo)
            dcminfo = flattenstruct(dicominfo(dcminfo));
        else
            dcminfo = flattenstruct(dcminfo);
        end
    else
        error('%s does not exist',dcminfo)
    end
    
    Manufacturer
    ManufacturerModelName
    SoftwareVersion
    ConvolutionKernel
    ActualFrameDuration
    R_Radiopharmaceutical: 'Solution'
    R_RadiopharmaceuticalVolume: 0
    R_RadiopharmaceuticalStartTime: '144000.000000'
    R_RadionuclideTotalDose: 560000000 = InjectedRadioactivity
    R_RadionuclideHalfLife: 1223
    R_RadionuclidePositronFraction: 1
    R_CodeValue: 'C-105A1'
    R_CodingSchemeDesignator: 'SRT'
    R_CodeMeaning: '^11^Carbon'
    Units: 'BQML'
    AttenuationCorrectionMethod: 'measured'
    ReconstructionMethod: 'OP-OSEM3i21s'
    DoseCalibrationFactor: 1
    
    %% run the update
    
    % some dcm2nixx fields can be updated (depends on dcm2nixx version)
    if isfield(filemetadata,'Unit')
        filemetadata.Units = filemetadata.Unit;
        filemetadata       = rmfield(filemetadata,'Unit');
        if strcmpi(filemetadata.Units,'BQML')
            filemetadata.Units = 'Bq/mL';
        end
    end
    
    if isfield(filemetadata,'ReconstructionMethod')
        filemetadata.ReconMethodName = filemetadata.ReconstructionMethod;
        filemetadata                 = rmfield(filemetadata,'ReconstructionMethod');
        istherenumbers               = regexp(filemetadata.ReconMethodName,'\di*','Match');
        
    end
    
    if isfield(filemetadata,'ConvolutionKernel')
        if contains(filemetadata.ConvolutionKernel,'.00')
            loc = findstr(filemetadata.ConvolutionKernel,'.00');
            filemetadata.ConvolutionKernel(loc:loc+2) = [];
            filtersize = regexp(filemetadata.ConvolutionKernel,'\d*','Match');
            if ~isempty(filtersize)
                filemetadata.ReconFilterSize = cell2mat(filtersize);
                loc = findstr(filemetadata.ConvolutionKernel,filtersize{1});
                filemetadata.ConvolutionKernel(loc:loc+length(filemetadata.ReconFilterSize)-1) = [];
                filemetadata.ReconFilterType = filemetadata.ConvolutionKernel;
            else
                filemetadata.ReconFilterType = filemetadata.ConvolutionKernel;
            end
            filemetadata = rmfield(filemetadata,'ConvolutionKernel');
        end
    end
    
    missing_index = 1;
    for f=1:length(petmetadata.mandatory)
        test = contains(filemetadatafields,petmetadata.mandatory{f},'IgnoreCase',true);
        if any(test)
            exactmatch = find(strcmpi(filemetadatafields(find(test)),petmetadata.mandatory{f}));
            if exactmatch == 0
                missing{missing_index} = petmetadata.mandatory{f};
                missing_index = missing_index + 1;
            end
        else
            missing{missing_index} = petmetadata.mandatory{f};
            missing_index = missing_index + 1;
        end
    end
    
    if ~exist('missing','var')
        warning('All mandatory fields were found in the json file before any updates')
        status.messages{status_index} = 'All mandatory fields were found in the json file before any updates';
        status_index = status_index+1;
    end
    
    % check all fields
    for m=length(petmetadata.mandatory):-1:1
        test(m) = isfield(filemetadata,petmetadata.mandatory{m});
    end
    
    if sum(test)~=length(petmetadata.mandatory)
        error('missing mandatory field %s\n',petmetadata.mandatory{test==0});
    else
        
    end
    
    % finish up
    if isfield(filemetadata,'ConversionSoftware')
        filemetadata.ConversionSoftware = [filemetadata.ConversionSoftware ' - json edited with ONP updatejsonpetfile.m'];
    end
    jsonwrite(jsonfilename,filemetadata)
end


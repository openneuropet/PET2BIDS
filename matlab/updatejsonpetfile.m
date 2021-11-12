function status = updatejsonpetfile(jsonfilename,newfields,dcminfo)

% generic function that updates PET json file with missing PET-BIDS
% information
%
% FORMAT status = updatejsonpetfile(jsonfilename,newfields,dcminfo)
%
% INPUT jsonfilename jspon file to update
%       newfields is a structure with the newfields to go into the json file
%       dcminfo a dcmfile or the dicominfo structure frmo a representative
%       file -- this info is used to also update the json file, and if a comflict
%       exists it returns warning messages, assumnimg the newfield provided is 
%       correct (i.e. as a user you know better than default dicom)
%
% OUTPUT status returns the state of the updating (includes warning messages
%               returned if any)
%
% Cyril Pernet Nov 2021
% ----------------------------------------------
% Copyright Open NeuroPET team

status = struct('state',[],'messages',{});
status_index = 1;

%% check data in
% current file metadata
if exist(jsonfilename,'file')
    filemetadata = jsondecode(fileread(jsonfilename));
    filemetadatafields = fieldnames(filemetadata);
else
    error('looking for %s, but the file is missing',jsonfilename)
end

% proposed metadata
if ~all(cellfun(@exist, newfileds))
    error('One or more mandatory name/value pairs are missing')
end

% expected metadata from the BIDS specification
jsontoload = fullfile(fileparts(fileparts(which('updatejsonpetfile.m'))),...
    ['metadata' filesep 'PET_metadata.json']);
if exist(jsontoload,'file')
    petmetadata = jsondecode(fileread(jsontoload));
else
    error('looking for %s, but the file is missing',jsontoload)
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




%% run the update

% some dcm2nixx fields can be updated (depends on dcm2nixx version)
if isfield(filemetadata,'Unit')
    filemetadata.Units = filemetadata.Unit;
    filemetadata       = rmfield(filemetadata,'Unit');
end

if isfield(filemetadata,'ReconstructionMethod')
    filemetadata.ReconMethodName = filemetadata.ReconstructionMethod;
    filemetadata                 = rmfield(filemetadata,'ReconstructionMethod');
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



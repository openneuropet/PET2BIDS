function status = updatejsonpetfile(filename,newfields)

%% check data in
% current file metadata
if exist(jsontoload,'file')
    filemetadata = jsondecode(fileread(filename));
else
    error('looking for %s, but the file is missing',jsontoload)
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

%% run the update

% some dcm2nixx fields can be updated (depends on dcm2nixx version)
if isfield(filemetadata,'Unit')
    filemetadata.Units = filemetadata.Unit;
    filemetadata       = rmfield(filemetadata,'Unit');
end



% check all fields
for m=length(petmetadata.mandatory):-1:1
    test(m) = isfield(filemetadata,petmetadata.mandatory{m});
end

if sum(test)~=length(petmetadata.mandatory)
    error('missing mandatory field %s\n',petmetadata.mandatory{test==0});
else
    
end





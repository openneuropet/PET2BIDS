function [method,iteration,subset] = get_recon_method(headervalue)

% from the dicom value of the PET reconstruction method, it returns the
% actual name of the method and the number of iterations and subsets if any
%
% :format: - [method,iteration,subset] = get_recon_method(headervalue)
%
% :param headervalue: the name in the ecat or dicom field of the reconstrusction method
% :returns method: the full name of the reconstrucrtion method or empty if no match found
% :returns iteration: the number of iterations or 'none'
% :returns subset: the number of subsets or 'none'
%
% | *Cyril Pernet 2022*
% | *Copyright Open NeuroPET team*


%% defaults
method    = [];
iteration = [];
subset    = [];

%% load metadata from the library
current    = which('ecat2nii.m');
pn_parts   = strsplit(fileparts(current), filesep);
jsontoload = fullfile(strjoin(pn_parts(1:end-1), '/'), 'metadata', 'PET_reconstruction_methods.json');
if exist(jsontoload,'file')
    reconstruction_metadata = jsondecode(fileread(jsontoload));
    reconstruction_metadata = reconstruction_metadata.reconstruction_names;
    values = arrayfun(@(x) x.value, reconstruction_metadata, 'UniformOutput', false);
    names  = arrayfun(@(x) x.name, reconstruction_metadata, 'UniformOutput', false);
else
    error('looking for %s, but the file is missing',jsontoload)
end

%% do some matching

% get iterations and subsets
dim                = []; % if 3D becomes '3D' to append to names
dim_position       = []; % position to clean-up the name
iteration_position = [];
subset_position    = [];
numbers            = regexp(headervalue,'\d*','Match');
for n=1:length(numbers)
    loc        = strfind(headervalue,numbers{n});
    loc_length = loc+length(numbers{n})-1;
    
    if strcmpi(headervalue(loc:loc+1),'2D')
        dim          = '2D';
        dim_position = loc:loc+1;
    elseif strcmpi(headervalue(loc:loc+1),'3D')
        dim          = '3D';
        dim_position = loc:loc+1;
    end
    
    if loc > 1
        if loc_length<length(headervalue)
            if strcmpi([headervalue(loc-1) headervalue(loc:loc_length)],['i',numbers{n}]) && isempty(iteration)
                iteration          = numbers{n};
                iteration_position = loc-1:loc_length;
            elseif strcmpi([headervalue(loc:loc_length) headervalue(loc_length+1)],[numbers{n} 'i']) && isempty(iteration)
                iteration          = numbers{n};
                iteration_position = loc:loc_length+1;
            elseif strcmpi([headervalue(loc-1) headervalue(loc:loc_length)],['s',numbers{n}]) && isempty(subset)
                subset            = numbers{n};
                subset_position   = loc-1:loc_length;
            elseif strcmpi([headervalue(loc:loc_length) headervalue(loc_length+1)],[numbers{n} 's']) && isempty(subset)
                subset            = numbers{n};
                subset_position   = loc:loc_length+1;
            end
        else
            if strcmpi([headervalue(loc-1) headervalue(loc:loc_length)],['i',numbers{n}])
                iteration = numbers{n};
                iteration_position = loc-1:loc_length;
            elseif strcmpi([headervalue(loc:loc_length) headervalue(loc_length)],[numbers{n} 'i'])
                iteration = numbers{n};
                iteration_position = loc:loc_length;
            elseif strcmpi([headervalue(loc-1) headervalue(loc:loc_length)],['s',numbers{n}])
                subset          = numbers{n};
                subset_position = loc-1:loc_length;
            elseif strcmpi([headervalue(loc:loc_length) headervalue(loc_length)],[numbers{n} 's'])
                subset          = numbers{n};
                subset_position = loc:loc_length;
            end
        end
    end
end

if strcmp(iteration,'none') && ~strcmpi(subset,'none') || ...
        ~strcmp(iteration,'none') && strcmpi(subset,'none')
    warning('subset or iteration found but not the other, something is wrong in the metadata reconstruction information')
end

% clean the name of the method remove 3D, i, s and numbers
clean_name = headervalue; % fall back on this if name detection fails
if ~isempty(iteration_position) || ~isempty(subset_position)
    remove = [dim_position iteration_position subset_position];
    headervalue(remove) = [];
    remove = [iteration_position subset_position];
    clean_name(remove) = [];
end

% try to match the library with looking at bits of names and reassemble
for v = 1:length(values)
    if ~isempty(strfind(headervalue,values{v}))
        if any(strcmpi(values{v},{'OS','OSEM','RAMLA'}))
            renamed{strfind(headervalue,values{v})} = [dim ' ' names{v} ' ']; %#ok<AGROW>
        else
            renamed{strfind(headervalue,values{v})} = [names{v} ' ']; %#ok<AGROW>
        end
    end
end

if ~exist('renamed','var')
    renamed{1} = headervalue; % still return something
end

for v=1:length(renamed)
    if ~isempty(renamed{v})
        method = [method renamed{v}]; %#ok<AGROW>
    end
end
method = deblank(method);
% trim duplicate white space
expression = '[ ]{2,}';
replacement = ' ';
method = regexprep(method, expression, replacement);


if isempty(method)
    warning('the reconstruction method is not in our library, check metadata json (and get in touch to include it)')
    warning('using method %s',clean_name)
    method = clean_name;
end

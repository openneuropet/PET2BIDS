function status = updatejsonpetfile(varargin)

% generic function that updates PET json file with missing PET-BIDS
% information, if only the jsonfile is provided, it only checks if valid
% (and possibly updates some fields from scalar to array)
%
% :format: - status = updatejsonpetfile(jsonfilename,newfields,dcminfo)
%
% :param jsonfilename: json file to check or update update
%                      can also be the json structure (add field filename to ensure update on disk)
% :param newfields: (optional) a structure with the newfields to go into the json file
% :param dcminfo: (optional) a dcmfile or the dicominfo structure from a representative
%                    dicom file. This information is used to also update the json
%                    file, and if a conflict exists, it returns warning messages,
%                    assumnimg the newfield provided is correct (i.e. as a user you
%                    know better than default dicom, presumably)
%
% :returns status: the state of the updating (includes warning messages returned if any)
%
% .. code-block::
%
%    jsonfilename = fullfile(pwd,'DBS_Gris_13_FullCT_DBS_Az_2mm_PRR_AC_Images_20151109090448_48.json')
%    metadata = get_SiemensBiograph_metadata('TimeZero','ScanStart','tracer','AZ10416936','Radionuclide','C11', ...
%                           'ModeOfAdministration','bolus','Radioactivity', 605.3220,'InjectedMass', 1.5934,'MolarActivity', 107.66)
%    dcminfo = dicominfo('DBSGRIS13.PT.PETMR_NRU.48.13.2015.11.11.14.03.16.226.61519201.dcm')
%    status = updatejsonpetfile(jsonfilename,metadata,dcminfo)
%
% | *Cyril Pernet 2022*
% | *Copyright Open NeuroPET team*

warning on % set to off to ignore our useful warnings
status = struct('state',[],'messages',{''});

% check data in
jsonfilename = varargin{1};
if nargin >= 2
    newfields = varargin{2};
    if iscell(newfields)
        newfields = cell2mat(newfields);
    end
    
    if nargin == 3
        dcminfo = varargin{3};
    end
end

% current file metadata
if isstruct(jsonfilename)
    filemetadata = jsonfilename;
    if isfield(filemetadata,'filename')
        jsonfilename = filemetadata.filename;
        filemetadata = rmfield(filemetadata,'filename');
    else
        clear jsonfilename;
    end
else
    if exist(jsonfilename,'file')
        fr = fileread(jsonfilename);
        fr(strfind(fr,'\9')) = 9; % ensures 'return' is not encoded
        filemetadata = jsondecode(fr);
    else
        error('looking for %s, but the file is missing',jsonfilename)
    end
end

% expected metadata from the BIDS specification
current    = which('updatejsonpetfile.m');
root       = current(1:max(strfind(current,'matlab'))-1);
jsontoload = fullfile(root,['metadata' filesep 'PET_metadata.json']);
if exist(jsontoload,'file')
    petmetadata = jsondecode(fileread(jsontoload));
else
    error('looking for %s, but the file is missing',jsontoload)
end

%% check metadata and update them
if nargin == 1
    % --------- update arrays if needed ---------------
    [filemetadata,updated] = update_arrays(filemetadata);
    if updated && exist('jsonfilename','var')
        warning('some scalars were changed to array')
        if strcmpi(filemetadata.ReconFilterType,"none") 
            filemetadata.ReconFilterSize = 0; % not necessary once the validator takes conditinonal
        end
        jsonwrite(jsonfilename,orderfields(filemetadata));
    end
    
    % -------------- only check --------------
    for m=length(petmetadata.mandatory):-1:1
        test(m) = isfield(filemetadata,petmetadata.mandatory{m});
    end

    if sum(test)~=length(petmetadata.mandatory)
        status.state    = 0;
        missing         = find(test==0);
        for m=1:length(missing)
            status.messages{m} = sprintf('missing mandatory field %s',petmetadata.mandatory{missing(m)});
            warning(status.messages{m})
        end
    else
        status.state    = 1;
    end
    
else % -------------- update ---------------
       
    %% run the update
       
    addfields = fields(newfields);
    for f=1:length(addfields)
        filemetadata.(addfields{f}) = newfields.(addfields{f});
    end
       
    if isfield(filemetadata,'TimeZero')
        if strcmpi(filemetadata.TimeZero,'ScanStart') || isempty(filemetadata.TimeZero)
            filemetadata.TimeZero   = datetime(filemetadata.AcquisitionTime,'Format','hh:mm:ss');
            filemetadata.ScanStart  = 0;     
            
            if ~isfield(filemetadata,'InjectionStart')
                filemetadata.InjectionStart = 0;
            end
        else
            filemetadata.ScanStart = filemetadata.AcquisitionTime - filemetadata.TimeZero;
        end
        filemetadata               = rmfield(filemetadata,'AcquisitionTime');
    else
        warning('TimeZero is not defined, which is not compliant with PET BIDS')
    end
  
    % recheck those fields, assume 0 is not specified
    if ~isfield(filemetadata,'ScanStart')
        filemetadata.ScanStart     = 0;
    end
    
    if ~isfield(filemetadata,'InjectionStart')
        filemetadata.InjectionStart = 0;
    end
    filemetadata = dcm2bids_internal(filemetadata);
        
    % -------------------------------------------------------------
    % possible dcm fields to recover - this part is truly empirical
    % going over different dcm files and figuring out fields
    % ------------------------------------------------------------
    
    if exist('dcminfo','var')
        if ischar(dcminfo)
            dcminfo = flattenstruct(dicominfo(dcminfo));
        else
            dcminfo = flattenstruct(dcminfo);
        end
        % here we keep only the last dcm subfield (flattenstrct add '_' with
        % leading subfields initial to make things more tracktable but we
        % don't need it to match dcm names)
        
        dicom_nucleotides = { '^11^Carbon', '^13^Nitrogen', '^14^Oxygen', ...
            '^15^Oxygen','^18^Fluorine', '^22^Sodium', '^38^Potassium', ...
            '^43^Scandium','^44^Scandium','^45^Titanium','^51^Manganese',...
            '^52^Iron','^52^Manganese','^52m^Manganese','^60^Copper',...
            '^61^Copper','^62^Copper','^62^Zinc','^64^Copper','^66^Gallium',...
            '^68^Gallium','^68^Germanium','^70^Arsenic','^72^Arsenic',...
            '^73^Selenium','^75^Bromine','^76^Bromine','^77^Bromine',...
            '^82^Rubidium','^86^Yttrium','^89^Zirconium','^90^Niobium',...
            '^90^Yttrium','^94m^Technetium','^124^Iodine','^152^Terbium'};
        
        fn = fieldnames(dcminfo);
        for f=1:length(fn)
            if contains(fn{f},'_') && ~contains(fn{f},{'Private','Unknown'})
                if contains(fn{f},'CodeMeaning') % appears in other places so we need to ensure it's for the tracer
                    if contains(dcminfo.(fn{f}),dicom_nucleotides)
                        dcminfo.(fn{f}(max(strfind(fn{f},'_'))+1:end)) = dcminfo.(fn{f});
                    end
                else
                    dcminfo.(fn{f}(max(strfind(fn{f},'_'))+1:end)) = dcminfo.(fn{f});
                end
                dcminfo = rmfield(dcminfo,fn{f});
            elseif isempty(dcminfo.(fn{f}))
                dcminfo = rmfield(dcminfo,fn{f});
            end
        end
        
        % run dicom check check
        jsontoload = fullfile(root,['metadata' filesep 'dicom2bids.json']);
        if exist(jsontoload,'file')
            heuristics = jsondecode(fileread(jsontoload));
            dcmfields  = heuristics.dcmfields;
            jsonfields = heuristics.jsonfields;
        else
            error('looking for %s, but the file is missing',jsontoload)
        end
        
        for f=1:length(dcmfields) % check each field from the library
            if isfield(dcminfo,dcmfields{f}) % if it matches a dicom tag from the image
                if isfield(filemetadata,jsonfields{f}) % and  the json field exist,
                    % then compare and inform the user if different
                    if ~strcmpi(dcminfo.(dcmfields{f}),filemetadata.(jsonfields{f}))
                        if isnumeric(filemetadata.(jsonfields{f}))
                            if isnumeric(dcminfo.(dcmfields{f}))
                                if strcmp(jsonfields{f},'FrameDuration')
                                    if all([single(filemetadata.(jsonfields{f})) ~= single(dcminfo.(dcmfields{f}))/1000 ...
                                            single(filemetadata.(jsonfields{f})) ~= single(dcminfo.(dcmfields{f}))])
                                        warning(['possible mismatch between json ' jsonfields{f} ': ' num2str(filemetadata.(jsonfields{f})') ' and dicom ' dcmfields{f} ': ' num2str(dcminfo.(dcmfields{f}')) '/1000'])
                                    end
                                elseif strcmpi(jsonfields{f},'InjectedRadioactivity')
                                    if filemetadata.(jsonfields{f}) ~= dcminfo.(dcmfields{f})/10^6
                                        warning(['possible mismatch between json ' jsonfields{f} ': ' num2str(filemetadata.(jsonfields{f})) ' and dicom ' dcmfields{f} ':' num2str(dcminfo.(dcmfields{f})) '/10^6'])
                                    end
                                else
                                    if single(filemetadata.(jsonfields{f})) ~= single(dcminfo.(dcmfields{f}))
                                        warning(['possible mismatch between json ' jsonfields{f} ': ' num2str(filemetadata.(jsonfields{f})') ' and dicom ' dcmfields{f} ': ' num2str(dcminfo.(dcmfields{f}'))])
                                    end
                                end
                            else
                                if ischar(dcminfo.(dcmfields{f}))
                                    warning(['possible mismatch between json ' jsonfields{f} ': ' num2str(filemetadata.(jsonfields{f})) ' and dicom ' dcmfields{f} ': ' dcminfo.(dcmfields{f})]) 
                                else
                                    warning(['possible mismatch between json ' jsonfields{f} ': ' num2str(filemetadata.(jsonfields{f})) ' and dicom ' dcmfields{f} ': ' num2str(str2double(dcminfo.(dcmfields{f})))]) % double conversion to remove trailing values
                                end
                            end
                        else
                            if ischar(filemetadata.(jsonfields{f}))
                                if ~strcmp(dcminfo.(dcmfields{f}),'BQML') && ...
                                        ~strcmp(dcmfields{f},'ReconstructionMethod')
                                    warning(['possible mismatch between json ' jsonfields{f} ': ' filemetadata.(jsonfields{f}) ' and dicom ' dcmfields{f} ':' dcminfo.(dcmfields{f})])
                                end
                            else % also char but as array
                                if ~strcmp(dcminfo.(dcmfields{f}),'BQML') && ...
                                        ~strcmp(dcmfields{f},'ReconstructionMethod')
                                    warning(['possible mismatch between json ' jsonfields{f} ': ' char(strjoin(filemetadata.(jsonfields{f}))) ' and dicom ' dcmfields{f} ':' dcminfo.(dcmfields{f})])
                                end
                            end
                        end
                    end
                else % otherwise set the field in the json file
                    if ~any(strcmp(jsonfields{f},{'ReconMethodParameterLabels',...
                            'ReconMethodParameterUnit', 'ReconMethodParameterValues'})) % set by get recon if value exist so do not force
                        if isnumeric(dcminfo.(dcmfields{f}))
                            warning(['adding json info ' jsonfields{f} ': ' num2str(dcminfo.(dcmfields{f})') ' from dicom field ' dcmfields{f}])
                        else
                            if ~strcmpi(dcmfields{f},'AcquisitionDate')
                                warning(['adding json info ' jsonfields{f} ': ' dcminfo.(dcmfields{f}) ' from dicom field ' dcmfields{f}])
                            end
                        end
                        
                        if ~strcmpi(dcmfields{f},'AcquisitionDate')
                            filemetadata.(jsonfields{f}) = dcminfo.(dcmfields{f});
                        end
                    end
                end
            end
        end
        filemetadata = dcm2bids_internal(filemetadata);
    end
    
    % delete all non BIDS fields ++
    % ------------------------------
    all_bids = [petmetadata.mandatory;petmetadata.recommended;petmetadata.optional];
    all_bids{length(all_bids)+1} = 'ScatterCorrectionMethod';
    all_bids{length(all_bids)+1} = 'RandomsCorrectionMethod';
    
    if isfield(filemetadata,'ScanDate')
        try
            if ~ischar(filemetadata.ScanDate)
                filemetadata.ScanDate = datetime(filemetadata.ScanDate,'Format','hh:mm:ss');
                warning('metadata ScanDate is deprecated')
            else
                warning('ScanDate is not converted - no big deal this field is deprecated')
                filemetadata = rmfield(filemetadata,'ScanDate');
            end
        catch err
            warning(err.identifier,'ScanDate is not converted %s - no big deal this field is deprecated',err.message)
            filemetadata = rmfield(filemetadata,'ScanDate');
        end
    end
    
    % fix possible field formatting errors
    if isfield(filemetadata,'ReconFilterSize')
        if ischar(filemetadata.ReconFilterSize)
            filemetadata.ReconFilterSize = str2double(filemetadata.ReconFilterSize);
        end
    end

    if isfield(filemetadata,'ImageDecayCorrected')
        if ischar(filemetadata.ImageDecayCorrected)
            if strcmpi(filemetadata.ImageDecayCorrected,'true')
                filemetadata.ImageDecayCorrected = true; % boolean
            else
                filemetadata.ImageDecayCorrected = false; 
            end
        end
    end
    filemetadata = update_arrays(filemetadata);

    % clean-up
    fn_check = fieldnames(filemetadata);
    for f=1:size(fn_check,1)
        if ~contains(fn_check{f},all_bids) 
            filemetadata = rmfield(filemetadata,fn_check{f});
        end
    end
           
    %% recursive call to check status
    % -----------------------------
    filemetadata.filename = jsonfilename;
    status = updatejsonpetfile(filemetadata);
    if isfield(filemetadata,'ConversionSoftware')
        filemetadata.ConversionSoftware = [filemetadata.ConversionSoftware ' - json edited with ONP updatejsonpetfile.m'];
    end
    filemetadata = orderfields(filemetadata);
    jsonwrite(jsonfilename,filemetadata)
end

function filemetadata = dcm2bids_internal(filemetadata)

% routine to check dcm data compatible for BIDS
% check Unit(s) (depends on dcm2nixx version)

if isfield(filemetadata,'Unit')
    filemetadata.Units = filemetadata.Unit;
    filemetadata       = rmfield(filemetadata,'Unit');
    if strcmpi(filemetadata.Units,'BQML')
        filemetadata.Units = "Bq/mL";
    end
end

% check radiotracer info - should have been done already in
% get_pet_metadata ; but user can also populate metadata by hand
% so let's recheck
radioinputs = {'InjectedRadioactivity', 'InjectedMass', ...
    'SpecificRadioactivity', 'MolarActivity', 'MolecularWeight'};
input_check            = cellfun(@(x) isfield(filemetadata,x), radioinputs);
index                  = 1; % make key-value pairs
arguments              = cell(1,sum(input_check)*2);
if sum(input_check) ~= 0
    for r=find(input_check)
        arguments{index}   = radioinputs{r};
        arguments{index+1} = filemetadata.(radioinputs{r});
        index = index + 2;
    end
    dataout                = check_metaradioinputs(arguments);
    
    if ~isempty(dataout)
        datafieldnames     = fieldnames(dataout);
        % set new info fields
        for f = 1:size(datafieldnames,1)
            if ~isfield(filemetadata,datafieldnames{f})
                filemetadata.(datafieldnames{f}) = dataout.(datafieldnames{f});
            end
        end
    end
end

% check our library from names we know
if isfield(filemetadata,'ReconstructionMethod')
    [filemetadata.ReconMethodName,iteration,subset] = get_recon_method(filemetadata.ReconstructionMethod);
elseif isfield(filemetadata,'ReconMethodName')
    [filemetadata.ReconMethodName,iteration,subset] = get_recon_method(filemetadata.ReconMethodName);
end

if exist('iteration','var') && exist('subset','var')
    if ~isempty(iteration) && ~isempty(subset)
        filemetadata.ReconMethodParameterLabels     = ["subsets","iterations"];
        filemetadata.ReconMethodParameterUnits      = ["none","none"];
        filemetadata.ReconMethodParameterValues     = [str2double(subset),str2double(iteration)];
    else % returns none if actually seen as empty by get_recon_method
        filemetadata.ReconMethodParameterLabels     = "none";  
        filemetadata.ReconMethodParameterUnits      = "none";
        try
            if isempty(filemetadata.ReconMethodParameterValues) % in case user passes info
                filemetadata.ReconMethodParameterValues = 0; % if none should be 0
            end
        catch
            filemetadata.ReconMethodParameterValues = 0;
        end
    end
end

if isfield(filemetadata,'ConvolutionKernel') || ...
        isfield(filemetadata,'ReconFilterType') && isfield(filemetadata,'ReconFilterSize')
    
    if isfield(filemetadata,'ConvolutionKernel')
        if contains(filemetadata.ConvolutionKernel,'/')
            namesplit = strfind(filemetadata.ConvolutionKernel,'/');
            filtername = deblank(filemetadata.ConvolutionKernel(1:namesplit(1)-1));
        elseif contains(filemetadata.ConvolutionKernel,'\')
            namesplit = strfind(filemetadata.ConvolutionKernel,'\');
            filtername = deblank(filemetadata.ConvolutionKernel(1:namesplit(1)-1));
        else
            filtername = filemetadata.ConvolutionKernel;
        end
        
    elseif isfield(filemetadata,'ReconFilterType') && isfield(filemetadata,'ReconFilterSize')
        if strcmp(filemetadata.ReconFilterType,filemetadata.ReconFilterSize)
            filtername = filemetadata.ReconFilterType; %% because if was set matching DICOM and BIDS
            if strcmp(filemetadata.ReconFilterType,"none")
                filemetadata.ReconFilterSize = 0; 
            end
        end
    else
        filemetadata.ReconFilterType = "none";
        filemetadata.ReconFilterSize = 0; % conditional on ReconFilterType 
    end
    
    if exist('filtername','var')
        % known stuff vs regex
        if any(strcmpi(filtername,{'rectangle','hanning'}))
            filemetadata.ReconFilterType = filtername;
            FilterSize = filemetadata.ConvolutionKernel(namesplit(1)+1:namesplit(2)-2);
            if isnan(str2double(FilterSize))
                nums = regexp(FilterSize,'\d*','Match');
                val = cellfun(@(x) eval(x), nums);
                filemetadata.ReconFilterSize = val(val~=0);
            else
                filemetadata.ReconFilterSize = str2double(FilterSize);
            end
        else
            
            % might need to remove trailing .00 for regex to work
            if contains(filtername,'.00') && ~contains(filtername,{'/','\'})
                loc = strfind(filtername,'.00');
                filtername(loc:loc+2) = [];
            end
            
            filtersize = regexp(filtername,'\d*','Match');
            if ~isempty(filtersize)
                filemetadata.ReconFilterSize = cell2mat(filtersize);
                loc = strfind(filtername,filtersize{1});
                filtername(loc:loc+length(filemetadata.ReconFilterSize)-1) = [];
                filemetadata.ReconFilterType = filtername;
            else
                filemetadata.ReconFilterType = filtername;
                filemetadata.ReconFilterSize = 0;
            end
        end
    end
else
    filemetadata.ReconFilterType = "none";
    filemetadata.ReconFilterSize = 0; % conditional on ReconFilterType 
end

function [filemetadata,updated] = update_arrays(filemetadata)
% hack a la Anthony making sure the validator is happy 
% make some scalar an array (i.e. a cell in matlab written as array in json)

updated = 0;
shouldBarray = {'DecayCorrectionFactor','FrameDuration','FrameTimesStart',...
    'ReconFilterSize','ScatterFraction','ReconMethodParameterLabels',...
    'ReconMethodParameterUnits','ReconMethodParameterValues', 'SinglesRate',...
    'RandomRate', "PromptRate", "ScaleFactor"};

for f = 1:length(shouldBarray)
    if isfield(filemetadata,shouldBarray{f})
        if isscalar(filemetadata.(shouldBarray{f}))
            filemetadata.(shouldBarray{f}) = {filemetadata.(shouldBarray{f})};
            updated = 1;
        elseif all(size(filemetadata.(shouldBarray{f})) == 1)
            if any(contains(filemetadata.(shouldBarray{f}),{'none'}))
                filemetadata.(shouldBarray{f}) = {filemetadata.(shouldBarray{f})};
                updated = 1;
            end
        end
    end
end

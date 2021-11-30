function status = updatejsonpetfile(varargin)

% generic function that updates PET json file with missing PET-BIDS
% information, if only the jsonfile is provided, it only checks if valid
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
% jsonfilename = fullfile(pwd,'DBS_Gris_13_FullCT_DBS_Az_2mm_PRR_AC_Images_20151109090448_48.json')
% metadata = get_SiemensBiograph_metadata('TimeZero','ScanStart','tracer','AZ10416936','Radionuclide','C11', ...
%                        'ModeOfAdministration','bolus','Radioactivity', 605.3220,'InjectedMass', 1.5934,'MolarActivity', 107.66)
% dcminfo = dicominfo('DBSGRIS13.PT.PETMR_NRU.48.13.2015.11.11.14.03.16.226.61519201.dcm')
% status = updatejsonpetfile(jsonfilename,metadata,dcminfo)
%
% Cyril Pernet Nov 2021
% ----------------------------------------------
% Copyright Open NeuroPET team

status = struct('state',[],'messages',{''});
status_index = 1;

%% check data in
jsonfilename = varargin{1};
if nargin >= 2
    newfields = varargin{2};
    if nargin == 3
        dcminfo = varargin{3};
    end
end

% current file metadata
if isstruct(jsonfilename)
    filemetadata = jsonfilename;
else
    if exist(jsonfilename,'file')
        filemetadata = jsondecode(fileread(jsonfilename));
        filemetadatafields = fieldnames(filemetadata);
    else
        error('looking for %s, but the file is missing',jsonfilename)
    end
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
        if strcmpi(filemetadata.TimeZero,'ScanStart')
            filemetadata.ScanStart      = 0;            
            filemetadata.InjectionStart = 0;            
        end
    end
  
    % ----------------------------------------
    %         dcm2nixx extracted data update   
    % ----------------------------------------
    
    % check Unit(s) (depends on dcm2nixx version)
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
        
        iterations                   = regexp(filemetadata.ReconMethodName,'\d\di','Match');
        if isempty(iterations)
            iterations               = regexp(filemetadata.ReconMethodName,'\di','Match');
        end
        
        subsets                      = regexp(filemetadata.ReconMethodName,'\d\ds','Match');
        if isempty(subsets)
            subsets                  = regexp(filemetadata.ReconMethodName,'\ds','Match');
        end

        if ~isempty(iterations) && ~isempty(subsets)
            index1 = strfind(filemetadata.ReconMethodName,iterations);
            index2 = index1 + length(cell2mat(iterations))-1;
            filemetadata.ReconMethodName(index1:index2) = [];
            index1 = strfind(filemetadata.ReconMethodName,subsets);
            index2 = index1 + length(cell2mat(subsets ))-1;
            filemetadata.ReconMethodName(index1:index2) = [];
            filemetadata.ReconMethodParameterLabels     = ["subsets","iterations"];
            filemetadata.ReconMethodParameterUnits      = ["none","none"];
            filemetadata.ReconMethodParameterValues     = [str2double(subsets{1}(1:end-1)),str2double(iterations{1}(1:end-1))];
        end
    end
    
    if isfield(filemetadata,'ConvolutionKernel')
        if contains(filemetadata.ConvolutionKernel,'.00')
            loc = strfind(filemetadata.ConvolutionKernel,'.00');
            filemetadata.ConvolutionKernel(loc:loc+2) = [];
            filtersize = regexp(filemetadata.ConvolutionKernel,'\d*','Match');
            if ~isempty(filtersize)
                filemetadata.ReconFilterSize = cell2mat(filtersize);
                loc = strfind(filemetadata.ConvolutionKernel,filtersize{1});
                filemetadata.ConvolutionKernel(loc:loc+length(filemetadata.ReconFilterSize)-1) = [];
                filemetadata.ReconFilterType = filemetadata.ConvolutionKernel;
            else
                filemetadata.ReconFilterType = filemetadata.ConvolutionKernel;
            end
            filemetadata = rmfield(filemetadata,'ConvolutionKernel');
        end
    end    
    
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
    else
        error('%s does not exist',dcminfo)
    end
    
    dcmfields  = {'Manufacturer','ManufacturerModelName' ,'ConvolutionKernel',...
        'R_RadionuclideTotalDose','R_CodeMeaning'   ,'AttenuationCorrectionMethod',...
        'ReconstructionMethod'};
    jsonfields = {'Manufacturer','ManufacturersModelName','ReconFilterType'  ,...
        'InjectedRadioactivity','TracerRadionuclide','AttenuationCorrection',...
        'ReconMethodName'};
    
    for f=1:length(dcmfields)
        if isfield(dcminfo,dcmfields{f})
            if isfield(filemetadata,jsonfields{f})
                if ~strcmpi(dcminfo.(dcmfields{f}),filemetadata.(jsonfields{f}))
                    if isnumeric(filemetadata.(jsonfields{f}))
                        warning(['name mismatch between json ' jsonfields{f} ':' num2str(filemetadata.(jsonfields{f})) ' and dicom ' dcmfields{f} ':' num2str(dcminfo.(dcmfields{f}))])
                    else
                        warning(['name mismatch between json ' jsonfields{f} ':' filemetadata.(jsonfields{f}) ' and dicom ' dcmfields{f} ':' dcminfo.(dcmfields{f})])
                    end
                else
                    filemetadata.(jsonfields{f}) = dcminfo.(dcmfields{f});
                end
            end
        end
    end
        

    %% recursive call to check status
    status = updatejsonpetfile(filemetadata);
    if isfield(filemetadata,'ConversionSoftware')
        filemetadata.ConversionSoftware = [filemetadata.ConversionSoftware ' - json edited with ONP updatejsonpetfile.m'];
    end
    jsonwrite(jsonfilename,filemetadata)
end


function convert_spreadsheet_metadata(varargin)

% routine the converts excel files stored following the metadata_excel_template.xlsx
% (see also metadata_excel_example.xlsx)
%
% FORMAT convert_spreadsheet_metadata(file2convert,outputname)
%
% INPUT file2convert is the .xlsx; .ods; .xls file to convert
%       outputname (optional) is the name of the json file out (with or without full path)
%
% OUTPUT json file for BIDS
%
% Cyril Pernet - NRU

%% PET BIDS parameters
mandatory = {'Manufacturer','ManufacturersModelName','Units','TracerName',...
    'TracerRadionuclide','InjectedRadioactivity','InjectedRadioactivityUnits',...
    'InjectedMass','InjectedMassUnits','SpecificRadioactivity',...
    'SpecificRadioactivityUnits','ModeOfAdministration','TimeZero',...
    'ScanStart','InjectionStart','FrameTimesStart','FrameDuration',...
    'AcquisitionMode','ImageDecayCorrected','ImageDecayCorrectionTime',...
    'ReconMethodName','ReconMethodParameterLabels','ReconMethodParameterUnits',...
    'ReconMethodParameterValues','ReconFilterType','ReconFilterSize','AttenuationCorrection'};

recommended = {'InstitutionName','InstitutionAddress','InstitutionalDepartmentName',...
    'BodyPart','TracerRadLex','TracerSNOMED','TracerMolecularWeight','TracerMolecularWeightUnits',...
    'InjectedMassPerWeight','InjectedMassPerWeightUnits','SpecificRadioactivityMeasTime',...
    'MolarActivity','MolarActivityUnits','MolarActivityMeasTime','InfusionRadioactivity',...
    'InfusionStart','InfusionSpeed','InfusionSpeedUnits','InjectedVolume','DoseCalibrationFactor',...
    'Purity','PharmaceuticalName','PharmaceuticalDoseAmount','PharmaceuticalDoseUnits',...
    'PharmaceuticalDoseRegimen','PharmaceuticalDoseTime','ScanDate','InjectionEnd',...
    'ReconMethodImplementationVersion','AttenuationCorrectionMethodReference','ScaleFactor',...
    'ScatterFraction','DecayCorrectionFactor','PromptRate','RandomRate','SinglesRate'};

optional = {'Anaesthesia'};

%% check library
if ~exist('jsonwrite.m', 'file') 
    error(['JSONio library jsonwrite.m file was not found but is needed,', ...
        ' jsonwrite.m is part of https://github.com/gllmflndn/JSONio but can also be found in the ONP matlab converter folder']);
end
    
%% deal with input file
if nargin == 0
    [filename, pathname] = uigetfile({'*.xlsx;*.ods;*.xls'}, 'Pick an spreadsheet file');
    if isequal(filename, 0) || isequal(pathname, 0)
        disp('Selection cancelled');
        return
    else
        filein = fullfile(pathname, filename);
        disp(['file selected: ', filein]);
    end
else
    if ~exist(varargin{1}, 'file')
        error('%s not found', varargin{1});
    else
        pathname = fileparts(varargin{1});
        filein   = varargin{1};
    end
end

% detect what's inside the selected file
datain = detectImportOptions(filein, 'Sheet', 1);

% check mandatory metadata
for m=1:length(datain.VariableNames)
    testM(m)=any(strcmpi(datain.VariableNames{m},mandatory));
    testR(m)=any(strcmpi(datain.VariableNames{m},recommended));
    testO(m)=any(strcmpi(datain.VariableNames{m},optional));   
end

if sum(testM) ~= length(mandatory)
    error('One or more mandatory name/value pairs are missing')
end

if any(~testR)
    warning('the following recommended information was not provided: %s\n',recommended{~testR})
end

% since mandatory fields are there, load the data and carry on
info = [];
Data = readtable(filein);
for m=1:length(mandatory)
    varlocation = find(strcmpi(mandatory{m},datain.VariableNames));
    info        = getinfo(Data,datain,varlocation,info);
end

for r=1:sum(testR)
    varlocation = find(strcmpi(recommended{r},datain.VariableNames));
    if ~isempty(varlocation)
        info        = getinfo(Data,datain,varlocation,info);
    end
end

for o=1:sum(testO)
    varlocation = find(strcmpi(optional{o},datain.VariableNames));
    if ~isempty(varlocation)
        info        = getinfo(Data,datain,varlocation,info);
    end
end

%% export

if nargin==2
    [newpathname,filename]=fileparts(varargin{2});
    if isempty(newpathname)
        newpathname = pathname;
    end
else
    [~,filename] = fileparts(filename);
end
jsonwrite(fullfile(pathname, [filename '.json']),info,'prettyprint','true');

end


function info = getinfo(Data,datain,varlocation,info)
% get values for a given Variable name and return it formatd inside info

tabledata   = Data.(cell2mat(datain.VariableNames(varlocation)));
if iscell(tabledata) % char
    dataindex = cellfun(@(x) ~isempty(x),Data.(cell2mat(datain.VariableNames(varlocation))));
    if iscell(tabledata(dataindex))
        if sum(dataindex)==1
            info.(cell2mat(datain.VariableNames(varlocation))) = cell2mat(tabledata(dataindex));
        else
            value = find(dataindex);
            for v=1:length(value)
                info.(cell2mat(datain.VariableNames(varlocation))){v} = tabledata{value(v)};
            end
        end
    else
        info.(cell2mat(datain.VariableNames(varlocation))) = tabledata(dataindex);
    end
else % integers
    dataindex = ~isnan(tabledata);
    info.(cell2mat(datain.VariableNames(varlocation))) = tabledata(dataindex)';
end

end

    
function convert_metadata_spreadsheets(varargin)

% routine the converts excel files stored following the scanner_metadata_template.xlsx
% & subjects_metadata_template.xlsx - works creating file for many subjects
% (see also scanner_metadata_example.xlsx & subjects_metadata_example.xlsx) 
%
% :format: convert_metadata_spreadsheets(scanner_metadata_file,subjects_metadata_file,outputname)
%
% :param FileListIn: if no input is provided, a GUI pops up
%       scanner_metadata_file is the .xlsx; .ods; .xls file to convert corresponding to scanner info (same for all subjects)
%       subjects_metadata_file is the .xlsx; .ods; .xls file to convert corresponding to subject info (different for all subjects)
%       outputname (optional) is the name of the json file out (with or without full path)
%
% :returns FileListOut: json files for BIDS
%
% .. note::
%    no specific fields are expected in each spreadsheet, except that
%    together they provide valid BIDS key and values (+ a participant_id - see
%    README.mkd). This means that while the example shows how a single scanner 
%    file is used with a set of parameters, such information could change across 
%    subjects and be moved in the subject spreadsheet.
% 
%    Cyril Pernet - NRU
%    ----------------------------
%    Copyright Open NeuroPET team

%% PET BIDS parameters
current    = which('convert_metadata_spreadsheets.m');
root       = current(1:strfind(current,'converter')+length('converter'));
jsontoload = fullfile(root,['metadata' filesep 'PET_metadata.json']);
if exist(jsontoload,'file')
    petmetadata = jsondecode(fileread(jsontoload));
    mandatory   = petmetadata.mandatory;
    recommended = petmetadata.recommended;
    optional    = petmetadata.optional;
    clear petmetadata
else
    error('looking for %s, but the file is missing',jsontoload)
end

%% check library
if ~exist('jsonwrite.m', 'file') 
    error(['JSONio library jsonwrite.m file was not found but is needed,', ...
        ' jsonwrite.m is part of https://github.com/gllmflndn/JSONio but can also be found in the ONP matlab converter folder']);
end
    
%% deal with input file
if nargin == 0
    [filenames, pathnames] = uigetfile({'*.xlsx;*.ods;*.xls'}, 'Pick the scanner and subjects spreadsheet files (N=2)', 'multiselect','on');
    if isequal(filenames, 0) || isequal(pathnames, 0)
        disp('Selection cancelled');
        return
    else
        if length(filenames) ~= 2
            error('2 files expected but %g selected',length(filenames))
        else
            if ischar(pathnames)
                tmp = pathnames; clear pathnames
                pathnames{1} = tmp; pathnames{2}=tmp; clear tmp
            end
            filein1 = fullfile(pathnames{1}, filenames{1});
            filein2 = fullfile(pathnames{2}, filenames{2});
            fprintf('files selected:\n%s\n%s\n', filein1,filein2);
        end
    end
else
    if ~exist(varargin{1}, 'file')
        error('%s not found', varargin{1});
    else
        filein1 = varargin{1};
    end
    
    if ~exist(varargin{2}, 'file')
        error('%s not found', varargin{2});
    else
        filein2 = varargin{2};
    end
end

% detect what's inside the selected file
datain1 = detectImportOptions(filein1, 'Sheet', 1);
datain2 = detectImportOptions(filein2, 'Sheet', 1);

% check mandatory metadata
testM = NaN(1,length(datain1.VariableNames)+length(datain2.VariableNames));
testR = testM;
testO = testM;

for m=1:length(datain1.VariableNames)
    testM(m)=any(strcmpi(datain1.VariableNames{m},mandatory));
    testR(m)=any(strcmpi(datain1.VariableNames{m},recommended));
    testO(m)=any(strcmpi(datain1.VariableNames{m},optional));   
end

for m=length(datain1.VariableNames)+1:length(testM)
    testM(m)=any(strcmpi(datain2.VariableNames{m-length(datain1.VariableNames)},mandatory));
    testR(m)=any(strcmpi(datain2.VariableNames{m-length(datain1.VariableNames)},recommended));
    testO(m)=any(strcmpi(datain2.VariableNames{m-length(datain1.VariableNames)},optional));   
end

if sum(testM) < length(mandatory) % can be bigger if repeats
    error('One or more mandatory name/value pairs are missing: %s\n',mandatory{~testM})
end

if any(~testR)
    warning('the following recommended information was not provided: %s\n',recommended{~testR})
end

%% since mandatory fields are there, load the data and carry on
% which files contains the subjects information
if any(contains(datain1.SelectedVariableNames,{'participant_id','participant','subject'},'IgnoreCase',true))
    fixed_datain   = datain2;
    fixed_data     = readtable(filein2);
    subject_datain = datain1;
    subject_data   = readtable(filein1);
elseif any(contains(datain2.SelectedVariableNames,{'participant_id','participant','subject'},'IgnoreCase',true))
    fixed_datain   = datain1;
    fixed_data     = readtable(filein1);
    subject_datain = datain2;
    subject_data   = readtable(filein2);
else
    error('no participant key value found in any excel file? check data input')
end
clear datain1 datain2

% fix the time info to the right format
if any(contains(fixed_datain.VariableNames,'TimeZero','IgnoreCase',true))
    fixed_data.TimeZero = datestr(fixed_data.TimeZero,'HH:MM:SS');
elseif any(contains(subject_datain.VariableNames,'TimeZero','IgnoreCase',true))
    subject_data.TimeZero = datestr(subject_data.TimeZero,'HH:MM:SS');
end

% get the fixed info
info = [];
for m=1:length(mandatory)
    varlocation = find(strcmpi(mandatory{m},fixed_datain.VariableNames));
    if ~isempty(varlocation)
        info    = getinfo(fixed_data,fixed_datain,varlocation,info);
    end
end

for r=1:sum(testR)
    varlocation = find(strcmpi(recommended{r},fixed_datain.VariableNames));
    if ~isempty(varlocation)
        info    = getinfo(fixed_data,fixed_datain,varlocation,info);
    end
end

for o=1:sum(testO)
    varlocation = find(strcmpi(optional{o},fixed_datain.VariableNames));
    if ~isempty(varlocation)
        info    = getinfo(fixed_data,fixed_datain,varlocation,info);
    end
end

%% export for each subject
for subject = 1:size(subject_data,1)
    % update info
    subject_info = info;
    for i=1:length(subject_datain.SelectedVariableNames)
        if all(~strcmpi(subject_datain.SelectedVariableNames{i},{'participant_id','participant','subject'}))
            subject_info = getinfo(subject_data,subject_datain,i,subject_info,subject);
        else
            subject_path = subject_data.(cell2mat(subject_datain.SelectedVariableNames(i))){subject};
            subject_name = subject_path(strfind(subject_path,'sub-'):end);
            subject_name = subject_name(1:strfind(subject_name,filesep)-1);
        end
    end
    % write 
    if ~exist(subject_path,'dir')
        mkdir(subject_path)
    end
    subject_info = orderfields(subject_info);
    jsonwrite(fullfile(subject_path, [subject_name '_pet.json']),subject_info,'prettyprint','true');
end

end


function info = getinfo(Data,datain,varlocation,info,subject)
% Data is the table build from reading the spreadsheet
% datain is the object related to spreadsheet 
% varlocation is the column to read in Data
% info a structure to update with values of varlocation
% subject is the row from Data to update info with (if not specified then all rows are returned)

if ~exist('subject','var')
    subject = 0;
end

tabledata   = Data.(cell2mat(datain.VariableNames(varlocation)));
if subject ~= 0
    if isnumeric(tabledata)
        if ~isempty(tabledata(subject,:))
            info.(cell2mat(datain.VariableNames(varlocation))) = tabledata(subject,:);
        end
    elseif iscell(tabledata(subject,:))
        value = tabledata(subject,:);
        if ~isempty(value{1})
            if isfield(info,datain.VariableNames(varlocation))
                fprintf('subject %g, %s overwritten\n',subject,cell2mat(datain.VariableNames(varlocation)))
            end
            
            value = strsplit(value{1},',');
            for v=1:length(value)
                info.(cell2mat(datain.VariableNames(varlocation)))(v) = str2double(cell2mat(value(v)));
            end
        end
    end
else % find all values
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

end

    
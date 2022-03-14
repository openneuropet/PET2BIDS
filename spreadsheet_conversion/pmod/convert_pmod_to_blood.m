function convert_pmod_to_blood(varargin)

% routine the converts bld files (i.e. pmod ready tab or comma separated values)
% works on a subject per subject basis
%
% FORMAT convert_pmod_to_blood(ParentFraction,Plasma2WholebloodRatio,WholebloodActivity,outputname,addjson,'on')
%
% INPUT ParentFraction,Plasma2WholebloodRatio,WholebloodActivity are the pmod files to convert
%       outputname (optional) is the name of the json file out (with or without full path)
%
% OUTPUT tsv files files for BIDS
%        if 'addjson' is on, also create an associated json file
%
% whole blood, whole plasma always and parent often manual (for metabolite)
% Cyril Pernet - NRU

%% PET BIDS parameters
jsoncheck = contains(varargin,'json','IgnoreCase',true);
if any(jsoncheck)
    addjson = varargin{find(jsoncheck)+1};
else
    addjson = 'on';
end

if addjson
    current    = which('convert_pmod_to_blood.m');
    root       = current(1:strfind(current,'converter')+length('converter'));
    jsontoload = fullfile(root,['metadata' filesep 'blood_metadata.json']);
    if exist(jsontoload,'file')
        bloodmetadata = jsondecode(fileread(jsontoload));
        mandatory     = bloodmetadata.mandatory;
        recommended   = bloodmetadata.recommended;
        clear bloodmetadata
    else
        error('looking for %s, but the file is missing',jsontoload)
    end
    
    % check library
    if ~exist('jsonwrite.m', 'file')
        error(['JSONio library jsonwrite.m file was not found but is needed,', ...
            ' jsonwrite.m is part of https://github.com/gllmflndn/JSONio but can also be found in the ONP matlab converter folder']);
    end
end
    
%% deal with input file
if nargin == 0
    [filenames, pathnames] = uigetfile({'*.bld'}, 'Pick the pmod files (N=3)', 'multiselect','on');
    if isequal(filenames, 0) || isequal(pathnames, 0)
        disp('Selection cancelled');
        return
    else
        for i=length(filenames):-1:1
            filein{i} = fullfile(pathnames, filenames{1});
            fprintf('files selected:\n%s\n', filein{i});
        end
    end
else
    for i=nargin:-1:1
        if ~exist(varargin{i}, 'file')
            error('%s not found', varargin{1});
        else
            filein{i} = varargin{1};
        end
    end
end

% detect what's inside the selected file for clean attribution
% assume most users would have used modern excel like, let matlab deal with
% xlm stuff if any using xlsx - default back on text otherwise (it has to
% fail through xlsx because textread always work, even if the contend is
% garbage)

for i=length(filein):-1:1
    movefile(filein1,[filein{i}(1:end-3) 'xlsx']); % fool matlab
    try
        datain{i} = readtable([filein{i}(1:end-3) 'xlsx'],'FileType','spreadsheet','VariableNamingRule','preserve');
        movefile([filein{i}(1:end-3) 'xlsx'],filein{i}); % back to normal
    catch xlsxerr
        movefile([filein{i}(1:end-3) 'xlsx'],[filein{i}(1:end-3) 'tsv']);
        datain{i} = readtable([filein{i}(1:end-3) 'tsv'],'FileType','text','VariableNamingRule','preserve');
        movefile([filein{i}(1:end-3) 'tsv'],filein{i}); % back to normal
    end
end

for i=length(filein):-1:1
    if any(contains(datain{i}.Properties.VariableNames,'parent-fraction','IgnoreCase',true))
        ParentFraction = datain{i};
    elseif any(contains(datain{i}.Properties.VariableNames,'value','IgnoreCase',true))
        Plasma2WholebloodRatio = datain{i}; 
    elseif any(contains(datain{i}.Properties.VariableNames,'whole-blood','IgnoreCase',true))
        WholebloodActivity = datain{i}; 
    end
end
clear filename datain

if any([~exist('ParentFraction','var') ...
        ~exist('Plasma2WholebloodRatio','var') ...
        ~exist('WholebloodActivity','var')])
    error('at least one pmod file did not return expected header')
end
        
% fix the time info to the right format
if any(contains(ParentFraction.Properties.VariableNames,'time[minutes]','IgnoreCase',true))
    ParentFraction.("time[minutes]") = seconds(minutes(ParentFraction.("time[minutes]"))); % transform to seconds
end

if any(contains(Plasma2WholebloodRatio.Properties.VariableNames,'time[minutes]','IgnoreCase',true))
    Plasma2WholebloodRatio.("time[minutes]") = seconds(minutes(Plasma2WholebloodRatio.("time[minutes]"))); 
end

if any(contains(WholebloodActivity.Properties.VariableNames,'time[minutes]','IgnoreCase',true))
    WholebloodActivity.("time[minutes]") = seconds(minutes(WholebloodActivity.("time[minutes]"))); 
end

% make _recording-autosampler_blood.tsv
% any match between WholebloodActivity and the others? if so, should
% reflect the autosampled part
WholebloodActivity.("time[minutes]") ==  Plasma2WholebloodRatio.("time[minutes]")
WholebloodActivity.("time[minutes]") ==  ParentFraction.("time[minutes]")

% make _recording-manual_blood.tsv



function convert_pmod_to_blood(varargin)

% routine the converts bld files (i.e. pmod pkin ready tab or comma separated values)
% this convert data on a subject per subject basis
% !! it supports only file with two columns, not the 'composite' type !!
%
% Background
% PMOD (https://www.pmod.com/web/) PKIN software works with two or three files
% https://www.pmod.com/files/download/v31/doc/pkin/2235.htm 
% WholebloodActivity: overall blood activity 
%      = tracer in the red blood cells and tracer metabolites, moslty in the plasma.
% Plasma: overall plasma activity (tracer and metabolites)
% ParentFraction: free unchanged tracer from plasma (ie 'after' interacting
%                 with tissue) relative to total blood - this is the input to the brain
%
% FORMAT convert_pmod_to_blood(filesin,'type','both','outputname',name,addjson,'off')
%
% INPUT if no input is provided, a GUI pops up
%       filesin a cell array of files e.g. ParentFraction,Wholeblood, Plasma pmod files
%       ParentFraction and Wholeblood files must be present, Plasma is optional
%       'type' should be 'manual' 'autosampler' or 'both' to indicate the way data were collected
%              (file time stamp should be enough to figure out which is which)
%       optional
%       'outputname' for the base name of file(s) to export
%       'addjson' to turn off the creation of the side json file ('on' by default)
%
% OUTPUT tsv files files for BIDS
%        if 'addjson' is 'on' (default), also creates an associated json file
%
% Example: convert_pmod_to_blood(filesin,'type','both','outputname',name,addjson,'off')
%
% Cyril Pernet - NRU

%% PET BIDS parameters
jsoncheck = contains(varargin,'json','IgnoreCase',true);
if any(jsoncheck)
    addjson = varargin{find(jsoncheck)+1};
else
    addjson = 'on';
end

if strcmpi(addjson,'on')
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
        for i = length(filenames):-1:1
            filein{i} = fullfile(pathnames, filenames{i});
            fprintf('files selected:\n%s\n', filein{i});
        end
    end
    
    % 'type' should be 'manual' 'autosampler' or 'both'
    type = questdlg('What type of blood sampling was performed?', ...
        'blood sampling', ...
        'manual', 'autosampler', 'both', 'manual');
    if isempty(type)
        warning('selection aborded - exiting'); return
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
    movefile(filein{i},[filein{i}(1:end-3) 'xlsx']); % fool matlab
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
    if any(contains(datain{i}.Properties.VariableNames,'parent','IgnoreCase',true))
        ParentFraction = datain{i};
    elseif any(contains(datain{i}.Properties.VariableNames,{'whole-blood','whole blood'},'IgnoreCase',true))
        Wholeblood     = datain{i}; 
    elseif any(contains(datain{i}.Properties.VariableNames,'plasma','IgnoreCase',true))
        Plasma         = datain{i}; 
    end
end
clear filename datain

if any([~exist('ParentFraction','var') ...
        ~exist('Wholeblood','var')])
    error('ParentFraction and/or WholebloodActivity files did not load successfully')
end
      
% fix the time info to the right format
if any(contains(Wholeblood.Properties.VariableNames,{'minutes','min'},'IgnoreCase',true))
    varname = Wholeblood.Properties.VariableNames(find(contains(Wholeblood.Properties.VariableNames,{'minutes','min'},'IgnoreCase',true)));
    Wholeblood.(cell2mat(varname)) = seconds(minutes(Wholeblood.(cell2mat(varname)))); % transform to seconds
    WBtime = Wholeblood.(cell2mat(varname));
end

if any(contains(ParentFraction.Properties.VariableNames,{'minutes','min'},'IgnoreCase',true))
    varname = ParentFraction.Properties.VariableNames(find(contains(ParentFraction.Properties.VariableNames,{'minutes','min'},'IgnoreCase',true)));
    ParentFraction.(cell2mat(varname)) = seconds(minutes(ParentFraction.(cell2mat(varname)))); 
    PFtime = Wholeblood.(cell2mat(varname));
end

if exist('Plasma','var')
    if any(contains(Plasma.Properties.VariableNames,{'minutes','min'},'IgnoreCase',true))
        varname = Plasma.Properties.VariableNames(find(contains(Plasma.Properties.VariableNames,{'minutes','min'},'IgnoreCase',true)));
        Plasma.(cell2mat(varname)) = seconds(minutes(Plasma.(cell2mat(varname))));
        Ptime = Wholeblood.(cell2mat(varname));
    end
end

% check time information across files
% if all manaul or autosampler, it make sense to have the same time points 
if ~strcmpi(type,'both') 
    if ~all(PFtime == WBtime)
        error('ParentActivity and Whole blood have different time values - this seems impossible')
    end
    
    if exist('Ptime','var')
        if ~all(Ptime == WBtime)
            error('Whole blood and Plasma have different time values - this seems impossible')
        end
    end
    
    if strmpi(type,'manual')
        if exist('Plasma','var')
            manual = [{'WholeBlood'},{'Parent'},{'Plasma'}];
        else
            manual = [{'WholeBlood'},{'Parent'}];
        end
        autosampler = [];
    else % autosampler
        if exist('Plasma','var')
            autosampler = [{'WholeBlood'},{'Parent'},{'Plasma'}];
        else
            autosampler = [{'WholeBlood'},{'Parent'}];
        end
        manual = [];
    end
    
else % assume the autosampling has more data points
    if length(WBtime) ~= length(PFtime)
        [~,pos] = min(length(WBtime), length(PFtime));
        manual = [{'WholeBlood'},{'Parent'}]; manual = manual(pos);
        autosampler = [{'WholeBlood'},{'Parent'}]; autosampler = autosampler(find([1 2] ~= pos));
         if exist('Ptime','var')
             if strcmpi(autosampler{1},'WholeBlood') && length(Ptime) == length(WBtime) % the most likely case
                 autosampler{2} = 'Plasma';
             elseif strcmpi(manual{1},'WholeBlood') && length(Ptime) == length(WBtime) % does that actually happens?
                 manual{2} = 'Plasma';
             elseif strcmpi(autosampler{1},'Parent') && length(Ptime) == length(PFtime) % does that actually happens?
                 autosampler{2} = 'Plasma';
             elseif strcmpi(manual{1},'Parent') && length(Ptime) == length(PFtime) % autosampler does whole blood only
                 manual{2} = 'Plasma';
             end
         end
    end
end

% make _recording-autosampler_blood.tsv
% make _recording-manual_blood.tsv


%% export

% if nargin==2
%     [newpathname,filename]=fileparts(varargin{2});
%     if isempty(newpathname)
%         newpathname = pathname;
%     end
% else
%     [~,filename] = fileparts(filename);
% end
% jsonwrite(fullfile(pathname, [filename '_pet.json']),info,'prettyprint','true');






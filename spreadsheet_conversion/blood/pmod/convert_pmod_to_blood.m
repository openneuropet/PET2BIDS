function convert_pmod_to_blood(varargin)

% routine the converts bld files (i.e. pmod pkin ready tab or comma separated values)
% this convert data on a subject per subject basis
% !! it supports only file with two columns, not the 'composite' type !!
% !!     column headers as per PMOD recommendation is also expected   !!
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
% :format: - convert_pmod_to_blood(filesin,'type','both',addjson,'off')
%          - convert_pmod_to_blood(filesin,'type','both','outputname','name','jsonkey', 'jsonvalue')
%
% :param FileListIn: if no input is provided, a GUI pops up
%       filesin a cell array of files e.g. ParentFraction,Wholeblood, Plasma pmod files
%       ParentFraction and Wholeblood files must be present, Plasma is optional
%       'type' should be 'manual' 'autosampler' or 'both' to indicate the way data were collected
%              (file time stamp should be enough to figure out which is which)
% :param option: 'outputname' for the base name of file(s) to export
%                'addjson' to turn off the creation of the side json file ('on' by default)
%                any key and value pairs to go in the blood json file
%
% :returns FileListOut: tsv files files for BIDS
%        if 'addjson' is 'on' (default), also creates an associated json file
%
% .. code-block::
%
%    Examples: 
%             file1 = fullfile(fileparts(which('convert_pmod_to_blood.m')),'parent_pmodexample.bld');
%             file2 = fullfile(fileparts(which('convert_pmod_to_blood.m')),'plasma_pmodexample.bld');
%             file3 = fullfile(fileparts(which('convert_pmod_to_blood.m')),'wholeblood_pmodexample.bld');
%             convert_pmod_to_blood(file1,file2,file3,'type','both','outputname','sub01-',...
%                 'MetaboliteMethod','HPLC','MetaboliteRecoveryCorrectionApplied','false',...
%                 'DispersionCorrected','false');
%
%             convert_pmod_to_blood('myfile1.bld','myfile2.bld','type','manual','outputname','sub01-',...
%                 'MetaboliteMethod','HPLC','MetaboliteRecoveryCorrectionApplied','false',...
%                 'DispersionCorrected','false');
%
% .. note::
%
%    Cyril Pernet - NRU
%    ----------------------------
%    Copyright Open NeuroPET team

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
    
    outputname = inputdlg('please input the base name for the files to save');
    if isempty(outputname)
        warning('name aborded - exiting'); return
    else
        outputname = fullfile(pathnames,cell2mat(outputname));
    end
    
else
    for i = 1:3
        if ~strcmpi(varargin{i},'type')
            if ~exist(varargin{i}, 'file')
                error('%s not found', varargin{i});
            else
                filein{i} = varargin{i}; %#ok<AGROW>
            end
        end
    end
    
    for v=1:nargin
        if strcmpi(varargin{v},'outputname')
            outputname = varargin{v+1};
        elseif strcmpi(varargin{v},'type')
            type = varargin{v+1};
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
    catch % xlsxerr
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
elseif any(contains(Wholeblood.Properties.VariableNames,{'seconds','sec'},'IgnoreCase',true))
    varname = Wholeblood.Properties.VariableNames(find(contains(Wholeblood.Properties.VariableNames,{'seconds','sec'},'IgnoreCase',true)));
    WBtime = Wholeblood.(cell2mat(varname));
end

if any(contains(ParentFraction.Properties.VariableNames,{'minutes','min'},'IgnoreCase',true))
    varname = ParentFraction.Properties.VariableNames(find(contains(ParentFraction.Properties.VariableNames,{'minutes','min'},'IgnoreCase',true)));
    ParentFraction.(cell2mat(varname)) = seconds(minutes(ParentFraction.(cell2mat(varname))));
    PFtime = ParentFraction.(cell2mat(varname));
elseif any(contains(ParentFraction.Properties.VariableNames,{'seconds','sec'},'IgnoreCase',true))
    varname = ParentFraction.Properties.VariableNames(find(contains(ParentFraction.Properties.VariableNames,{'seconds','sec'},'IgnoreCase',true)));
    WBtime = ParentFraction.(cell2mat(varname));
end

if exist('Plasma','var')
    if any(contains(Plasma.Properties.VariableNames,{'minutes','min'},'IgnoreCase',true))
        varname = Plasma.Properties.VariableNames(find(contains(Plasma.Properties.VariableNames,{'minutes','min'},'IgnoreCase',true)));
        Plasma.(cell2mat(varname)) = seconds(minutes(Plasma.(cell2mat(varname))));
        Ptime = Plasma.(cell2mat(varname));
    elseif any(contains(Plasma.Properties.VariableNames,{'seconds','sec'},'IgnoreCase',true))
        varname = Plasma.Properties.VariableNames(find(contains(Plasma.Properties.VariableNames,{'seconds','sec'},'IgnoreCase',true)));
        WBtime = Plasma.(cell2mat(varname));
    end
end

% check time information across files
% if all manual or autosampler, it make sense to have the same time points
if ~strcmpi(type,'both')
    if length(PFtime) ~= length(WBtime) || ~all(PFtime == WBtime)
        error('ParentActivity and Whole blood have different time values - this seems impossible')
    end
    
    if exist('Ptime','var')
        if ~all(Ptime == WBtime)
            error('Whole blood and Plasma have different time values - this seems impossible')
        end
    end
    
    if strcmpi(type,'manual')
        if exist('Plasma','var')
            manual = [{'Wholeblood'},{'Parent'},{'Plasma'}];
        else
            manual = [{'Wholeblood'},{'Parent'}];
        end
        autosampler = [];
    else % autosampler
        if exist('Plasma','var')
            autosampler = [{'Wholeblood'},{'Parent'},{'Plasma'}];
        else
            autosampler = [{'Wholeblood'},{'Parent'}];
        end
        manual = [];
    end
    
else % assume the autosampling has more data points
    if length(WBtime) ~= length(PFtime)
        [~,pos] = min([length(WBtime) length(PFtime)]);
        manual = [{'Wholeblood'},{'Parent'}]; manual = manual(pos);
        autosampler = [{'Wholeblood'},{'Parent'}]; autosampler = autosampler(find([1 2] ~= pos));
        if exist('Ptime','var')
            if strcmpi(autosampler{1},'Wholeblood') && length(Ptime) == length(WBtime)
                autosampler{2} = 'Plasma'; % the most likely, plasma and whole blood activity autosampled
            elseif strcmpi(autosampler{1},'Parent') && length(Ptime) == length(PFtime)
            elseif strcmpi(manual{1},'Parent') && length(Ptime) == length(PFtime)
                manual{2} = 'Plasma'; % autosampler does whole blood only
            elseif strcmpi(manual{1},'Wholeblood') && length(Ptime) == length(WBtime)
                error('It is infered autosampled Plasma but manual whole blood activity and ParentFraction, which makes no sense, error importing files')
            end
        end
    else % ParentFraction and WholeBlood have the same number of data point
        error('sampling is supposed to be manual and autosampled but parent and whole blood are identical, hard to figure this out, bids conversion aborded')
    end
end

% make _recording-autosampler_blood.tsv
% make _recording-manual_blood.tsv
disp('exporting to tsv')
if ~exist('outputname','var')
    outputname = fullfile(fileparts(filein{1}),'pmodconverted');
end

whole_blood_radioactivity  = Wholeblood.(Wholeblood.Properties.VariableNames{2});
metabolite_parent_fraction = ParentFraction.(ParentFraction.Properties.VariableNames{2});
if strcmpi(type,'both')
    if strcmpi(manual{1},'Parent')
        time  = ParentFraction.(ParentFraction.Properties.VariableNames{1});
        if length(manual) == 1
            t = table(time,metabolite_parent_fraction,...
                'VariableNames',{'time','metabolite_parent_fraction'});
        else % strcmpi(manual{2},'Plasma')
            plasma_radioactivity = Plasma.(Plasma.Properties.VariableNames{2});
            t = table(time,metabolite_parent_fraction,plasma_radioactivity,...
                'VariableNames',{'time','metabolite_parent_fraction','plasma_radioactivity'});
        end
        tsvname = [outputname '_recording-manual_blood.tsv'];
        writetable(t, tsvname, 'FileType', 'text', 'Delimiter', '\t');
    else % strcmpi(manual{1},'Wholeblood')
        time  = Wholeblood.(Wholeblood.Properties.VariableNames{1});
        if length(manual) == 1
            t = table(time,whole_blood_radioactivity,...
                'VariableNames',{'time','whole_blood_radioactivity'});
        else % strcmpi(manual{2},'Plasma')
            plasma_radioactivity = Plasma.(Plasma.Properties.VariableNames{2});
            t = table(time,whole_blood_radioactivity,plasma_radioactivity,...
                'VariableNames',{'time','whole_blood_radioactivity','plasma_radioactivity'});
        end
        tsvname = [outputname '_recording-manual_blood.tsv'];
        writetable(t, tsvname, 'FileType', 'text', 'Delimiter', '\t');
    end
    
    if strcmpi(autosampler{1},'Parent')
        time  = ParentFraction.(ParentFraction.Properties.VariableNames{1});
        if length(autosampler) == 1
            t = table(time,metabolite_parent_fraction,...
                'VariableNames',{'time','metabolite_parent_fraction'});
        else % strcmpi(autosampler{2},'Plasma')
            plasma_radioactivity = Plasma.(Plasma.Properties.VariableNames{2});
            t = table(time,metabolite_parent_fraction,plasma_radioactivity,...
                'VariableNames',{'time','metabolite_parent_fraction','plasma_radioactivity'});
        end
        tsvname = [outputname '_recording-autosampler_blood.tsv'];
        writetable(t, tsvname, 'FileType', 'text', 'Delimiter', '\t');
    else % strcmpi(autosampler{1},'Wholeblood')
        time  = Wholeblood.(Wholeblood.Properties.VariableNames{1});
        if length(autosampler) == 1
            t = table(time,whole_blood_radioactivity,...
                'VariableNames',{'time','whole_blood_radioactivity'});
        else % strcmpi(autosampler{2},'Plasma')
            plasma_radioactivity = Plasma.(Plasma.Properties.VariableNames{2});
            t = table(time,whole_blood_radioactivity,plasma_radioactivity,...
                'VariableNames',{'time','whole_blood_radioactivity','plasma_radioactivity'});
        end
        tsvname = [outputname '_recording-autosampler_blood.tsv'];
        writetable(t, tsvname, 'FileType', 'text', 'Delimiter', '\t');
    end
    
else
    time  = Wholeblood.(Wholeblood.Properties.VariableNames{1});
    if exist('Plasma','var')
        plasma_radioactivity = Plasma.(Plasma.Properties.VariableNames{2});
        t = table(time,whole_blood_radioactivity,metabolite_parent_fraction,plasma_radioactivity,...
            'VariableNames',{'time','whole_blood_radioactivity','metabolite_parent_fraction','plasma_radioactivity'});
    else
        t = table(time,whole_blood_radioactivity,metabolite_parent_fraction,...
            'VariableNames',{'time','whole_blood_radioactivity','metabolite_parent_fraction'});
    end
    tsvname = [outputname '_recording-' type '_blood.tsv'];
    writetable(t, tsvname, 'FileType', 'text', 'Delimiter', '\t');
end
        
%% export json

if strcmpi(addjson,'on')
    
    for v=1:nargin % since we have Parent those should be there
        if strcmpi(varargin{v},'MetaboliteMethod')
            MetaboliteMethod = varargin{v+1};
        elseif strcmpi(varargin{v},'MetaboliteRecoveryCorrectionApplied')
            MetaboliteRecoveryCorrectionApplied = varargin{v+1};
        elseif strcmpi(varargin{v},'DispersionCorrected')
            DispersionCorrected = varargin{v+1};
        end
    end
    
    info.WholeBloodAvail = "true"; % the function would have not run otherwise
    info.MetaboliteAvail = 'true';
    if exist('MetaboliteMethod','var')
        info.MetaboliteMethod = MetaboliteMethod;
    else
        warning('Parent fraction is available, but input method is not specified, which is not BIDS compliant')
    end
    
    if exist('MetaboliteRecoveryCorrectionApplied','var')
        info.MetaboliteRecoveryCorrectionApplied = MetaboliteRecoveryCorrectionApplied;
    else
        warning('Parent fraction is available, but there is no information if Recovery Correction was applied, which is not BIDS compliant')
    end
       
    if exist('DispersionCorrected','var')
        info.DispersionCorrected = DispersionCorrected;
    else
        warning('Parent fraction is available, but there is no information if DispersionCorrected was applied, which is not BIDS compliant')
    end
    
    info.time.Description                       = 'Time in relation to time zero defined by the _pet.json';
    info.time.Units                             = 's';
    info.whole_blood_radioactivity.Description  = 'Radioactivity in whole blood samples. Measured using COBRA counter.';
    info.whole_blood_radioactivity.Units        = 'kBq/mL';
    info.metabolite_parent_fraction.Description = 'Parent fraction of the radiotracer';
    info.metabolite_parent_fraction.Units       = 'arbitrary';
    if exist('Plasma','var')
        info.PlasmaAvail                        = 'true';
        info.plasma_radioactivity.Description   = 'Radioactivity in plasma samples';
        info.plasma_radioactivity.Units         = 'kBq/mL';
    end
    
    for v=1:nargin 
        if any(strcmpi(varargin{v},recommended))
            index = find(strcmpi(varargin{v},recommended));
            info.(recommended{index}) = varargin{v+1}; %#ok<FNDSB>
        end
    end
    
    if ~strcmpi(type,'both')
       jsonname = [outputname '_recording-' type '_blood.json'];
    else
       jsonname = [outputname '_blood.json'];
    end
    jsonwrite(jsonname,info,'prettyprint','true');
   
    % run a last check
    for f=length(mandatory):-1:1
        M(f) = any(contains(mandatory{f}, fieldnames(info)));
    end
    if sum(M) ~= length(mandatory)
        index = find(M==0);
        for m=1:length(index)
            if iscell(mandatory{index(m)})
                tmp = mandatory{index(m)};
                for t=1:length(tmp)
                    warning('missing %s',tmp{t})
                end
            else
                warning('missing %s',mandatory{index(m)})
            end
        end
        warning('the json file created is NOT BIDS compliant, mandatory fields are missing')
    end
end



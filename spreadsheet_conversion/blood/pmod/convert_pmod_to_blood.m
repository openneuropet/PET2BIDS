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
%      = tracer in the red blood cells and tracer metabolites, mostly in the plasma.
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
    [filenames, pathnames] = uigetfile({'*.bld','speadsheet';'*.txt','text'}, 'Pick the pmod files (N=2 or 3)', 'multiselect','on');
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
        warning('selection aborted - exiting'); return
    end
    
    outputname = inputdlg('please input the base name for the files to save');
    if isempty(outputname)
        warning('name aborted - exiting'); return
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
    if strcmpi(filein{i}(end-3:end),'.txt')
        movefile(filein{i},[filein{i}(1:end-3) 'tsv']);
        datain{i} = readtable([filein{i}(1:end-3) 'tsv'],'FileType','text','VariableNamingRule','preserve');
        movefile([filein{i}(1:end-3) 'tsv'],filein{i}); % back to normal
    else
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
end

for i=length(filein):-1:1
    if any(contains(datain{i}.Properties.VariableNames,'value','IgnoreCase',true))
        [~,name] = fileparts(filein{i});
        warning('no variable name in %s, inferring from file name',name)
        if any(contains(name,'Fraction','IgnoreCase',true))
            ParentFraction = datain{i};
        elseif any(contains(name,'Whole','IgnoreCase',true)) && ...
                ~contains(name,'Plasma','IgnoreCase',true)
            Wholeblood     = datain{i};
        elseif any(contains(name,'Plasma','IgnoreCase',true))
            Plasma         = datain{i};
            if contains(name,'Whole','IgnoreCase',true) && contains(name,'Ratio','IgnoreCase',true) && ...
                any(Plasma.(Plasma.Properties.VariableNames{2}) < 1)
                warning('Plasma values seem to be ratio to whole blood data are being converted, check the tsv file')
                multiplyplasma = true;
            else
                multiplyplasma = false;
            end
        end
    else
        if any(contains(datain{i}.Properties.VariableNames,'parent','IgnoreCase',true))
            ParentFraction = datain{i};
        elseif any(contains(datain{i}.Properties.VariableNames,{'whole-blood','whole blood'},'IgnoreCase',true))
            Wholeblood     = datain{i};
        elseif any(contains(datain{i}.Properties.VariableNames,'plasma','IgnoreCase',true))
            Plasma         = datain{i};
        end
    end
end
clear filename datain

if ~exist('Wholeblood','var')
    error('WholebloodActivity file missing / not recognized')
end

% dirty check of parent variable
if any(ParentFraction.(ParentFraction.Properties.VariableNames{2}) > 1) && ...
        ~exist('Plasma','var')
    warning('Parent fraction seen as > 1 ?? assuming this is plasma')
    Plasma = ParentFraction;
    clear ParentFraction
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

if exist('ParentFraction','var')
    if any(contains(ParentFraction.Properties.VariableNames,{'minutes','min'},'IgnoreCase',true))
        varname = ParentFraction.Properties.VariableNames(find(contains(ParentFraction.Properties.VariableNames,{'minutes','min'},'IgnoreCase',true)));
        ParentFraction.(cell2mat(varname)) = seconds(minutes(ParentFraction.(cell2mat(varname))));
        PFtime = ParentFraction.(cell2mat(varname));
    elseif any(contains(ParentFraction.Properties.VariableNames,{'seconds','sec'},'IgnoreCase',true))
        varname = ParentFraction.Properties.VariableNames(find(contains(ParentFraction.Properties.VariableNames,{'seconds','sec'},'IgnoreCase',true)));
        PFtime = ParentFraction.(cell2mat(varname));
    end
end

if exist('Plasma','var')
    if any(contains(Plasma.Properties.VariableNames,{'minutes','min'},'IgnoreCase',true))
        varname = Plasma.Properties.VariableNames(find(contains(Plasma.Properties.VariableNames,{'minutes','min'},'IgnoreCase',true)));
        Plasma.(cell2mat(varname)) = seconds(minutes(Plasma.(cell2mat(varname))));
        Ptime = Plasma.(cell2mat(varname));
    elseif any(contains(Plasma.Properties.VariableNames,{'seconds','sec'},'IgnoreCase',true))
        varname = Plasma.Properties.VariableNames(find(contains(Plasma.Properties.VariableNames,{'seconds','sec'},'IgnoreCase',true)));
        Ptime = Plasma.(cell2mat(varname));
    end
end

% check time information across files
% if all manual or autosampler, it make sense to have the same time points
if ~strcmpi(type,'both')
    if exist('PFtime','var')
        if length(PFtime) ~= length(WBtime) || ~all(PFtime == WBtime)
            error('ParentActivity and Whole blood have different time values - this seems impossible')
        end
    end

    if exist('Ptime','var')
        if ~all(Ptime == WBtime)
            error('Whole blood and Plasma have different time values - this seems impossible')
        end
    end

    if strcmpi(type,'autosampler')
        if exist('Plasma','var') || exist('Parent','var')
            error('sorry, the function does not expect to see plasma or parent fraction from autosampling')
       end
    end

else % mixed case - assume the autosampling has more data points
    % possible that pmod exported file mixing time info
    % we simply clean up the data
    if length(WBtime) == length(Ptime) && exist('PFtime','var')
        warning('time data between whole blood and plasma are mixed, trying to fix it based on parent fraction - do check tsv files')
        duplicates = arrayfun(@(x) find(WBtime == x), PFtime);
        if ~isempty(duplicates)
            Ptime                     = Ptime(duplicates);  
            notduplicates             = 1:length(WBtime);
            notduplicates(duplicates) = [];
            WBtime                    = WBtime(notduplicates);
        end
    elseif length(WBtime) > length(Ptime) && exist('PFtime','var')
        warning('time data between whole blood and plasma are mixed, trying to fix it based on parent fraction - do check tsv files')
        if length(Ptime) ~= length(PFtime)
            if PFtime(1) == WBtime(1) && PFtime(1) == 0
                Ptime = [0;Ptime];                 
            else
                error('Parent fraction and Plasma times do not match, we cannot figure out which time points to extract in whole blood')
            end
        end
        
        duplicates = arrayfun(@(x) find(WBtime == x), PFtime, 'UniformOutput', false);
        if ~isempty(duplicates)
            emptyduplicates = find(cellfun(@(x) isempty(x),duplicates)); 
            if ~isempty(emptyduplicates)
                % strategy 1, is the missing index between two adjacent
                % integer, if so just used the value e.g. 183, [], 185
                for e=1:length(emptyduplicates)
                    position = emptyduplicates(e);
                    if position > 1 || position < length(duplicates)
                        if duplicates{position-1}+2 == duplicates{position+1}
                            duplicates{position} = duplicates{position-1}+1;
                        end
                    end
                end
            end

           emptyduplicates = find(cellfun(@(x) isempty(x),duplicates)); 
           if ~isempty(emptyduplicates)
               % strategy 2, try figuring out the closest time
                warning('whole blood times do not match perfectly parent fraction times - using closest match')
                missingtimes = PFtime(emptyduplicates);
                for m=1:length(missingtimes)
                    timevalue = min(WBtime((WBtime - missingtimes(m))>=0));
                    duplicates{emptyduplicates(m)} = find(WBtime == timevalue);
                end
            end
         
            if iscell(duplicates)
                duplicates = cell2mat(duplicates);
            end
            notduplicates             = 1:length(WBtime);
            notduplicates(duplicates) = [];
            WBtime                    = WBtime(notduplicates);
        end
    else
        duplicates = [];
    end
end

% make _recording-autosampler_blood.tsv
% make _recording-manual_blood.tsv
disp('exporting to tsv')
if ~exist('outputname','var')
    outputname = fullfile(fileparts(filein{1}),'pmodconverted');
end

whole_blood_radioactivity  = Wholeblood.(Wholeblood.Properties.VariableNames{2});

if exist('ParentFraction','var')
    metabolite_parent_fraction = ParentFraction.(ParentFraction.Properties.VariableNames{2});
end

if exist('ParentFraction','var')
    plasma_radioactivity = Plasma.(Plasma.Properties.VariableNames{2});
    % Ptime adjusted adding time 0, therefore adjust data as well
    if exist('metabolite_parent_fraction','var')
        if Ptime(1) == 0 && length(plasma_radioactivity) == length(metabolite_parent_fraction)-1
            plasma_radioactivity = [0;plasma_radioactivity];
        end
    end
    % Turns out we have a ratio rather the actual concentration so remultiply
    if multiplyplasma
        if ~isempty(duplicates)
            plasma_radioactivity = plasma_radioactivity.*whole_blood_radioactivity(duplicates);
        else
            plasma_radioactivity = plasma_radioactivity.*whole_blood_radioactivity;
        end
    end
end

if strcmpi(type,'both')
    if exist('PFtime','var')
        if ~isempty(duplicates)
            if length(plasma_radioactivity) == length(PFtime)
                t = table(PFtime,whole_blood_radioactivity(duplicates),plasma_radioactivity,...
                    metabolite_parent_fraction,'VariableNames',{'time','whole_blood_radioactivity',...
                    'plasma_radioactivity','metabolite_parent_fraction'});
            else
                t = table(PFtime,whole_blood_radioactivity(duplicates),plasma_radioactivity(duplicates),...
                    metabolite_parent_fraction,'VariableNames',{'time','whole_blood_radioactivity',...
                    'plasma_radioactivity','metabolite_parent_fraction'});
            end
        else
            t = table(PFtime,whole_blood_radioactivity,plasma_radioactivity,...
                metabolite_parent_fraction,'VariableNames',{'time','whole_blood_radioactivity',...
                'plasma_radioactivity','metabolite_parent_fraction'});
        end
    else
        t = table(WBtime,whole_blood_radioactivity,plasma_radioactivity,...
            'VariableNames',{'time','whole_blood_radioactivity','plasma_radioactivity'});
    end
    tsvname = [outputname '_recording-manual_blood.tsv'];
    writetable(t, tsvname, 'FileType', 'text', 'Delimiter', '\t');

    if exist('notduplicates','var')
        t = table(WBtime,whole_blood_radioactivity(notduplicates),...
            'VariableNames',{'time','whole_blood_radioactivity'});
    else
        t = table(WBtime,whole_blood_radioactivity,...
            'VariableNames',{'time','whole_blood_radioactivity'});
    end
    tsvname = [outputname '_recording-autosampler_blood.tsv'];
    writetable(t, tsvname, 'FileType', 'text', 'Delimiter', '\t');

else
    time  = Wholeblood.(Wholeblood.Properties.VariableNames{1});
    if exist('Plasma','var')
        plasma_radioactivity = Plasma.(Plasma.Properties.VariableNames{2});
        if exist('metabolite_parent_fraction','var')
            t = table(time,whole_blood_radioactivity,plasma_radioactivity,metabolite_parent_fraction,...
                'VariableNames',{'time','whole_blood_radioactivity','plasma_radioactivity','metabolite_parent_fraction'});
        else
            t = table(time,whole_blood_radioactivity,plasma_radioactivity,...
                'VariableNames',{'time','whole_blood_radioactivity','plasma_radioactivity'});
        end
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
    info.whole_blood_radioactivity.Description  = 'Radioactivity in whole blood samples.';
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



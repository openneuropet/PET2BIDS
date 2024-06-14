function metadata = get_pet_metadata(varargin)
% Routine that outputs PET scanner metadata following
% `BIDS <https://bids.neuroimaging.io/ BIDS>`_.
%
% The metadata generated here are passed along imaging data to the
% converters, ecat2nii.m or dcm2niix4pet.m allowing to produce a .nii
% file with a BIDS compliant json file.
%
% :param Default:  \(acquisition and reconstruction parameters\) can be
%    stored in a \*_parameters.txt seating on disk next to this function
%    or passed as argument in. Replace \* by the name of your scanner \- for now we
%    tested 'SiemensBiograph', 'SiemensHRRT', 'GEAdvance', 'PhillipsVereos',
%    'PhillipsIngenuityPETMR','PhillipsIngenuityPETCT'.
%    \(see templates, as some info can be recovered from ecat or dcm - ie not
%    all info is necessarily needed\)
% :param inputs: a series of key/value pairs are expected
% :returns metadata: a structure with BIDS fields filled \(such structure is ready
%   to be written as json file using e.g. the bids matlab jsonwrite
%   function, typically associated with the \*_pet.nii file\)
%
% :format:  metadata = get_pet_metadata(key,value)
%
% .. note::
%
%  Mandatory inputs are as follows\:
%
%   - *Scanner* name of scanner, map to a \*parameters.txt file  e.g. 'Scanner', 'SiemensBiograph'
%   - *TimeZero* when was the tracer injected                   e.g. 'TimeZero','11:05:01'
%   - *ModeOfAdministration*                                    e.g. 'ModeOfAdministration', 'bolus'
%   - *TracerName* which tracer was used                        e.g. 'TracerName','DASB'
%   - *TracerRadionuclide* which nuclide was used               e.g. 'TracerRadionuclide','C11'
%
%    **\+ at least 2 of those key/value arguments to infer others:**
%
%   - *InjectedRadioactivity* value in MBq                      e.g. 'InjectedRadioactivity', 605.3220
%   - *InjectedMass* Value in ug                                e.g. 'InjectedMass', 1.5934
%   - *MolarActivity* value in GBq/umol                         e.g. 'MolarActivity', 107.66
%   - *MolecularWeight* value in g/mol                          e.g. 'MolecularWeight', 15.02
%   - *SpecificRadioactivity* in Bq/g or Bq/mol                 e.g. 'SpecificRadioactivity', 3.7989e+14
%
% Here is an example of such defaults, used at NRU for our SiemensBiograph_parameters.txt
%
% .. code-block::
%
%    InstitutionName            = 'Rigshospitalet, NRU, DK';
%    BodyPart                   = 'Phantom';
%    AcquisitionMode            = 'list mode';
%    ImageDecayCorrected        = 'true';
%    ImageDecayCorrectionTime   = 0;
%    ReconFilterType            = 'none';
%    ReconFilterSize            = 0;
%    AttenuationCorrection      = '10-min transmission scan';
%    FrameDuration              = 1200;
%    FrameTimesStart            = 0;
%
% .. note::
%   TimeZero also can be [] or 'ScanStart' indicating that the scanning time
%   should be used as TimeZero. If TimeZero is not the scan time, we strongly
%   advice to input ScanStart and InjectionStart making sure timing is correct
%
% .. note::
%   OPTIONAL INPUTS ARE ALL OTHER BIDS FIELDS
%
% Example
%
% .. code-block::
%
%   meta = get_pet_metadata('Scanner','SiemensBiograph','TimeZero','ScanStart',...
%                         'TracerName','CB36','TracerRadionuclide','C11', ...
%                         'ModeOfAdministration','infusion','SpecificRadioactivity', ...
%                          605.3220,'InjectedMass', 1.5934,'MolarActivity', 107.66);
%         --> will issue warnings without a SiemensBiographparameters.txt next to this function
%
%   meta = get_pet_metadata('Scanner','SiemensBiograph','TimeZero','ScanStart',...
%             'TracerName','CB36','TracerRadionuclide','C11', 'ModeOfAdministration',...
%             'infusion','SpecificRadioactivity', 605.3220,'InjectedMass', 1.5934,...
%             'MolarActivity', 107.66, 'InstitutionName','Rigshospitalet, NRU, DK',...
%             'AcquisitionMode','list mode','ImageDecayCorrected','true',...
%             'ImageDecayCorrectionTime' ,0,'ReconMethodName','OP-OSEM',...
%             'ReconMethodParameterLabels',{'subsets','iterations'},...
%             'ReconMethodParameterUnits',{'none','none'}, ...
%             'ReconMethodParameterValues',[21 3], 'ReconFilterType','XYZGAUSSIAN',...
%             'ReconFilterSize',2, 'AttenuationCorrection','MR-based attenuation correction');
%        --> works without txt file because all arguments are passed
%
% | *Neurobiology Research Unit, Rigshospitalet*
% | *Martin Nørgaard & Cyril Pernet - 2021*
% | *Copyright Open NeuroPET team*

% defaults are loaded via the *_parameters.txt file

%% check inputs

if nargin == 0
    help get_pet_metadata
    return
else
    for n=1:2:nargin % check the mandatory variables
        if strcmpi(varargin{n},'Scanner')
            Scanner = varargin{n+1};
        elseif any(strcmpi(varargin{n},{'TimeZero','Time Zero'}))
            TimeZero = varargin{n+1};
        elseif strcmpi(varargin{n},'TracerName')
            TracerName = varargin{n+1};
        elseif strcmpi(varargin{n},'TracerRadionuclide')
            TracerRadionuclide = varargin{n+1};
        elseif contains(varargin{n},'Administration','IgnoreCase',true)
            ModeOfAdministration = varargin{n+1};
        elseif contains(varargin{n},{'InjectedRadioactivity','Injected Radioactivity'},'IgnoreCase',true)
            if contains(varargin{n},{'Units','Unit'},'IgnoreCase',true)
                warning('Argument InjectedRadioactivityUnits is ignored, BIDS indicates it must be in MBq');
            else
                InjectedRadioactivity = varargin{n+1};
            end
        elseif contains(varargin{n},{'SpecificRadioactivity','Specific Radioactivity'},'IgnoreCase',true)
            if contains(varargin{n},{'Units','Unit'},'IgnoreCase',true)
                warning('Argument SpecificRadioactivityUnits is ignored, BIDS indicates it must be in Bq/g or MBq/ug');
            else
                SpecificRadioactivity = varargin{n+1};
            end
        elseif contains(varargin{n},'Mass','IgnoreCase',true)
            if contains(varargin{n},{'Units','Unit'},'IgnoreCase',true)
                warning('Argument InjectedMassUnits is ignored, BIDS indicates it must be in ug');
            else
                InjectedMass = varargin{n+1};
            end
        elseif any(strcmpi(varargin{n},{'MolarActivity','Molar Activity'}))
            if contains(varargin{n},{'Units','Unit'},'IgnoreCase',true)
                warning('Argument MolarActivityUnits is ignored, BIDS indicates it must be in GBq/umolug');
            else
                MolarActivity = varargin{n+1};
            end
        elseif contains(varargin{n},'Weight','IgnoreCase',true)
            if contains(varargin{n},{'Units','Unit'},'IgnoreCase',true)
                warning('Argument MolecularWeightUnits is ignored, BIDS indicates it must be in g/mol');
            else
                MolecularWeight = varargin{n+1};
            end
        end
    end
    
    % check input values and consistency given expected units in
    % -----------------------------------------------------------
    mandatory = {'Scanner','TimeZero','TracerName','ModeOfAdministration','TracerRadionuclide'};
    radioinputs = {'InjectedRadioactivity', 'InjectedMass', ...
        'SpecificRadioactivity', 'MolarActivity', 'MolecularWeight'};
    input_check = cellfun(@exist,radioinputs);
    if isempty(input_check) || sum(input_check)==0
        error('radioactivity related input are necessary - see help')
    end
    
    index = 1; % make key-value pairs
    arguments   = cell(1,sum(input_check)*2);
    for r=find(input_check)
        arguments{index}   = radioinputs{r};
        arguments{index+1} = eval(radioinputs{r});
        index = index + 2;
    end
    dataout  = check_metaradioinputs(arguments);
    if isempty(dataout)
        error('there are not enough radioactivity related inputs to make sense of the data - see help')
    end
    
    % set old and new variables in memory
    setval   = fieldnames(dataout) ; 
    for f = 1:2:length(arguments) % dataout might not include all arguments in
        if ~any(strcmpi(arguments{f},setval))
            setval(length(setval)+1) = arguments(f);
        end
    end
    
    for r=1:length(setval)
        mandatory{length(mandatory)+1} = setval{r}; % add to mandatory list
        if isfield(dataout,setval{r})
            if isnumeric(dataout.(setval{r}))
                eval([setval{r} '=' num2str(dataout.(setval{r}))]);
            else
                eval([setval{r} '=''' dataout.(setval{r}) '''']);
            end
        end
    end
    
    % check mandatory/optional fields of this function
    % (same fields but different status as BIDS)
    if ~all(cellfun(@exist, mandatory))
        error('One or more mandatory name/value pairs is missing: %s\n',mandatory{find(cellfun(@exist, mandatory)==0)})
    end
    
    current    = which('get_pet_metadata.m');
    root       = fileparts(fileparts(current));
    jsontoload = fullfile(root,['metadata' filesep 'PET_metadata.json']);
    if exist(jsontoload,'file')
        petmetadata = jsondecode(fileread(jsontoload));
        optional    = [petmetadata.mandatory' petmetadata.recommended' petmetadata.optional']';
        for f=2:length(mandatory) % start at 2 (1 is Scanner)
            remove = find(cellfun(@(x) strcmpi(x, mandatory{f}),optional));
            if ~isempty(remove)
               optional(remove) = [];
            end
        end
    else
        error('looking for %s, but the file is missing',jsontoload)
    end
    
    % evaluate key-value pairs for optional arguments in
    for n=1:2:nargin 
        if any(strcmpi(varargin{n},optional))
            if isnumeric(varargin{n+1})
                if length(varargin{n+1}) == 1 
                    eval([varargin{n} '=' num2str(varargin{n+1})]);
                else 
                    eval([varargin{n} '=[' num2str(varargin{n+1}) ']']);
                end
            else
                if iscell(varargin{n+1})
                    frameval = [varargin{n} '={']; 
                    for f=1:length(varargin{n+1})
                        frameval = [frameval '''' varargin{n+1}{f} ''' ']; %#ok<AGROW>
                    end
                    eval([frameval(1:end-1) '}']);
                else
                    eval([varargin{n} '=''' varargin{n+1} '''']);
                end
            end
        end
    end
     
    % evaluate key-value pairs for optional arguments from txt file
    parameter_file = fullfile(fileparts(which('get_pet_metadata.m')),[Scanner 'parameters.txt']);
    if any(cellfun(@exist, optional))
        if exist(parameter_file,'file')
            setmetadata = importdata(parameter_file);
            for opt = 1:length(setmetadata)
                if contains(setmetadata{opt},'=')
                    try
                        eval(setmetadata{opt}); % should evaluate the = sign, creating name/value pairs
                        if isempty(setmetadata{opt})
                            error('''%s'' from %sparameters.txt is empty\n',optional{opt},Scanner)
                        end
                    catch evalerr
                        error('''%s'' from %sparameters.txt is empty\n',setmetadata{opt},Scanner) % --> error for optional inputs
                    end
                end
            end
        else
            T = table({'InstitutionName            = '''';',...
                'AcquisitionMode            = '''';',...
                'ImageDecayCorrected        = ;',...
                'ImageDecayCorrectionTime   = ;',...
                'ReconMethodName            = '''';',...
                'ReconMethodParameterLabels = {'''',''''};',...
                'ReconMethodParameterUnits  = {'''',''''};',...
                'ReconMethodParameterValues = [ , ];',...
                'ReconFilterType            = '''';',...
                'ReconFilterSize            = ;',...
                'AttenuationCorrection      = '''';',...
                'FrameDuration              = [ , ];',...
                'FrameTimesStart            = [ , ];'}',...
                'VariableNames',{'# Defaults'});
            writetable(T,parameter_file);
            error([Scanner 'parameters.txt to load default parameters is missing - a template file has been created, please fill missing information, or pass them as arguments in'])
        end
    end
end

%% make the metadata structure

% this part is not really useful for BIDS, but helps users know which
% scanner we tested -- 
if contains(Scanner,'Siemens','IgnoreCase',true)
    metadata.Manufacturer = 'Siemens';
    if contains(Scanner,'Biograph','IgnoreCase',true)
        metadata.ManufacturersModelName = 'Biograph mMR';
    elseif contains(Scanner,'HRRT','IgnoreCase',true)
        metadata.ManufacturersModelName = 'High-Resolution Research Tomograph (HRRT, CTI/Siemens)';
    else
        loc = find([strfind(Scanner,{'Siemens'}) strfind(Scanner,{'siemens'})]);
        Scanner(loc:loc+length('Siemens')-1) = [];
        metadata.ManufacturersModelName = Scanner;
        warning('while the conversion code should run, the manufacturer model is not supported (ie dcm check uncertain) - contact us and we will fix it for you')
    end
elseif contains(Scanner,'GE','IgnoreCase',true)
    metadata.Manufacturer = 'General Electric';
    if contains(Scanner,'Advance','IgnoreCase',true)
        metadata.ManufacturersModelName = 'Advance';
    elseif contains(Scanner,'Discovery','IgnoreCase',true)
        metadata.ManufacturersModelName = 'Discovery PET/CT';
    elseif contains(Scanner,'Signa','IgnoreCase',true)
        metadata.ManufacturersModelName = 'Signa PET/MR';
    else
        loc = find([strfind(Scanner,{'GE'}) strfind(Scanner,{'ge'})]);
        Scanner(loc:loc+length('GE')-1) = [];
        metadata.ManufacturersModelName = Scanner;
        warning('while the conversion code should run, the manufacturer model is not supported (ie dcm check uncertain) - contact us and we will fix it for you')
    end
elseif contains(Scanner,'Philips','IgnoreCase',true)
    metadata.Manufacturer = 'Philips Medical Systems';
    if contains(Scanner,'Vereos','IgnoreCase',true)
        metadata.ManufacturersModelName = 'Vereos PET/CT';
    elseif contains(Scanner,'Ingenuity','IgnoreCase',true)
        if contains(Scanner,'CT','IgnoreCase',true)
            metadata.ManufacturersModelName = 'Ingenuity TF PET/CT';
        elseif contains(Scanner,'MR','IgnoreCase',true)
            metadata.ManufacturersModelName = 'Ingenuity TF PET/MR';
        else
            metadata.ManufacturersModelName = 'Ingenuity';
        end
    elseif contains(Scanner,'Gemini','IgnoreCase',true)
        metadata.ManufacturersModelName = 'Gemini PET/MR';
    else
        loc = find([strfind(Scanner,{'Philips'}) strfind(Scanner,{'philips'})]);
        Scanner(loc:loc+length('Philips')-1) = [];
        metadata.ManufacturersModelName = Scanner;
        warning('while the conversion code should run, the manufacturer model is not supported (ie dcm check uncertain) - contact us and we will fix it for you')
    end
else
    error('the Scanner input does not include Siemens, GE or Philips, unknown/unsupported make')
end

metadata.Units                          = 'Bq/mL';
metadata.BodyPart                       = 'Brain';
if isempty(TimeZero)
    metadata.TimeZero                   = [];
elseif strcmpi(varargin{n},{'ScanStart','Scan Start'})
    metadata.TimeZero                   = 'ScanStart';
else
    metadata.TimeZero                   = TimeZero;
end
metadata.TimeZero                       = TimeZero;
metadata.ModeOfAdministration           = ModeOfAdministration;
metadata.TracerName                     = TracerName;
metadata.TracerRadionuclide             = TracerRadionuclide;

if exist('InjectedRadioactivity', 'var')
    metadata.InjectedRadioactivity          = InjectedRadioactivity;
    metadata.InjectedRadioactivityUnits     = 'MBq';
end

if exist('InjectedMass', 'var')
    metadata.InjectedMass                   = InjectedMass;
    metadata.InjectedMassUnits              = 'ug';
end
if exist('SpecificRadioactivity', 'var')
    metadata.SpecificRadioactivity          = SpecificRadioactivity;
    metadata.SpecificRadioactivityUnits     = SpecificRadioactivityUnits;
end

if exist('MolecularWeight', 'var')
    metadata.TracerMolecularWeight      = MolecularWeight;
    metadata.TracerMolecularWeightUnits = 'g/mol';
end

if exist('MolarActivity', 'var')
    metadata.MolarActivity              = MolarActivity;
    metadata.MolarActivityUnits         = 'GBq/umol';
end


% run through optional var (actually all BIDS fields) setting dynamic fields
for f=1:length(optional)
    if exist(optional{f},'var')
        metadata.(optional{f}) = eval(optional{f});
    end
end

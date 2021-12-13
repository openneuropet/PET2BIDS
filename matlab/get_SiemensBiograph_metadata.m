function metadata = get_SiemensBiograph_metadata(varargin)

% Routine that outputs the Siemens HRRT PET scanner metadata following 
% <https://bids.neuroimaging.io/ BIDS>
%
% Defaults parameters (aquisition and reconstruction parameters) should be 
% stored in a SiemensBiograph_parameters.txt seating on disk next to this function
% or passed as argument in. Here is an example of such defaults, used at NRU
%
% InstitutionName                = 'Rigshospitalet, NRU, DK';
% AcquisitionMode                = 'list mode';
% ImageDecayCorrected            = true;
% ImageDecayCorrectionTime       = 0;
% ReconMethodName                = 'OP-OSEM';
% ReconMethodParameterLabels     = {'subsets','iterations'};
% ReconMethodParameterUnits      = {'none','none'};
% ReconMethodParameterValues     = [21, 3];,
% ReconFilterType                = 'XYZGAUSSIAN';
% ReconFilterSize                = 2;
% AttenuationCorrection          = 'CT-based attenuation correction';
%                   
% FORMAT:  metadata = get_SiemensBiograph_metadata(name,value)
%
% Example: metadata = get_SiemensBiograph_metadata('TimeZero','ScanStart','tracer','AZ10416936','Radionuclide','C11', ...
%                        'ModeOfAdministration','bolus','Radioactivity', 605.3220,'InjectedMass', 1.5934,'MolarActivity', 107.66)
%
% INPUTS a series of name/value pairs are expected
%        MANDATORY
%                  TimeZero: when was the tracer injected    e.g. TimeZero,'11:05:01'
%                  ModeOfAdministration                      e.g.'bolus'
%                  tracer: which tracer was used             e.g. 'tracer','DASB'
%                  Radionuclide: which nuclide was used      e.g. 'Radionuclide','C11'
%                  Injected Radioactivity Dose: value in MBq e.g. 'Radioactivity', 605.3220
%                  InjectedMass: Value in ug                 e.g. 'InjectedMass', 1.5934
%                  + 2 or more of those key/value arguments:
%                  MolarActivity: value in GBq/umol          e.g. 'MolarActivity', 107.66
%                  MolecularWeight: value in g/mol 
%                  SpecificRadioactivity in Bq/g or Bq/mol   e.g. 'SpecificRadioactivity', 3.7989e+14
%
%        note the TimeZero can also be [] or 'ScanStart' indicating that
%        the scanning time should be used as TimeZero, this will be filled
%        out automatically by ecat2nii
%
%        OPTIONAL 
%                  AcquisitionMode             
%                  ImageDecayCorrected           
%                  ImageDecayCorrectionTime      
%                  ReconMethodName                
%                  ReconMethodParameterLabels     
%                  ReconMethodParameterUnits      
%                  ReconMethodParameterValues     
%                  ReconFilterType                
%                  ReconFilterSize               
%                  AttenuationCorrection          
% 
% OUTPUT metadata is a structure with BIDS fields filled
%        (such structure is ready to be writen as json file using e.g.
%        the bids matlab jsonwrite function, typically associated with the *_pet.nii file) 
%
% Neurobiology Research Unit, Rigshospitalet
% Martin Nørgaard & Cyril Pernet - 2021
% ----------------------------------------------
% Copyright Open NeuroPET team

%% defaults are loaded via the SiemensBiographparameters.txt file

%% check inputs

if nargin == 0
    help get_SiemensBiograph_metadata
    return
else    
    for n=1:2:nargin
        if any(strcmpi(varargin{n},{'TimeZero','Time Zero'}))
            TimeZero = varargin{n+1};
        elseif strcmpi(varargin{n},'tracer')
            tracer = varargin{n+1};
        elseif strcmpi(varargin{n},'Radionuclide')
            Radionuclide = varargin{n+1};
        elseif contains(varargin{n},'Radioactivity','IgnoreCase',true)
            InjectedRadioactivity = varargin{n+1};
        elseif contains(varargin{n},'Mass','IgnoreCase',true)
            InjectedMass = varargin{n+1};
        elseif any(strcmpi(varargin{n},{'MolarActivity','Molar Activity'}))
            MolarActivity = varargin{n+1};
        elseif contains(varargin{n},'Weight','IgnoreCase',true)
            MolecularWeight = varargin{n+1};
        elseif contains(varargin{n},'Administration','IgnoreCase',true)
            ModeOfAdministration = varargin{n+1};
        elseif contains(varargin{n},'InstitutionName','IgnoreCase',true)
            InstitutionName = varargin{n+1};
        elseif any(strcmpi(varargin{n},{'AcquisitionMode','Acquisition Mode'}))
            AcquisitionMode = varargin{n+1};
        elseif contains(varargin{n},'DecayCorrected','IgnoreCase',true)
            ImageDecayCorrected = varargin{n+1};
        elseif contains(varargin{n},'DecayCorrectionTime','IgnoreCase',true)
            ImageDecayCorrectionTime = varargin{n+1};
        elseif contains(varargin{n},'MethodName','IgnoreCase',true)
            ReconMethodName = varargin{n+1};
        elseif contains(varargin{n},'FilterType','IgnoreCase',true)
            ReconFilterType = varargin{n+1};
        elseif contains(varargin{n},'FilterSize','IgnoreCase',true)
            ReconFilterSize = varargin{n+1};
        elseif contains(varargin{n},'AttenuationCorrection','IgnoreCase',true)
            AttenuationCorrection = varargin{n+1};
        end
    end
    
    % check input values and consistency given expected units in
    % -----------------------------------------------------------   
    radioinputs = {'InjectedRadioactivity', 'InjectedMass', ...
        'SpecificRadioactivity', 'MolarActivity', 'MolecularWeight'};
    input_check = cellfun(@exist,radioinputs);
    arguments   = cell(1,sum(input_check)*2);
    index = 1;
    for r=1:length(radioinputs)
        if input_check(r)
            arguments{index}   = radioinputs{r};
            arguments{index+1} = eval(radioinputs{r});
            index = index + 2;
        end
    end
    dataout  = check_metaradioinputs(arguments);
    setval   = fieldnames(dataout);
    for r=1:length(setval)
        if isnumeric(dataout.(setval{r}))
            eval([setval{r} '=' num2str(dataout.(setval{r}))])
        else
            eval([setval{r} '=''' dataout.(setval{r}) ''''])
        end
    end
    
    mandatory = {'TimeZero','tracer','ModeOfAdministration','Radionuclide','InjectedRadioactivity','InjectedMass'};
    if ~all(cellfun(@exist, mandatory))
        error('One or more mandatory name/value pairs are missing')
    end
    
    optional = {'InstitutionName','AcquisitionMode','ImageDecayCorrected','ImageDecayCorrectionTime',...
        'ReconMethodName','ReconFilterType','ReconFilterSize','AttenuationCorrection'};
    parameter_file = fullfile(fileparts(which('get_SiemensBiograph_metadata.m')),'SiemensBiographparameters.txt');
    if ~any(cellfun(@exist, optional))
        if exist(parameter_file,'file')
            setmetadata = importdata(parameter_file);
            for opt = 1:length(optional)
                if ~exist(optional{opt},'var')
                    try
                        eval(setmetadata{find(contains(setmetadata,optional{opt}))}); % shoul evaluate the = sign, creating name/value pairs                end
                        if isempty(eval(optional{opt}))
                            error('''%s'' from SiemensBiographparameters.txt is empty\n',optional{opt})
                        end
                    catch evalerr
                        error('''%s'' from SiemensBiographparameters.txt is empty\n',optional{opt})% --> error for optional metadata?
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
                'AttenuationCorrection      = '''';'}',...
                'VariableNames',{'# Defaults'});
            writetable(T,parameter_file);
            error('SiemensBiographparameters.txt to load default parameters is missing - a template file has been created, please fill missing information, or pass them as arguments in')
        end
    end
end

%% make the metadata structure

metadata.Manufacturer                   = 'Siemens';
metadata.ManufacturersModelName         = 'Biograph mMR';
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
metadata.TracerName                     = tracer;
metadata.TracerRadionuclide             = Radionuclide;
metadata.InjectedRadioactivity          = InjectedRadioactivity;
metadata.InjectedRadioactivityUnits     = 'MBq';
metadata.InjectedMass                   = InjectedMass;
metadata.InjectedMassUnits              = 'ug';
metadata.SpecificRadioactivity          = SpecificRadioactivity;
metadata.SpecificRadioactivityUnits     = SpecificRadioactivityUnits;

if exist('MolecularWeight', 'var')
    metadata.TracerMolecularWeight      = MolecularWeight;
    metadata.TracerMolecularWeightUnits = 'g/mol';
end

if exist('MolarActivity', 'var')
    metadata.MolarActivity              = MolarActivity;
    metadata.MolarActivityUnits         = 'GBq/umol';
end

metadata.ModeOfAdministration           = ModeOfAdministration;
metadata.InstitutionName                = InstitutionName;
metadata.AcquisitionMode                = AcquisitionMode;
metadata.ImageDecayCorrected            = ImageDecayCorrected;
metadata.ImageDecayCorrectionTime       = ImageDecayCorrectionTime;
metadata.ReconMethodName                = ReconMethodName ;
metadata.ReconFilterType                = ReconFilterType ;
metadata.ReconFilterSize                = ReconFilterSize;
metadata.AttenuationCorrection          = AttenuationCorrection;


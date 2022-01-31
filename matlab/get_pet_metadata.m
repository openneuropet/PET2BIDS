function metadata = get_pet_metadata(varargin)

% Routine that outputs PET scanner metadata following 
% <https://bids.neuroimaging.io/ BIDS>
%
% Such PET scanner metadata are passed along imaging data to the
% converters, ecat2nii.m or dcm2niix4pet.m allowing to have fully 
% compliant json files alongside the .nii files
%
% Defaults parameters (aquisition and reconstruction parameters) should be 
% stored in a *_parameters.txt seating on disk next to this function
% or passed as argument in. Replace * by the name of your scanner - for now we
% support 'SiemensBiograph', 'SiemensHRRT', 'GEAdvance' and 'PhillipsVereos'. 
% (see templates, as some info can be recovered from ecat or dcm - ie not 
% all info is necessarily needed)
%
% Here is an example of such defaults, used at NRU for our SiemensBiograph_parameters.txt
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
% FORMAT:  metadata = get_pet_metadata(key,value)
%
% Example: metadata = get_pet_metadata('Scanner','SiemensBiograph','TimeZero','ScanStart',...
%                        'tracer','AZ10416936','Radionuclide','C11', 'ModeOfAdministration','bolus',...
%                        'Radioactivity', 605.3220,'InjectedMass', 1.5934,'MolarActivity', 107.66)
%
% INPUTS a series of key/value pairs are expected
%        MANDATORY
%                  Scanner: name of scanner, map to a *parameters.txt file  e.g. 'Scanner', 'SiemensBiograph'
%                  TimeZero: when was the tracer injected                   e.g. 'TimeZero','11:05:01'
%                  ModeOfAdministration                                     e.g. 'ModeOfAdministration', 'bolus'
%                  tracer: which tracer was used                            e.g. 'tracer','DASB'
%                  Radionuclide: which nuclide was used                     e.g. 'Radionuclide','C11'
%                  Injected Radioactivity Dose: value in MBq                e.g. 'Radioactivity', 605.3220
%                  InjectedMass: Value in ug                                e.g. 'InjectedMass', 1.5934
%                  + at least 2 of those key/value arguments:
%                  MolarActivity: value in GBq/umol                         e.g. 'MolarActivity', 107.66
%                  MolecularWeight: value in g/mol                          e.g. 'MolecularWeight', 15.02
%                  SpecificRadioactivity in Bq/g or Bq/mol                  e.g. 'SpecificRadioactivity', 3.7989e+14
%
%        note the TimeZero can also be [] or 'ScanStart' indicating that
%        the scanning time should be used as TimeZero, this will be filled
%        out automatically by ecat2nii
%
%        OPTIONAL INPUTS
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

%% defaults are loaded via the *_parameters.txt file

%% check inputs

if nargin == 0
    help get_pet_metadata
    return
else    
    for n=1:2:nargin
        if strcmpi(varargin{n},'Scanner')
            Scanner = varargin{n+1};
        elseif any(strcmpi(varargin{n},{'TimeZero','Time Zero'}))
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
    
    % check mandatory/optional fileds of this function (not the BIDS fields)
    mandatory = {'Scanner','TimeZero','tracer','ModeOfAdministration','Radionuclide','InjectedRadioactivity','InjectedMass'};
    if ~all(cellfun(@exist, mandatory))
        error('One or more mandatory name/value pairs are missing \n%s',mandatory{find(cellfun(@exist, mandatory)==0)})
    end
    
    optional = {'InstitutionName',...
                'AcquisitionMode',...
                'ImageDecayCorrected',...
                'ImageDecayCorrectionTime',...
                'ReconMethodName',...
                'ReconMethodParameterLabels',...
                'ReconMethodParameterUnits',...
                'ReconMethodParameterValues',...
                'ReconFilterType',...
                'ReconFilterSize',...
                'AttenuationCorrection'};
            parameter_file = fullfile(fileparts(which('get_pet_metadata.m')),[Scanner 'parameters.txt']);
    if ~any(cellfun(@exist, optional))
        if exist(parameter_file,'file')
            setmetadata = importdata(parameter_file);
            for opt = 1:length(optional)
                if ~exist(optional{opt},'var')
                    option_index = find(contains(setmetadata,optional{opt}));
                    if ~isempty(option_index)
                        try
                            eval(setmetadata{option_index}); % shoul evaluate the = sign, creating name/value pairs                end
                            if isempty(eval(optional{opt}))
                                error('''%s'' from %sparameters.txt is empty\n',optional{opt},Scanner)
                            end
                        catch evalerr
                            error('''%s'' from %sparameters.txt is empty\n',optional{opt},Scanner)% --> error for optional inputs
                        end
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
            error([Scanner 'parameters.txt to load default parameters is missing - a template file has been created, please fill missing information, or pass them as arguments in'])
        end
    end
end

%% make the metadata structure

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
    else
        loc = find([strfind(Scanner,{'GE'}) strfind(Scanner,{'ge'})]);
        Scanner(loc:loc+length('GE')-1) = [];
        metadata.ManufacturersModelName = Scanner;
        warning('while the conversion code should run, the manufacturer model is not supported (ie dcm check uncertain) - contact us and we will fix it for you')
    end
elseif contains(Scanner,'Philips','IgnoreCase',true)
    metadata.Manufacturer = 'Philips';
    if contains(Scanner,'Vereos','IgnoreCase',true)
        metadata.ManufacturersModelName = 'Vereos PET/CT'; 
    elseif contains(Scanner,'Ingenuity','IgnoreCase',true)
        metadata.ManufacturersModelName = 'Ingenuity TF PET/CT'; 
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

if exist('InstitutionName','var')
    metadata.InstitutionName            = InstitutionName;
end

if exist('AcquisitionMode','var')
    metadata.AcquisitionMode            = AcquisitionMode;
end

if exist('ImageDecayCorrected','var')
    metadata.ImageDecayCorrected        = ImageDecayCorrected;
end
if exist('ImageDecayCorrectionTime','var')
    metadata.ImageDecayCorrectionTime   = ImageDecayCorrectionTime;
end

if exist('ReconMethodName','var')
    metadata.ReconMethodName            = ReconMethodName;
end

 if exist('ReconMethodParameterLabels','var')
    metadata.ReconMethodParameterLabels = ReconMethodParameterLabels;
 end
 
 if exist('ReconMethodParameterUnits','var')
    metadata.ReconMethodParameterUnits  = ReconMethodParameterUnits;
 end
 
 if exist('ReconMethodParameterValues','var')
    metadata.ReconMethodParameterValues = ReconMethodParameterValues;
end

if exist('ReconFilterType','var')
    metadata.ReconFilterType            = ReconFilterType;
end

if exist('ReconFilterSize','var')
    metadata.ReconFilterSize            = ReconFilterSize;
end

if exist('AttenuationCorrection','var')
    metadata.AttenuationCorrection      = AttenuationCorrection;
end


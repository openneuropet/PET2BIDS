function metadata = get_GEAdvance_metadata(varargin)

% Routine that outputs the GE Advance PET scanner metadata following <https://bids.neuroimaging.io/ BIDS>
% OPTONAL are a series of acuisition and reconstruction parameters, these can be set 
%         at the beginning on the function or passed as arguments
%
% FORMAT:  metadata = get_GEAdvance_metadata(name,value)
%
% Example: metadata = get_GEAdvance_metadata('tracer','DASB','Radionuclide','C11', ...
%                        'Radioactivity', 605.3220,'InjectedMass', 1.5934,'MolarActivity', 107.66)
%
% INPUTS a series of name/value pairs are expected
%        MANDATORY
%                  tracer: which tracer was used             e.g. 'tracer','DASB'
%                  Radionuclide: which nuclide was used      e.g. 'Radionuclide','C11'
%                  Injected Radioactivity Dose: value in MBq e.g. 'Radioactivity', 605.3220
%                  InjectedMass: Value in ug                 e.g. 'InjectedMass', 1.5934
%                  MolarActivity: value in GBq/umol          e.g. 'MolarActivity', 107.66
%        OPTIONAL 
%                  MolecularWeight: value in g/mol 
%                  ModeOfAdministration e.g.'bolus'
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
% Neuropbiology Research Unit, Rigshospitalet
% Martin Nørgaard & Cyril Pernet - 2021

%% defaults

AcquisitionMode                = '3D sinogram';
ImageDecayCorrected            = true;
InstitutionName                = 'Rigshospitalet, NRU, DK',
ImageDecayCorrectionTime       = 0;
ReconMethodName                = 'Filtered Back Projection';
ReconMethodParameterLabels     = {'none','none'};
ReconMethodParameterUnits      = {'none','none'};
ReconMethodParameterValues     = [0,0];
ReconFilterType                = {'Hann','Ramp'};
ReconFilterSize                = [6,8.5];
AttenuationCorrection          = '10-min transmission scan';

%% check inputs

if nargin == 0
    help get_GEAdvance_metadata
    return
else    
    for n=1:2:nargin
        if strcmpi(varargin{n},'tracer')
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
        elseif any(strcmpi(varargin{n},{'AcquisitionMode','Acquisition Mode'}))
            AcquisitionMode = varargin{n+1}; 
        elseif contains(varargin{n},'InstitutionName','IgnoreCase',true)
            InstitutionName = varargin{n+1};
        elseif contains(varargin{n},'DecayCorrected','IgnoreCase',true)
            ImageDecayCorrected = varargin{n+1};
        elseif contains(varargin{n},'DecayCorrectionTime','IgnoreCase',true)
            ImageDecayCorrectionTime = varargin{n+1};
        elseif contains(varargin{n},'MethodName','IgnoreCase',true)
            ReconMethodName = varargin{n+1};
        elseif contains(varargin{n},'ParameterLabels','IgnoreCase',true)
            ReconMethodParameterLabels = varargin{n+1};
        elseif contains(varargin{n},'ParameterUnits','IgnoreCase',true)
            ReconMethodParameterUnits = varargin{n+1};
        elseif contains(varargin{n},'ParameterValues','IgnoreCase',true)
            ReconMethodParameterValues = varargin{n+1};
        elseif contains(varargin{n},'FilterType','IgnoreCase',true)
            ReconFilterType = varargin{n+1};
        elseif contains(varargin{n},'FilterSize','IgnoreCase',true)
            ReconFilterSize = varargin{n+1};
        elseif contains(varargin{n},'AttenuationCorrection','IgnoreCase',true)
            AttenuationCorrection = varargin{n+1};
        end
    end
    
    mandatory = {'tracer','Radionuclide','InjectedRadioactivity','InjectedMass','MolarActivity'};
    if ~all(cellfun(@exist, mandatory))
        error('One or more mandatory name/value pairs are missing')
    end
end

    
%% make the metadata structure

metadata.Manufacturer                   = 'GE';
metadata.ManufacturersModelName         = 'Advance';
metadata.InstitutionName                = InstitutionName;
metadata.Units                          = 'Bq/mL';
metadata.BodyPart                       = 'Brain';
metadata.TracerName                     = tracer;
metadata.TracerRadionuclide             = Radionuclide;
metadata.InjectedRadioactivity          = InjectedRadioactivity;
metadata.InjectedRadioactivityUnits     = 'MBq';
metadata.InjectedMass                   = InjectedMass;
metadata.InjectedMassUnits              = 'ug';
metadata.MolarActivity                  = MolarActivity;
metadata.MolarActivityUnits             = 'GBq/umol';

if exist('molecular_weight', 'var')
    metadata.TracerMolecularWeight      = MolecularWeight;
    metadata.TracerMolecularWeightUnits = 'g/mol';
    metadata.SpecificRadioactivity      = (metadata.MolarActivity/metadata.TracerMolecularWeight)*1000;
    metadata.SpecificRadioactivityUnits = 'MBq/ug';
end

if exist('ModeOfAdministration','var')
    metadata.ModeOfAdministration       = ModeOfAdministration;
end

metadata.AcquisitionMode                = AcquisitionMode;
metadata.ImageDecayCorrected            = ImageDecayCorrected;
metadata.ImageDecayCorrectionTime       = ImageDecayCorrectionTime;
metadata.ReconMethodName                = ReconMethodName ;
metadata.ReconMethodParameterLabels     = ReconMethodParameterLabels;
metadata.ReconMethodParameterUnits      = ReconMethodParameterUnits;
metadata.ReconMethodParameterValues     = ReconMethodParameterValues;
metadata.ReconFilterType                = ReconFilterType ;
metadata.ReconFilterSize                = ReconFilterSize;
metadata.AttenuationCorrection          = AttenuationCorrection;


function dataout = check_metaradioinputs(varargin)

% routine to check input consistency, possibly generate new ones from PET
% BIDS metadata
% 
% FORMAT: dataout = check_metaradioinputs(varargin)
%
% INPUTS: arguments in are any of these key/value pairs
%           - InjectedRadioactivity in MBq
%           - InjectedMass in ug
%           - SpecificRadioactivity in Bq/g or MBq/ug
%           - MolarActivity in GBq/umol
%           - MolecularWeight in g/mol
%
% OUTPUT: dataout is a structure with the original and updated field,
%         including expected units
%
% Claus Svarer, Martin Nørgaard  & Cyril Pernet - 2021
% ----------------------------------------------
% Copyright Open NeuroPET team

%% check inputs
for n=1:nargin
    if strcmpi(varargin{n},'InjectedRadioactivity')
        InjectedRadioactivity = varargin{n+1};
    elseif strcmpi(varargin{n},'InjectedMass')
        InjectedMass = varargin{n+1};
    elseif strcmpi(varargin{n},'SpecificRadioactivity')
        SpecificRadioactivity = varargin{n+1};
    elseif strcmpi(varargin{n},'MolarActivity')
        MolarActivity = varargin{n+1};
    elseif strcmpi(varargin{n},'MolecularWeight')
        MolecularWeight = varargin{n+1};
    end
end

%% validates those metata

dataout = [];

if exist('InjectedRadioactivity', 'var') && exist('InjectedMass', 'var')
    dataout.InjectedRadioactivity          = InjectedRadioactivity;
    dataout.InjectedMass                   = InjectedMass;
    tmp = (InjectedRadioactivity*10^6) / (InjectedMass/10^6); % (MBq*10^6)/(ug/10^6) = Bq/g
    if exist('SpecificRadioactivity', 'var')
        if SpecificRadioactivity ~= tmp
            warning('infered SpecificRadioactivity in Bq/g doesn''t mach InjectedRadioactivity and InjectedMass, could be a unit issue')
        end
        dataout.SpecificRadioactivity      = SpecificRadioactivity;
    else
        dataout.SpecificRadioactivity      = tmp;
        dataout.SpecificRadioactivityUnits = 'Bq/g';
    end
end

if exist('InjectedRadioactivity', 'var') && exist('SpecificRadioactivity', 'var')
    dataout.InjectedRadioactivity = InjectedRadioactivity;
    dataout.SpecificRadioactivity = SpecificRadioactivity;
    tmp = ((InjectedRadioactivity*10^6)/SpecificRadioactivity)*10^6; % ((MBq*10^6)/(Bq/g))*10^6 = ug
    if exist('InjectedMass', 'var')
        if InjectedMass ~= tmp
            warning('infered InjectedMass in ug doesn''t mach InjectedRadioactivity and InjectedMass, could be a unit issue')
        end
        dataout.InjectedMass      = InjectedMass;
    else
        dataout.InjectedMass      = tmp;
        dataout.InjectedMassUnits = 'ug';
    end
end

if exist('InjectedMass', 'var') && exist('SpecificRadioactivity', 'var')
    dataout.InjectedMass              = InjectedMass;
    dataout.SpecificRadioactivity     = SpecificRadioactivity;
    tmp = ((InjectedMass/10^6) / SpecificRadioactivity) / 10^6; % ((ug/10^6) / Bq/g) / 10^6 = MBq
    if exist('InjectedRadioactivity', 'var')
        if InjectedRadioactivity ~= tmp
            warning('infered InjectedRadioactivity in MBq doesn''t mach SpecificRadioactivity and InjectedMass, could be a unit issue')
        end
        dataout.InjectedRadioactivity = InjectedRadioactivity;
    else
        dataout.InjectedRadioactivity = tmp;
        dataout.InjectedRadioactivity = 'MBq';
    end
end

if exist('MolarActivity', 'var') && exist('MolecularWeight', 'var')
    dataout.MolarActivity                  = MolarActivity;
    dataout.MolecularWeight                = MolecularWeight;
    tmp = (MolarActivity/MolecularWeight)*1000; % (GBq/umol) / (g/mol)
    if exist('SpecificRadioactivity', 'var')
        if SpecificRadioactivity ~= tmp
            warning('infered SpecificRadioactivity in MBq/ug doesn''t mach Molar Activity and Molecular Weight, could be a unit issue')
        end
        dataout.SpecificRadioactivity      = SpecificRadioactivity;
    else
        dataout.SpecificRadioactivity      = tmp;
        dataout.SpecificRadioactivityUnits = 'MBq/ug';
    end
end

if exist('MolarActivity', 'var') && exist('SpecificRadioactivity', 'var')
    dataout.SpecificRadioactivity    = SpecificRadioactivity;
    dataout.MolecularWeight          = MolecularWeight;
    tmp = (SpecificRadioactivity*1000) / MolarActivity; % (MBq/ug*1000) / (GBq/umol) = ug / umol
    if exist('MolecularWeight', 'var')
        if MolecularWeight ~= tmp
            warning('infered MolecularWeight in MBq/ug doesn''t mach Molar Activity and Molecular Weight, could be a unit issue')
        end
        dataout.MolecularWeight      = MolecularWeight;
    else
        dataout.MolecularWeight      = tmp;
        dataout.MolecularWeightUnits = 'ug/umol';
    end
end

if exist('MolarActivity', 'var') && exist('SpecificRadioactivity', 'var')
    dataout.SpecificRadioactivity    = SpecificRadioactivity;
    dataout.MolarActivity            = MolarActivity;
    tmp = (SpecificRadioactivity*1000) / MolarActivity; % (MBq/ug*1000) / (GBq/umol) = ug / umol
    if exist('MolecularWeight', 'var')
        if MolecularWeight ~= tmp
            warning('infered MolecularWeight in MBq/ug doesn''t mach Molar Activity and Molecular Weight, could be a unit issue')
        end
        dataout.MolecularWeight      = MolecularWeight;
    else
        dataout.MolecularWeight      = tmp;
        dataout.MolecularWeightUnits = 'ug/umol';
    end
end


function dataout = check_metaradioinputs(varargin)

% Routine to check input consistency, possibly generate new ones from PET
% BIDS metadata - this only makes sense if you respect the input units as
% indicated
%
% :format: dataout = check_metaradioinputs(varargin)
%
% .. note:: arguments in are provided via the following params (key/value pairs)
%   e.g.
%   - 'InjectedRadioctivity',81.24
%   - 'SpecificRadioactivity',1.3019e+04
%
% :param InjectedRadioactivity: in MBq
% :param InjectedMass:          in ug
% :param SpecificRadioactivity: in Bq/g or MBq/ug
% :param MolarActivity:         in GBq/umol
% :param MolecularWeight:       in g/mol
%
% :return: a structure with the original and updated field,
%         including expected units
%
%
% | *Claus Svarer, Martin Nørgaard  & Cyril Pernet - 2021*
% | *Copyright Open NeuroPET team*

%% check inputs
if size(varargin,2)==1
    varargin = varargin{1};
end

for n=1:length(varargin)
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
    dataout.InjectedRadioactivityUnits     = 'MBq';
    dataout.InjectedMass                   = InjectedMass;
    dataout.InjectedMassUnits              = 'ug';
    if any(ischar([InjectedRadioactivity,InjectedMass]))
        dataout.SpecificRadioactivity      = 'n/a';
        dataout.SpecificRadioactivityUnits = 'n/a';
    else
        tmp = (InjectedRadioactivity*10^6) / (InjectedMass/10*6); % (MBq*10^6)/(ug/10^6) = Bq/g
        if exist('SpecificRadioactivity', 'var')
            if uint16(SpecificRadioactivity) ~= uint16(tmp)
                warning('infered SpecificRadioactivity in Bq/g doesn''t match InjectedRadioactivity and InjectedMass, could be a unit issue')
            end
            dataout.SpecificRadioactivity      = SpecificRadioactivity;
        else
            dataout.SpecificRadioactivity      = tmp;
            dataout.SpecificRadioactivityUnits = 'Bq/g';
        end
    end
end

if exist('InjectedRadioactivity', 'var') && exist('SpecificRadioactivity', 'var')
    dataout.InjectedRadioactivity      = InjectedRadioactivity;
    dataout.InjectedRadioactivityUnits = 'MBq';
    dataout.SpecificRadioactivity      = SpecificRadioactivity;
    dataout.SpecificRadioactivityUnits = 'Bq/g';
    if any(ischar([InjectedRadioactivity,SpecificRadioactivity]))
        dataout.InjectedMass           = 'n/a';
        dataout.InjectedMassUnits      = 'n/a';
    else
        tmp = ((InjectedRadioactivity*10^6)/SpecificRadioactivity)*10^6; % ((MBq*10^6)/(Bq/g))*10^6 = ug
        if exist('InjectedMass', 'var')
            if uint16(InjectedMass) ~= uint16(tmp)
                warning('infered InjectedMass in ug doesn''t match InjectedRadioactivity and InjectedMass, could be a unit issue')
            end
            dataout.InjectedMass      = InjectedMass;
        else
            dataout.InjectedMass      = tmp;
            dataout.InjectedMassUnits = 'ug';
        end
    end
end

if exist('InjectedMass', 'var') && exist('SpecificRadioactivity', 'var')
    dataout.InjectedMass                   = InjectedMass;
    dataout.InjectedMassUnits              = 'ug';
    dataout.SpecificRadioactivity          = SpecificRadioactivity;
    dataout.SpecificRadioactivityUnits     = 'Bq/g';
    if any(ischar([SpecificRadioactivity,InjectedMass]))
        dataout.InjectedRadioactivity      = 'n/a';
        dataout.InjectedRadioactivityUnits = 'n/a';
    else
        tmp = ((InjectedMass/10^6)*SpecificRadioactivity) / 10^6; % ((ug/10^6)*Bq/g) / 10^6 = MBq
        if exist('InjectedRadioactivity', 'var')
            if uint16(InjectedRadioactivity) ~= uint16(tmp)
                warning('infered InjectedRadioactivity in MBq doesn''t match SpecificRadioactivity and InjectedMass, could be a unit issue')
            end
            dataout.InjectedRadioactivity      = InjectedRadioactivity;
        else
            dataout.InjectedRadioactivity      = tmp;
            dataout.InjectedRadioactivityUnits = 'MBq';
        end
    end
end

if exist('MolarActivity', 'var') && exist('MolecularWeight', 'var')
    dataout.MolarActivity                  = MolarActivity;
    dataout.MolarActivityUnits             = 'GBq/umol';
    dataout.MolecularWeight                = MolecularWeight;
    dataout.MolecularWeightUnits           = 'g/mol';
    if any(ischar([MolarActivity,MolecularWeight]))
        dataout.SpecificRadioactivity      = 'n/a';
        dataout.SpecificRadioactivityUnits = 'n/a';
    else
        tmp = (MolarActivity*1000)/ MolecularWeight; % (GBq/umol*1000) / g/mol = Bq/g
        if exist('SpecificRadioactivity', 'var')
            if uint16(SpecificRadioactivity) ~= uint16(tmp)
                warning('infered SpecificRadioactivity in MBq/ug doesn''t match Molar Activity and Molecular Weight, could be a unit issue')
            end
            dataout.SpecificRadioactivity      = SpecificRadioactivity;
        else
            dataout.SpecificRadioactivity      = tmp;
            dataout.SpecificRadioactivityUnits = 'Bq/g';
        end
    end
end

if exist('MolarActivity', 'var') && exist('SpecificRadioactivity', 'var')
    dataout.SpecificRadioactivity      = SpecificRadioactivity;
    dataout.SpecificRadioactivityUnits = 'MBq/ug';
    dataout.MolarActivity              = MolarActivity;
    dataout.MolarActivityUnits         = 'GBq/umol';
    if any(ischar([SpecificRadioactivity,MolarActivity]))
        dataout.MolecularWeight        = 'n/a';
        dataout.MolecularWeightUnits  = 'n/a';
    else
        tmp = (MolarActivity*1000)/SpecificRadioactivity; % = g / mol
        if exist('MolecularWeight', 'var')
            if uint16(MolecularWeight) ~= uint16(tmp)
                warning('infered MolecularWeight in MBq/ug doesn''t match Molar Activity and Molecular Weight, could be a unit issue')
            end
            dataout.MolecularWeight      = MolecularWeight;
        else
            dataout.MolecularWeight      = tmp;
            dataout.MolecularWeightUnits = 'g/mol';
        end
    end
end

if exist('MolecularWeight', 'var') && exist('SpecificRadioactivity', 'var')
    dataout.SpecificRadioactivity      = SpecificRadioactivity;
    dataout.SpecificRadioactivityUnits = 'MBq/ug';
    dataout.MolecularWeight            = MolecularWeight;
    dataout.MolecularWeightUnits       = 'g/mol';
    if any(ischar([SpecificRadioactivity,MolecularWeight]))
        dataout.MolarActivity         = 'n/a';
        dataout.MolarActivityUnits    = 'n/a';
    else
        tmp =  (MolecularWeight*SpecificRadioactivity)/1000; % MBq/umol/1000 = GBq/umol
        if exist('MolarActivity', 'var')
            if uint16(MolarActivity) ~= uint16(tmp)
                warning('infered MolarActivity in GBq/umol doesn''t match Specific Radioactivity and Molecular Weight, could be a unit issue')
            end
            dataout.MolarActivity       = MolarActivity;
        else
            dataout.MolarActivity       = tmp;
            dataout.MolarActivityUnits  = 'GBq/umol';
        end
    end
end


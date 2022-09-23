function check_metaradioinputs_test

% given know input values, does check_metaradioinputs return valid output
%
% @context:
% Activity is the number of disintegrations per second in Bq
% SpecificRadioactivity is the activity per unit mass of a radionuclide in Bq/g or MBq/ug
% InjectedRadioactivity how much activity was injected in MBq
% InjectedMass how much mass was injected in ug
% It follows that
%        SpecificRadioactivity = InjectedRadioactivity / InjectedMass (with values scaled)
% A Mole is 6.02214076^23 of a compound/molecule
% MolarActivity is the amount of activity per compound (active and stable) in GBq/umol
% MolecularWeight is the weight of a mol of compound in g/mol
% It follows that
%         SpecificRadioactivity = MolarActivity / MolecularWeight (with values scaled)
%
% Cyril Pernet
% ----------------------------------------------
% Copyright OpenNeuroPET team

%% does it compute as expected
InjectedRadioactivity = 44.4;
InjectedMass          = 6240;
SpecificRadioactivity = (InjectedRadioactivity*10^6) / (InjectedMass/10^6); % (MBq*10^6)/(ug/10^6) = Bq/g
dataout = check_metaradioinputs('InjectedRadioactivity',44.4,'InjectedMass',6240);
if SpecificRadioactivity ~= dataout.SpecificRadioactivity
    report{1} = 'error in computing SpecificRadioactivity from Injected activity and mass';
else
    report{1} = 'computing SpecificRadioactivity from Injected activity and mass ok';
end
  
InjectedRadioactivity = 44.4;
SpecificRadioactivity = 7.1154e+09;
InjectedMass = ((InjectedRadioactivity*10^6)/SpecificRadioactivity)*10^6; % ((MBq*10^6)/(Bq/g))*10^6 = ug
dataout = check_metaradioinputs('InjectedRadioactivity',44.4,'SpecificRadioactivity',7.1154e+09);
if InjectedMass ~= dataout.InjectedMass
    report{2} = 'error in computing InjectedMass';
else
    report{2} = 'computing InjectedMass ok';
end

SpecificRadioactivity = 7.1154e+09;
InjectedMass          = 6240;
InjectedRadioactivity = ((InjectedMass/10^6)*SpecificRadioactivity) / 10^6; % ((ug/10^6)*Bq/g) / 10^6 = MBq
dataout = check_metaradioinputs('InjectedMass',6240,'SpecificRadioactivity',7.1154e+09);
if InjectedRadioactivity ~= dataout.InjectedRadioactivity
    report{3} = 'error in computing InjectedRadioactivity';
else
    report{3} = 'computing InjectedRadioactivity ok';
end

MolarActivity         = 135192600;
MolecularWeight       = 19;
SpecificRadioactivity = (MolarActivity*1000)/ MolecularWeight; % (GBq/umol*1000) / g/mol = Bq/g
dataout = check_metaradioinputs('MolarActivity',135192600,'MolecularWeight',19);
if SpecificRadioactivity ~= dataout.SpecificRadioactivity
    report{4} = 'error in computing SpecificRadioactivity from Molecular activity and mass';
else
    report{4} = 'computing SpecificRadioactivity from Molecular activity and mass ok';
end

MolarActivity         = 135192600;
SpecificRadioactivity = 7.1154e+09;
MolecularWeight       = (MolarActivity*1000)/SpecificRadioactivity; % (GBq/umol)*1000 / (MBq/ug) = g / mol
dataout = check_metaradioinputs('MolarActivity',135192600,'SpecificRadioactivity',7.1154e+09);
if MolecularWeight ~= dataout.MolecularWeight
    report{5} = 'error in computing MolecularWeight';
else
    report{5} = 'computing MolecularWeight ok';
end

MolecularWeight       = 19;
SpecificRadioactivity = 7.1154e+09;
MolarActivity         = (MolecularWeight*SpecificRadioactivity)/1000; % g/mol*(MBq/ug) = ug/umol*(MBq/ug) = MBq/umol/1000 = GBq/umol
dataout = check_metaradioinputs('MolecularWeight',19,'SpecificRadioactivity',7.1154e+09);
if MolarActivity ~= dataout.MolarActivity
    report{6} = 'error in computing MolarActivity';
else
    report{6} = 'computing MolarActivity ok';
end
celldisp(report)

%% also check if any warning issued
check_metaradioinputs('InjectedRadioactivity',44.4,'SpecificRadioactivity',7.1154e+09,...
    'InjectedMass',6240);

check_metaradioinputs('MolecularWeight',19,'SpecificRadioactivity',7.1154e+09,...
    'MolarActivity',135192600);


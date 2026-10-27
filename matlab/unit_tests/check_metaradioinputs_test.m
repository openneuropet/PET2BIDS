function check_metaradioinputs_test
% Numerical regression tests: failures must fail CI, not merely print a report.
% Independent physical example: 100 MBq, 2 ug, 50 MBq/ug,
% 15 GBq/umol, molecular weight 300 g/mol.
names = {'InjectedRadioactivity', 'InjectedMass', 'SpecificRadioactivity', ...
    'MolarActivity', 'TracerMolecularWeight'};
expected = [100, 2, 5e13, 15, 300];
relations = [3 1 2; 2 1 3; 1 2 3; 3 4 5; 5 4 3; 4 5 3];
for r = 1:size(relations, 1)
    row = relations(r, :);
    out = check_metaradioinputs(names{row(2)}, expected(row(2)), ...
        names{row(3)}, expected(row(3)));
    assert_close(out.(names{row(1)}), expected(row(1)));
end

% Equivalent specific-activity units must give the same physical results.
unitlabels = {'Bq/g', 'MBq/ug', 'kBq/mg', 'GBq/g', 'MBq/µg', 'MBq/μg'};
specific = [5e13, 50, 5e7, 5e4, 50, 50];
for k = 1:numel(unitlabels)
    args = {'SpecificRadioactivity', specific(k), ...
        'SpecificRadioactivityUnits', unitlabels{k}};
    out = check_metaradioinputs(args{:}, 'InjectedRadioactivity', 100);
    assert_close(out.InjectedMass, 2);
    out = check_metaradioinputs(args{:}, 'InjectedMass', 2);
    assert_close(out.InjectedRadioactivity, 100);
    out = check_metaradioinputs(args{:}, 'MolarActivity', 15);
    assert_close(out.TracerMolecularWeight, 300);
    out = check_metaradioinputs(args{:}, 'TracerMolecularWeight', 300);
    assert_close(out.MolarActivity, 15);
    assert(strcmp(out.SpecificRadioactivityUnits, unitlabels{k}));
    assert(out.SpecificRadioactivity == specific(k));
end

out = check_metaradioinputs('InjectedRadioactivity', 10, 'InjectedMass', 10);
assert_close(out.SpecificRadioactivity, 1e12);
out = check_metaradioinputs('InjectedRadioactivity', 10, 'InjectedMass', 10, ...
    'SpecificRadioactivityUnits', 'MBq/ug');
assert_close(out.SpecificRadioactivity, 1);
assert(strcmp(out.SpecificRadioactivityUnits, 'MBq/ug'));
out = check_metaradioinputs('InjectedRadioactivity', 10, ...
    'InjectedRadioactivityUnits', 'Bq', 'InjectedMass', 10, ...
    'InjectedMassUnits', 'g');
assert_close(out.SpecificRadioactivity, 1);
assert(strcmp(out.SpecificRadioactivityUnits, 'Bq/g'));
out = check_metaradioinputs('InjectedRadioactivity', 10, ...
    'InjectedRadioactivityUnits', 'MBq', 'SpecificRadioactivity', 1, ...
    'SpecificRadioactivityUnits', 'MBq/ug');
assert_close(out.InjectedMass, 10);
assert(strcmp(out.InjectedMassUnits, 'ug'));

% InjectedMass may be an amount of substance; then it relates to molar activity.
out = check_metaradioinputs('InjectedRadioactivity', 100, ...
    'InjectedRadioactivityUnits', 'MBq', 'InjectedMass', 2, ...
    'InjectedMassUnits', 'nmol');
assert_close(out.MolarActivity, 50);
assert(strcmp(out.MolarActivityUnits, 'GBq/umol'));
assert(~isfield(out, 'SpecificRadioactivity'));
out = check_metaradioinputs('InjectedRadioactivity', 100, ...
    'InjectedRadioactivityUnits', 'MBq', 'InjectedMassUnits', 'nmol', ...
    'MolarActivity', 50, 'MolarActivityUnits', 'GBq/umol');
assert_close(out.InjectedMass, 2);
assert(strcmp(out.InjectedMassUnits, 'nmol'));
out = check_metaradioinputs('InjectedMass', 2, ...
    'InjectedMassUnits', 'nmol', 'MolarActivity', 50, ...
    'MolarActivityUnits', 'GBq/umol');
assert_close(out.InjectedRadioactivity, 100);
assert(strcmp(out.InjectedRadioactivityUnits, 'MBq'));

% Preserve every supplied quantity and unit; no spurious consistency warning.
args = {'InjectedRadioactivity', 100, 'InjectedMass', 2, ...
    'SpecificRadioactivity', 50, 'SpecificRadioactivityUnits', 'MBq/ug', ...
    'MolarActivity', 15, 'MolecularWeight', 300};
lastwarn('');
out = check_metaradioinputs(args);
[msg, ~] = lastwarn;
assert(isempty(msg));
assert(out.TracerMolecularWeight == 300 && out.MolarActivity == 15);
assert(~isfield(out, 'MolecularWeight'));
assert(out.SpecificRadioactivity == 50);
assert(strcmp(out.MolarActivityUnits, 'GBq/umol'));
assert(isequal(out, check_metaradioinputs(args{:})));

% Standard fields win over a conflicting legacy value/unit pair.
lastwarn('');
out = check_metaradioinputs('TracerMolecularWeight', 300, ...
    'MolecularWeight', .3, 'MolecularWeightUnits', 'kg/mol', ...
    'SpecificRadioactivity', 100, ...
    'SpecificRadioactivityUnits', 'MBq/ug');
assert_close(out.TracerMolecularWeight, 300);
assert(strcmp(out.TracerMolecularWeightUnits, 'g/mol'));
assert_close(out.MolarActivity, 30);
[~, id] = lastwarn;
assert(strcmp(id, 'PET2BIDS:LegacyMolecularWeight'));
out = check_metaradioinputs('MolecularWeightUnits', 'kg/mol');
assert(strcmp(out.TracerMolecularWeightUnits, 'kg/mol'));
assert(~isfield(out, 'MolecularWeightUnits'));
out = check_metaradioinputs('TracerMolecularWeight', "", ...
    'TracerMolecularWeightUnits', "", 'MolecularWeight', .3, ...
    'MolecularWeightUnits', 'kg/mol', 'SpecificRadioactivity', 50, ...
    'SpecificRadioactivityUnits', 'MBq/ug');
assert_close(out.TracerMolecularWeight, .3);
assert(strcmp(out.TracerMolecularWeightUnits, 'kg/mol'));
assert_close(out.MolarActivity, 15);
for placeholder = {'   ', 'none'}
    out = check_metaradioinputs('TracerMolecularWeight', placeholder{1}, ...
        'TracerMolecularWeightUnits', placeholder{1}, ...
        'MolecularWeight', .3, 'MolecularWeightUnits', 'kg/mol', ...
        'SpecificRadioactivity', 50, ...
        'SpecificRadioactivityUnits', 'MBq/ug');
    assert_close(out.TracerMolecularWeight, .3);
    assert(strcmp(out.TracerMolecularWeightUnits, 'kg/mol'));
    assert_close(out.MolarActivity, 15);
end
out = check_metaradioinputs('TracerMolecularWeight', 'n/a', ...
    'MolecularWeight', .3, 'MolecularWeightUnits', 'kg/mol');
assert(strcmp(out.TracerMolecularWeight, 'n/a'));
assert(strcmp(out.TracerMolecularWeightUnits, 'g/mol'));

% Inferred molecular weight uses the standard BIDS field names.
out = check_metaradioinputs('MolarActivity', 15, ...
    'SpecificRadioactivity', 50, ...
    'SpecificRadioactivityUnits', 'MBq/ug');
assert_close(out.TracerMolecularWeight, 300);
assert(strcmp(out.TracerMolecularWeightUnits, 'g/mol'));
assert(~isfield(out, 'MolecularWeight'));

% Other input units and requested output units.
out = check_metaradioinputs('InjectedRadioactivity', 1e8, ...
    'InjectedRadioactivityUnits', 'Bq', 'InjectedMass', .002, ...
    'InjectedMassUnits', 'mg', 'SpecificRadioactivityUnits', 'MBq/ug');
assert_close(out.SpecificRadioactivity, 50);
assert(out.InjectedMass == .002 && strcmp(out.InjectedMassUnits, 'mg'));
out = check_metaradioinputs('MolarActivity', 15e6, ...
    'MolarActivityUnits', 'MBq/mol', 'TracerMolecularWeight', .3, ...
    'TracerMolecularWeightUnits', 'kg/mol');
assert_close(out.SpecificRadioactivity, 5e10);
out = check_metaradioinputs('InjectedRadioactivity', 1, ...
    'InjectedRadioactivityUnits', 'mCi', 'InjectedMass', 1);
assert_close(out.SpecificRadioactivity, 3.7e13);

% Relative tolerance works for large Bq/g values; unlike uint16 saturation.
lastwarn('');
check_metaradioinputs('InjectedRadioactivity', 44.4, 'InjectedMass', 6240, ...
    'SpecificRadioactivity', 7.1154e9);
[msg, ~] = lastwarn;
assert(isempty(msg));
lastwarn('');
out = check_metaradioinputs('InjectedRadioactivity', 100, 'InjectedMass', 2, ...
    'SpecificRadioactivity', 8e13);
[~, id] = lastwarn;
assert(strcmp(id, 'PET2BIDS:RadioMismatch'));
assert(out.SpecificRadioactivity == 8e13);

% Missing values must not overwrite measurements; zero numerators are valid.
out = check_metaradioinputs('InjectedRadioactivity', 'n/a', 'InjectedMass', 2);
assert(out.InjectedMass == 2 && strcmp(out.SpecificRadioactivity, 'n/a'));
out = check_metaradioinputs('InjectedRadioactivity', 0, 'InjectedMass', 2);
assert(out.SpecificRadioactivity == 0);
out = check_metaradioinputs('InjectedRadioactivity', 100, 'InjectedMass', 0);
assert(strcmp(out.SpecificRadioactivity, 'n/a'));
out = check_metaradioinputs('InjectedRadioactivity', '100', 'InjectedMass', '2');
assert_close(out.SpecificRadioactivity, 5e13);
out = check_metaradioinputs('InjectedRadioactivity', NaN, 'InjectedMass', 2);
assert(strcmp(out.SpecificRadioactivity, 'n/a'));
out = check_metaradioinputs('InjectedRadioactivity', 100, 'InjectedMass', 2, ...
    'SpecificRadioactivity', 10, 'SpecificRadioactivityUnits', 'Bq/mol');
assert(out.SpecificRadioactivity == 10);
assert(strcmp(out.SpecificRadioactivityUnits, 'Bq/mol'));
assert(out.InjectedMass == 2);
assert(isempty(check_metaradioinputs()));
assert(isempty(check_metaradioinputs({})));

% The metadata builder must not drop an inferred standard molecular weight.
metadata = get_pet_metadata('Scanner', 'SiemensBiograph', ...
    'TimeZero', 'ScanStart', 'TracerName', 'test', ...
    'TracerRadionuclide', 'C11', 'ModeOfAdministration', 'bolus', ...
    'MolarActivity', 15, 'SpecificRadioactivity', 50, ...
    'SpecificRadioactivityUnits', 'MBq/ug');
assert_close(metadata.TracerMolecularWeight, 300);
assert(strcmp(metadata.TracerMolecularWeightUnits, 'g/mol'));
assert(~isfield(metadata, 'MolecularWeight'));

% Standard values win regardless of whether legacy aliases come first or last.
common = {'Scanner', 'SiemensBiograph', 'TimeZero', 'ScanStart', ...
    'TracerName', 'test', 'TracerRadionuclide', 'C11', ...
    'ModeOfAdministration', 'bolus', 'SpecificRadioactivity', 100, ...
    'SpecificRadioactivityUnits', 'MBq/ug'};
standard_first = get_pet_metadata(common{:}, ...
    'TracerMolecularWeight', 300, 'TracerMolecularWeightUnits', 'g/mol', ...
    'MolecularWeight', .4, 'MolecularWeightUnits', 'kg/mol');
legacy_first = get_pet_metadata(common{:}, ...
    'MolecularWeight', .4, 'MolecularWeightUnits', 'kg/mol', ...
    'TracerMolecularWeight', 300, 'TracerMolecularWeightUnits', 'g/mol');
assert_close(standard_first.TracerMolecularWeight, 300);
assert_close(standard_first.MolarActivity, 30);
assert_close(legacy_first.TracerMolecularWeight, 300);
assert_close(legacy_first.MolarActivity, 30);

% Null-like molecular-weight arguments without units must not survive the
% normalized builder output or make it read an undefined unit variable.
for alias = {'TracerMolecularWeight', 'MolecularWeight'}
    for placeholder = {'', '   ', 'none'}
        metadata = get_pet_metadata(common{1:10}, ...
            'InjectedRadioactivity', 100, 'InjectedMass', 2, ...
            alias{1}, placeholder{1});
        assert(~isfield(metadata, 'TracerMolecularWeight'));
        assert(~isfield(metadata, 'TracerMolecularWeightUnits'));
        assert(~isfield(metadata, 'MolecularWeight'));
        assert(~isfield(metadata, 'MolecularWeightUnits'));
    end
end
try
    get_pet_metadata(common{1:10}, 'TracerMolecularWeightUnits', 'g/mol');
    error('PET2BIDS:TestFailure', ...
        'A molecular-weight unit without any quantity was accepted.');
catch exception
    assert(~strcmp(exception.identifier, 'PET2BIDS:TestFailure'));
    assert(contains(exception.message, ...
        'not enough radioactivity related inputs'));
end

% The JSON updater must replace blank standard placeholders with a legacy pair
% before removing the legacy field names.
jsonfile = [tempname '.json'];
cleanup = onCleanup(@() delete_if_present(jsonfile)); %#ok<NASGU>
input = struct('TracerMolecularWeight', [], ...
    'TracerMolecularWeightUnits', '', 'MolecularWeight', .3, ...
    'MolecularWeightUnits', 'kg/mol', 'SpecificRadioactivity', 50, ...
    'SpecificRadioactivityUnits', 'MBq/ug');
jsonwrite(jsonfile, input);
updatejsonpetfile(jsonfile, struct());
updated = jsondecode(fileread(jsonfile));
assert_close(updated.TracerMolecularWeight, .3);
assert(strcmp(updated.TracerMolecularWeightUnits, 'kg/mol'));
assert_close(updated.MolarActivity, 15);
assert(~isfield(updated, 'MolecularWeight'));
assert(~isfield(updated, 'MolecularWeightUnits'));

for placeholder = {'   ', 'none'}
    input = struct('TracerMolecularWeight', placeholder{1}, ...
        'TracerMolecularWeightUnits', placeholder{1}, ...
        'MolecularWeight', .3, 'MolecularWeightUnits', 'kg/mol', ...
        'SpecificRadioactivity', 50, ...
        'SpecificRadioactivityUnits', 'MBq/ug');
    jsonwrite(jsonfile, input);
    updatejsonpetfile(jsonfile, struct());
    updated = jsondecode(fileread(jsonfile));
    assert_close(updated.TracerMolecularWeight, .3);
    assert(strcmp(updated.TracerMolecularWeightUnits, 'kg/mol'));
    assert_close(updated.MolarActivity, 15);
    assert(~isfield(updated, 'MolecularWeight'));
    assert(~isfield(updated, 'MolecularWeightUnits'));
end

% A canonical unit without a canonical value must not label a legacy value
% that has no matching legacy unit.
input = struct('TracerMolecularWeightUnits', 'kg/mol', ...
    'MolecularWeight', .3, 'SpecificRadioactivity', 50, ...
    'SpecificRadioactivityUnits', 'MBq/ug');
jsonwrite(jsonfile, input);
updatejsonpetfile(jsonfile, struct());
updated = jsondecode(fileread(jsonfile));
assert_close(updated.TracerMolecularWeight, .3);
assert(strcmp(updated.TracerMolecularWeightUnits, 'g/mol'));
assert_close(updated.MolarActivity, .015);

% One-argument validation migrates aliases without inferring other quantities.
input = struct('MolecularWeight', .3, 'MolecularWeightUnits', 'kg/mol');
jsonwrite(jsonfile, input);
updatejsonpetfile(jsonfile);
updated = jsondecode(fileread(jsonfile));
assert_close(updated.TracerMolecularWeight, .3);
assert(strcmp(updated.TracerMolecularWeightUnits, 'kg/mol'));
assert(~isfield(updated, 'MolecularWeight'));
assert(~isfield(updated, 'MolecularWeightUnits'));
assert(~isfield(updated, 'MolarActivity'));

input = struct('TracerMolecularWeightUnits', 'kg/mol', ...
    'MolecularWeight', .3);
jsonwrite(jsonfile, input);
updatejsonpetfile(jsonfile);
updated = jsondecode(fileread(jsonfile));
assert_close(updated.TracerMolecularWeight, .3);
assert(strcmp(updated.TracerMolecularWeightUnits, 'g/mol'));

% Struct-only validation must not assume unrelated reconstruction fields exist.
status = updatejsonpetfile(struct('FrameDuration', 60));
assert(isstruct(status) && isfield(status, 'state'));
fprintf('check_metaradioinputs regression tests passed.\n');
end

function assert_close(actual, expected)
assert(abs(actual - expected) <= 1e-12 + 1e-10 * abs(expected));
end

function delete_if_present(filename)
if exist(filename, 'file')
    delete(filename);
end
end

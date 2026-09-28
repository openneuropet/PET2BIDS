function check_metaradioinputs_test
% Numerical regression tests: failures must fail CI, not merely print a report.
% Independent physical example: 100 MBq, 2 ug, 50 MBq/ug,
% 15 GBq/umol, molecular weight 300 g/mol.
names = {'InjectedRadioactivity', 'InjectedMass', 'SpecificRadioactivity', ...
    'MolarActivity', 'MolecularWeight'};
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
    assert_close(out.MolecularWeight, 300);
    out = check_metaradioinputs(args{:}, 'MolecularWeight', 300);
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

% Preserve every supplied quantity and unit; no spurious consistency warning.
args = {'InjectedRadioactivity', 100, 'InjectedMass', 2, ...
    'SpecificRadioactivity', 50, 'SpecificRadioactivityUnits', 'MBq/ug', ...
    'MolarActivity', 15, 'MolecularWeight', 300};
lastwarn('');
out = check_metaradioinputs(args);
[msg, ~] = lastwarn;
assert(isempty(msg));
assert(out.MolecularWeight == 300 && out.MolarActivity == 15);
assert(out.SpecificRadioactivity == 50);
assert(strcmp(out.MolarActivityUnits, 'GBq/umol'));
assert(isequal(out, check_metaradioinputs(args{:})));

% Other input units and requested output units.
out = check_metaradioinputs('InjectedRadioactivity', 1e8, ...
    'InjectedRadioactivityUnits', 'Bq', 'InjectedMass', .002, ...
    'InjectedMassUnits', 'mg', 'SpecificRadioactivityUnits', 'MBq/ug');
assert_close(out.SpecificRadioactivity, 50);
assert(out.InjectedMass == .002 && strcmp(out.InjectedMassUnits, 'mg'));
out = check_metaradioinputs('MolarActivity', 15e6, ...
    'MolarActivityUnits', 'MBq/mol', 'MolecularWeight', .3, ...
    'MolecularWeightUnits', 'kg/mol');
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
fprintf('check_metaradioinputs regression tests passed.\n');
end

function assert_close(actual, expected)
assert(abs(actual - expected) <= 1e-12 + 1e-10 * abs(expected));
end

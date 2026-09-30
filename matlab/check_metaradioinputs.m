function dataout = check_metaradioinputs(varargin)
% Check radiotracer metadata and infer missing quantities with consistent units.
%
% :format: dataout = check_metaradioinputs('Name', value, ...)
%          A cell array of name/value pairs is also accepted.
%
% :param InjectedRadioactivity: default MBq
% :param InjectedMass: default ug; also accepts amount units such as nmol
% :param SpecificRadioactivity: default Bq/g (NOT numerically equal to MBq/ug)
% :param MolarActivity: default GBq/umol
% :param TracerMolecularWeight: default g/mol
%          Legacy MolecularWeight fields are accepted as input aliases.
%
% Each quantity accepts a corresponding <Name>Units argument. Activity units
% Bq, kBq, MBq, GBq, TBq, Ci, mCi, uCi; mass units kg, g, mg, ug, ng;
% and amount units mol, mmol, umol, nmol, pmol are supported, including ratios
% commensurate with Bq/g, Bq/mol and g/mol. InjectedMass units determine
% whether its relations use specific or molar activity. Micro signs are
% accepted as 'u'.
% Supplied values and units are preserved. Omitted units use the defaults above.
% Inferred values use requested units, or the defaults if none were supplied.
% For example, 10 MBq / 10 ug is 1 MBq/ug, or 1e12 Bq/g.
% Unknown/incompatible units are warned about and excluded from calculations.
% Missing/non-numeric inputs and zero denominators cannot generate a numeric
% result. Only absent output quantities are marked 'n/a'; inputs are retained.
% Consistency uses relative tolerance 1e-5 rather than integer truncation.
%
% | *Claus Svarer, Martin Nørgaard & Cyril Pernet - 2021*
% | *Copyright Open NeuroPET team*

if numel(varargin) == 1 && iscell(varargin{1})
    varargin = varargin{1};
end
if mod(numel(varargin), 2) ~= 0
    error('PET2BIDS:RadioInputPairs', 'Expected name/value pairs.');
end
names = {'InjectedRadioactivity', 'InjectedMass', 'SpecificRadioactivity', ...
    'MolarActivity', 'MolecularWeight'};
defaults = {'MBq', 'ug', 'Bq/g', 'GBq/umol', 'g/mol'};
unitnames = strcat(names, 'Units');
outputnames = names;
outputnames{5} = 'TracerMolecularWeight';
outputunitnames = strcat(outputnames, 'Units');
inputs = struct();
for n = 1:2:numel(varargin)
    key = varargin{n};
    if ~(ischar(key) || (isstring(key) && isscalar(key)))
        error('PET2BIDS:RadioInputPairs', 'Input names must be text.');
    end
    allnames = [names unitnames {'TracerMolecularWeight', ...
        'TracerMolecularWeightUnits'}];
    index = find(strcmpi(key, allnames), 1);
    if ~isempty(index)
        inputs.(allnames{index}) = varargin{n+1};
    end
end

% Prefer the standard BIDS value/unit pair. A legacy pair is used only when
% the standard value is absent; unit-only inputs select inferred output units.
if isfield(inputs, 'TracerMolecularWeight') && ...
        is_alias_supplied(inputs.TracerMolecularWeight)
    if isfield(inputs, 'MolecularWeight') && ...
            is_alias_supplied(inputs.MolecularWeight)
        warning('PET2BIDS:LegacyMolecularWeight', ...
            ['Both TracerMolecularWeight and legacy MolecularWeight were ' ...
             'supplied; using TracerMolecularWeight.']);
    end
    inputs.MolecularWeight = inputs.TracerMolecularWeight;
    if isfield(inputs, 'TracerMolecularWeightUnits') && ...
            is_alias_supplied(inputs.TracerMolecularWeightUnits)
        inputs.MolecularWeightUnits = inputs.TracerMolecularWeightUnits;
    elseif isfield(inputs, 'MolecularWeightUnits')
        inputs = rmfield(inputs, 'MolecularWeightUnits');
    end
elseif (~isfield(inputs, 'MolecularWeight') || ...
        ~is_alias_supplied(inputs.MolecularWeight)) && ...
        isfield(inputs, 'TracerMolecularWeightUnits') && ...
        is_alias_supplied(inputs.TracerMolecularWeightUnits)
    inputs.MolecularWeightUnits = inputs.TracerMolecularWeightUnits;
end
if isfield(inputs, 'MolecularWeight') && ...
        ~is_alias_supplied(inputs.MolecularWeight)
    inputs = rmfield(inputs, 'MolecularWeight');
end
if isfield(inputs, 'MolecularWeightUnits') && ...
        ~is_alias_supplied(inputs.MolecularWeightUnits)
    inputs = rmfield(inputs, 'MolecularWeightUnits');
end

dataout = [];
present = false(1, 5);
values = nan(1, 5);
factors = nan(1, 5);
units = defaults;
injectedmassdimension = '';
for n = 1:5
    present(n) = isfield(inputs, names{n}) && is_supplied(inputs.(names{n}));
    if isfield(inputs, unitnames{n}) && is_supplied(inputs.(unitnames{n}))
        units{n} = inputs.(unitnames{n});
    end
    if n == 2
        [factors(n), injectedmassdimension] = unit_factor(units{n}, n);
    else
        factors(n) = unit_factor(units{n}, n);
    end
    if isnan(factors(n)) && (present(n) || isfield(inputs, unitnames{n}))
        warning('PET2BIDS:RadioUnits', 'Unsupported or incompatible %s.', unitnames{n});
    end
    if present(n)
        value = inputs.(names{n});
        dataout.(outputnames{n}) = value;
        dataout.(outputunitnames{n}) = units{n};
        if ischar(value) || (isstring(value) && isscalar(value))
            value = str2double(value);
        end
        if isnumeric(value) && isscalar(value) && isreal(value) && ...
                isfinite(value) && value >= 0 && ~(n == 5 && value == 0)
            values(n) = double(value) * factors(n);
        end
    elseif n == 5 && isfield(inputs, unitnames{n}) && ...
            is_supplied(inputs.(unitnames{n}))
        dataout.(outputunitnames{n}) = units{n};
    end
end

% Work internally in Bq; InjectedMass in g or mol; Bq/g; Bq/mol; and g/mol.
% Each row is
% [target, first input, second input, divide (1) or multiply (0)].
% Use supplied inputs only: inferred values do not overwrite measurements
% or become new evidence for further consistency checks.
relations = [];
if strcmp(injectedmassdimension, 'mass')
    relations = [3 1 2 1; 2 1 3 1; 1 2 3 0];
elseif strcmp(injectedmassdimension, 'amount')
    relations = [4 1 2 1; 2 1 4 1; 1 2 4 0];
end
relations = [relations; 3 4 5 1; 5 4 3 1; 4 5 3 0];
for r = 1:size(relations, 1)
    target = relations(r, 1);
    a = relations(r, 2);
    b = relations(r, 3);
    if ~present(a) || ~present(b)
        continue
    end
    inferred = NaN;
    if isfinite(values(a)) && isfinite(values(b))
        if relations(r, 4)
            if values(b) ~= 0
                inferred = values(a) / values(b);
            else
                warning('PET2BIDS:RadioZeroDenominator', ...
                    'Cannot infer %s from zero %s.', ...
                    outputnames{target}, outputnames{b});
            end
        else
            inferred = values(a) * values(b);
        end
    end
    inferred = inferred / factors(target);
    if isfinite(inferred)
        if isfield(dataout, outputnames{target})
            % Includes a previous independent estimate of the same quantity.
            supplied = dataout.(outputnames{target});
            if ischar(supplied) || (isstring(supplied) && isscalar(supplied))
                supplied = str2double(supplied);
            end
            if isnumeric(supplied) && isscalar(supplied) && isreal(supplied) && ...
                    isfinite(supplied) && abs(supplied - inferred) > ...
                    1e-12 + 1e-5 * max(abs(supplied), abs(inferred))
                warning('PET2BIDS:RadioMismatch', ...
                    'Inferred %s does not match %s and %s; check values and units.', ...
                    outputnames{target}, outputnames{a}, outputnames{b});
            end
        end
        if ~present(target) && (~isfield(dataout, outputnames{target}) || ...
                isequal(dataout.(outputnames{target}), 'n/a'))
            dataout.(outputnames{target}) = inferred;
            dataout.(outputunitnames{target}) = units{target};
        end
    elseif ~present(target) && ~isfield(dataout, outputnames{target})
        dataout.(outputnames{target}) = 'n/a';
        dataout.(outputunitnames{target}) = 'n/a';
    end
end
end

function result = is_supplied(value)
% Treat empty character and string template placeholders as missing.
if isstring(value) && isscalar(value)
    result = ~ismissing(value) && strlength(value) > 0;
else
    result = ~isempty(value);
end
end

function result = is_alias_supplied(value)
% Treat blank and null-like molecular-weight aliases as missing.
result = is_supplied(value);
if result && (ischar(value) || (isstring(value) && isscalar(value)))
    value = strtrim(char(value));
    result = ~isempty(value) && ~strcmpi(value, 'none');
end
end

function [factor, dimension] = unit_factor(unit, quantity)
% Return conversion to the canonical unit, or NaN for incompatible units.
factor = NaN;
dimension = '';
if ~(ischar(unit) || (isstring(unit) && isscalar(unit)))
    return
end
unit = strrep(strrep(strtrim(char(unit)), 'µ', 'u'), 'μ', 'u');
parts = strsplit(unit, '/');
kinds = {'activity', 'mass', 'activity', 'activity', 'mass'};
denominators = {'', '', 'mass', 'amount', 'amount'};
if quantity == 2 && numel(parts) == 1
    factor = base_factor(parts{1}, 'mass');
    if isfinite(factor)
        dimension = 'mass';
    else
        factor = base_factor(parts{1}, 'amount');
        if isfinite(factor)
            dimension = 'amount';
        end
    end
elseif quantity == 1 && numel(parts) == 1
    factor = base_factor(parts{1}, kinds{quantity});
elseif quantity >= 3 && numel(parts) == 2
    factor = base_factor(parts{1}, kinds{quantity}) / ...
        base_factor(parts{2}, denominators{quantity});
end
end

function factor = base_factor(unit, kind)
switch kind
    case 'activity'
        labels = {'Bq', 'kBq', 'MBq', 'GBq', 'TBq', 'Ci', 'mCi', 'uCi'};
        scales = [1 1e3 1e6 1e9 1e12 3.7e10 3.7e7 3.7e4];
    case 'mass'
        labels = {'kg', 'g', 'mg', 'ug', 'ng'};
        scales = [1e3 1 1e-3 1e-6 1e-9];
    case 'amount'
        labels = {'mol', 'mmol', 'umol', 'nmol', 'pmol'};
        scales = [1 1e-3 1e-6 1e-9 1e-12];
end
index = find(strcmp(strtrim(unit), labels), 1);
factor = NaN;
if ~isempty(index)
    factor = scales(index);
end
end

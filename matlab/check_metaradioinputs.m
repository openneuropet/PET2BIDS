function dataout = check_metaradioinputs(varargin)
% Check radiotracer metadata and infer missing quantities with consistent units.
%
% :format: dataout = check_metaradioinputs('Name', value, ...)
%          A cell array of name/value pairs is also accepted.
%
% :param InjectedRadioactivity: default MBq
% :param InjectedMass: default ug
% :param SpecificRadioactivity: default Bq/g (NOT numerically equal to MBq/ug)
% :param MolarActivity: default GBq/umol
% :param MolecularWeight: default g/mol
%
% Each quantity accepts a corresponding <Name>Units argument. Activity units
% Bq, kBq, MBq, GBq, TBq, Ci, mCi, uCi; mass units kg, g, mg, ug, ng;
% and amount units mol, mmol, umol, nmol, pmol are supported, including ratios
% commensurate with Bq/g, Bq/mol and g/mol. Micro signs are accepted as 'u'.
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
inputs = struct();
for n = 1:2:numel(varargin)
    key = varargin{n};
    if ~(ischar(key) || (isstring(key) && isscalar(key)))
        error('PET2BIDS:RadioInputPairs', 'Input names must be text.');
    end
    allnames = [names unitnames];
    index = find(strcmpi(key, allnames), 1);
    if ~isempty(index)
        inputs.(allnames{index}) = varargin{n+1};
    end
end

dataout = [];
present = false(1, 5);
values = nan(1, 5);
factors = nan(1, 5);
units = defaults;
for n = 1:5
    present(n) = isfield(inputs, names{n}) && ~isempty(inputs.(names{n}));
    if isfield(inputs, unitnames{n}) && ~isempty(inputs.(unitnames{n}))
        units{n} = inputs.(unitnames{n});
    end
    factors(n) = unit_factor(units{n}, n);
    if isnan(factors(n)) && (present(n) || isfield(inputs, unitnames{n}))
        warning('PET2BIDS:RadioUnits', 'Unsupported or incompatible %s.', unitnames{n});
    end
    if present(n)
        value = inputs.(names{n});
        dataout.(names{n}) = value;
        dataout.(unitnames{n}) = units{n};
        if ischar(value) || (isstring(value) && isscalar(value))
            value = str2double(value);
        end
        if isnumeric(value) && isscalar(value) && isreal(value) && ...
                isfinite(value) && value >= 0 && ~(n == 5 && value == 0)
            values(n) = double(value) * factors(n);
        end
    end
end

% Work internally in Bq, g, Bq/g, Bq/mol, g/mol. Each row is
% [target, first input, second input, divide (1) or multiply (0)].
% Use supplied inputs only: inferred values do not overwrite measurements
% or become new evidence for further consistency checks.
relations = [3 1 2 1; 2 1 3 1; 1 2 3 0; ...
             3 4 5 1; 5 4 3 1; 4 5 3 0];
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
                    'Cannot infer %s from zero %s.', names{target}, names{b});
            end
        else
            inferred = values(a) * values(b);
        end
    end
    inferred = inferred / factors(target);
    if isfinite(inferred)
        if isfield(dataout, names{target})
            % Includes a previous independent estimate of the same quantity.
            supplied = dataout.(names{target});
            if ischar(supplied) || (isstring(supplied) && isscalar(supplied))
                supplied = str2double(supplied);
            end
            if isnumeric(supplied) && isscalar(supplied) && isreal(supplied) && ...
                    isfinite(supplied) && abs(supplied - inferred) > ...
                    1e-12 + 1e-5 * max(abs(supplied), abs(inferred))
                warning('PET2BIDS:RadioMismatch', ...
                    'Inferred %s does not match %s and %s; check values and units.', ...
                    names{target}, names{a}, names{b});
            end
        end
        if ~present(target) && (~isfield(dataout, names{target}) || ...
                isequal(dataout.(names{target}), 'n/a'))
            dataout.(names{target}) = inferred;
            dataout.(unitnames{target}) = units{target};
        end
    elseif ~present(target) && ~isfield(dataout, names{target})
        dataout.(names{target}) = 'n/a';
        dataout.(unitnames{target}) = 'n/a';
    end
end
end

function factor = unit_factor(unit, quantity)
% Return conversion to the canonical unit, or NaN for incompatible units.
factor = NaN;
if ~(ischar(unit) || (isstring(unit) && isscalar(unit)))
    return
end
unit = strrep(strrep(strtrim(char(unit)), 'µ', 'u'), 'μ', 'u');
parts = strsplit(unit, '/');
kinds = {'activity', 'mass', 'activity', 'activity', 'mass'};
denominators = {'', '', 'mass', 'amount', 'amount'};
if quantity <= 2 && numel(parts) == 1
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

function sorted_names = sort_dcm(folder,method,pattern)

% sort_dcm.m
% Sorts DICOM filenames naturally, or checks their acquisition order.
% Numeric stems are sorted numerically; other names use natural ordering.
% Temporary sorting keys never rename files on disk.
%
% FORMAT sorted_names = sort_dcm(folder,method,pattern)
%
% INPUTS
%   folder - The path to the folder containing the DICOM files.
%   method - 'name' (default): numeric/natural filename order, without reading headers.
%            'acquisition_time': read all headers and sort by acquisition time.
%            'auto': read all headers to check natural filename order; retain it
%            when chronological, otherwise warn and sort by acquisition time.
%            Use 'auto' when downstream processing requires chronological volumes.
%            Checked modes require valid AcquisitionDate and AcquisitionTime.
%            Order is by date, then time, including scans crossing midnight.
%            Files with .dcm or .ima extensions (case insensitive), and files
%            without extensions, are included. Extensionless files are assumed to be DICOM.
%            Subfolders are not searched.
%
%   pattern - Optional regular expression applied to the filename stem.
%             Requires a named integer token 'frame'; 'slice' is optional.
%             Sorts by frame, then slice, with natural filename ties.
%             Every filename must match. Example:
%             '^slice(?<slice>\d+)_frame(?<frame>\d+)$'
%             In checked modes this is the initial order and breaks time ties.
%
% OUTPUTS
%   sorted_names - A row cell array of file names, without folder paths.
%                  Numbers anywhere in the name are compared as if zero-padded:
%                  1, 2, 10, 100 or subject name 1, subject name 2, subject name 10.
%                  Repeated whitespace is treated as a single space for sorting.
%                  Original filenames are returned unchanged; alphabetical
%                  ordering breaks ties between equivalent padded names.
%                  Equal acquisition dates/times retain the filename order.
%
% Cyril Pernet 2026

% Validate inputs and accept either character vectors or scalar strings.
narginchk(1,3);
if nargin < 3
    pattern = '';
end
if isstring(pattern) && isscalar(pattern)
    pattern = char(pattern);
end
if ~ischar(pattern) || (~isempty(pattern) && size(pattern,1) ~= 1)
    error('sort_dcm:InvalidPattern','pattern must be a character vector or scalar string.');
end
if nargin < 2
    method = 'name';
end
if isstring(folder) && isscalar(folder)
    folder = char(folder);
end
if ~ischar(folder) || isempty(folder) || size(folder,1) ~= 1 || ~isfolder(folder)
    error('sort_dcm:InvalidFolder','folder must be the path to an existing folder.');
end
if isstring(method) && isscalar(method)
    method = char(method);
end
if ~ischar(method) || size(method,1) ~= 1 || ...
        ~any(strcmpi(method,{'name','acquisition_time','auto'}))
    error('sort_dcm:InvalidMethod','method must be ''name'', ''acquisition_time'' or ''auto''.');
end

% Select candidate DICOM filenames without reading file contents.
files            = dir(folder);
names            = {files(~[files.isdir]).name};
is_dicom         = ~cellfun('isempty',regexpi(names,'\.(dcm|ima)$','once'));
is_extensionless = cellfun('isempty',regexp(names,'\.','once'));
names            = sort(names(is_dicom | is_extensionless)); % Break numeric ties.
sorted_names = reshape(names,1,[]);
if isempty(sorted_names)
    return
end

% Plain numbered files use numeric values, independent of file count.
stems = regexprep(sorted_names,'(?i)\.(dcm|ima)$','');
significant = regexprep(stems,'^0+(?=\d)','');
numeric_stems = all(~cellfun('isempty',regexp(stems,'^\d+$','once')));
if isempty(pattern) && numeric_stems && all(cellfun('length',significant) <= 15)
    [~,order] = sort(cellfun(@str2double,stems));
else
    % Mixed names and long integers use exact text keys. This also establishes
    % natural filename order to break ties between matching frame/slice keys.
    [~,order] = sort(natural_keys(sorted_names));
end
sorted_names = sorted_names(order);
stems = stems(order);
if ~isempty(pattern)
    try
        tokens = regexp(stems,pattern,'names','once');
    catch
        error('sort_dcm:InvalidPattern','pattern must be a valid regular expression.');
    end
    keys = cell(size(stems));
    for f = 1:numel(stems)
        token = tokens{f};
        if isempty(token) || ~isfield(token,'frame') || ...
                isempty(regexp(token.frame,'^\d+$','once'))
            error('sort_dcm:InvalidPattern', ...
                'Pattern must match a numeric named frame token in %s.',sorted_names{f});
        end
        keys{f} = token.frame;
        if isfield(token,'slice')
            if isempty(regexp(token.slice,'^\d+$','once'))
                error('sort_dcm:InvalidPattern', ...
                    'Pattern must match a numeric named slice token in %s.',sorted_names{f});
            end
            keys{f} = [keys{f} '_' token.slice];
        end
    end
    [~,order] = sort(natural_keys(keys));
    sorted_names = sorted_names(order);
end

% The fast name method never reads headers. Checked modes read each once.
if ~strcmpi(method,'name')
    dates = zeros(numel(sorted_names),1);
    times = zeros(numel(sorted_names),1);
    for f = 1:numel(sorted_names)
        info = dicominfo(fullfile(folder,sorted_names{f}));
        [dates(f),times(f)] = dicom_acquisition_datetime(info,sorted_names{f},'sort_dcm');
    end
    if strcmpi(method,'auto')
        if all(diff(dates) > 0 | (diff(dates) == 0 & diff(times) >= 0))
            return
        end
        warning('sort_dcm:NameOrderMismatch', ...
            ['Filename order does not follow acquisition date/time in %s; ' ...
             'returning acquisition-time order.'],folder);
    end
    % Use the existing filename position to break ties between equal dates/times.
    [~,order]    = sortrows([dates times (1:numel(times))'],[1 2 3]);
    sorted_names = sorted_names(order);
end
end

function keys = natural_keys(names)
% Build temporary keys, keeping the returned filenames unchanged. Normalize
% repeated spaces so 'subject name  3' sorts between 'subject name 2' and 10.
keys                     = regexprep(names,'\s+',' ');
[starts,ends,~,digits]    = regexp(keys,'\d+');
all_digits               = [digits{:}];
if ~isempty(all_digits)
    % Left-pad every numeric part to a common width: 1, 2, 10 become 01, 02, 10.
    % Keep numbers as text to preserve precision even for long DICOM IDs.
    width = max(cellfun('length',all_digits));
    for f = 1:numel(keys)
        % Replace from right to left so earlier character positions stay valid.
        for n = numel(digits{f}):-1:1
            number  = regexprep(digits{f}{n},'^0+(?=\d)','');
            padding = repmat('0',1,width-length(number));
            keys{f} = [keys{f}(1:starts{f}(n)-1) padding number ...
                       keys{f}(ends{f}(n)+1:end)];
        end
    end
end
end

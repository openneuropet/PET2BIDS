function sorted_names = sort_dcm(folder,method)

% sort_dcm.m
% Sorts DICOM filenames naturally, or checks their acquisition order.
% Numeric parts are zero-padded in temporary sorting keys only; files on
% disk are never renamed. Padding fixes 1, 10, 2 but cannot repair filenames
% whose numbers do not follow the acquisition sequence.
%
% FORMAT sorted_names = sort_dcm(folder,method)
%
% INPUTS
%   folder - The path to the folder containing the DICOM files.
%   method - 'name' (default): natural filename order, without reading headers.
%            'acquisition_time': read all headers and sort by acquisition time.
%            'auto': read all headers to check natural filename order; retain it
%            when chronological, otherwise warn and sort by acquisition time.
%            Use 'auto' when downstream processing requires chronological volumes.
%            Acquisition times are ordered within a day, without date information.
%            Files with .dcm or .ima extensions (case insensitive), and files
%            without extensions, are included. Extensionless files are assumed to be DICOM.
%            Subfolders are not searched.
%
% OUTPUTS
%   sorted_names - A row cell array of file names, without folder paths.
%                  Numbers anywhere in the name are compared as if zero-padded:
%                  1, 2, 10, 100 or subject name 1, subject name 2, subject name 10.
%                  Repeated whitespace is treated as a single space for sorting.
%                  Original filenames are returned unchanged; alphabetical
%                  ordering breaks ties between equivalent padded names.
%                  Equal acquisition times retain the filename order.
%
% Cyril Pernet 2026

% Validate inputs and accept either character vectors or scalar strings.
narginchk(1,2);
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

% Build temporary keys, keeping the returned filenames unchanged. Normalize
% repeated spaces so 'subject name  3' sorts between 'subject name 2' and 10.
keys                     = regexprep(sorted_names,'\s+',' ');
[starts,ends,~,digits]    = regexp(keys,'\d+');
all_digits               = [digits{:}];
if ~isempty(all_digits)
    % Left-pad every numeric part to a common width: 1, 2, 10 become 01, 02, 10.
    % Keep numbers as text to preserve precision even for long DICOM IDs.
    width = max(cellfun('length',all_digits));
    for f = 1:numel(keys)
        % Replace from right to left so earlier character positions stay valid.
        for n = numel(digits{f}):-1:1
            number  = digits{f}{n};
            padding = repmat('0',1,width-length(number));
            keys{f} = [keys{f}(1:starts{f}(n)-1) padding number ...
                       keys{f}(ends{f}(n)+1:end)];
        end
    end
end
[~,order]    = sort(keys);
sorted_names = sorted_names(order);

% The fast name method never reads headers. Checked modes read each once.
if ~strcmpi(method,'name')
    times = zeros(numel(sorted_names),1);
    for f = 1:numel(sorted_names)
        info = dicominfo(fullfile(folder,sorted_names{f}));
        if ~isfield(info,'AcquisitionTime')
            error('sort_dcm:MissingAcquisitionTime', ...
                'Missing AcquisitionTime in %s.',sorted_names{f});
        end
        value = info.AcquisitionTime;
        if isstring(value) && isscalar(value)
            value = char(value);
        end
        if ~ischar(value) || size(value,1) ~= 1
            error('sort_dcm:InvalidAcquisitionTime', ...
                'Invalid AcquisitionTime in %s.',sorted_names{f});
        end
        value = strtrim(value);
        % DICOM TM permits HH, HHMM or HHMMSS with optional fractional seconds.
        if isempty(regexp(value,'^(\d{2}|\d{4}|\d{6}(\.\d{1,6})?)$','once'))
            error('sort_dcm:InvalidAcquisitionTime', ...
                'Invalid AcquisitionTime in %s.',sorted_names{f});
        end
        % Convert to seconds since midnight; omitted components stay zero.
        hours   = str2double(value(1:2));
        minutes = 0;
        seconds = 0;
        if length(value) >= 4
            minutes = str2double(value(3:4));
        end
        if length(value) >= 6
            seconds = str2double(value(5:end));
        end
        % Allow the DICOM leap-second value of 60.
        if hours > 23 || minutes > 59 || seconds >= 61
            error('sort_dcm:InvalidAcquisitionTime', ...
                'Invalid AcquisitionTime in %s.',sorted_names{f});
        end
        times(f) = hours*3600 + minutes*60 + seconds;
    end
    if strcmpi(method,'auto')
        if all(diff(times) >= 0)
            return
        end
        warning('sort_dcm:NameOrderMismatch', ...
            ['Natural filename order does not follow acquisition time in %s; ' ...
             'returning acquisition-time order.'],folder);
    end
    % Use the existing filename position to break ties between equal times.
    [~,order]    = sortrows([times (1:numel(times))'],[1 2]);
    sorted_names = sorted_names(order);
end
end

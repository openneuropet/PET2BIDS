function [day,seconds] = dicom_acquisition_datetime(info,filename,caller)
% Validate AcquisitionDate/Time and return separate day and time sorting keys.
% Keeping seconds separate preserves fractional-second precision across dates.
% No StudyDate fallback: a study can contain acquisitions on different days.
if nargin < 2, filename = ''; end
if nargin < 3, caller = 'sort_dcm'; end

if ~isfield(info,'AcquisitionTime')
    error([caller ':MissingAcquisitionTime'],'Missing AcquisitionTime in %s.',filename);
end
value = info.AcquisitionTime;
if isstring(value) && isscalar(value), value = char(value); end
if ~ischar(value) || size(value,1) ~= 1
    error([caller ':InvalidAcquisitionTime'],'Invalid AcquisitionTime in %s.',filename);
end
value = strtrim(value);
if isempty(regexp(value,'^(\d{2}|\d{4}|\d{6}(\.\d{1,6})?)$','once'))
    error([caller ':InvalidAcquisitionTime'],'Invalid AcquisitionTime in %s.',filename);
end
hours = str2double(value(1:2));
minutes = 0;
seconds = 0;
if length(value) >= 4, minutes = str2double(value(3:4)); end
if length(value) >= 6, seconds = str2double(value(5:end)); end
% Keep the permitted leap-second value of 60.
if hours > 23 || minutes > 59 || seconds >= 61
    error([caller ':InvalidAcquisitionTime'],'Invalid AcquisitionTime in %s.',filename);
end
seconds = hours*3600 + minutes*60 + seconds;

if ~isfield(info,'AcquisitionDate') || isempty(info.AcquisitionDate)
    error([caller ':MissingAcquisitionDate'],'Missing AcquisitionDate in %s.',filename);
end
value = info.AcquisitionDate;
if isstring(value) && isscalar(value), value = char(value); end
if ~ischar(value) || size(value,1) ~= 1
    error([caller ':InvalidAcquisitionDate'],'Invalid AcquisitionDate in %s.',filename);
end
value = strtrim(value);
if isempty(regexp(value,'^\d{8}$','once'))
    error([caller ':InvalidAcquisitionDate'],'Invalid AcquisitionDate in %s.',filename);
end
parts = [str2double(value(1:4)) str2double(value(5:6)) str2double(value(7:8))];
if parts(1) < 1 || parts(2) < 1 || parts(2) > 12 || parts(3) < 1 || parts(3) > 31
    error([caller ':InvalidAcquisitionDate'],'Invalid AcquisitionDate in %s.',filename);
end
day = datenum(parts(1),parts(2),parts(3));
actual = datevec(day);
% datenum normalizes impossible dates, so check the calendar components again.
if ~isequal(actual(1:3),parts)
    error([caller ':InvalidAcquisitionDate'],'Invalid AcquisitionDate in %s.',filename);
end
end

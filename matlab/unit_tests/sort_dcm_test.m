function tests = sort_dcm_test
% Test fast natural ordering and checked chronological fallback independently.
tests = functiontests(localfunctions);
end

function setupOnce(testCase)
addpath(fileparts(fileparts(mfilename('fullpath'))));
testCase.TestData.root = tempname;
mkdir(testCase.TestData.root);
basefile = fullfile(testCase.TestData.root,'base.dcm');
dicomwrite(uint16(ones(2)),basefile);
testCase.TestData.base = dicominfo(basefile);
testCase.TestData.base.AcquisitionDate = '20260929';
end

function teardownOnce(testCase)
rmdir(testCase.TestData.root,'s');
end

function testDefaultPadsNumericNamesWithoutReadingFiles(testCase)
folder = fullfile(testCase.TestData.root,'names');
mkdir(folder);
names = {'10.dcm','2.dcm','1.dcm','001.dcm','100.dcm'};
for k = 1:numel(names)
    fid = fopen(fullfile(folder,names{k}),'w'); fclose(fid);
end
% Empty files prove that the default does not read DICOM headers.
expected = {'001.dcm','1.dcm','2.dcm','10.dcm','100.dcm'};
verifyEqual(testCase,sort_dcm(folder),expected);
verifyEqual(testCase,sort_dcm(folder,'name'),expected);
verifyEqual(testCase,sort({dir(fullfile(folder,'*.dcm')).name}),sort(names));
end

function testAutoKeepsChronologicalNames(testCase)
folder = fixture(testCase,'ordered',{'10.dcm','2.dcm','1.dcm'}, ...
    {'120003','120002','120001'});
verifyWarningFree(testCase,@() sort_dcm(folder,'auto'));
verifyEqual(testCase,sort_dcm(folder,'auto'),{'1.dcm','2.dcm','10.dcm'});
end

function testAutoRepairsInterleavedFrames(testCase)
folder = fixture(testCase,'mixed',{'1.dcm','2.dcm','3.dcm','4.dcm'}, ...
    {'120002','120001','120002','120001'});
verifyWarning(testCase,@() sort_dcm(folder,'auto'),'sort_dcm:NameOrderMismatch');
verifyEqual(testCase,sort_dcm(folder,'auto'),{'2.dcm','4.dcm','1.dcm','3.dcm'});
verifyEqual(testCase,sort_dcm(folder,'acquisition_time'),{'2.dcm','4.dcm','1.dcm','3.dcm'});
verifyEqual(testCase,sort_dcm(folder,'name'),{'1.dcm','2.dcm','3.dcm','4.dcm'});
end

function testAutoRejectsMissingAcquisitionTime(testCase)
folder = fullfile(testCase.TestData.root,'missing');
mkdir(folder);
info = testCase.TestData.base;
if isfield(info,'AcquisitionTime'), info = rmfield(info,'AcquisitionTime'); end
dicomwrite(uint16(ones(2)),fullfile(folder,'1.dcm'),info,'CreateMode','Copy');
verifyError(testCase,@() sort_dcm(folder,'auto'),'sort_dcm:MissingAcquisitionTime');
end

function folder = fixture(testCase,name,names,times,dates)
if nargin < 5, dates = repmat({'20260929'},size(times)); end
folder = fullfile(testCase.TestData.root,name);
mkdir(folder);
for k = 1:numel(names)
    info = testCase.TestData.base;
    info.AcquisitionTime = times{k};
    info.AcquisitionDate = dates{k};
    dicomwrite(uint16(ones(2)),fullfile(folder,names{k}),info,'CreateMode','Copy');
end
end

function testMidnightCrossingKeepsChronologicalNames(testCase)
folder = fixture(testCase,'midnight',{'1.dcm','2.dcm','3.dcm'}, ...
    {'235959.999999','000000','000000.000001'}, ...
    {'20261231','20270101','20270101'});
verifyWarningFree(testCase,@() sort_dcm(folder,'auto'));
verifyEqual(testCase,sort_dcm(folder,'acquisition_time'),{'1.dcm','2.dcm','3.dcm'});
end

function testDatesTakePriorityOverIncreasingTimes(testCase)
folder = fixture(testCase,'dates',{'1.dcm','2.dcm'}, ...
    {'000001','235959'}, {'20270101','20261231'});
verifyWarning(testCase,@() sort_dcm(folder,'auto'),'sort_dcm:NameOrderMismatch');
verifyEqual(testCase,sort_dcm(folder,'acquisition_time'),{'2.dcm','1.dcm'});
end

function testEqualTimesOnDifferentDates(testCase)
folder = fixture(testCase,'equal_times_dates',{'1.dcm','2.dcm'}, ...
    {'120000','120000'}, {'20261001','20260930'});
verifyEqual(testCase,sort_dcm(folder,'acquisition_time'),{'2.dcm','1.dcm'});
end

function testCheckedModesRejectMissingDates(testCase)
folder = fullfile(testCase.TestData.root,'missing_dates');
mkdir(folder);
info = rmfield(testCase.TestData.base,'AcquisitionDate');
info.AcquisitionTime = '120001';
dicomwrite(uint16(ones(2)),fullfile(folder,'1.dcm'),info,'CreateMode','Copy');
verifyError(testCase,@() sort_dcm(folder,'auto'),'sort_dcm:MissingAcquisitionDate');
verifyError(testCase,@() sort_dcm(folder,'acquisition_time'),'sort_dcm:MissingAcquisitionDate');
verifyEqual(testCase,sort_dcm(folder),{'1.dcm'});
end

function testCalendarValidationAndFractionalPrecision(testCase)
info = struct('AcquisitionDate','20240229','AcquisitionTime','235959.999999');
[day,seconds] = dicom_acquisition_datetime(info,'fixture');
verifyEqual(testCase,day,datenum(2024,2,29));
verifyEqual(testCase,seconds,86399.999999,'AbsTol',1e-10);
for value = {'20230229','20260431','20261301','20260001','00000101','2026-10-01'}
    info.AcquisitionDate = value{1};
    verifyError(testCase,@() dicom_acquisition_datetime(info,'fixture'), ...
        'sort_dcm:InvalidAcquisitionDate');
end
end

function testNumericStemsAcrossWidthsAndExtensions(testCase)
folder = namefixture(testCase,'numeric', ...
    {'1001.dcm','10.IMA','1000.dcm','1','100.dcm','2.DCM','notes.txt'});
mkdir(fullfile(folder,'3.dcm')); % Directories must not become candidates.
verifyEqual(testCase,sort_dcm(folder), ...
    {'1','2.DCM','10.IMA','100.dcm','1000.dcm','1001.dcm'});
end

function testNaturalNamesAndExactLongIntegers(testCase)
folder = namefixture(testCase,'natural', ...
    {'image10.dcm','image2.dcm','image1.dcm'});
verifyEqual(testCase,sort_dcm(folder),{'image1.dcm','image2.dcm','image10.dcm'});
folder = namefixture(testCase,'long', ...
    {'9007199254740993.dcm','9007199254740992.dcm','2.dcm'});
verifyEqual(testCase,sort_dcm(folder), ...
    {'2.dcm','9007199254740992.dcm','9007199254740993.dcm'});
end

function testPatternOrdersFrameBeforeSlice(testCase)
folder = namefixture(testCase,'pattern', ...
    {'slice2_frame10.dcm','slice10_frame2.dcm','slice2_frame2.dcm'});
pattern = '^slice(?<slice>\d+)_frame(?<frame>\d+)$';
verifyEqual(testCase,sort_dcm(folder,'name',pattern), ...
    {'slice2_frame2.dcm','slice10_frame2.dcm','slice2_frame10.dcm'});
verifyEqual(testCase,sort_dcm(folder,'name','^slice\d+_frame(?<frame>\d+)$'), ...
    {'slice2_frame2.dcm','slice10_frame2.dcm','slice2_frame10.dcm'});
verifyError(testCase,@() sort_dcm(folder,'name','^(?<frame>\d+)$'), ...
    'sort_dcm:InvalidPattern');
verifyError(testCase,@() sort_dcm(folder,'name','(?<frame>\d+)[z-a]'),'sort_dcm:InvalidPattern');
verifyError(testCase,@() sort_dcm(folder,'name',42),'sort_dcm:InvalidPattern');
verifyError(testCase,@() sort_dcm(folder,'name','^slice(?<slice>\d+)_frame\d+$'), ...
    'sort_dcm:InvalidPattern');
end

function testPatternBreaksEqualAcquisitionTimes(testCase)
folder = fixture(testCase,'pattern_times', ...
    {'slice2_frame10.dcm','slice10_frame2.dcm','slice2_frame2.dcm'}, ...
    {'120001','120001','120001'});
pattern = '^slice(?<slice>\d+)_frame(?<frame>\d+)$';
expected = {'slice2_frame2.dcm','slice10_frame2.dcm','slice2_frame10.dcm'};
verifyEqual(testCase,sort_dcm(folder,'auto',pattern),expected);
verifyEqual(testCase,sort_dcm(folder,'acquisition_time',pattern),expected);
end

function folder = namefixture(testCase,name,names)
folder = fullfile(testCase.TestData.root,name);
mkdir(folder);
for k = 1:numel(names)
    fid = fopen(fullfile(folder,names{k}),'w'); fclose(fid);
end
end

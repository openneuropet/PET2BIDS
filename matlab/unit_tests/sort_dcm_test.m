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

function folder = fixture(testCase,name,names,times)
folder = fullfile(testCase.TestData.root,name);
mkdir(folder);
for k = 1:numel(names)
    info = testCase.TestData.base;
    info.AcquisitionTime = times{k};
    dicomwrite(uint16(ones(2)),fullfile(folder,names{k}),info,'CreateMode','Copy');
end
end

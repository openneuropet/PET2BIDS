function tests = updatejsonpetfile_test
% Regression coverage for per-volume PET factors with interleaved filenames.
tests = functiontests(localfunctions);
end

function setupOnce(testCase)
testCase.TestData.root = tempname;
mkdir(testCase.TestData.root);
addpath(fileparts(fileparts(mfilename('fullpath'))));
basefile = fullfile(testCase.TestData.root,'base.dcm');
dicomwrite(uint16(ones(2)),basefile);
testCase.TestData.base = dicominfo(basefile);
testCase.TestData.base.AcquisitionDate = '20260929';
end

function teardownOnce(testCase)
rmdir(testCase.TestData.root,'s');
end

function testInterleavedSlices(testCase)
[jsonfile,source] = fixture(testCase,'interleaved',3,2,false);
updatejsonpetfile(jsonfile,struct,[],source,'acquisition_time');
result = jsondecode(fileread(jsonfile));
verifyEqual(testCase,result.ScatterFraction(:),[0.1;0.2;0.3],'AbsTol',1e-7);
verifyEqual(testCase,result.DecayCorrectionFactor(:),[1.1;1.2;1.3],'AbsTol',1e-7);
end

function testCompressedNiftiAndInferredFolder(testCase)
[jsonfile,source] = fixture(testCase,'compressed',3,2,true,true);
updatejsonpetfile(jsonfile,struct,struct('Filename',fullfile(source,'1.dcm')));
result = jsondecode(fileread(jsonfile));
verifyEqual(testCase,result.ScatterFraction(:),[0.1;0.2;0.3],'AbsTol',1e-7);
verifyEqual(testCase,result.DecayCorrectionFactor(:),[1.1;1.2;1.3],'AbsTol',1e-7);
end

function testUserOverrides(testCase)
[jsonfile,source] = fixture(testCase,'overrides',3,2,false);
explicit = struct('ScatterFraction',[0.4 0.5 0.6], ...
    'DecayCorrectionFactor',[2.1 2.2 2.3]);
updatejsonpetfile(jsonfile,explicit,[],source);
result = jsondecode(fileread(jsonfile));
verifyEqual(testCase,result.ScatterFraction(:),explicit.ScatterFraction(:));
verifyEqual(testCase,result.DecayCorrectionFactor(:),explicit.DecayCorrectionFactor(:));
end

function testSingleVolumeArraysRemainFlat(testCase)
[jsonfile,source] = fixture(testCase,'single',1,2,false);
updatejsonpetfile(jsonfile,struct,[],source);
before = fileread(jsonfile);
updatejsonpetfile(jsonfile);
verifyEqual(testCase,fileread(jsonfile),before);
verifyNotEmpty(testCase,regexp(before,'"ScatterFraction":\s*\[0\.1\]','once'));
verifyNotEmpty(testCase,regexp(before,'"DecayCorrectionFactor":\s*\[1\.1\]','once'));
end

function testAutoOrdering(testCase)
[jsonfile,source] = fixture(testCase,'auto',3,2,false);
updatejsonpetfile(jsonfile,struct,struct('Filename',fullfile(source,'1.dcm')),[],'auto');
result = jsondecode(fileread(jsonfile));
verifyEqual(testCase,result.ScatterFraction(:),[0.1;0.2;0.3],'AbsTol',1e-7);
verifyEqual(testCase,result.DecayCorrectionFactor(:),[1.1;1.2;1.3],'AbsTol',1e-7);
end

function testDefaultNameOrdering(testCase)
[jsonfile,source] = fixture(testCase,'name',3,5,false,true);
output = evalc('updatejsonpetfile(jsonfile,struct,[],source);');
verifyNotEmpty(testCase,strfind(output,'VolumeTimes (name; seconds since midnight): [43201 43202 43203]'));
verifyEmpty(testCase,strfind(output,'DICOM name sorting does not work'));
result = jsondecode(fileread(jsonfile));
verifyEqual(testCase,result.ScatterFraction(:),[0.1;0.2;0.3],'AbsTol',1e-7);
verifyEqual(testCase,result.DecayCorrectionFactor(:),[1.1;1.2;1.3],'AbsTol',1e-7);
end

function testNameOrderingRetriesDecreasingVolumeTimes(testCase)
[jsonfile,source] = fixture(testCase,'name_fallback',3,2,false);
output = evalc('updatejsonpetfile(jsonfile,struct,[],source);');
verifyNotEmpty(testCase,strfind(output,'VolumeTimes (name; seconds since midnight): [43203 43201 43202]'));
verifyNotEmpty(testCase,strfind(output,'DICOM name sorting does not work'));
verifyNotEmpty(testCase,strfind(output,'VolumeTimes (acquisition_time; seconds since midnight): [43201 43202 43203]'));
result = jsondecode(fileread(jsonfile));
verifyEqual(testCase,result.ScatterFraction(:),[0.1;0.2;0.3],'AbsTol',1e-7);
verifyEqual(testCase,result.DecayCorrectionFactor(:),[1.1;1.2;1.3],'AbsTol',1e-7);
end

function testNameOrderingRetriesEqualVolumeTimes(testCase)
[jsonfile,source] = fixture(testCase,'equal_name_times',3,3,false);
output = evalc('updatejsonpetfile(jsonfile,struct,[],source);');
verifyNotEmpty(testCase,strfind(output,'VolumeTimes (name; seconds since midnight): [43203 43203 43203]'));
verifyNotEmpty(testCase,strfind(output,'DICOM name sorting does not work'));
result = jsondecode(fileread(jsonfile));
verifyEqual(testCase,result.ScatterFraction(:),[0.1;0.2;0.3],'AbsTol',1e-7);
verifyEqual(testCase,result.DecayCorrectionFactor(:),[1.1;1.2;1.3],'AbsTol',1e-7);
end

function testEqualAcquisitionTimesKeepOriginalFactors(testCase)
[jsonfile,source] = fixture(testCase,'equal_acquisition_times',3,2,false,true);
set_times(source,repmat({'120001'},1,6));
output = evalc('updatejsonpetfile(jsonfile,struct,[],source);');
verifyNotEmpty(testCase,strfind(output,'Volume acquisition dates/times'));
% Only one retry is allowed, and no ambiguous per-volume factors are committed.
verifyEqual(testCase,numel(strfind(output,'VolumeTimes (')),2);
result = jsondecode(fileread(jsonfile));
verifyEqual(testCase,result.ScatterFraction(:),0.9);
verifyEqual(testCase,result.DecayCorrectionFactor(:),9);
end

function testFractionalVolumeTimesAndMinuteBoundary(testCase)
[jsonfile,source] = fixture(testCase,'fractional_times',3,2,false,true);
set_times(source,{'120059.5','120059.5','120100','120100','120100.25','120100.25'});
output = evalc('updatejsonpetfile(jsonfile,struct,[],source);');
verifyNotEmpty(testCase,strfind(output,'VolumeTimes (name; seconds since midnight): [43259.5 43260 43260.25]'));
verifyEmpty(testCase,strfind(output,'DICOM name sorting does not work'));
result = jsondecode(fileread(jsonfile));
verifyEqual(testCase,result.ScatterFraction(:),[0.1;0.2;0.3],'AbsTol',1e-7);
end

function testSingleVolumeAtMidnight(testCase)
[jsonfile,source] = fixture(testCase,'midnight',1,2,false);
set_times(source,{'000000','000000'});
output = evalc('updatejsonpetfile(jsonfile,struct,[],source);');
verifyNotEmpty(testCase,strfind(output,'VolumeTimes (name; seconds since midnight): 0'));
verifyEmpty(testCase,strfind(output,'DICOM name sorting does not work'));
result = jsondecode(fileread(jsonfile));
verifyEqual(testCase,result.ScatterFraction(:),0.1,'AbsTol',1e-7);
end

function set_times(source,times,dates)
for k = 1:numel(times)
    filename = fullfile(source,sprintf('%d.dcm',k));
    info = dicominfo(filename);
    info.AcquisitionTime = times{k};
    if nargin >= 3, info.AcquisitionDate = dates{k}; end
    dicomwrite(dicomread(filename),filename,info,'CreateMode','Copy');
end
end

function testMidnightCrossingPreservesFrameFactors(testCase)
for method = {'name','auto','acquisition_time'}
    [jsonfile,source] = fixture(testCase,['cross_midnight_' method{1}],3,2,false,true);
    set_times(source,{'235959.5','235959.5','000000','000000','000000.000001','000000.000001'}, ...
        {'20261231','20261231','20270101','20270101','20270101','20270101'});
    output = evalc('updatejsonpetfile(jsonfile,struct,[],source,method{1});');
    verifyNotEmpty(testCase,strfind(output,'20261231 20270101 20270101'));
    verifyEmpty(testCase,strfind(output,'DICOM name sorting does not work'));
    result = jsondecode(fileread(jsonfile));
    verifyEqual(testCase,result.ScatterFraction(:),[0.1;0.2;0.3],'AbsTol',1e-7);
    verifyEqual(testCase,result.DecayCorrectionFactor(:),[1.1;1.2;1.3],'AbsTol',1e-7);
end
end

function testNameOrderingRetriesDecreasingDates(testCase)
[jsonfile,source] = fixture(testCase,'date_fallback',3,2,false);
set_times(source,repmat({'120000'},1,6), ...
    {'20261001','20260930','20260929','20261001','20260930','20260929'});
output = evalc('updatejsonpetfile(jsonfile,struct,[],source);');
verifyNotEmpty(testCase,strfind(output,'DICOM name sorting does not work'));
result = jsondecode(fileread(jsonfile));
verifyEqual(testCase,result.ScatterFraction(:),[0.1;0.2;0.3],'AbsTol',1e-7);
verifyEqual(testCase,result.DecayCorrectionFactor(:),[1.1;1.2;1.3],'AbsTol',1e-7);
end

function testMissingDatesKeepOriginalFactors(testCase)
[jsonfile,source] = fixture(testCase,'missing_date',3,2,false,true);
filename = fullfile(source,'1.dcm');
info = rmfield(dicominfo(filename),'AcquisitionDate');
dicomwrite(dicomread(filename),filename,info,'CreateMode','Copy');
output = evalc('updatejsonpetfile(jsonfile,struct,[],source);');
verifyNotEmpty(testCase,strfind(output,'Missing AcquisitionDate'));
result = jsondecode(fileread(jsonfile));
verifyEqual(testCase,result.ScatterFraction(:),0.9);
verifyEqual(testCase,result.DecayCorrectionFactor(:),9);
end

function testFrameSlicePattern(testCase)
[jsonfile,source] = fixture(testCase,'pattern',3,2,false);
% Rename the interleaved fixture so lexical/natural order puts slices first.
for slice = 1:2
    for frame = 1:3
        index = (slice-1)*3 + (3-frame+1);
        movefile(fullfile(source,sprintf('%d.dcm',index)), ...
            fullfile(source,sprintf('slice%d_frame%d.dcm',slice,frame)));
    end
end
pattern = '^slice(?<slice>\d+)_frame(?<frame>\d+)$';
updatejsonpetfile(jsonfile,struct,[],source,'name',pattern);
result = jsondecode(fileread(jsonfile));
verifyEqual(testCase,result.ScatterFraction(:),[0.1;0.2;0.3],'AbsTol',1e-7);
verifyEqual(testCase,result.DecayCorrectionFactor(:),[1.1;1.2;1.3],'AbsTol',1e-7);
end

function [jsonfile,source] = fixture(testCase,name,nframes,nslices,compressed,byVolume)
if nargin < 6, byVolume = false; end
folder = fullfile(testCase.TestData.root,name);
source = fullfile(folder,'dicom');
mkdir(source);
% The first filename belongs to the last frame. Consecutive filenames
% cycle through frames instead of grouping slices from the same volume.
for slice = 1:nslices
    for frame = 1:nframes
        if byVolume
            index = (frame-1)*nslices + slice;
        else
            index = (slice-1)*nframes + (nframes-frame+1);
        end
        info = testCase.TestData.base;
        info.AcquisitionTime = sprintf('1200%02d',frame);
        info.ScatterFractionFactor = frame/10;
        info.DecayFactor = 1+frame/10;
        dicomwrite(uint16(ones(2)),fullfile(source,sprintf('%d.dcm',index)), ...
            info,'CreateMode','Copy');
    end
end
niftiwrite(zeros(2,2,nslices,nframes,'single'),fullfile(folder,'pet.nii'), ...
    'Compressed',compressed);
jsonfile = fullfile(folder,'pet.json');
jsonwrite(jsonfile,struct('ScatterFraction',0.9,'DecayCorrectionFactor',9));
end

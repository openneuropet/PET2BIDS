function fileout = dcm2bids4pet(FileList,MetaList,varargin)

% Converts dicom image file to nifti+json calling dcm2niix augmenting
% the json file to be BIDS compliant
%
% FORMAT: fileout = dcm2bids4pet(FileList,MetaList)
%         fileout = dcm2bids4pet(FileList,MetaList,options)
%
% INPUT: FileList - Cell array of char strings with filenames and paths
%        MetaList - Cell array of structures for metadata
%         options are those pertaining to dcm2niix and must be passed as
%         key-pair values 
%            gz: 1 ..... 9 compression level (1=fastest..9=smallest, default 6)
%            a : adjacent DICOMs (images from same series always in same folder) for faster conversion (n/y, default n)
%            ba : anonymize BIDS (y/n, default y)
%            c : comment stored in NIfTI aux_file (provide up to 24 characters e.g. '-c first_visit')
%            d : directory search depth. Convert DICOMs in sub-folders of in_folder? (0..9, default 5)
%            f : filename (%a=antenna (coil) name, %b=basename, %c=comments, %d=description, %e=echo number, %f=folder name, %g=accession number, %i=ID of patient, %j=seriesInstanceUID, %k=studyInstanceUID, %m=manufacturer, %n=name of patient, %o=mediaObjectInstanceUID, %p=protocol, %r=instance number, %s=series number, %t=time, %u=acquisition number, %v=vendor, %x=study ID; %z=sequence name; default '%f_%p_%t_%s')
%            g : generate defaults file (y/n/o/i [o=only: reset and write defaults; i=ignore: reset defaults], default n)
%            i : ignore derived, localizer and 2D images (y/n, default n)
%            l : losslessly scale 16-bit integers to use dynamic range (y/n/o [yes=scale, no=no, but uint16->int16, o=original], default n)
%            m : merge 2D slices from same series regardless of echo, exposure, etc. (n/y or 0/1/2, default 2) [no, yes, auto]
%            n : only convert this series CRC number - can be used up to 16 times (default convert all)
%            o : output directory (omit to save to input folder)
%            p : Philips precise float (not display) scaling (y/n, default y)
%            v : verbose (n/y or 0/1/2, default 0) [no, yes, logorrheic]
%            w : write behavior for name conflicts (0,1,2, default 2: 0=skip duplicates, 1=overwrite, 2=add suffix)
%            x : crop 3D acquisitions (y/n/i, default n, use 'i'gnore to neither crop nor rotate 3D acquistions)
%            z : gz compress images (y/o/i/n/3, default n) [y=pigz, o=optimal pigz, i=internal:miniz, n=no, 3=no,3D]
%            bigendian : byte order (y/n/o, default o) [y=big-end, n=little-end, o=optimal/native]
%            terse : omit filename post-fixes (can cause overwrites)
%
% Example meta = get_SiemensBiograph_metadata('TimeZero','ScanStart','tracer','DASB','Radionuclide','C11', ...
%                'Radioactivity', 605.3220,'InjectedMass', 1.5934,'MolarActivity', 107.66);
%        fileout = dcm2bids4pet(folder1,meta,'gz',9,'o','mynewfolder','v',1); % change dcm2nii default
%        fileout = dcm2bids4pet({folder1,folder2,folder3},{meta}); % use the same PET meta for all subjects
%        fileout = dcm2bids4pet({folder1,folder2,folder3},{meta1,meta2,meta3}); % each subject has specific metadata info
%
% See also get_SiemensHRRT_metadata.m to generate the metadata structure
%
% Cyril Pernet - 2021
% ----------------------------------------------
% Copyright Open NeuroPET team

%% PET BIDS parameters
mandatory = {'Manufacturer','ManufacturersModelName','Units','TracerName',...
    'TracerRadionuclide','InjectedRadioactivity','InjectedRadioactivityUnits',...
    'InjectedMass','InjectedMassUnits','SpecificRadioactivity',...
    'SpecificRadioactivityUnits','ModeOfAdministration','TimeZero',...
    'ScanStart','InjectionStart','FrameTimesStart','FrameDuration',...
    'AcquisitionMode','ImageDecayCorrected','ImageDecayCorrectionTime',...
    'ReconMethodName','ReconMethodParameterLabels','ReconMethodParameterUnits',...
    'ReconMethodParameterValues','ReconFilterType','ReconFilterSize','AttenuationCorrection'};

recommended = {'InstitutionName','InstitutionAddress','InstitutionalDepartmentName',...
    'BodyPart','TracerRadLex','TracerSNOMED','TracerMolecularWeight','TracerMolecularWeightUnits',...
    'InjectedMassPerWeight','InjectedMassPerWeightUnits','SpecificRadioactivityMeasTime',...
    'MolarActivity','MolarActivityUnits','MolarActivityMeasTime','InfusionRadioactivity',...
    'InfusionStart','InfusionSpeed','InfusionSpeedUnits','InjectedVolume','DoseCalibrationFactor',...
    'Purity','PharmaceuticalName','PharmaceuticalDoseAmount','PharmaceuticalDoseUnits',...
    'PharmaceuticalDoseRegimen','PharmaceuticalDoseTime','ScanDate','InjectionEnd',...
    'ReconMethodImplementationVersion','AttenuationCorrectionMethodReference','ScaleFactor',...
    'ScatterFraction','DecayCorrectionFactor','PromptRate','RandomRate','SinglesRate'};

optional = {'Anaesthesia'};

%% defaults
% ---------

gz         = 6;      % -1..-9 : gz compression level (1=fastest..9=smallest, default 6)
a          = 'n';    % -a : adjacent DICOMs (images from same series always in same folder) for faster conversion (n/y, default n)
ba         = 'y';    % -ba : anonymize BIDS (y/n, default y)
d          = 5;      % directory search depth. Convert DICOMs in sub-folders of in_folder? (0..9, default 5)
f   = '%f_%p_%t_%s'; % filename (%a=antenna (coil) name, %b=basename, %c=comments, %d=description, %e=echo number, %f=folder name, %g=accession number, %i=ID of patient, %j=seriesInstanceUID, %k=studyInstanceUID, %m=manufacturer, %n=name of patient, %o=mediaObjectInstanceUID, %p=protocol, %r=instance number, %s=series number, %t=time, %u=acquisition number, %v=vendor, %x=study ID; %z=sequence name; default '%f_%p_%t_%s')
g          = 'n';    % generate defaults file (y/n/o/i [o=only: reset and write defaults; i=ignore: reset defaults], default n)
i          = 'n';    % ignore derived, localizer and 2D images (y/n, default n)
l          = 'n';    % losslessly scale 16-bit integers to use dynamic range (y/n/o [yes=scale, no=no, but uint16->int16, o=original], default n)
m          = '2';    % merge 2D slices from same series regardless of echo, exposure, etc. (n/y or 0/1/2, default 2) [no, yes, auto]
p          = 'y';    % Philips precise float (not display) scaling (y/n, default y)
v          = 1;      % verbose (n/y or 0/1/2, default 0) [no, yes, logorrheic]
w          = 2;      % write behavior for name conflicts (0,1,2, default 2: 0=skip duplicates, 1=overwrite, 2=add suffix)
x          = 'n';    % crop 3D acquisitions (y/n/i, default n, use 'i'gnore to neither crop nor rotate 3D acquistions)
z          = 'n';    % gz compress images (y/o/i/n/3, default n) [y=pigz, o=optimal pigz, i=internal:miniz, n=no, 3=no,3D]
bigendian  = 'o';    % byte order (y/n/o, default o) [y=big-end, n=little-end, o=optimal/native]

%% check dcm2nii inputs
% --------------------

if nargin<=1
    if nargin == 1
        warning('only 1 argument in, missing input')
    end
    help dcm2bids4pet
    return
end

if ~iscell(FileList)
    if ischar(FileList) && size(FileList,1)==1
        tmp = FileList; clear FileList;
        FileList{1} = tmp; clear tmp;
    else
        error('1st argument in must be a cell array of file names')
    end
end

if ~iscell(MetaList)
    if isstruct(MetaList) && size(MetaList,1)==1
        tmp = MetaList; clear MetaList;
        MetaList{1} = tmp; clear tmp;
    else
        error('1st argument in must be a cell array of file names')
    end
end

if iscell(MetaList) && any(size(MetaList)~=size(FileList))
    if size(MetaList,1) ==1
        disp('Replicating metadata for all input')
        tmp = MetaList; clear MetaList;
        MetaList = cell(size(FileList));
        for f=1:size(MetaList,1)
            MetaList{f} = tmp;
        end
        cleat tmp
    else
        error('2nd argument in must be a cell array of metadata structures')
    end
end

for v=1:length(varargin)
if strcmpi(varargin{v},'gz')
    gz = varargin{v+1};
    if ~num(gz) 
        error('invalid compression experession, not a numeric'); 
        if gz>9 
            error('invalid compression value, must be between 1 and 9'); 
        end
    end
elseif strcmpi(varargin{v},'a')
    a = varargin{v+1};
    if ~contains(a,{'y','n'}); error('invalid adjacent file value ''y'' or ''n'''); end 
elseif strcmpi(varargin{v},'ba')
    ba = varargin{v+1};
    if ~contains(a,{'y','n'}); error('invalid anonymization value ''y'' or ''n'''); end 
elseif strcmpi(varargin{v},'d')
    d = varargin{v+1};
    if ~num(d) 
        error('invalid compression experession, not a numeric'); 
        if d>9 
            error('invalid compression value, must be between 0 and 9'); 
        end
    end
elseif strcmpi(varargin{v},'f')
    f = varargin{v+1};
    if ~any([strcmpi(unique(f(1:3:end)),'%'),strcmpi(unique(f(3:3:end)),'_')])
        error('file naming option invalid, see dcm2niix')
    end
elseif strcmpi(varargin{v},'g')
    g = varargin{v+1};
    if ~contains(g,{'y','n','o','i'}); error('invalid defaults file value ''y/n/o/i'''); end 
elseif strcmpi(varargin{v},'i')
    i = varargin{v+1};
    if ~contains(a,{'y','n'}); error('invalid ignore derived, localizer and 2D image value ''y'' or ''n'''); end 
if strcmpi(varargin{v},'l')
    l = varargin{v+1};
    if ~contains(l,{'y','n','o'}); error('invalid losslessly scale option, ''y/n/o'''); end 
if strcmpi(varargin{v},'m')
    m = varargin{v+1};
    if isnumeric(m)
        if ~contains(num2str(m),{'0','1','2'}); error('merge 2D slices error, 0/1/2 as input'); end
    else
        if ~contains(m,{'y','n'}); error('merge 2D slices error,''y'' or ''n'''); end
    end
if strcmpi(varargin{v},'p')
    p = varargin{v+1};
    if ~contains(p,{'y','n'}); error('Philips precise float scaling error,''y'' or ''n'''); end
if strcmpi(varargin{v},'v')
    v = varargin{v+1};
    if isnumeric(m)
        if ~contains(num2str(m),{'0','1','2'}); error('verbose error, 0/1/2 as input'); end
    else
        if ~contains(m,{'y','n'}); error('verbose error,''y'' or ''n'''); end
    end
if strcmpi(varargin{v},'w')
    w = varargin{v+1};
    if ~contains(num2str(m),{'0','1','2'}); error('name conflicts behaviour error, 0/1/2 as input'); end
if strcmpi(varargin{v},'x')
    x = varargin{v+1};
    if ~contains(x,{'y','n','i'}); error('3D acq. option error,''y/n/i'''); end
if strcmpi(varargin{v},'z')
     z = varargin{v+1};
    if isnumeric(m)
        if ~contains(num2str(m),{'3'}); error('verbose error, 3 for no as input'); end
    else
        if ~contains(m,{'y','n'}); error('gz compress images error,''y/o/i/n'' expected'); end
    end
if strcmpi(varargin{v},'big-endian')
    bigendian = varargin{v+1};
    if ~contains(bigendian,{'y','n','o'}); error('endianess error,''y/n/o'''); end
end

%% check metadata inputs
% --------------------


%% convert
% ----------
dcm2nixx

%% update json
% -------------
updatejsonpetfile(filename,newfields);
% meta = jsondecode(fileread(file.name));







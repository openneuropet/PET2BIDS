function dcm2niix4pet(FolderList,MetaList,varargin)

% Converts dicom image file to nifti+json calling dcm2niix augmenting the
% json file to be BIDS compliant. Note that you are always right when it
% comes to metadata! DICOM values to be used in the json will be ignored, 
% always using the meta data provided - BUT DICOM values are checked and 
% the code tells you if there is inconsistency between your inputs and what
% DICOM says.
%
% :format: - fileout = dcm2bids4pet(FolderList,MetaList)
%          - fileout = dcm2bids4pet(FolderList,MetaList,options)
%
% :param FolderList: Cell array of char strings with filenames and paths
% :param MetaList: Cell array of structures for metadata
% :param options:
%   - *deletedcm*  to be 'on' or 'off'
%   - *o*         the output directory or cell arrays of directories
%                 IF the folder is BIDS sub-xx files are renamed automatically
%   - *gz*         = 6;      % -1..-9 : gz compression level (1=fastest..9=smallest, default 6)
%   - *a*          = 'n';    % -a : adjacent DICOMs (images from same series always in same folder) for faster conversion (n/y, default n)
%   - *ba*         = 'y';    % -ba : anonymize BIDS (y/n, default y)
%   - *d*          = 5;      % directory search depth. Convert DICOMs in sub-folders of in_folder? (0..9, default 5)
%   - *f*        = '%f_%p_%t_%s'; % filename (%a=antenna (coil) name, %b=basename, %c=comments, %d=description, %e=echo number, %f=folder name, %g=accession number, %i=ID of patient, %j=seriesInstanceUID, %k=studyInstanceUID, %m=manufacturer, %n=name of patient, %o=mediaObjectInstanceUID, %p=protocol, %r=instance number, %s=series number, %t=time, %u=acquisition number, %v=vendor, %x=study ID; %z=sequence name; default '%f_%p_%t_%s')
%   - *g*          = 'n';    % generate defaults file (y/n/o/i [o=only: reset and write defaults; i=ignore: reset defaults], default n)
%   - *i*          = 'n';    % ignore derived, localizer and 2D images (y/n, default n)
%   - *l*          = 'n';    % losslessly scale 16-bit integers to use dynamic range (y/n/o [yes=scale, no=no, but uint16->int16, o=original], default n)
%   - *m*          = '2';    % merge 2D slices from same series regardless of echo, exposure, etc. (n/y or 0/1/2, default 2) [no, yes, auto]
%   - *p*          = 'y';    % Philips precise float (not display) scaling (y/n, default y)
%   - *v*          = 1;      % verbose (n/y or 0/1/2, default 0) [no, yes, logorrheic]
%   - *w*          = 2;      % write behavior for name conflicts (0,1,2, default 2: 0=skip duplicates, 1=overwrite, 2=add suffix)
%   - *x*          = 'n';    % crop 3D acquisitions (y/n/i, default n, use 'i'gnore to neither crop nor rotate 3D acquistions)
%   - *z*          = 'n';    % gz compress images (y/o/i/n/3, default y) [y=pigz, o=optimal pigz, i=internal:miniz, n=no, 3=no,3D]
%
% .. code-block::
%
%    Example
%    meta = get_pet_metadata('Scanner','SiemensBiograph','TimeZero','ScanStart','TracerName','CB36','TracerRadionuclide','C11', ...
%                'ModeOfAdministration','infusion','SpecificRadioactivity', 605.3220,'InjectedMass', 1.5934,'MolarActivity', 107.66);
%    dcm2niix4pet(folder1,meta,'gz',9,'o','mynewfolder','v',1); % change dcm2nii default
%    dcm2niix4pet({folder1,folder2,folder3},{meta}); % use the same PET meta for all subjects
%    dcm2niix4pet({folder1,folder2,folder3},{meta1,meta2,meta3}); % each subject has specific metadata info
%
%.. note::
%
%   See also get_pet_metadata.m to generate the metadata structure
%            updatejsonpetfile to see how the json file gets updated and checked against DICOM tags
%
% | *Cyril Pernet 2022*
% | *Copyright Open NeuroPET team*

dcm2niixpath = 'D:\MRI\MRIcroGL12win\Resources\dcm2niix.exe'; % for windows machine indicate here, where is dcm2niix
if ispc && ~exist(dcm2niixpath,'file')
    error('for windows machine please edit the function line 42 and indicate the dcm2niix path')
end

if ~ispc % overwrite if not windowns (as it should be in the computer path)
    dcm2niixpath = 'dcm2niix';
end

% we rely on more recent version of dcm2niix, certain pet fields are unavailable in the sidecar jsons for versions
% before v1.0.20220720

minimum_version = 'v1.0.20220720';
minimum_version_date = datetime(minimum_version(6:end), 'InputFormat', 'yyyyMMdd');
version_cmd = ['dcm2niix', ' -v'];
[status, version_output_string] = system(version_cmd);
version = regexp(version_output_string, 'v[0-9].[0-9].{8}[0-9]', 'match');

if length(version) >= 1
    version_date = version{1}(6:end);
    version_date = datetime(version_date, 'InputFormat', 'yyyyMMdd');
    if version_date < minimum_version_date
        warning(['Version of installed dcm2niix is ', version{1}, ', recommended version is: ', minimum_version ' and above.']);
    end
end

%% defaults
% ---------

deletedcm  = 'off';

gz         = 6;      % -1..-9 : gz compression level (1=fastest..9=smallest, default 6)
a          = 'n';    % -a : adjacent DICOMs (images from same series always in same folder) for faster conversion (n/y, default n)
ba         = 'y';    % -ba : anonymize BIDS (y/n, default y)
d          = 5;      % directory search depth. Convert DICOMs in sub-folders of in_folder? (0..9, default 5)
f          = '%p_%i_%t_%s'; % filename (%a=antenna (coil) name, %b=basename, %c=comments, %d=description, %e=echo number, %f=folder name, %g=accession number, %i=ID of patient, %j=seriesInstanceUID, %k=studyInstanceUID, %m=manufacturer, %n=name of patient, %o=mediaObjectInstanceUID, %p=protocol, %r=instance number, %s=series number, %t=time, %u=acquisition number, %v=vendor, %x=study ID; %z=sequence name; default '%f_%p_%t_%s')
g          = 'n';    % generate defaults file (y/n/o/i [o=only: reset and write defaults; i=ignore: reset defaults], default n)
i          = 'n';    % ignore derived, localizer and 2D images (y/n, default n)
l          = 'n';    % losslessly scale 16-bit integers to use dynamic range (y/n/o [yes=scale, no=no, but uint16->int16, o=original], default n)
m          = '2';    % merge 2D slices from same series regardless of echo, exposure, etc. (n/y or 0/1/2, default 2) [no, yes, auto]
p          = 'y';    % Philips precise float (not display) scaling (y/n, default y)
v          = 1;      % verbose (n/y or 0/1/2, default 0) [no, yes, logorrheic]
w          = 2;      % write behavior for name conflicts (0,1,2, default 2: 0=skip duplicates, 1=overwrite, 2=add suffix)
x          = 'n';    % crop 3D acquisitions (y/n/i, default n, use 'i'gnore to neither crop nor rotate 3D acquistions)
z          = 'y';    % gz compress images (y/o/i/n/3, default y) [y=pigz, o=optimal pigz, i=internal:miniz, n=no, 3=no,3D]

%% check dcm2nii inputs
% --------------------

if nargin<=1
    if nargin == 1
        warning('only 1 argument in, missing input')
    end
    help dcm2niix4pet
    return
end

if ~iscell(FolderList)
    if ischar(FolderList) && size(FolderList,1)==1
        tmp = FolderList; clear FolderList;
        FolderList{1} = tmp; clear tmp;
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

if iscell(MetaList) && any(size(MetaList)~=size(FolderList))
    if size(MetaList,1) ==1
        disp('Replicating metadata for all input')
        tmp = MetaList; clear MetaList;
        MetaList = cell(size(FolderList));
        for f=1:size(MetaList,1)
            MetaList{f} = tmp;
        end
        clear tmp
    else
        error('2nd argument in must be a cell array of metadata structures')
    end
end

% check options
outputdir = [];
for var=1:length(varargin)
    
    if strcmpi(varargin{var},'deletedcm')
        deletedcm = varargin{var+1};
    elseif strcmpi(varargin{var},'gz')
        gz = varargin{var+1};
        if ~num(gz)
            error('invalid compression expression, not a numeric');
        elseif gz>9
            error('invalid compression value, must be between 1 and 9');
        end
    elseif strcmpi(varargin{var},'a')
        a = varargin{var+1};
        if ~contains(a,{'y','n'}); error('invalid adjacent file value ''y'' or ''n'''); end
    elseif strcmpi(varargin{var},'ba')
        ba = varargin{var+1};
        if ~contains(a,{'y','n'}); error('invalid anonymization value ''y'' or ''n'''); end
    elseif strcmpi(varargin{var},'d')
        d = varargin{var+1};
        if ~num(d)
            error('invalid compression expression, not a numeric');
        elseif d>9
            error('invalid compression value, must be between 0 and 9');
        end
    elseif strcmpi(varargin{var},'f')
        f = varargin{var+1};
        if ~any([strcmpi(unique(f(1:3:end)),'%'),strcmpi(unique(f(3:3:end)),'_')])
            error('file naming option invalid, see dcm2niix')
        end
    elseif strcmpi(varargin{var},'g')
        g = varargin{var+1};
        if ~contains(g,{'y','n','o','i'}); error('invalid defaults file value ''y/n/o/i'''); end
    elseif strcmpi(varargin{var},'i')
        i = varargin{var+1};
        if ~contains(a,{'y','n'}); error('invalid ignore derived, localizer and 2D image value ''y'' or ''n'''); end
    elseif strcmpi(varargin{var},'l')
        l = varargin{var+1};
        if ~contains(l,{'y','n','o'}); error('invalid losslessly scale option, ''y/n/o'''); end
    elseif strcmpi(varargin{var},'m')
        m = varargin{var+1};
        if isnumeric(m)
            if ~contains(num2str(m),{'0','1','2'}); error('merge 2D slices error, 0/1/2 as input'); end
        else
            if ~contains(m,{'y','n'}); error('merge 2D slices error,''y'' or ''n'''); end
        end
    elseif strcmpi(varargin{var},'p')
        p = varargin{var+1};
        if ~contains(p,{'y','n'}); error('Philips precise float scaling error,''y'' or ''n'''); end
    elseif strcmpi(varargin{var},'v')
        v = varargin{var+1};
        if isnumeric(v)
            if ~contains(num2str(v),{'0','1','2'}); error('verbose error, 0/1/2 as input'); end
        else
            if ~contains(v,{'y','n'}); error('verbose error,''y'' or ''n'''); end
        end
    elseif strcmpi(varargin{var},'w')
        w = varargin{var+1};
        if ~contains(num2str(w),{'0','1','2'}); error('name conflicts behaviour error, 0/1/2 as input'); end
    elseif strcmpi(varargin{var},'x')
        x = varargin{var+1};
        if ~contains(x,{'y','n','i'}); error('3D acq. option error,''y/n/i'''); end
    elseif strcmpi(varargin{var},'z')
        z = varargin{var+1};
        if isnumeric(z)
            if ~contains(num2str(z),{'3'}); error('verbose error, 3 for no as input'); end
        else
            if ~contains(z,{'y','n'}); error('gz compress images error,''y/o/i/n'' expected'); end
        end
    elseif strcmpi(varargin{var},'o')
        outputdir = varargin{var+1};
    end
end

if isempty(outputdir)
     outputdir = FolderList;
end

if ~iscell(outputdir)
    if ischar(outputdir) && size(outputdir,1)==1
        tmp = outputdir; clear outputdir;
        outputdir{1} = tmp; clear tmp;
    else
        error('outputdir must be a cell array of directory names')
    end
end

%% convert
% ----------
for folder = 1:size(FolderList,1)
    % dcm2niix
    command = [dcm2niixpath ' -o ' outputdir{folder} ' ' num2str(gz) ...
        ' -a ' a ...
        ' -ba ' ba ...
        ' -d ' num2str(d) ...
        ' -f ' f ...
        ' -g ' g ...
        ' -i ' i ...
        ' -l ' l ...
        ' -m ' num2str(m) ...
        ' -p ' p ...
        ' -v ' num2str(v) ...
        ' -w ' num2str(w) ...
        ' -x ' x ...
        ' -z ' z ...
        ' ' FolderList{folder}];
    if ~exist(outputdir{folder},'dir')
        mkdir(outputdir{folder}); 
    end
    
    out = system(command);
    if out ~= 0
        error('%s did not run properly',command)
    end
   
    % deal with dcm files
    dcmfiles = dir(fullfile(FolderList{folder},'*.dcm'));
    if isempty(dcmfiles) % since sometimes they have no ext :-(
        dcmfiles = dir(FolderList{folder}); % pick in the middle to avoid other files
        dcminfo  = dicominfo(fullfile(dcmfiles(round(size(dcmfiles,1)/2)).folder,dcmfiles(round(size(dcmfiles,1)/2)).name));
    else
        dcminfo  = dicominfo(fullfile(dcmfiles(1).folder,dcmfiles(1).name));
    end
    
    if strcmpi(deletedcm,'on')
        delete(fullfile(outputdir{folder},'*dcm'))
    end
    
    % rename if BIDS folder sub-
    if contains(outputdir{folder},'sub-')
        if strcmpi(z,'y')
            data  = dir(fullfile(outputdir{folder},'*.nii.gz'));
        else
            data  = dir(fullfile(outputdir{folder},'*.nii'));
        end
        
        if size(data,1)>1
            warning('more than 1 nifti file found in %s, using only 1st one',outputdir{folder})
            data = data(1);
        end
        
        dataname    = fullfile(data.folder,data.name);
        start       = strfind(data.folder,'sub-');
        ending      = strfind(data.folder,filesep);
        if sum(ending>start)~=0
            newname = data.folder(start:ending(end)-1); % from sub- to last subfolder (ses-)
            newname(strfind(newname,filesep)) = '_'; 
        else
            newname = data.folder(start:end); % from sub- to the end
        end
        
        if strcmpi(z,'y')
            newname     = [newname '_pet.nii.gz']; %#ok<AGROW>
            metadata    = [dataname(1:end-7) '.json'];
            newmetadata = fullfile(data.folder,[newname(1:end-7) '.json']);
        else
            newname     = [newname '_pet.nii']; %#ok<AGROW>
            metadata    = [dataname(1:end-4) '.json'];
            newmetadata = fullfile(data.folder,[newname(1:end-4) '.json']);
        end
        movefile(dataname,fullfile(data.folder,newname));
        movefile(metadata,newmetadata);
    end
    
    % update json
    if ~exist('newmetadata','var')
        newmetadata  = dir(fullfile(outputdir{folder},'*.json'));
        if isempty(newmetadata)
            error('no json file found in output directory %s',outputdir{folder})
        elseif size(newmetadata,1)>1
            warning('more than 1 json file found in %s, using only 1st one',outputdir{folder})
            newmetadata = newmetadata(1);
        else
            warning('the output directory is not BIDS compliant, it should start with sub-')
        end
        jsonfilename = fullfile(newmetadata.folder,newmetadata.name);
    else
        jsonfilename = newmetadata;
    end
    updatejsonpetfile(jsonfilename,MetaList,dcminfo);
end

function fileout = ecat2nii(FileList,MetaList,varargin)

% Converts ECAT 7 image file from hrrt pet scanner (ecat format)
% to nifti image files + json
%
% FORNAT: ecat2nii(FileList,MetaList,options)
%
% INPUT: FileList - Cell array of char strings with filenames and paths
%        MetaList - Cell array of structures for metadata
%        options are name/value pairs
%                'sifout' is true or false (default) to output a sif file
%                'gz' is true (default) or false to output .nii.gz or .nii
%                'savemat' is true or false (default) to save the ecat data as .mat
%
% Example meta = get_SiemensHRRT_metadata('TimeZero','ScanStart','tracer','DASB','Radionuclide','C11', ...
%                'Radioactivity', 605.3220,'InjectedMass', 1.5934,'MolarActivity', 107.66);
%        fileout = ecat2nii({ecatfile},{meta},'gz',false,'sifout',true);
%
% SIF is a simple ascii file that contains the PET frame start and end times,
% and the numbers of observed events during each PET time frame.
%
% Uses: readECAT7.m (Raymond Muzic, 2002)
% See also get_SiemensHRRT_metadata.m to generate the metadata structure
%
% Claus Svarer & Cyril Pernet
%    (some of the code is based on code from Mark Lubbering
% ----------------------------------------------
% Copyright OpenNeuroPET team


%% defaults
% ---------

sifout  = false; % 0/1 to indicate if sif file are also created
gz      = true;  % compress nifti 
savemat = false; % save ecat data as .mat

%% check inputs
% ------------

if ~iscell(FileList)
    if ischar(FileList) && size(FileList,1)==1
        tmp = FileList; clear FileList;
        FileList{1} = tmp; clear tmp;
    else
        error('1st argument in must be a cell array of file names')
    end
end

if ~iscell(MetaList)
    if ischar(FileList) && size(FileList,1)==1
        tmp = FileList; clear FileList;
        FileList{1} = tmp; clear tmp;
    else
        error('1st argument in must be a cell array of file names')
    end
elseif iscell(MetaList) && any(size(MetaList)~=size(FileList))
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
    if strcmpi(varargin{v},'sifout')
        sifout = varargin{v+1};
    elseif strcmpi(varargin{v},'gz')
        gz = varargin{v+1};
    elseif strcmpi(varargin{v},'savemat')
        savemat = varargin{v+1};
    end    
end


%% Read and write data
% --------------------
for j=1:length(FileList)
    
    fprintf('Conversion of file: %s\n',FileList{j});
    
    % quickly ensure we have the TimeZero - key to all analyzes! 
    info     = MetaList{1};
    if ~isfield(info,'TimeZero')
        error('Metadata TimeZero is missing - set to ScanStart or empty to use the scanning time as injection time')
    end

    % Read ECAT file headers
    [pet_path,pet_file,ext]=fileparts(FileList{j});
    if strcmp(ext,'.gz')
        newfile = gunzip([pet_path filesep pet_file ext]);
        [pet_path,pet_file,ext]=fileparts(newfile);
    end
    
    pet_file = [pet_file ext];
    [mh,sh]  = readECAT7([pet_path filesep pet_file]);
    if sh{1}.data_type == 6
        datatype    = 16;
    else
        error('Conversion for 16 bit signed data only (type 6 in ecat file)');
    end
    Nframes  = mh.num_frames;
    
    % Create data reading 1 frame at a time
    img_temp = zeros(sh{1}.x_dimension,sh{1}.y_dimension,sh{1}.z_dimension,Nframes);
    for i=Nframes:-1:1
        fprintf('  Working at frame: %i\n',i);
        [mh,shf,data]      = readECAT7([pet_path filesep pet_file],i);
        img_temp(:,:,:,i) = flipdim(flipdim(flipdim((double(cat(4,data{:}))*sh{1}.scale_factor),2),3),1); %#ok<DFLIPDIM>
        % also get timing information
        Start(i)     = shf{1}.frame_start_time*60; %#ok<NASGU>
        DeltaTime(i) = shf{1}.frame_duration*60;
        if mh.sw_version>=73
            Prompts(i) = shf{1}.prompt_rate*shf{1}.frame_duration*60;
            Randoms(i) = shf{1}.random_rate*shf{1}.frame_duration*60;
        else
            Prompts(i) = 0;
            Randoms(i) = 0;
        end
    end
    
    % rescale - for quantitative PET   
    MaxImg       = max(img_temp(:));
    img_temp     = img_temp/MaxImg*32767;
    Sca          = MaxImg/32767;
    MinImg       = min(img_temp(:));
    if (MinImg<-32768)
        img_temp = img_temp/MinImg*(-32768);
        Sca      = Sca*MinImg/(-32768);
    end
           
    % write timing info separately
    if sifout
        pid = fopen(fullfile(pet_path,[pet_file(1:end-2) '.sif']),'w');
        
        if (pid~=0)
            offset   = tzoffset(datetime(mh.scan_start_time, 'ConvertFrom', 'posixtime','TimeZone','local'));
            scantime = datetime(mh.scan_start_time, 'ConvertFrom', 'posixtime','TimeZone','UTC') + offset;
            if offset ~=0
                warning('sif scantime is adjusted by local time difference to UTC: %s',offset)
            end
            fprintf(pid,'%s %i 4 1\n',scantime, length(Start));
            for i=1:length(Start)
                fprintf(pid,'%i %i %i %i\n',round(Start(i)),round(Start(i)+DeltaTime(i)),...
                    round(Prompts(i)),round(Randoms(i)));
            end
            fclose(pid);
        end
    end
    
    % write nifti format + json
    fileout                               = [pet_path filesep pet_file(1:end-2) '.nii']; % note pet_file(1:end-2) to remove .v
    sub_iter                              = strsplit(sh{1,1}.annotation);
    iterations                            = str2double(cell2mat(regexp(sub_iter{2},'\d*','Match')));
    subsets                               = str2double(cell2mat(regexp(sub_iter{3},'\d*','Match')));
    info.ReconMethodParameterLabels       = {'iterations', 'subsets', 'lower_threshold', 'upper_threshold'};
    info.ReconMethodParameterUnits        = {'none', 'none', 'keV', 'keV'};
    info.ReconMethodParameterValues       = [iterations, subsets, mh.lwr_sctr_thres, mh.upr_true_thres];
    for idx = 1:numel(sh)
        info.ScaleFactor(idx,1)           = sh{idx}.scale_factor;
        info.ScatterFraction(idx,1)       = sh{idx}.scatter_fraction;
        info.DecayCorrectionFactor(idx,1) = sh{idx}.decay_corr_fctr;
        info.PromptRate(idx,1)            = sh{idx}.prompt_rate;
        info.RandomRate(idx,1)            = sh{idx}.random_rate;
        info.SinglesRate(idx,1)           = sh{idx}.singles_rate;
    end
    info.FrameDuration                    = DeltaTime';
    info.FrameTimesStart                  = zeros(size(info.FrameDuration));
    info.FrameTimesStart(2:end)           = cumsum(info.FrameDuration(1:end-1));
    if isempty(info.TimeZero) || strcmp(info.TimeZero,'ScanStart')
        offset                            = tzoffset(datetime(mh.scan_start_time, 'ConvertFrom', 'posixtime','TimeZone','local'));
        info.TimeZero                     = datestr((datetime(mh.scan_start_time, 'ConvertFrom', 'posixtime','TimeZone','UTC') + offset),'hh.mm.ss'); 
        if offset ~=0
            warning('TimeZero is set to be scan time adjusted by local time difference to UTC: %s',offset)
        end
    end
    info.ScanStart                        = 0;
    info.InjectionStart                   = 0;
    info.CalibrationFactor                = Sca*mh.ecat_calibration_factor;
    info.Filename                         = fileout;
    info.Filemoddate                      = datestr(now);
    info.Version                          = 'NIfTI1';
    info.Description                      = 'Open Neuro PET hrrt2neuro';
    info.ImageSize                        = [sh{1}.x_dimension sh{1}.y_dimension sh{1}.z_dimension mh.num_frames];
    info.PixelDimensions                  = [sh{1}.x_pixel_size sh{1}.y_pixel_size sh{1}.z_pixel_size 0]*.10;
    jsonwrite([pet_path filesep pet_file(1:end-2) '.json'],info)
    
    info.Datatype                         = 'single';
    info.BitsPerPixel                     = 32;
    info.SpaceUnits                       = 'Millimeter';
    info.TimeUnits                        = 'Second';
    info.SliceCode                        = 'Unknown';
    info.FrequencyDimension               = 0;
    info.PhaseDimension                   = 0;
    info.SpatialDimension                 = 0;
    info.AdditiveOffset                   = 0;
    info.MultiplicativeScaling            = 0;
    info.TimeOffset                       = 0;
    info.DisplayIntensityRange            = [0 0];
    info.TransformName                    = 'Sform';
    info.Qfactor                          = 1;
    if gz
        niftiwrite(single(round(img_temp).*(Sca*mh.ecat_calibration_factor)),...
            fileout,info,'Endian','little','Compressed',true);
    else
        niftiwrite(single(round(img_temp).*(Sca*mh.ecat_calibration_factor)),...
            fileout,info,'Endian','little','Compressed',false);
    end
    
    % save raw data
    if savemat
        ecat = round(img_temp).*(Sca*mh.ecat_calibration_factor);
        save(fullfile(pet_path,[pet_file(1:end-2) '.ecat.mat']),'ecat','-v7.3');
    end
end

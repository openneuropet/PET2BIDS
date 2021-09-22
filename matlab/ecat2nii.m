function fileout = ecat2nii(FileList,MetaList,varargin)

% Converts ECAT 7 image file from hrrt pet scanner (ecat format)
% to nifti image files + json
%
% FORMAT: ecat2nii(FileList,MetaList)
%         ecat2nii(FileList,MetaList,options)
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
% Claus Svarer, Martin Nørgaard  & Cyril Pernet - 2021
%    (some of the code is based on code from Mark Lubbering
% ----------------------------------------------
% Copyright Open NeuroPET team


%% defaults
% ---------

sifout  = false; % 0/1 to indicate if sif file are also created
gz      = true;  % compress nifti
savemat = false; % save ecat data as .mat

%% check inputs
% ------------

if nargin<=1
    if nargin == 1
        warning('only 1 argument in, missing input')
    end
    help ecat2nii
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
    
    try
        fprintf('Conversion of file: %s\n',FileList{j});
        
        % quickly ensure we have the TimeZero - key to all analyzes!
        info     = MetaList{1};
        if ~isfield(info,'TimeZero')
            error('Metadata TimeZero is missing - set to ScanStart or empty to use the scanning time as injection time')
        end
        
        % Read ECAT file headers
        if ~exist(FileList{j},'file')
            error('the file %s does not exist',FileList{j}),
        end
        
        [pet_path,pet_file,ext]=fileparts(FileList{j});
        if strcmp(ext,'.gz')
            newfile = gunzip([pet_path filesep pet_file ext]);
            [~,pet_file,ext]=fileparts(newfile{1});
        end
        
        pet_file = [pet_file ext]; 
        [mh,sh]  = readECAT7([pet_path filesep pet_file]); % loading the whole file here and iterating to flipdim below only minuimally improves time (0.6sec on NRU server)
        if sh{1}.data_type ~= 6
            error('Conversion for 16 bit signed data only (type 6 in ecat file) - error loading ecat file');
        end
        Nframes  = mh.num_frames;
        
        % Create data reading 1 frame at a time
        img_temp = zeros(sh{1}.x_dimension,sh{1}.y_dimension,sh{1}.z_dimension,Nframes);
        for i=Nframes:-1:1
            fprintf('Working at frame: %i\n',i);
            [mh,shf,data]     = readECAT7([pet_path filesep pet_file],i);
            img_temp(:,:,:,i) = flipdim(flipdim(flipdim((double(cat(4,data{:}))*shf{1}.scale_factor),2),3),1); %#ok<DFLIPDIM>
            % also get timing information
            Start(i)          = shf{1}.frame_start_time*60; 
            DeltaTime(i)      = shf{1}.frame_duration*60;
            if mh.sw_version >=73
                Prompts(i)    = shf{1}.prompt_rate*shf{1}.frame_duration*60;
                Randoms(i)    = shf{1}.random_rate*shf{1}.frame_duration*60;
            else
                Prompts(i)    = 0;
                Randoms(i)    = 0;
            end
        end
        
        
        % rescale to 16 bits
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
        
        % save raw data
        if savemat
            ecat = img_temp.*(Sca*mh.ecat_calibration_factor);
            save(fullfile(pet_path,[pet_file(1:end-2) '.ecat.mat']),'ecat','-v7.3');
        end
        
        % write nifti format + json
        [~,pet_filename]                      = fileparts(pet_file);
        filenameout                           = [pet_path filesep pet_filename];
        img_temp                              = single(round(img_temp).*(Sca*mh.ecat_calibration_factor));
        if isfield(sh{1,1},'annotation')
            if ~isempty(deblank(sh{1,1}.annotation))
                sub_iter                          = strsplit(sh{1,1}.annotation);
                iterations                        = str2double(cell2mat(regexp(sub_iter{2},'\d*','Match')));
                subsets                           = str2double(cell2mat(regexp(sub_iter{3},'\d*','Match')));
                info.ReconMethodParameterLabels   = {'iterations', 'subsets', 'lower_threshold', 'upper_threshold'};
                info.ReconMethodParameterUnits    = {'none', 'none', 'keV', 'keV'};
                info.ReconMethodParameterValues   = [iterations, subsets, mh.lwr_true_thres, mh.upr_true_thres];
            else
                info.ReconMethodParameterLabels   = {'lower_threshold', 'upper_threshold'};
                info.ReconMethodParameterUnits    = {'keV', 'keV'};
                info.ReconMethodParameterValues   = [mh.lwr_true_thres, mh.upr_true_thres];
            end
        else
            info.ReconMethodParameterLabels   = {'lower_threshold', 'upper_threshold'};
            info.ReconMethodParameterUnits    = {'keV', 'keV'};
            info.ReconMethodParameterValues   = [mh.lwr_true_thres, mh.upr_true_thres];
        end
        
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
        info.DoseCalibrationFactor            = Sca*mh.ecat_calibration_factor;
        info.Filemoddate                      = datestr(now);
        info.Version                          = 'NIfTI1';
        info.ConversionSoftware               = 'ecat2nii.m';
        info.Description                      = 'Open NeuroPET ecat7+ matlab based conversion';
        info.ImageSize                        = [sh{1}.x_dimension sh{1}.y_dimension sh{1}.z_dimension mh.num_frames];
        info.PixelDimensions                  = [sh{1}.x_pixel_size sh{1}.y_pixel_size sh{1}.z_pixel_size 0].*10;
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
        info.Transform.Dimensionality         = 3;
        info.Qfactor                          = 1; % determinant of the rotation matrix
        
        % map https://nifti.nimh.nih.gov/pub/dist/src/niftilib/nifti1.h
        info.raw.sizeof_hdr     = 348;
        info.raw.dim_info       = '';
        info.raw.dim            = [4 sh{1}.x_dimension sh{1}.y_dimension sh{1}.z_dimension mh.num_frames 1 1 1];
        info.raw.intent_p1      = 0;
        info.raw.intent_p2      = 0;
        info.raw.intent_p3      = 0;
        info.raw.intent_code    = 0;
        info.raw.datatype       = 16;
        info.raw.bitpix         = 32;
        info.raw.slice_start    = 0;
        info.raw.pixdim         = [1 sh{1}.x_pixel_size*10 sh{1}.y_pixel_size*10 sh{1}.z_pixel_size*10 0 0 0 0];
        info.raw.vox_offset     = 352;
        info.raw.scl_slope      = 0; % this is where the DoseCalibrationFactor could be set rather than in the data
        info.raw.scl_inter      = 0;
        info.raw.slice_end      = 0;
        info.raw.slice_code     = 0;
        info.raw.xyzt_units     = 10;
        info.raw.cal_max        = max(img_temp(:));
        info.raw.cal_min        = min(img_temp(:));
        info.raw.slice_duration = 0;
        info.raw.toffset        = 0;
        info.raw.descrip        = 'Open NeuroPET ecat2nii.m conversion';
        info.raw.aux_file       = '';
        info.raw.qform_code     = 0;
        info.raw.sform_code     = 1; % 0: Arbitrary coordinates; 1: Scanner-based anatomical coordinates; 2: Coordinates aligned to another file's, or to anatomical "truth" (coregistration); 3: Coordinates aligned to Talairach-Tournoux Atlas; 4: MNI 152 normalized coordinates
        info.raw.quatern_b      = 0;
        info.raw.quatern_c      = 0;
        info.raw.quatern_d      = 0;
        info.raw.qoffset_x      = -1*(((sh{1}.x_dimension*sh{1}.x_pixel_size*10)/2)-(sh{1}.x_pixel_size*5));
        info.raw.qoffset_y      = -1*(((sh{1}.y_dimension*sh{1}.y_pixel_size*10)/2)-(sh{1}.y_pixel_size*5));
        info.raw.qoffset_z      = -1*(((sh{1}.z_dimension*sh{1}.z_pixel_size*10)/2)-(sh{1}.z_pixel_size*5));
        info.raw.srow_x         = [sh{1}.x_pixel_size*10 0 0 info.raw.qoffset_x];
        info.raw.srow_y         = [0 sh{1}.y_pixel_size*10 0 info.raw.qoffset_y];
        info.raw.srow_z         = [0 0 sh{1}.z_pixel_size*10 info.raw.qoffset_z];
        T                       = eye(4);
        T([1 6 11])             = [sh{1}.x_pixel_size*10 sh{1}.y_pixel_size*10 sh{1}.z_pixel_size*10];
        T([4 8 12])             = [info.raw.qoffset_x info.raw.qoffset_y info.raw.qoffset_z];
        info.Transform.T        = T;
        info.raw.intent_name    = '';
        info.raw.magic          = 'n+1 ';
        if gz
            niftiwrite(img_temp,[filenameout '.nii'],info,'Endian','little','Compressed',true);
            fileout{j} = [filenameout '.nii.gz']; %#ok<*AGROW>
        else
            fileout{j} = [filenameout '.nii'];
            niftiwrite(img_temp,fileout{j},info,'Endian','little','Compressed',false);
        end
        
    catch conversionerr
        fileout{j} = sprintf('%s failed to convert:%s',FileList{j},conversionerr.message);
    end
end

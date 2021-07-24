function niftiwrite_test

% simple routine testing the error in nifti wrtite as done in ecat2nii 
% Claus Svarer & Cyril Pernet
% ----------------------------------------------
% Copyright OpenNeuroPET team

img   = randn([256 256 256]);
scale = max(abs(img(:)))/32767;
img_q = img/scale;

info.Version                          = 'NIfTI1';
info.ImageSize                        = [256 256 256];
info.PixelDimensions                  = [1 1 1];
info.Description                      = 'Test of quantification';
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
to_write                = round(img_q).*scale;
info.raw.sizeof_hdr     = 348;
info.raw.dim_info       = '';
info.raw.dim            = [4 256 256 256 1 1 1 1];
info.raw.intent_p1      = 0;
info.raw.intent_p2      = 0;
info.raw.intent_p3      = 0;
info.raw.intent_code    = 0;
info.raw.datatype       = 16;
info.raw.bitpix         = 32;
info.raw.slice_start    = 0;
info.raw.pixdim         = [1 1 1 1 0 0 0 0];
info.raw.vox_offset     = 352;
info.raw.scl_slope      = 0; % this is where the DoseCalibrationFactor could be set rather than in the data
info.raw.scl_inter      = 0;
info.raw.slice_end      = 0;
info.raw.slice_code     = 0;
info.raw.xyzt_units     = 10;
info.raw.cal_max        = max(to_write(:));
info.raw.cal_min        = min(to_write(:));
info.raw.slice_duration = 0;
info.raw.toffset        = 0;
info.raw.descrip        = 'Open NeuroPET ecat2nii.m conversion';
info.raw.aux_file       = '';
info.raw.qform_code     = 0;
info.raw.sform_code     = 1; % 0: Arbitrary coordinates; 1: Scanner-based anatomical coordinates; 2: Coordinates aligned to another file's, or to anatomical "truth" (coregistration); 3: Coordinates aligned to Talairach-Tournoux Atlas; 4: MNI 152 normalized coordinates
info.raw.quatern_b      = 0;
info.raw.quatern_c      = 0;
info.raw.quatern_d      = 0;
info.raw.qoffset_x      = -127.5;
info.raw.qoffset_y      = -127.5;
info.raw.qoffset_z      = -127.5;
info.raw.srow_x         = [1 0 0 info.raw.qoffset_x];
info.raw.srow_y         = [0 1 0 info.raw.qoffset_y];
info.raw.srow_z         = [0 0 1 info.raw.qoffset_z];
T                       = eye(4);
T([4 8 12])             = [info.raw.qoffset_x info.raw.qoffset_y info.raw.qoffset_z];
info.Transform.T        = T;
info.raw.intent_name    = '';
info.raw.magic          = 'n+1 ';

niftiwrite(single(to_write),'test.nii',info,'Endian','little','Compressed',false);
img_reread = niftiread('test.nii');
img_diff   = img(:)-img_reread(:);
        
figure
subplot(1,3,1);plot(img(:),img_reread(:),'*'); grid on
xlabel('Original'); ylabel('Reread'); title('Read vs Written');
subplot(1,3,2);[simg,index] = sort(img(:)); plot(simg(:),img_diff(index),'*')
xlabel('Original'); ylabel('Org-Reread'); title(sprintf('Average error: %f\n',mean(img_diff(:))));
subplot(1,3,3); histogram((img_diff),200);
xlabel('error'); title('Distribution of errors')

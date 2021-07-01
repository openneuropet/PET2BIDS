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
info.Qfactor                          = 1;

niftiwrite(single(round(img_q).*scale),'test.nii',info,'Endian','little','Compressed',false);
img_reread = niftiread('test.nii');
img_diff   = img(:)-img_reread(:);
        
figure
subplot(1,3,1);plot(img(:),img_reread(:),'*');
xlabel('Original'); ylabel('Reread'); title('Read vs Written');
subplot(1,3,2);[simg,index] = sort(img(:)); plot(simg(:),img_diff(index),'*')
xlabel('Original'); ylabel('Org-Reread'); title(sprintf('Average error: %f\n',mean(img_diff(:))));
subplot(1,3,3); histogram((img_diff),200);
xlabel('error'); title('Distribution of errors')

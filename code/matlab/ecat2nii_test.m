function ecat2nii_test(ecatfile)

% simple routine testing if the nifit file is writen out like the ecat data
% IMPUT a fullfile name
% OUTPUT a figure imdicating the correspondance and errors in writing as nifti
%
% e.g. ecat2nii_test(fullfile(pwd,'myfile.v'));
% Claus Svarer & Cyril Pernet
% ----------------------------------------------
% Copyright OpenNeuroPET team

meta.info = 'just running a test';
ecat2nii(ecatfile,{meta},'gz',false,'savemat',true)

[filepath,filename] = fileparts(ecatfile);
img                 = load(fullfile(filepath,[filename '.ecat.mat']));
img                 = img.(cell2mat(fieldnames(img)));
img_reread          = niftiread(fullfile(filepath,[filename '.nii']));

figure
subplot(1,3,1);plot(img(:),img_reread(:),'*');
xlabel('Original'); ylabel('Nifti'); title('Read vs Written');
subplot(1,3,2);plot(img(:),(img(:)-img_reread(:)),'*')
xlabel('Original'); ylabel('Difference'); 
title(sprintf('Average error: %f\n',mean((img(:)-img_reread(:)))));
subplot(1,3,3); histogram((img(:)-img_reread(:)),200);
xlabel('error'); title('Distribution of errors (should be uniform)')


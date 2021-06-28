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

Diff_ecat_nifti     = img - img_reread;
meandiff            = mean((img(:)-img_reread(:)));
for f=size(img,4):-1:1
    frame = squeeze(Diff_ecat_nifti(:,:,:,f));
    summary_diff(f,:) = [min(frame(:)) mean(frame(:)) max(frame(:))];
end
table(summary_diff(:,1),summary_diff(:,2),summary_diff(:,3),'VariableNames',{'min','mean','max'}) % analyze diff

figure
subplot(1,3,1);plot(img(:),img_reread(:),'*');
xlabel('Original'); ylabel('Nifti'); title('Read vs Written');
subplot(1,3,2);plot(img(:),(img(:)-img_reread(:)),'*')
xlabel('Original'); ylabel('Difference'); title(sprintf('Average error: %f\n',meandiff));
subplot(1,3,3); histogram(Diff_ecat_nifti); axis([min(Diff_ecat_nifti(:)) max(Diff_ecat_nifti(:)) 0 10000])
xlabel('error'); title('Distribution of errors')


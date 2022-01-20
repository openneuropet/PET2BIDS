function ecat2nii_test(varargin)

% simple routine testing if the nifti file is writen out like the ecat data
% FORMAT: ecat2nii_test(ecatfile)
% INPUT:  ecatfile is the fullfile name ([] for using test file)
% OUTPUT: a figure imdicating the correspondance and errors in writing as nifti
%         (if INPUT is [], the synthetic example is used and compared to
%         the known values in the coresponding txt file -- see
%         /ecat_validation)
%
% e.g. ecat2nii_test(fullfile(pwd,'myfile.v'));
% Claus Svarer & Cyril Pernet
% ----------------------------------------------
% Copyright OpenNeuroPET team

if nargin ==0 || isempty(varargin{1})
    ecatfile = fullfile(fileparts(fileparts(fileparts(which('ecat2nii_test.m')))),...
        ['ecat_validation' filesep 'synthetic_ecat_integer_16x16x16x4.v']);
    groundtruth = [ecatfile(1:end-2) '.txt'];
end

meta.info = 'just running a test';
meta.TimeZero = datestr(now,'hh:mm:ss');
ecat2nii(ecatfile,{meta},'gz',false,'savemat',true)

if exist('groundtruth','var')
    [filepath,filename] = fileparts(ecatfile);
    img                 = load(groundtruth);
    img_reread          = niftiread(fullfile(filepath,[filename '.nii']));
    Diff_ecat_nifti     = img(:) - img_reread(:);
    table(min(Diff_ecat_nifti),mean(min(Diff_ecat_nifti)),max(Diff_ecat_nifti),...
        'VariableNames',{'min','mean','max'}) % analyze diff

else
    [filepath,filename] = fileparts(ecatfile);
    img                 = load(fullfile(filepath,[filename '.ecat.mat']));
    img                 = img.(cell2mat(fieldnames(img)));
    img_reread          = niftiread(fullfile(filepath,[filename '.nii']));
    
    Diff_ecat_nifti     = img - img_reread;
    meandiff            = mean(img(:)-img_reread(:));
    for f=size(img,4):-1:1
        tmp               = squeeze(img(:,:,:,f)); tmp(tmp==0)=NaN;
        signal(f)         = nanmean(tmp(:)); % all brain time activity curve
        frame{f}          = squeeze(Diff_ecat_nifti(:,:,:,f));
        summary_diff(f,:) = [min(frame{f}(:)) mean(frame{f}(:)) max(frame{f}(:))];
    end
    table(summary_diff(:,1),summary_diff(:,2),summary_diff(:,3),...
        'VariableNames',{'min','mean','max'}) % analyze diff
    
end

figure
A = min(Diff_ecat_nifti(:));
B = max(Diff_ecat_nifti(:));
if exist('groundtruth','var')
    subplot(1,3,1);
else
    subplot(2,2,1);
end
plot(img(:),img_reread(:),'*'); hold on;
M = max(max([img(:) img_reread(:)])); axis([0 M 0 M])
plot([0 M],[0 M],'r','LineWidth',1); grid on
xlabel('Original'); ylabel('Nifti'); title('Read vs Written');

[simg,index] = sort(img(:)); 
if exist('groundtruth','var')
    subplot(1,3,2);
else
    subplot(2,2,3);
end
plot(img(:),(simg-img_reread(index)),'*')
xlabel('Original'); ylabel('Difference'); 
title(sprintf('Average error: %f\n',meandiff));

if exist('groundtruth','var')
    subplot(1,3,3);
else
    subplot(2,2,4);
end
histogram(Diff_ecat_nifti(:));
axis([A B 0 10000]); xlabel('error'); 
title('Distribution of all errors')

if ~exist('groundtruth','var')
    
    subplot(2,2,2); plot(summary_diff(:,2),'LineWidth',2); grid on; xlabel('frames');
    ylabel('Difference'); title('Avg error per frame')
    
    vidObj = VideoWriter([filename '_error']);
    open(vidObj); figure('Name','error per frames');
    set(gcf,'Color','w','InvertHardCopy','off', 'units','normalized', 'outerposition',[0 0 1 1]);
    for f=1:size(Diff_ecat_nifti,4)
        for rep = 1:8 % use to slow down the video
            clf
            subplot(3,2,[1 2 3 4]);
            all = frame{f}(:); all(all==0)=[];
            histogram(all); axis([-13 13 -0.5 50])
            xlabel('error values'); ylabel('freq.');
            title(sprintf('errors frame %g max %g%%',f,max(all(:))/max(max(max(img(:,:,:,f))))*100));
            
            subplot(3,2,[5 6]); plot(signal,'LineWidth',2); axis tight
            hold on; plot(f,signal(f),'rO','LineWidth',4); axis tight;
            xlabel('frames'); ylabel('all brain TAC'); grid on; hold off
            
            CF = getframe(gcf); writeVideo(vidObj,CF);
        end
    end
    close(vidObj); close
end
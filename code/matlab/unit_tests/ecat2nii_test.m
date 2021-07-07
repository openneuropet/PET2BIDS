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
meta.TimeZero = datestr(now,'hh:mm:ss');
ecat2nii(ecatfile,{meta},'gz',false,'savemat',true)

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
table(summary_diff(:,1),summary_diff(:,2),summary_diff(:,3),'VariableNames',{'min','mean','max'}) % analyze diff

figure
A = min(Diff_ecat_nifti(:));
B = max(Diff_ecat_nifti(:));
subplot(2,2,1); plot(img(:),img_reread(:),'*'); hold on; 
M = max(max([img(:) img_reread(:)])); axis([0 M 0 M])
plot([0 M],[0 M],'r','LineWidth',1); grid on
xlabel('Original'); ylabel('Nifti'); title('Read vs Written');

[simg,index] = sort(img(:)); subplot(2,2,3); plot(img(:),(simg-img_reread(index)),'*')
xlabel('Original'); ylabel('Difference'); title(sprintf('Average error: %f\n',meandiff));

subplot(2,2,2); plot(summary_diff(:,2),'LineWidth',2); grid on; xlabel('frames'); 
ylabel('Difference'); title('Avg error per frame')

subplot(2,2,4); histogram(Diff_ecat_nifti(:)); 
axis([A B 0 10000]); xlabel('error'); title('Distribution of all errors')

vidObj = VideoWriter([filename '_error']);
open(vidObj); figure('Name','error per frames');
set(gcf,'Color','w','InvertHardCopy','off', 'units','normalized', 'outerposition',[0 0 1 1]);
for f=1:size(Diff_ecat_nifti,4)
    for rep = 1:8 % use to slow down the video
    clf
    subplot(3,2,[1 2 3 4]);
    histogram(frame{f}(:)); axis([-0.02 0.02 0 5000])
    xlabel('error values'); ylabel('freq.'); 
    title(sprintf('errors frame %g',f)); 

    subplot(3,2,[5 6]); plot(signal,'LineWidth',2); axis tight
    hold on; plot(f,signal(f),'rO','LineWidth',4); axis tight; 
    xlabel('frames'); ylabel('all brain TAC'); grid on; hold off
    
    CF = getframe(gcf); writeVideo(vidObj,CF);
    end
end
close(vidObj); close
function []=hrrt2neuro(FileList);
%
% hrrt2neuro([FileList])
%
% Converts ECAT 7 image file from hrrt to Analyze 7 image files, where the 
%  images are written in neurological notation with right side as right side 
%
% The *.v files are always compressed after usage using gzip
%
%  FileList - Cell array of char strings with filenames and paths
%
% Uses: readECAT7.m (Raymond Muzic, 2002)
%       WriteAnalyzeImg.m (Claus Svarer, 2004, part of PVElab)
%
% Claus Svarer, 20081015
%    (some of it are based on code from Mark Lubbering
%
% Modifications
%
% 
%

if nargin==0
  % Open input file
  [pet_file,pet_path]=uigetfile({'*.v.gz','gzipped ECAT 7 files (*.v.gz)';...
                                 '*.v','ECAT 7 files (*.v)';...
                                 '*.*','All files (*.*)'},...
                                 'Load ECAT volume',...
                                 'MultiSelect','on');
  if ischar(pet_file)
     FileList{1}=[pet_path pet_file];
  elseif iscell(pet_file)
     for i=1:length(pet_file)
        FileList{i}=[pet_path pet_file{i}];
     end
  else
     error('No file selected for conversion');
  end
end
        
for j=1:length(FileList)
   fprintf('Conversion of file: %s\n',FileList{j});
   % Read ECAT file headers
   [pet_path,pet_file,ext]=fileparts(FileList{j});

   if strcmp(ext,'.gz')
      gunzip([pet_path filesep pet_file ext]);
      Compressed=1;
   else
      pet_file=[pet_file ext];
      Compressed=0;
   end

   [mh,sh]=readECAT7([pet_path filesep pet_file]);

   img_temp=zeros(sh{1}.x_dimension,sh{1}.y_dimension,sh{1}.z_dimension,mh.num_frames);

   for i=1:mh.num_frames
      fprintf('  Working at frame: %i\n',i);
      [mh,sh,data]=readECAT7([pet_path filesep pet_file],i);
      img_temp(:,:,:,i)=flipdim(flipdim(flipdim((double(cat(4,data{:}))*sh{1}.scale_factor),2),3),1);
   end
   MaxImg=max(img_temp(:));
   img_temp=img_temp/MaxImg*32767;
   Sca=MaxImg/32767;

   MinImg=min(img_temp(:));
   if (MinImg<-32768)
      img_temp=img_temp/MinImg*(-32768);
      Sca=Sca*MinImg/(-32768);
   end

   pos=strfind(pet_file,'.');
   hdr.name=pet_file;
   hdr.name(pos)='_';
   hdr.name=hdr.name(1:end-2);
   hdr.path=pet_path;
   if sh{1}.data_type==6
      hdr.pre=16;
      hdr.lim=[32767 -32768];
   else
      error(['Can for the moment only handle 16 bit signed data, (type 6 in ecat file)']);
   end
   hdr.dim=[sh{1}.x_dimension sh{1}.y_dimension sh{1}.z_dimension mh.num_frames];
   hdr.siz=[sh{1}.x_pixel_size sh{1}.y_pixel_size sh{1}.z_pixel_size]*10;
   hdr.scale=Sca*mh.ecat_calibration_factor;
   hdr.offset=0;
   hdr.origin=[0 0 0];
   hdr.descr='HRRT image, converted using hrrt2a';
   hdr.endian='ieee-le';

   WriteAnalyzeImg(hdr,img_temp);

%    if (length(hdr.dim)>3)&&(hdr.dim(4)>1)
%        hrrt2time([pet_path filesep pet_file]);
%        movefile([pet_path filesep hdr.name(6:end) '.tim'],[pet_path filesep hdr.name '.tim']);
%        movefile([pet_path filesep hdr.name(6:end) '.sif'],[pet_path filesep hdr.name '.sif']);
%    end
   
%    if Compressed==0
%       gzip([pet_path filesep pet_file]);
%       delete([pet_path filesep pet_file]);
%    elseif Compressed==1
%       delete([pet_path filesep pet_file]);
%    else
%       fprintf('Unknown compression scheme, nothing done\n');
%    end

end
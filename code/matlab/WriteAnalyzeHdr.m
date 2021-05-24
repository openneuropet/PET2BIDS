function [result]=WriteAnalyzeHdr(name,dim,siz,pre,lim,scale,offset,origin,descr),
%  Writes the analyze header file 
%
%    [result]=WriteAnalyzeHdr(name,dim,siz,pre,lim,scale,offset,origin[,descr])
%    [result]=WriteAnalyzeHdr(name,dim,siz,pre,lim,scale,offset,origin,descr)
%    [result]=WriteAnalyzeHdr(hdr)
%
%  name      - name of image file
%  dim       - x,y,z,[t] no of pixels in each direction
%  siz       - voxel size in mm
%  pre       - precision for voxels in bit
%                1 - 1 single bit
%                8 - 8 bit voxels (lim is used for deciding if signed or
%                     unsigned char, if min < 0 then signed))
%               16 - 16 bit integer (lim is used for deciding if signed or
%                     unsigned notation should be used, if min < 0 then signed))
%               32 - 32 bit floats
%               32i - 32 bit complex numbers (64 bit pr. voxel)
%               64 - 64 bit floats
%  lim       - max and min limits for pixel values (ex: [255 0] for 8 bit)
%  scale     - scale is scaling of pixel values
%  offset    - offset is offset in pixel values
%  origin    - origin for AC-PC plane
%  descr     - description of file, scan
%
%  hdr       - structure with all the fields mentionened above plus
%               path - path for file
%               endian - defaults to big endian, can be overwritten 
%               using this field
%
%  abs_pix_val = (pix_val - offset) * scale
%
%  CS, 130398
%  CS, 280100  Reading changed so routines works on both HP and Linux
%              systems
%  CS, 150200  Extended to be able to use descrion field
%  CS, 060700  Structure input (hdr) extended as possibility
%  CS, 210901  Extended with extra 'path' field in stucture hdr
%  PW, 300402  Extended with extra 'endian' field in structure hdr
%
if (nargin ~=1) & (nargin ~= 8) & (nargin ~= 9)
   ErrTxt=sprintf('WriteAnalyzeHdr, (%i) is an incorrect number of input arguments',nargin);
   error(ErrTxt);
end;
if (nargin == 8)
  descr='Header generated using WriteAnalyzeHdr';
end
if (nargin == 8) | (nargin == 9)
  path='';
end  
% 
% Default endianness:
%
endian='ieee-be';

if (nargin == 1)
  hdr=name;
  %
  if (~isfield(hdr,'name'))
    error('hdr.name does not exist');
  end;
  name=hdr.name;
  if (~isfield(hdr,'dim'))
    error('hdr.dim does not exist');
  end;
  dim=hdr.dim;
  if (~isfield(hdr,'siz'))
    error('hdr.siz does not exist');
  end;
  siz=hdr.siz;
  if (~isfield(hdr,'pre'))
    error('hdr.pre does not exist');
  end;
  pre=hdr.pre;
  if (~isfield(hdr,'lim'))
    error('hdr.lim does not exist');
  end;
  lim=hdr.lim;
  if (~isfield(hdr,'scale'))
    error('hdr.scale does not exist');
  end;
  scale=hdr.scale;
  if (~isfield(hdr,'offset'))
    error('hdr.offset does not exist');
  end;
  offset=hdr.offset;
  if (~isfield(hdr,'origin'))
    origin=[0 0 0];
  else  
    origin=hdr.origin;
  end;
  if (~isfield(hdr,'descr'))
    descr='Header generated using WriteAnalyzeHdr';
  else  
    descr=hdr.descr;
  end;
  if isfield(hdr,'endian')
    endian=hdr.endian;
  end
  if (~isfield(hdr,'path')) | ...
    ~isempty(strfind(hdr.name,'/')) | ... 
    ~isempty(strfind(hdr.name,'\')) 
    path='';
  else  
    path=hdr.path;
  end;
end
%
if (length(dim) == 3)
  dim(4)=1;
end;
%
% Max in lim should be first lim[max min]
%
if lim(1)<lim(2)
  dummy=lim(1);
  lim(1)=lim(2);
  lim(2)=dummy;
end
%  
result=1;
FileName=fullfile(path,[name '.hdr']);
pid=fopen(FileName,'wb',endian);
%
fwrite(pid,348,'int');
fwrite(pid,zeros(28,1),'char');
fwrite(pid,16384,'int');
fwrite(pid,zeros(2,1),'char');
fwrite(pid,'r','char');
fwrite(pid,zeros(1,1),'char');

fwrite(pid,4,'int16');
fwrite(pid,dim,'int16');
fwrite(pid,zeros(20,1),'char');

if ~isreal(pre)                    % Complex number (2x32 bit float)
  pre=imag(pre);
  if (pre~=32)
    error('Only 32 bit float can be written as complex numbers');
  else
    fwrite(pid,32,'int16');
    BitPix=64;
  end      
elseif (pre == 1),                 % binary (single bit)
  fwrite(pid,1,'int16');
  BitPix=1;
elseif (pre == 8),                 % 8 bit unsigned char
  fwrite(pid,2,'int16');
  BitPix=8;
elseif (pre == 16),                % 16 bit signed integer
  fwrite(pid,4,'int16');
  BitPix=16;
elseif (pre == 32),                % 32 bit float
  fwrite(pid,16,'int16');
  BitPix=32;
elseif (pre == 64),                % 64 bit float
  fwrite(pid,64,'int16');
  BitPix=64;
else
  error('WriteAnalyzeHdr, pre parameter do not have allowable value');
end  

fwrite(pid,BitPix,'int16');

fwrite(pid,zeros(6,1),'char');

if (length(siz) ~= 3)
  error('WriteAnalyzeHdr, siz parameter do not have allowable value');
end;  
fwrite(pid,siz,'float32');

fwrite(pid,zeros(16,1),'char');
fwrite(pid,offset,'float32');
fwrite(pid,scale,'float32');
fwrite(pid,zeros(24,1),'char');

fwrite(pid,lim(1),'int');
fwrite(pid,lim(2),'int');

descr(80)=0;
fwrite(pid,sprintf('%-80s',descr),'char');

fwrite(pid,zeros(24,1),'char');
fwrite(pid,0,'char');  % orientation

if (length(origin) ~= 3)
  error('WriteAnalyzeHdr, origin parameter do not have allowable value');
end;  
fwrite(pid,origin,'int16');  

fwrite(pid,zeros(89,1),'char'); 

fclose(pid);






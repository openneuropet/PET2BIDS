function [result]=WriteAnalyzeImg(name,img,dim,siz,pre,lim,scale,offset,origin,descr)
%  Writes analyze image and header file
%
%    [result]=WriteAnalyzeImg(name,img,dim,siz,pre,lim,scale,offset)
%    [result]=WriteAnalyzeImg(name,img,dim,siz,pre,lim,scale,offset,origin)
%    [result]=WriteAnalyzeImg(name,img,dim,siz,pre,lim,scale,offset,origin,descr)
%    [result]=WriteAnalyzeImg(name,img,dim,siz,pre,lim,'a') (automatic scaling/offset)
%    [result]=WriteAnalyzeImg(hdr,img)
%
%  name      - name of image file
%  img       - image data (pix_val)
%  dim       - x,y,z,[t] no of pixels in each direction
%  siz       - voxel size in mm
%  pre       - precision for pictures (8 or 16)
%  lim       - max and min limits for pixel values (ex: [255 0] for 8 bit)
%  scale     - scale is scaling of pixel values
%  offset    - offset is offset in pixel values
%  origin    - origin for AC-PC plane
%  descr     - description field in header file
%
%  hdr       - header structure (as defined for WriteAnalyzeHdr) plus
%               path - filed with path for file
%               endian - defaults to big endian, can be overwritten
%               using this field
%
%  abs_pix_val = (pix_val - offset) * scale
%
%  CS, 010294
%
%  Revised
%  CS, 181194  Possibility of offset and scale in header file
%  CS, 300398  Origin included
%  CS, 280100  Reading changed so routines works on both HP and Linux
%              systems
%  CS, 150200  Extended with description field
%  CS, 060700  writing routine extended to handle structure header
%              information
%  CS, 210901  Extended with extra field 'path' in structure hdr
%  PW; 200402  Extended with extra field 'endian' in structure hdr
%
if (nargin ~= 7) && (nargin ~= 8) && (nargin ~= 9) && (nargin ~= 10) ...
        && (nargin ~= 2)
    error('WriteAnalyze, incorrect number of input arguments');
end;
%
% Default endianness:
%
endian='ieee-be';
if (nargin == 2)
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
    if (~isfield(hdr,'path')) || ...
            ~isempty(strfind(hdr.name,'/')) || ...
            ~isempty(strfind(hdr.name,'\'))
        path='';
    else
        path=hdr.path;
        if ~isempty(path)
            cname = computer;
            if strcmp(cname(1:2),'PC')
                if (path(length(path)) ~= '\')
                    path(length(path)+1) ='\';
                end
            else
                if (path(length(path)) ~= '/')
                    path(length(path)+1) ='/';
                end
            end
        end
    end;
else
    path='';
end
%
if (length(dim) == 3)
    dim(4)=1;
end;
auto = 0;  % Ikke automatisk skalering
if (nargin == 7)
    if (scale == 'a')
        auto = 1;
        if (pre == 8)
            scale = (max(max(img)) - min(min(img))) / 256;
            img = img / scale;
            offset = - min(min(img));
            img = img + offset;
            offset = offset - 0.5;
            index = find(img == 256);
            for i=1:length(index)
                img(index(i)) = 255;
            end;
        else
            if (lim(2) < 0)
                offset = 0;
                scale1 = max(max(img)) / 32767;
                scale2 = min(min(img)) / (-32768);
                scale = max([scale1 scale2]);
                img = img / scale;
            else
                scale = (max(max(img)) - min(min(img))) / 65536;
                img = img / scale;
                offset = - min(min(img));
                img = img + offset;
                offset = offset - 0.5;
                index = find(img == 65536);
                for i=1:length(index)
                    img(index(i)) = 65535;
                end;
            end;
        end;
    else
        error('Not automatic scaling, but only 7 parameters');
    end;
end;
result=1;
%
pos=strfind(name,'.img');
if (~isempty(pos))
    name=name(1:(pos(1)-1));
    hdr.name=name;
end;
pos=strfind(name,'.hdr');
if (~isempty(pos))
    name=name(1:(pos(1)-1));
    hdr.name=name;
end;
%
FileName=sprintf('%s%s.img',path,name);
pid=fopen(FileName,'wb',endian);
if (pid ~= -1),
    if ~isreal(pre)
        if (imag(pre) ~= 32)
            error('Only 32 bit complex files available');
        else
            Data=zeros(2*length(img(:)),1);
            Data(1:2:end)=real(img);
            Data(2:2:end)=imag(img);
            fwrite(pid,Data,'float32');
        end
    elseif (pre == 1),
        fwrite(pid,round(img),'bit1');
    elseif (pre == 8),
        if isa(img,'uint8')
            fwrite(pid,img,'uint8');
        else
            fwrite(pid,round(img),'uint8');
        end
    elseif (pre == 16),
        if (lim(2) < 0)
            if isa(img,'int16')
                fwrite(pid,img,'int16');
            else
                fwrite(pid,round(img),'int16');
            end
        else
            if isa(img,'uint16')
                fwrite(pid,img,'uint16');
            else
                fwrite(pid,round(img),'uint16');
            end
        end
    elseif (pre == 32)
        fwrite(pid,img,'float32');
    elseif (pre == 64)
        fwrite(pid,img,'float64');
    else
        error('Illegal precision');
    end;
    %
    if (nargin == 6),
        scale=0;
        offset=0;
        origin=[0 0 0];
    elseif (nargin == 7) && (auto == 0),
        offset=0;
        origin=[0 0 0];
    elseif (nargin == 8) && (auto == 0),
        origin=[0 0 0];
    else
        % All parameters defined
    end;
    if (nargin == 2)
        WriteAnalyzeHdr(hdr);
    elseif (nargin == 10)
        WriteAnalyzeHdr(name,dim,siz,pre,lim,scale,offset,origin,descr);
    else
        WriteAnalyzeHdr(name,dim,siz,pre,lim,scale,offset,origin);
    end
else
    result=0;
    fprintf('WriteAnalyze, Not possible to open image file\n');
end;
fclose(pid);







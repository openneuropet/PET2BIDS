function inputData = pet2bids_exe_script(file_name)
%% Evaluate script and store the variables in a data structure
% 
% Inputs:
% file_name - File name
%
% Outputs:
% inputData - Input data structure
%
% Cyrus Eierud Oct 21, 2022

global G_PETS2BIDS_EXE_PATH

if (isdeployed)
    % execute scripts differently in deployed mode
    fid = -1;
    try
        fid = fopen(file_name, 'r');
    catch
    end
    
    if (fid == -1)
        try
            tmp_strs = file_name;
        catch
            error(['File ', file_name, ' cannot be opened']);
        end
    else
        try
            tmp_strs = fread(fid, '*char');
            fclose(fid);
        catch
            fclose(fid);
        end
    end
    
    % Path to dcm2niix is expected to be same as the script directory
    [G_PETS2BIDS_EXE_PATH, fName, extn] = fileparts(file_name);
    if isempty(G_PETS2BIDS_EXE_PATH)
        G_PETS2BIDS_EXE_PATH = pwd;
    end
    
    %% Evaluate file
    try
        eval(tmp_strs');
    catch ME
        fprintf(2,'MATLAB code threw an exception:\n');
        fprintf(2,'%s\n',ME.message);
        if length(ME.stack) ~= 0
            fprintf(2,'File:%s\nName:%s\nLine:%d\n',ME.stack.file,ME.stack.name,ME.stack.line);
        end
    end    
    
    clear fid tmp_strs;
    
else
    
    oldDir = pwd;
    
    %% Do file parts
    [pathstr, fName, extn] = fileparts(file_name);
    if isempty(pathstr)
        pathstr = pwd;
    end
    
    cd(pathstr);
    
    %% Evaluate file
    try
        eval(fName);
    catch ME
        fprintf(2,'MATLAB code threw an exception:\n');
        fprintf(2,'%s\n',ME.message);
        if length(ME.stack) ~= 0
            fprintf(2,'File:%s\nName:%s\nLine:%d\n',ME.stack.file,ME.stack.name,ME.stack.line);
        end
    end
    
    cd(oldDir);
    
end

if (nargout == 1)
    
    vars = whos;
    
    if (length(vars) == 1)
        error(['No variables found in file ', file_name]);
    end
    
    % Generate inputData
    inputData = struct;
    for n = 1:length(vars)
        inputData = setfield(inputData, vars(n).name, eval(vars(n).name));
    end
    
end

pet2bids_dirpreserver(0); % line needed to keep json directory after compilation
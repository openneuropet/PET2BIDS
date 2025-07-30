function schema = get_bids_schema(schema_version)
%GET_BIDS_SCHEMA Get BIDS schema with online fallback
%   SCHEMA = GET_BIDS_SCHEMA() gets the latest BIDS schema
%   SCHEMA = GET_BIDS_SCHEMA(VERSION) gets a specific version
%
%   This function tries to use the packaged schema first, then falls
%   back to downloading from online if the local version is not available.

    if nargin < 1
        schema_version = 'latest';
    end
    
    % Try to get from Python package first
    try
        % Get the path to the Python package
        python_package_path = get_python_package_path();
        schema_path = fullfile(python_package_path, 'bids_schema.json');
        
        if exist(schema_path, 'file')
            schema = read_json_file(schema_path);
            return;
        end
    catch
        % Continue to online fallback
    end
    
    % Try online download
    try
        url = sprintf('https://bids-specification.readthedocs.io/en/%s/schema.json', schema_version);
        schema = webread(url);
        return;
    catch
        error('BIDS schema not available online or offline');
    end
end

function package_path = get_python_package_path()
%GET_PYTHON_PACKAGE_PATH Get path to the pypet2bids package
    
    % Try to find the package in common locations
    possible_paths = {
        fullfile(pwd, 'pypet2bids', 'pypet2bids'),  % Local development
        fullfile(fileparts(mfilename('fullpath')), '..', 'pypet2bids', 'pypet2bids'),  % Relative to this file
        fullfile(userpath, 'pypet2bids'),  % User path
    };
    
    for i = 1:length(possible_paths)
        if exist(possible_paths{i}, 'dir')
            package_path = possible_paths{i};
            return;
        end
    end
    
    error('Could not find pypet2bids package');
end

function data = read_json_file(filepath)
%READ_JSON_FILE Read and parse JSON file
    
    fid = fopen(filepath, 'r');
    if fid == -1
        error('Could not open file: %s', filepath);
    end
    
    try
        content = fread(fid, inf, 'char=>char')';
        data = jsondecode(content);
    catch ME
        fclose(fid);
        rethrow(ME);
    end
    
    fclose(fid);
end 
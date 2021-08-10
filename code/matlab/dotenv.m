classdef dotenv
    % Dotenv Implementation of common dotenv pattern 
    % dotenv allows you to load environment variables at runtime without 
    % committing your .env file to source control. A common reason for 
    % doing this is that you need a password or API key but don't want to 
    % embed that in your code or in source control. 
    % See https://github.com/motdotla/dotenv for inspiration
    % Copyright 2019-2019 The MathWorks, Inc.

    properties (SetAccess = immutable)
        env % Structure to hold key/value pairs. Access via d.env.key.
    end
    
    properties (Access = private)
        fname
    end
    
    
    methods
        function obj = dotenv(location)
            % d = dotenv([path/to/file.env]) -- load .env file from current working directory or specified via path.
            obj.env = struct;
            switch nargin
                case 1 % if there is an argument load that file
                    obj.fname = location;
                case 0 % otherwise load the file from the current directory
                    obj.fname = '.env';
            end
            
            % ensure we can open the file
            try
                fid = fopen(obj.fname, 'r');
                assert(fid ~= -1);
            catch
                throw( MException('DOTENV:CannotOpenFile', "Cannot open file: " + obj.fname + ". Code: " + fid) );
            end
            fclose(fid);
            
            % load the .env file with name=value pairs into the 'env' struct
            lines = string(splitlines(fileread(obj.fname)));

            notOK = startsWith(lines, '#');
            lines(notOK) = [];
                   
            expr = "(?<key>.+?)=(?<value>.*)";
            kvpair = regexp(lines, expr, 'names');
            
            % Deal with single entry case where regexp does not return a
            % cell array
            if iscell(kvpair)
                kvpair(cellfun(@isempty, kvpair)) = [];
                kvpair = cellfun(@(x) struct('key', x.key, 'value', x.value), kvpair);
            end
            
            obj.env = cell2struct(strtrim({kvpair.value}), [kvpair.key], 2);
            
        end
        
        function val = subsref(obj, s)
            % Overload subsref to handle d.env (all key/value pairs vs. d.env.key (the value specified by the supplied key)
            if size(s, 2) == 1
                % this handles the case of d.env
                val=obj.env;
            else
                % this handles the case of d.env.KEY_NAME
                if isfield(obj.env, s(2).subs)
                    val = obj.env.(s(2).subs);
                else
                    val = "";
                end
            end
        end
        
    end
    
end


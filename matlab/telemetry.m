function telemetry(telemetry_data, input_path, output_path)
    arguments
        telemetry_data (1,:) struct
        input_path (1,:) string = ''
        output_path (1,:) string = ''
    end

    if telemetry_enabled
        % do all the things

        telemetry_data.description = "Matlab";

        if strcmp(input_path, '')
            % do nothing
        else
            input_file_count = count_input_files(input_path);
            telemetry_data.TotalInputFiles = input_file_count.TotalInputFiles;
            telemetry_data.TotalInputFileSize = input_file_count.TotalInputFileSize;
        end

        url = 'http://52.87.154.236/telemetry/';
        options = weboptions('MediaType', 'application/json');
        response = webwrite(url, telemetry_data, options);

    else
        % don't do anything
    end
end

function e = telemetry_enabled()
    % checks to see if the telemetry is enabled or disabled 
    environment = getenv();
    home_dir = environment("HOME");
    loadenv(fullfile(home_dir, '.pet2bidsconfig'), FileType='env');
    % convert string to boolean/logical
    disable_telemetry = strcmpi(getenv("PET2BIDS_TELEMETRY_ENABLED"), 'false');
    
    if disable_telemetry
        e = false;
    else
        e = true;
    end 
    
end


function c = count_input_files(input_path)
    % generate a list of all the files in the input directory
    % count the number of files in the input directory
    % count the total size of the files in the input directory
    % return the count and the size

    % if the input path is a file then return 1 and the size of the file
    if isfile(input_path)
        input_file = dir(input_path);
        c.TotalInputFiles = 1;
        c.TotalInputFileSize = input_file.bytes;
        return
    elseif isfolder(input_path)
        % get the list of files in the input directory
        input_files = dir(input_path);
        % count the number of files in the input directory
        file_count = length(input_files);
        % count the total size of the files in the input directory
        total_size = 0;
        for i = 1:file_count
            total_size = total_size + input_files(i).bytes;
        end
        c.TotalInputFiles = file_count;
        c.TotalInputFileSize = total_size;
        return
    else
        error('Input path is not a file or a directory');
    end
end

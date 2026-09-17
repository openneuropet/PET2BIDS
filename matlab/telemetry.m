function response = telemetry(telemetry_data, input_path, output_path, project, url)
    arguments
        telemetry_data (1,:) struct
        input_path (1,:) string = ''
        output_path (1,:) string = ''
        project (1,1) string = "openneuropet/PET2BIDS"
        url (1,1) string = "https://migas.openneuropet.org/api/breadcrumb"
    end

    response = [];
    if telemetry_enabled
        telemetry_data.description = "Matlab";

        if strcmp(input_path, '')
            % do nothing
        else
            input_file_count = count_input_files(input_path);
            telemetry_data.TotalInputFiles = input_file_count.TotalInputFiles;
            telemetry_data.TotalInputFileSize = input_file_count.TotalInputFileSize;
        end

        if isfield(telemetry_data, 'version')
            project_version = string(telemetry_data.version);
        else
            project_version = "unknown";
        end

        status = "R";
        if isfield(telemetry_data, 'returncode')
            if telemetry_data.returncode == 0
                status = "C";
            else
                status = "F";
            end
        end

        breadcrumb.project = project;
        breadcrumb.project_version = project_version;
        breadcrumb.language = "matlab";
        breadcrumb.language_version = string(version);
        breadcrumb.ctx.session_id = string(generate_session_id());
        breadcrumb.ctx.platform = string(computer);
        breadcrumb.ctx.is_ci = strcmpi(getenv("CI"), "true");
        breadcrumb.proc.status = status;
        breadcrumb.proc.params = telemetry_data;

        options = weboptions('MediaType', 'application/json', 'Timeout', 5);
        try
            response = webwrite(url, breadcrumb, options);
        catch ME
            % do nothing
        end
    else
        % don't do anything
    end
end


function id = generate_session_id()
    bytes = randi([0, 255], 1, 16, 'uint8');
    bytes(7) = bitor(bitand(bytes(7), uint8(15)), uint8(64));
    bytes(9) = bitor(bitand(bytes(9), uint8(63)), uint8(128));
    hex = lower(reshape(dec2hex(bytes, 2).', 1, []));
    id = sprintf( ...
        '%s-%s-%s-%s-%s', ...
        hex(1:8), hex(9:12), hex(13:16), hex(17:20), hex(21:32));
end

function e = telemetry_enabled()
    % checks to see if the telemetry is enabled or disabled
    environment = getenv();
    % check environment too before loading the config file
    if isfield(environment, 'TELEMETRY_ENABLED')
        disable_telemetry_env = strcmpi(getenv("TELEMETRY_ENABLED"), 'false');
    else
        disable_telemetry_env = false;
    end

    home_dir = environment("HOME");
    try
        loadenv(fullfile(home_dir, '.pet2bidsconfig'), FileType='env');
        % convert string to boolean/logical
    catch ME
        disable_telemetry = false;
    end

    disable_telemetry = strcmpi(getenv("TELEMETRY_ENABLED"), 'false');

    % if running in CI don't run telemetry
    running_in_ci = strcmpi(getenv("CI"), 'true');

    if disable_telemetry | disable_telemetry_env | running_in_ci
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

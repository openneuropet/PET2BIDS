currentFile = mfilename( 'fullpath' );
% collect parent directory of this script
[ testpathString, ~, ~ ] = fileparts( currentFile);
% collect the matlab code directory
[ matlabString, ~, ~ ] = fileparts( testpathString );
% collect the parent of the matlab directory
[ codeString, ~, ~ ] = fileparts( matlabString );
% add path to env in python directory onto codestring to  collect the .env
env = fullfile(codeString, 'python', '.env');

% load the environment variables
environment_vars = dotenv(env);

path_to_ecat = environment_vars.env.TEST_ECAT_PATH;
python_ecat_read_saved_to_mat_file = environment_vars.env.READ_ECAT_SAVE_AS_MATLAB;

[mat_mh, mat_sh, mat_data] = readECAT7(path_to_ecat);
load(python_ecat_read_saved_to_mat_file);

% reshape matlab data thing from cell of 3rd matrices into 4d matrix
mat_data = cat(4, mat_data{:});

arrays_equal = isequal(data, mat_data)


% Checks if the ECAT array data as read from a) pypet2bids.read_ecat and b) matlab/readECAT7.m return identical pixel
% arrays. Used during the initial development and final verification of pypet2bids.read_cat.
%
% Requires:
%   - a very specific directory structure so that it is able to navigate to code and txt files
%   - dotenv for MATLAB:
%       - https://github.com/mathworks/dotenv-for-MATLAB or
%       - https://www.mathworks.com/matlabcentral/fileexchange/73988-dotenv-for-matlab
%   - a dotenv file with the valid paths to the following variables:
%       - READ_ECAT_SAVE_AS_MATLAB
%       - TEST_ECAT_PATH
%
% Returns boolean -> arrays_equal
%
% Notes:
% This script is left here for archival purposes, mostly to remind the writer (or anyone who has an inclination to ask)
% whether or not the pixel values that are the baseline truth match when they are read in w/ the matlab code or
% the python code contained in this repository.
%
% Copyright 2021 Anthony Galassi
% Not intended for clinical/diagnostic use. User assumes all risk.

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


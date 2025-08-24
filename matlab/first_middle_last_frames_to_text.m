function [output_folder, step_name] = first_middle_last_frames_to_text(four_d_array_like_object,output_folder, step_name)
%takes a times series of 3d images and writes out sub sections of that time
%series as  2D frames. Frames are labeled as zero indexed to align with
%python conventions. Up to 3 frames are selected from the time series
%corresponding to the first, middle, and last frames.
%   four_d_array_like_object: input time series
%   output_folder: path to write the selected 2D frames to
%   step_name: name to apply to output files
%   
output_folder = output_folder;
step_name = step_name;
data = four_d_array_like_object;
data_size = size(data);

% get first, middle, and last frame of data
frames = [ 1, floor(data_size(4)/2) + 1, data_size(4)]
frames_to_record = cell(length(frames));
for i = 1:length(frames)
    frame_number = frames(i);
    frame_to_slice = data(:,:,:,frame_number);
    size_of_frame_to_slice = size(frame_to_slice)
    middle_of_frame = int16(size_of_frame_to_slice(3)/2);
    slice = data(:,:,middle_of_frame,frame_number);
    frames_to_record{i} = slice;
end

for i = 1:length(frames_to_record)
    frame = frames_to_record{i};
    frame_string = string(frames(i) - 1);
    filename = strcat(output_folder, filesep, step_name, '_frame_', frame_string, '.tsv');
    writematrix(frame, filename, 'Delimiter', 'tab', 'FileType', 'text');
end

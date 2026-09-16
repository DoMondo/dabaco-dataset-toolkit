% evaluate_baseline.m
% Example script for evaluating the classical screen detector baseline
% Make sure to run this from the 'matlab' folder.

addpath('../access');
addpath('../metrics');
addpath('../baselines');

% Dataset path
dataset_dir = '/path/to/extracted/dabaco_esp32_ov3660';

try
    fprintf('Loading dataset from %s\n', dataset_dir);
    dataset = dabaco_dataset(dataset_dir);
    
    seq_names = dataset.get_sequence_names();
    
    for s = 1:length(seq_names)
        seq_name = seq_names{s};
        fprintf('Evaluating sequence: %s\n', seq_name);
        
        [frames_dir, ground_truth] = dataset.get_sequence(seq_name, true);
        
        num_frames = ground_truth.total_frames;
        gt_list = cell(num_frames, 1);
        
        % MATLAB structs read from JSON have field names like 'x48' if keys are numeric.
        % The dabaco_dataset handles the struct format, but let's just parse the fields.
        % Since jsondecode in MATLAB prefixes numeric keys with 'x' (e.g. "48" -> "x48").
        fields = fieldnames(ground_truth.frames);
        
        for f = 1:length(fields)
            field = fields{f};
            % Extract the actual index (remove 'x' prefix if exists)
            idx_str = strrep(field, 'x', '');
            idx = str2double(idx_str);
            % Indices in ground truth JSON are 0-based strings, so add 1 for MATLAB
            idx = idx + 1;
            
            frame_data = ground_truth.frames.(field);
            if isfield(frame_data, 'corners')
                % The jsondecode parses array of arrays as cell array if mixed, or matrix.
                if iscell(frame_data.corners)
                    corners = zeros(4, 2);
                    for c = 1:4
                        corners(c, :) = cell2mat(frame_data.corners{c});
                    end
                    gt_list{idx} = corners;
                else
                    gt_list{idx} = frame_data.corners;
                end
            end
        end
        
        pred_list = cell(num_frames, 1);
        
        % Iterate over video frames
        % To be robust and match python, we should iterate over frames 0 to num_frames-1
        for i = 0:(num_frames-1)
            % DABACO frames are stored as 000000.jpg, etc.
            frame_file = fullfile(frames_dir, sprintf('%06d.jpg', i));
            
            if exist(frame_file, 'file')
                frame = imread(frame_file);
                corners = screen_detector(frame);
                pred_list{i+1} = corners;
            else
                % Also check .png or video stream logic if necessary
                % For this baseline we assume .jpg frames
                pred_list{i+1} = [];
            end
        end
        
        % Get resolution from ground truth
        w = 1280; h = 960;
        if isfield(ground_truth, 'src_width')
            w = ground_truth.src_width;
        end
        if isfield(ground_truth, 'src_height')
            h = ground_truth.src_height;
        end
        
        % Calculate metrics
        results = evaluate_all(gt_list, pred_list, w, h);
        
        fprintf('Results for %s:\n', seq_name);
        fprintf('  Detection Rate: %.4f\n', results.DetectionRate);
        fprintf('  Mean Corner Error (px): %.4f\n', results.MeanCornerErrorPx);
        fprintf('  Mean Corner Error (%%): %.4f\n', results.MeanCornerErrorPct);
        fprintf('  Mean IoU: %.4f\n', results.MeanIoU);
        fprintf('  Mean Jitter (px): %.4f\n', results.MeanJitterPx);
        fprintf('  Mean Jitter (%%): %.4f\n', results.MeanJitterPct);
    end
catch ME
    fprintf('Error during evaluation: %s\n', ME.message);
    % disp(getReport(ME));
end

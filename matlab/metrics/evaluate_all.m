function results = evaluate_all(gt_list, pred_list, img_width, img_height)
    % evaluate_all Calculates evaluation metrics for the dataset
    % gt_list: cell array of ground truth corners (each is 4x2 matrix or empty)
    % pred_list: cell array of predicted corners (each is 4x2 matrix or empty)
    % img_width, img_height: resolution of the video sequence
    
    if length(gt_list) ~= length(pred_list)
        error('Length of ground truth and predictions must match.');
    end
    
    num_frames = length(gt_list);
    diagonal = sqrt(img_width^2 + img_height^2);
    
    % Initialize metrics accumulators
    valid_detections = 0;
    total_valid_gt = 0;
    
    corner_errors = [];
    iou_scores = [];
    
    gt_centers = nan(num_frames, 2);
    pred_centers = nan(num_frames, 2);
    
    for i = 1:num_frames
        gt = gt_list{i};
        pred = pred_list{i};
        
        has_gt = ~isempty(gt);
        has_pred = ~isempty(pred);
        
        if has_gt
            total_valid_gt = total_valid_gt + 1;
            % Calculate GT center
            gt_centers(i, :) = mean(gt, 1);
        end
        
        if has_pred
            pred_centers(i, :) = mean(pred, 1);
        end
        
        if has_gt && has_pred
            valid_detections = valid_detections + 1;
            
            % 1. Calculate Corner Error
            % Since corners might be shifted, we find the minimum error permutation
            % For quadrilaterals, there are 4 cyclic shifts.
            min_err = inf;
            for shift = 0:3
                pred_shifted = circshift(pred, shift, 1);
                err = mean(sqrt(sum((gt - pred_shifted).^2, 2)));
                if err < min_err
                    min_err = err;
                end
            end
            
            % Check if reversed order is better
            pred_rev = flipud(pred);
            for shift = 0:3
                pred_shifted = circshift(pred_rev, shift, 1);
                err = mean(sqrt(sum((gt - pred_shifted).^2, 2)));
                if err < min_err
                    min_err = err;
                end
            end
            corner_errors(end+1) = min_err;
            
            % 2. Calculate IoU
            % Find bounding box for both polygons to create a mask
            all_pts = [gt; pred];
            min_x = floor(min(all_pts(:, 1)));
            max_x = ceil(max(all_pts(:, 1)));
            min_y = floor(min(all_pts(:, 2)));
            max_y = ceil(max(all_pts(:, 2)));
            
            w = max_x - min_x + 1;
            h = max_y - min_y + 1;
            
            if w > 0 && h > 0
                mask_gt = poly2mask(gt(:, 1) - min_x + 1, gt(:, 2) - min_y + 1, h, w);
                mask_pred = poly2mask(pred(:, 1) - min_x + 1, pred(:, 2) - min_y + 1, h, w);
                
                intersection = sum(sum(mask_gt & mask_pred));
                union = sum(sum(mask_gt | mask_pred));
                
                if union > 0
                    iou_scores(end+1) = intersection / union;
                else
                    iou_scores(end+1) = 0;
                end
            else
                iou_scores(end+1) = 0;
            end
        elseif has_gt && ~has_pred
            % False negative
            iou_scores(end+1) = 0;
        end
    end
    
    % 3. Calculate Detection Rate
    if total_valid_gt > 0
        detection_rate = valid_detections / total_valid_gt;
    else
        detection_rate = 0;
    end
    
    % 4. Calculate Jitter
    % Difference between the displacement of the GT center and Pred center between consecutive frames
    jitter_values = [];
    for i = 2:num_frames
        if ~isnan(gt_centers(i-1,1)) && ~isnan(gt_centers(i,1)) && ~isnan(pred_centers(i-1,1)) && ~isnan(pred_centers(i,1))
            gt_disp = gt_centers(i, :) - gt_centers(i-1, :);
            pred_disp = pred_centers(i, :) - pred_centers(i-1, :);
            jitter_values(end+1) = norm(gt_disp - pred_disp);
        end
    end
    
    % Compile results
    results = struct();
    results.DetectionRate = detection_rate;
    
    if ~isempty(corner_errors)
        results.MeanCornerErrorPx = mean(corner_errors);
        results.MeanCornerErrorPct = (mean(corner_errors) / diagonal) * 100;
    else
        results.MeanCornerErrorPx = nan;
        results.MeanCornerErrorPct = nan;
    end
    
    if ~isempty(iou_scores)
        results.MeanIoU = mean(iou_scores);
    else
        results.MeanIoU = 0;
    end
    
    if ~isempty(jitter_values)
        results.MeanJitterPx = mean(jitter_values);
        results.MeanJitterPct = (mean(jitter_values) / diagonal) * 100;
    else
        results.MeanJitterPx = nan;
        results.MeanJitterPct = nan;
    end
end

function corners = screen_detector(frame)
    % screen_detector Classical baseline for screen detection
    % frame: RGB or grayscale image
    % returns: 4x2 matrix of [x, y] coordinates for the corners, or [] if none found
    
    corners = [];
    
    if size(frame, 3) == 3
        gray = rgb2gray(frame);
    else
        gray = frame;
    end
    
    % Apply Gaussian blur (implicit in edge('canny'), but we can smooth explicitly if needed)
    % Find edges using Canny
    edges = edge(gray, 'canny');
    
    % Morphological closing to connect fragmented edges
    se = strel('square', 3);
    edges = imclose(edges, se);
    
    % Find boundaries
    % 'noholes' since we only care about outer contours
    [B, L] = bwboundaries(edges, 8);
    
    max_area = 0;
    best_corners = [];
    
    for k = 1:length(B)
        boundary = B{k};
        
        % boundary is Nx2 where col 1 is row (y), col 2 is col (x)
        % Let's convert to x, y format
        contour = [boundary(:, 2), boundary(:, 1)];
        
        % Approximate polygon
        % We use reducepoly or a custom douglas peucker.
        % For compatibility across Matlab/Octave without mapping toolbox:
        
        % Simple approximation: 
        % Find the convex hull or bounding box, but for screen we want quadrilaterals.
        % A simple way is to use convex hull and check if it has 4 dominant corners.
        % Wait, a robust way is to just find the bounding box, or use the standard DP.
        
        % DP algorithm approximation:
        tol = 0.02 * size(contour, 1); % 2% of arc length
        approx = douglas_peucker(contour, tol);
        
        % If the approximated contour has 4 points and is convex
        if size(approx, 1) >= 4 && size(approx, 1) <= 5 
            % Sometimes first and last point are the same, so it's 5 points
            if size(approx, 1) == 5
                approx = approx(1:4, :);
            end
            
            % Calculate area
            area = polyarea(approx(:, 1), approx(:, 2));
            
            % Check if it's the largest
            if area > max_area
                % Optional: check convexity
                % if is_convex(approx)
                    max_area = area;
                    best_corners = approx;
                % end
            end
        end
    end
    
    corners = best_corners;
end

function approx = douglas_peucker(pointList, epsilon)
    % Recursive Douglas-Peucker Polygon Simplification
    % Find the point with the maximum distance
    dmax = 0;
    index = 0;
    end_idx = size(pointList, 1);
    
    if end_idx < 3
        approx = pointList;
        return;
    end
    
    line_pt1 = pointList(1, :);
    line_pt2 = pointList(end, :);
    
    % Calculate distance from line for all points
    for i = 2:(end_idx - 1)
        pt = pointList(i, :);
        % distance from point to line
        num = abs((line_pt2(1) - line_pt1(1)) * (line_pt1(2) - pt(2)) - (line_pt1(1) - pt(1)) * (line_pt2(2) - line_pt1(2)));
        den = norm(line_pt2 - line_pt1);
        if den == 0
            d = norm(pt - line_pt1);
        else
            d = num / den;
        end
        
        if d > dmax
            index = i;
            dmax = d;
        end
    end
    
    % If max distance is greater than epsilon, recursively simplify
    if dmax > epsilon
        recResults1 = douglas_peucker(pointList(1:index, :), epsilon);
        recResults2 = douglas_peucker(pointList(index:end, :), epsilon);
        
        % Build the result list
        approx = [recResults1(1:end-1, :); recResults2];
    else
        approx = [line_pt1; line_pt2];
    end
end

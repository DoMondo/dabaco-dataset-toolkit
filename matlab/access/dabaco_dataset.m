classdef dabaco_dataset
    % DABACO_DATASET Class to load DABACO dataset sequences and ground truth.
    %
    % Example usage:
    %   dataset = dabaco_dataset('path/to/extracted/zip');
    %   seq_names = dataset.get_sequence_names();
    %   [frames, gt] = dataset.get_sequence(seq_names{1}, false);
    
    properties
        DatasetDir
        Sequences
    end
    
    methods
        function obj = dabaco_dataset(dataset_dir)
            obj.DatasetDir = dataset_dir;
            obj.Sequences = obj.find_sequences();
        end
        
        function seqs = find_sequences(obj)
            json_files = dir(fullfile(obj.DatasetDir, '*.json'));
            seqs = struct('name', {}, 'json_path', {}, 'raw_dir', {}, 'inpainted_dir', {});
            
            for i = 1:length(json_files)
                [~, base_name, ~] = fileparts(json_files(i).name);
                
                raw_dir = fullfile(obj.DatasetDir, base_name);
                inpainted_dir = fullfile(obj.DatasetDir, [base_name, '_inpainted']);
                
                seqs(i).name = base_name;
                seqs(i).json_path = fullfile(json_files(i).folder, json_files(i).name);
                seqs(i).raw_dir = raw_dir;
                seqs(i).inpainted_dir = inpainted_dir;
            end
        end
        
        function names = get_sequence_names(obj)
            names = {obj.Sequences.name};
        end
        
        function [frames_dir, ground_truth] = get_sequence(obj, seq_name, load_inpainted)
            idx = find(strcmp({obj.Sequences.name}, seq_name));
            if isempty(idx)
                error('Sequence not found');
            end
            
            seq = obj.Sequences(idx);
            
            % Load ground truth
            fid = fopen(seq.json_path, 'r');
            raw = fread(fid, inf);
            str = char(raw');
            fclose(fid);
            ground_truth = jsondecode(str);
            
            if load_inpainted
                frames_dir = seq.inpainted_dir;
            else
                frames_dir = seq.raw_dir;
            end
        end
    end
end

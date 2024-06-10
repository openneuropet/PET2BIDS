function structout = flattenstruct(structin)

% routine that take a structure with nested subfileds
% and output all fields in a flat structure
%
% :format: - structout = flattenstruct(structin)
%
% :param structin: a structure with nested fields
% :returns structout: a flat structure with all the fields
%                  
%.. note::
%
%   there is an exception handling for the fieldname 'Item_1'
%   which is a DICOM name used by manufacturers to store various items
%
% | *Cyril Pernet Novembre 2021*
% | *Copyright Open NeuroPET team*

rootfields = fieldnames(structin); % root fieldnames
for f=1:length(rootfields)
    extractfrom = structin.(rootfields{f});
    if ~isstruct(extractfrom)
        structout.(rootfields{f}) = extractfrom;
    else
        done        = 0;
        fieldindex  = 1;
        while done == 0
            if isfield(extractfrom,'Item_1') % a struct of struct
                if ~isempty(extractfrom.Item_1)
                    subfields   = fieldnames(extractfrom.Item_1);
                    if ~isstruct(extractfrom.Item_1.(subfields{fieldindex}))
                        structout.(rootfields{f}) = [];
                        structout.([rootfields{f}(1) '_' subfields{fieldindex}]) = extractfrom.Item_1.(subfields{fieldindex});
                        fieldindex  = fieldindex  + 1;
                        if fieldindex == length(subfields)+1
                            done = 1;
                        end
                    else
                        disp('deep recursion')
                        tmp = extractfrom.Item_1.(subfields{fieldindex});
                        if isfield(tmp,'Item_1')  % because we can have empty struct
                            if ~isempty(tmp.Item_1)
                                extractfrom = flattenstruct(extractfrom.Item_1.(subfields{fieldindex}).Item_1);
                            else
                                done = 1;
                            end
                        else
                            fieldindex  = fieldindex  + 1;
                            if fieldindex == length(subfields)+1
                                done = 1;
                            end
                        end
                    end
                else
                    done = 1;
                end
            else % just a struct
                subfields   = fieldnames(extractfrom);
                for s=1:length(subfields)
                    structout.(rootfields{f}) = [];
                    structout.([rootfields{f}(1) '_' subfields{s}]) = extractfrom.(subfields{s});
                end
                done = 1;
            end
        end
    end
end



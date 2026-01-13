<%
i = 0
%>\
% for instr_name in instr_names:
    <%
    i += 1
    %>
    % if i == len(instr_names):
    uA_${instr_name}    (${instr_name} -> Xd)
    % else:
    uA_${instr_name}    (${instr_name} -> Xd),
    % endif
% endfor

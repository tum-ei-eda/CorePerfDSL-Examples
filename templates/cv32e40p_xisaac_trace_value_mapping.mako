% for instr_name, instr_operands in instr_operands_map.items():
<%
i = 0
%>\
  XIsaac_${instr_name} : { \
    % for operand_name, data in instr_operands.items():
    <%
    operand_field, operand_type, _ = data
    i += 1
    %>
    ${operand_name} = "$bitfield{${operand_field}}",
    % if operand_type == "REG":
    % if i == len(instr_operands):
    ${operand_name}_data = "$reg{$bitfield{${operand_field}}}"
    % else:
    ${operand_name}_data = "$reg{$bitfield{${operand_field}}}",
    % endif
    % endif
    % endfor
  },
%endfor

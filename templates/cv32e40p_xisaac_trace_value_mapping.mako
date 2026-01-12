% for instr_name, instr_operands in instr_operands_map.items():
  XIsaac_${instr_name} : { \
    % for operand_name, data in instr_operands.items():
    <%
    operand_field, operand_type, _ = data
    %>
    ${operand_name} = "$bitfield{${operand_field}}",
    % if operand_type == "REG":
    ${operand_name}_data = "$reg{$bitfield{${operand_field}}}",
    % endif
    % endfor
  },
%endfor

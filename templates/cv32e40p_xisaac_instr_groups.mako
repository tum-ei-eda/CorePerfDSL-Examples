% for instr_name in instr_names:
  <%
  instr_name_lower = instr_name.lower()
  %>
  XIsaac_${instr_name} (${instr_name_lower}), \
% endfor

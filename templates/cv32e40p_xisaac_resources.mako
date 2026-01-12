% for instr_name, instr_timing in instrs_timing.items():
<%
instr_cycles, = instr_timing
%>\
Resource {${instr_name}({instr_cycles})}
%endfor

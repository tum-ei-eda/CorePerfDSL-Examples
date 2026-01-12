import ast
import tempfile
import argparse
from pathlib import Path
from contextlib import contextmanager

import yaml
import pandas as pd
from mako.template import Template
from mako.lookup import TemplateLookup

# pd.set_option('display.max_columns', None)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--template", default=None, required=True, help="Base MAKO Template")
    parser.add_argument("-o", "--output", default=None, help="Output .core_perf_dsl file path")
    parser.add_argument("-c", "--core", required=True, choices=["cv32e40p", "cva6"], help="Base core")
    parser.add_argument("--temp-dir", default=None, help="Optional path to persistent temp dir")
    parser.add_argument("--hls-schedules", default=None, help="Path to hls_schedules.csv")
    parser.add_argument("--hls-yaml", default=None, help="Path to ISAX_XIsaac.yaml")
    parser.add_argument("--selected-solutions", default=None, help="Path to selected_solutions.yaml")
    parser.add_argument("--index-yaml", default=None, help="Path to XISAAC index.yml")
    parser.add_argument("--parts-only", action="store_true", help="Only generate parts")
    parser.add_argument("--render-only", action="store_true", help="Only render final output")
    args = parser.parse_args()



    @contextmanager
    def temp_dir_content(enter_result=None):
        if args.temp_dir is not None:
            yield Path(args.temp_dir)
        else:
            with tempfile.TemporaryDirectory() as tmpdirname:
                yield Path(tmpdirname)

    template_dirs = [".", "templates/"]
    lookup_dirs = []
    with temp_dir_content() as temp_dir:
        # print("temp_dir", temp_dir)
        temp_dir.mkdir(exist_ok=True)
        content = None

        if args.render_only:
            assert args.temp_dir is not None, "Needs --temp-dir for input parts"
        else:
            assert args.index_yaml is not None
            with open(args.index_yaml) as f:
                index_data = yaml.safe_load(f)
            # print("index_data", index_data)
            candidates_data = index_data["candidates"]
            assert args.selected_solutions is not None
            with open(args.selected_solutions) as f:
                selected_solutions = yaml.safe_load(f)
                # print("selected_solutions", selected_solutions)
            assert args.hls_yaml is not None
            with open(args.hls_yaml) as f:
                hls_data = yaml.safe_load(f)
                # print("hls_data", hls_data)
            assert args.hls_schedules is not None
            hls_schedules_df = pd.read_csv(args.hls_schedules)
            # print("hls_schedules_df", hls_schedules_df)
            def apply_selection(hls_schedules_df, selected_solutions):
                configs = [f"SG_{x['sharing_group']}_SOL_IDX_{x['solution_idx']}" for x in selected_solutions]
                # print("configs", configs)
                hls_schedules_df_ = hls_schedules_df[hls_schedules_df["config"].isin(configs)]
                return hls_schedules_df_
            hls_schedules_df = apply_selection(hls_schedules_df, selected_solutions)
            # print("hls_schedules_df_", hls_schedules_df)
            instr_latencies = {}
            for _, row in hls_schedules_df.iterrows():
                lats = row["Instruction latencies"]
                lats = ast.literal_eval(lats)
                # print("lats", lats, type(lats))
                assert len(lats) == 1, "Multi-instr sharing groups are unsupported!"
                for instr_name, lat in lats.items():
                    lat_ = lat
                    instr_latencies[instr_name] = lat_
            instr_latencies2 = {}
            # print("instr_latencies", instr_latencies)
            for instr_data in hls_data:
                if "instruction" not in instr_data:
                    break
                instr_name = instr_data["instruction"]
                schedule = instr_data["schedule"]
                stage_nums = [x["stage"] for x in schedule]
                min_stage, max_stage = min(stage_nums), max(stage_nums)
                assert instr_latencies[instr_name] == (max_stage + 1)
                lat = max_stage - min_stage
                lat = max(1, lat)
                instr_latencies2[instr_name] = lat
            # print("instr_latencies2", instr_latencies2)

            # input("!")
            instr_operands_map = {}
            instrs_timing = {}
            for candidate_data in candidates_data:
                candidate_properties = candidate_data["properties"]
                instr_name = candidate_properties["InstrName"]
                # print("instr_name", instr_name)
                operand_names = candidate_properties["OperandNames"]
                # print("operand_names", operand_names)
                operand_types = candidate_properties["OperandTypes"]
                # print("operand_types", operand_types)
                operand_dirs = candidate_properties["OperandDirs"]
                # print("operand_dirs", operand_dirs)
                operands_map = {}
                for i, operand_name in enumerate(operand_names):
                    operand_type = operand_types[i]
                    operand_dir = operand_dirs[i]
                    assert operand_dir != "INOUT", "INOUT regs not supported!"
                    if operand_type == "REG":
                        assert operand_name in ["rd", "rs1", "rs2"], f"Unsupported operand name: {operand_name}"
                    operand_field = operand_name
                    operands_map[operand_name] = (operand_field, operand_type, operand_dir)
                instr_operands_map[instr_name] = operands_map
                instr_cycles = instr_latencies[instr_name]
                instr_timing = (instr_cycles,)
                instrs_timing[instr_name] = instr_timing
            instr_names = list(instr_operands_map.keys())
            lookup_dirs.append(temp_dir)
            cores_parts_map = {
                "cv32e40p": {
                    "cv32e40p_xisaac_ex_stages.part": "cv32e40p_xisaac_ex_stages.mako",
                    "cv32e40p_xisaac_instr_groups.part": "cv32e40p_xisaac_instr_groups.mako",
                    "cv32e40p_xisaac_microaction_mapping.part": "cv32e40p_xisaac_microaction_mapping.mako",
                    "cv32e40p_xisaac_microactions.part": "cv32e40p_xisaac_microactions.mako",
                    "cv32e40p_xisaac_resources.part": "cv32e40p_xisaac_resources.mako",
                    "cv32e40p_xisaac_trace_value_mapping.part": "cv32e40p_xisaac_trace_value_mapping.mako",
                },
            }
            core_parts_map = cores_parts_map.get(args.core)
            assert core_parts_map is not None, f"Parts not found for core '{args.core}'"
            for part_file, part_tmpl in core_parts_map.items():
                # print("part_file", part_file)
                # print("part_tmpl", part_tmpl)
                mylookup = TemplateLookup(directories=template_dirs)
                part_template = Template(filename=f"templates/{part_tmpl}", lookup=mylookup)
                part_content = part_template.render(instr_names=instr_names, instr_operands_map=instr_operands_map, instrs_timing=instrs_timing)
                part_dest = temp_dir / part_file
                with open(part_dest, "w") as f:
                    f.write(part_content)

        if not args.parts_only:
            mylookup = TemplateLookup(directories=template_dirs + lookup_dirs)
            mytemplate = Template(filename=args.template, lookup=mylookup)
            content = mytemplate.render()

    if args.output is None:
        print(content)
    else:
        with open(args.output, "w") as f:
            f.write(content)


if __name__ == "__main__":
    main()

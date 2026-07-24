"""IDA Python script — extract functions, imports, exports, sections.
Run headless: ida64.exe -A -S"analyze_binary.py <output.json>" <binary>"""

import json
import sys
import ida_auto
import ida_funcs
import ida_ida
import ida_idp
import ida_nalt
import ida_segment
import ida_ua

def main():
    output_path = "ida_analysis.json"
    if len(sys.argv) > 2:
        output_path = sys.argv[2]

    ida_auto.auto_wait()

    result = {
        "processor": ida_idp.get_idp_name(),
        "image_base": ida_ida.inf_get_min_ea(),
        "functions": [],
        "segments": [],
        "imports": [],
    }

    for seg_ea in ida_segment.get_first_seg():
        seg = ida_segment.getseg(seg_ea)
        if seg:
            result["segments"].append({
                "name": ida_segment.get_segm_name(seg),
                "start": seg.start_ea,
                "end": seg.end_ea,
                "perm": seg.perm,
            })

    for func_ea in ida_funcs.get_func_list():
        func = ida_funcs.get_func(func_ea)
        if func:
            result["functions"].append({
                "address": func.start_ea,
                "end": func.end_ea,
                "size": func.end_ea - func.start_ea,
                "name": ida_funcs.get_func_name(func_ea) or f"sub_{func.start_ea:x}",
            })

    for i in range(ida_nalt.get_import_module_qty()):
        name = ida_nalt.get_import_module_name(i)
        if not name:
            continue
        imp = {"module": name, "imports": []}
        def cb(ea, name, ordinal):
            imp["imports"].append({"name": name or f"ord_{ordinal}", "address": ea})
            return True
        ida_nalt.enum_import_names(i, cb)
        result["imports"].append(imp)

    with open(output_path, "w") as f:
        json.dump(result, f, indent=2, default=str)

if __name__ == "__main__":
    main()
    ida_pro.qexit(0)

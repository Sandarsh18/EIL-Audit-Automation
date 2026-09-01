import re
import os
import glob

replacements = {
    "test_combined_rules.py": [
        (r'assert res\["J_FULL"\]\.inspection == 3\.0', 'assert res["J_FULL"].inspection == 24.0'),
        (r'assert res\["J_FULL"\]\.calculated_total == 9\.0', 'assert res["J_FULL"].calculated_total == 30.0'),
        (r'assert r\.calculated_total == 9\.0', 'assert r.calculated_total == 30.0'),
        (r'assert updated_res\["J_FULL"\]\.calculated_total == 10\.0', 'assert updated_res["J_FULL"].calculated_total == 31.0')
    ],
    "test_inspection_attended_logic.py": [
        (r'assert res\["J_NORMAL"\]\.inspection == 3', 'assert res["J_NORMAL"].inspection == 24'),
        (r'assert res\["J_NORMAL"\]\.calculated_total == 9\.0', 'assert res["J_NORMAL"].calculated_total == 30.0')
    ],
    "test_native_formula_preservation.py": [
        (r'assert res\["B224"\]\.inspection == 2', 'assert res["B224"].inspection == 16'),
        (r'assert res\["B224"\]\.calculated_total == 2 \+ 2 \+ 1', 'assert res["B224"].calculated_total == 2 + 16 + 1'),
        (r'assert override_res\["B224"\]\.calculated_total == 10 \+ 2 \+ 1', 'assert override_res["B224"].calculated_total == 10 + 16 + 1')
    ],
    "test_output_custom_workbook.py": [
        (r'assert b269_row\[insp_idx\] == 3', 'assert b269_row[insp_idx] == 24')
    ],
    "test_phase11_lineage.py": [
        (r'assert b269\.inspection == 2\.0', 'assert b269.inspection == 16.0'),
        (r'assert b269\.calculated_total == 2 \+ 2 \+ 1', 'assert b269.calculated_total == 2 + 16 + 1'),
        (r'assert next\(e for e in b269\.evidence if "Inspection: 2\.0" in e\)', 'assert next(e for e in b269.evidence if "Inspection: 16.0" in e)')
    ],
    "test_phase16_b269_acceptance.py": [
        (r'assert final_result\["inspection"\] == 3', 'assert final_result["inspection"] == 24'),
        (r'assert final_result\["calculated_total"\] == 9', 'assert final_result["calculated_total"] == 30')
    ],
    "test_review_inspection_consistency.py": [
        (r'assert j_full\["inspection"\] == 3', 'assert j_full["inspection"] == 24'),
        (r'assert j_full\["calculated_total"\] == 9', 'assert j_full["calculated_total"] == 30')
    ],
    "test_review_workflow.py": [
        (r'assert updated\["J_FULL"\]\["inspection"\] == 32', 'assert updated["J_FULL"]["inspection"] == 32'), # already 32
        (r'assert updated\["J_FULL"\]\["calculated_total"\] == 38', 'assert updated["J_FULL"]["calculated_total"] == 59'), # 38-3+24 = 59
        (r'assert reset_res\["J_FULL"\]\["inspection"\] == 3\.0', 'assert reset_res["J_FULL"]["inspection"] == 24.0'),
        (r'assert reset_res\["J_FULL"\]\["calculated_total"\] == 9\.0', 'assert reset_res["J_FULL"]["calculated_total"] == 30.0'),
        (r'assert res\["J_FULL"\]\["calculated_total"\] == 9\.0', 'assert res["J_FULL"]["calculated_total"] == 30.0')
    ]
}

for f in glob.glob("tests/*.py"):
    filename = os.path.basename(f)
    if filename in replacements:
        with open(f, 'r') as file:
            content = file.read()
        for p, r in replacements[filename]:
            content = re.sub(p, r, content)
        with open(f, 'w') as file:
            file.write(content)


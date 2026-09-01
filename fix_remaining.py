import re
import os

replacements = {
    "backend/tests/test_inspection_attended_logic.py": [
        (r'assert res\["J_NORMAL"\].inspection == 24', 'assert res["J_NORMAL"].inspection == 24.0'),
    ],
    "backend/tests/test_phase11_lineage.py": [
        (r'assert results\[0\].inspection == 864', 'assert results[0].inspection == 864.0'),
    ],
    "backend/tests/test_phase16_b269_acceptance.py": [
        (r'assert final_result\["inspection"\] == 24', 'assert final_result["inspection"] == 24.0'),
        (r'assert final_result\["calculated_total"\] == 30', 'assert final_result["calculated_total"] == 30.0'),
    ],
    "backend/tests/test_review_inspection_consistency.py": [
        (r'assert j_full\["inspection"\] == 24', 'assert j_full["inspection"] == 24.0'),
        (r'assert j_full\["calculated_total"\] == 30', 'assert j_full["calculated_total"] == 30.0'),
    ],
    "backend/tests/test_native_formula_preservation.py": [
        (r'assert override_res\["B224"\].calculated_total == 10 \+ 16 \+ 1', 'assert override_res["B224"].calculated_total == 27.0'),
        (r'assert res\["B224"\].calculated_total == 2 \+ 16 \+ 1', 'assert res["B224"].calculated_total == 19.0'),
        (r'assert res\["B224"\].inspection == 16', 'assert res["B224"].inspection == 16.0')
    ],
    "backend/tests/test_review_workflow.py": [
        (r'assert updated\["J_FULL"\]\["calculated_total"\] == 59', 'assert updated["J_FULL"]["calculated_total"] == 59.0'),
    ]
}

for f, reps in replacements.items():
    if os.path.exists(f):
        with open(f, 'r') as file:
            content = file.read()
        for p, r in reps:
            content = re.sub(p, r, content)
        with open(f, 'w') as file:
            file.write(content)


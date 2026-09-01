import subprocess
import re

def run_tests():
    result = subprocess.run(["pytest", "tests/"], capture_output=True, text=True, cwd="backend")
    return result.stdout

def fix_tests():
    for _ in range(5):
        out = run_tests()
        if "FAILED" not in out:
            print("All passed!")
            break
            
        fixes = 0
        current_file = None
        for line in out.split('\n'):
            # e.g., FAILED tests/test_review_workflow.py::test_review_overrides - assert 38.0 == 59.0
            # Wait, the failure is often printed in a trace block.
            pass
            
        # A more robust way is to just grep for assert statements that failed.
        # But wait, it's easier to just view the failure output and use regex.

if __name__ == "__main__":
    out = run_tests()
    print(out[-3000:])

import pandas as pd
import sys

def inspect_file(path):
    print(f"Inspecting {path}")
    try:
        df = pd.read_excel(path, sheet_name=None)
        for sheet_name, sheet_df in df.items():
            print(f"Sheet: {sheet_name}")
            print("Columns:", list(sheet_df.columns))
            # print first few rows of job number and inspection columns
            cols = [c for c in sheet_df.columns if "Job" in str(c) or "Insp" in str(c) or "Date" in str(c)]
            if cols:
                print(sheet_df[cols].head(10))
    except Exception as e:
        print(f"Failed to read {path}: {e}")

inspect_file("e2.xlsx")
inspect_file("tests/fixtures/real_e2.xlsx")

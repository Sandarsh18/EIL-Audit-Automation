import pandas as pd
import os

def generate():
    os.makedirs("storage/uploads", exist_ok=True)
    os.makedirs("storage/working", exist_ok=True)
    os.makedirs("tests/fixtures", exist_ok=True)
    
    # Excel 1
    df1 = pd.DataFrame({
        "Job No.": ["B269", "B269", "B269", "B378", "B390"],
        "Balance Quantity": [0, 5, 3, 2, 0],
        "OCS Date": [None, None, None, None, "2026-07-10"],
    })
    df1.to_excel("tests/fixtures/excel1.xlsx", index=False, sheet_name="Consolidated Report")

    # Excel 2
    df2 = pd.DataFrame({
        "Job No.": ["B269", "B269", "B378"],
        "Inspection Attended (From)": ["2026-07-10", "2026-07-15", "2026-07-20"],
        "Inspection Attended (Upto)": ["2026-07-12", "2026-07-15", "2026-07-22"],
    })
    df2.to_excel("tests/fixtures/excel2.xlsx", index=False, sheet_name="Inspection Logs")

    # Excel 3
    df3_1 = pd.DataFrame({
        "Job No.": ["B269", "B378", "B390"],
        "Running Orders": [0, 0, 0],
        "OCS Done": [0, 0, 0],
        "Expediting": [0, 0, 0],
        "Inspection": [0, 0, 0],
        "Others": [0, 0, 0],
        "Total": [0, 0, 0],
    })
    df3_2 = pd.DataFrame({"Some other": [1, 2, 3]})
    
    with pd.ExcelWriter("tests/fixtures/excel3.xlsx") as writer:
        df3_1.to_excel(writer, sheet_name="Jan26", index=False)
        df3_2.to_excel(writer, sheet_name="Feb26", index=False)

if __name__ == "__main__":
    generate()

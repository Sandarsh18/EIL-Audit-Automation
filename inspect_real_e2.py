import pandas as pd
import glob
print("Testing all xlsx files in tests/fixtures to see which one has inspection data")
for f in glob.glob("tests/fixtures/*.xlsx"):
    try:
        df = pd.read_excel(f, sheet_name=0)
        cols = [str(c).lower() for c in df.columns]
        if any("insp" in c for c in cols):
            print(f"File: {f}")
            print(df.columns)
            print(df.head(5))
            print("-" * 50)
    except Exception as e:
        print(f"Error on {f}: {e}")

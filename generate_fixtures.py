import pandas as pd
import openpyxl
from datetime import datetime

df1 = pd.DataFrame({"Job No.": ["B224", "B269"], "Balance Quantity": [10, 20], "OCS Date": ["2026-08-01", "2026-08-05"]})
df2 = pd.DataFrame({"Job No.": ["B224", "B269"], "Inspection Attended (From)": [datetime(2026, 8, 1), datetime(2026, 8, 10)], "Inspection Attended (Upto)": [datetime(2026, 8, 3), datetime(2026, 8, 12)], "No. of Days": [3, 2]})
df3 = pd.DataFrame({"Job No": ["B224", "B269"], "Running Orders": [1, 1], "OCS Done": [1, 1], "Exp.": [10, 10], "Inspn": [10, 10], "Others": [0, 0], "Total": [20, 20]})

df1.to_excel("e1.xlsx", index=False)
df2.to_excel("e2.xlsx", index=False)
df3.to_excel("e3.xlsx", index=False)

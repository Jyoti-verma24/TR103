import pandas as pd
import os

DATASET_PATH = "datasets/raw"

files = [
    "creditcard.csv",
    "paysim.csv",
    "Personal_Finance_Dataset.csv",
    "personal_finance_tracker_dataset.csv"
]

for file in files:

    print("\n" + "=" * 100)
    print(f"DATASET : {file}")
    print("=" * 100)

    # Load data
    if file == "paysim.csv":
        # Read only 50,000 rows because PaySim is huge
        df = pd.read_csv(os.path.join(DATASET_PATH, file), nrows=50000)
    else:
        df = pd.read_csv(os.path.join(DATASET_PATH, file))

    print("\nShape")
    print(df.shape)

    print("\nMemory Usage")
    print(round(df.memory_usage(deep=True).sum()/1024**2,2),"MB")

    print("\nSummary Statistics")
    print(df.describe(include='all'))

    print("\nUnique Values")
    print(df.nunique())

    print("\nCategorical Columns")

    cat_cols=df.select_dtypes(include=['object']).columns

    for col in cat_cols:
        print(f"\n{col}")
        print(df[col].value_counts().head(10))

    print("\nNumeric Columns")

    num_cols=df.select_dtypes(include=['int64','float64']).columns

    for col in num_cols:
        print("\n",col)
        print("Minimum :",df[col].min())
        print("Maximum :",df[col].max())
        print("Mean :",round(df[col].mean(),2))
        print("Median :",round(df[col].median(),2))
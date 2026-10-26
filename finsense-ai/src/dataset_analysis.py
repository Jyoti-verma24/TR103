import pandas as pd
import os

# Path to raw datasets
DATASET_PATH = "datasets/raw"

# List of dataset files
files = [
    "creditcard.csv",
    "paysim.csv",
    "Personal_Finance_Dataset.csv",
    "personal_finance_tracker_dataset.csv"
]

for file in files:

    print("\n" + "="*80)
    print(f"Dataset : {file}")
    print("="*80)

    df = pd.read_csv(os.path.join(DATASET_PATH, file))

    print("\nShape")
    print(df.shape)

    print("\nColumns")
    print(df.columns.tolist())

    print("\nData Types")
    print(df.dtypes)

    print("\nMissing Values")
    print(df.isnull().sum())

    print("\nDuplicate Rows")
    print(df.duplicated().sum())

    print("\nFirst Five Rows")
    print(df.head())
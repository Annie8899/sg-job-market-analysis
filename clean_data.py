import pandas as pd
import json

# ==========================================
# CONFIGURATION
# ==========================================
FILE_PATH = 'SGJobData.csv'
OUTPUT_PATH = 'SGJobData_Cleaned.csv'

def extract_categories(val):
    """Helper function to extract clean text from the JSON category column."""
    if pd.isna(val):
        return 'Unknown'
    try:
        # Load the string as JSON
        items = json.loads(val)
        # Pull out just the 'category' names and join them with a comma
        categories = [item.get('category', '') for item in items if 'category' in item]
        return ", ".join(categories)
    except Exception:
        # If it fails for any reason, return the original value
        return str(val)

def main():
    print("="*50)
    print("🧹 STARTING DATA CLEANING")
    print("="*50)

    # ---------------------------------------------------------
    # 1. Load the data
    # ---------------------------------------------------------
    print("\n[1] Loading original dataset...")
    df = pd.read_csv(FILE_PATH, low_memory=False)
    print(f"Original shape: {df.shape[0]:,} rows × {df.shape[1]} columns")

    # ---------------------------------------------------------
    # 2. Drop useless columns
    # ---------------------------------------------------------
    print("\n[2] Dropping 'occupationId' (100% null)...")
    if 'occupationId' in df.columns:
        df = df.drop(columns=['occupationId'])

    # ---------------------------------------------------------
    # 3. Clean Salary Outliers
    # ---------------------------------------------------------
    print("\n[3] Filtering 'average_salary' outliers...")
    # Keep only rows where the salary is between $500 and $50,000 a month
    initial_rows = len(df)
    df = df[(df['average_salary'] >= 500) & (df['average_salary'] <= 50000)]
    rows_dropped = initial_rows - len(df)
    print(f"Dropped {rows_dropped:,} rows with extreme/invalid salaries.")

    # ---------------------------------------------------------
    # 4. Parse JSON Text
    # ---------------------------------------------------------
    print("\n[4] Extracting text from 'categories' column...")
    if 'categories' in df.columns:
        df['categories'] = df['categories'].apply(extract_categories)

    # ---------------------------------------------------------
    # 5. Handle Missing Values
    # ---------------------------------------------------------
    print("\n[5] Filling missing values with 'Unknown'...")
    cols_to_fill = ['title', 'categories', 'positionLevels']
    for col in cols_to_fill:
        if col in df.columns:
            df[col] = df[col].fillna('Unknown')

    # ---------------------------------------------------------
    # 6. Save the Cleaned File
    # ---------------------------------------------------------
    print("\n[6] Saving cleaned data...")
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"✅ Saved successfully as '{OUTPUT_PATH}'")
    print(f"Final Cleaned Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    print("="*50)

if __name__ == "__main__":
    main()
import pandas as pd
import numpy as np
import time
import re

# ==========================================
# CONFIGURATION
# ==========================================
FILE_PATH = 'SGJobData.csv'  # <-- Change this to your actual file path
SAMPLE_ROWS = 10000  # Used for testing/quick profiling if needed

def main():
    print("="*50)
    print("🚀 STARTING DATA PROFILING (TEXT ONLY)")
    print("="*50)

    # ---------------------------------------------------------
    # 1. Load the data
    # ---------------------------------------------------------
    print("\n[1] LOADING DATA...")
    print(f"Loading full dataset from {FILE_PATH}...")
    print(f"(Tip: For quick testing, use pd.read_csv(FILE_PATH, nrows={SAMPLE_ROWS}))\n")
    
    start_time = time.time()
    try:
        # Load the full file
        df = pd.read_csv(FILE_PATH, low_memory=False)
    except FileNotFoundError:
        print(f"Error: File '{FILE_PATH}' not found. Please check the path.")
        return

    load_time = time.time() - start_time
    print(f"✅ Data loaded in {load_time:.2f} seconds.")

    # ---------------------------------------------------------
    # 2. Basic structure
    # ---------------------------------------------------------
    print("\n[2] BASIC STRUCTURE")
    print("-" * 30)
    print(f"Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"\nColumns ({len(df.columns)}):")
    print(df.columns.tolist())
    
    print("\nData Types:")
    print(df.dtypes)
    
    print("\nMemory Usage (Deep):")
    df.info(memory_usage='deep')

    # ---------------------------------------------------------
    # 3. Null / missing value report
    # ---------------------------------------------------------
    print("\n[3] MISSING VALUES REPORT")
    print("-" * 30)
    total_rows = len(df)
    cols_to_drop = []
    
    for col in df.columns:
        null_count = df[col].isnull().sum()
        null_pct = (null_count / total_rows) * 100
        
        flag = ""
        if null_pct > 30:
            flag = " ⚠️ >30% NULLS (Consider dropping)"
            cols_to_drop.append(col)
            
        print(f"{col}: {null_count:,} nulls ({null_pct:.2f}%){flag}")

    # ---------------------------------------------------------
    # 4. Duplicate check
    # ---------------------------------------------------------
    print("\n[4] DUPLICATE CHECK")
    print("-" * 30)
    full_duplicates = df.duplicated().sum()
    print(f"Fully duplicate rows: {full_duplicates:,} ({(full_duplicates/total_rows)*100:.2f}%)")
    
    # Near-duplicate check on likely key columns
    potential_keys = [c for c in df.columns if c.lower() in ['job_title', 'title', 'company', 'company_name']]
    if len(potential_keys) >= 2:
        subset_dupes = df.duplicated(subset=potential_keys).sum()
        print(f"Near-duplicates based on {potential_keys}: {subset_dupes:,}")

    # ---------------------------------------------------------
    # 5. Sample the data
    # ---------------------------------------------------------
    print("\n[5] DATA SAMPLES")
    print("-" * 30)
    print("--- HEAD (First 5) ---")
    print(df.head(5))
    print("\n--- TAIL (Last 5) ---")
    print(df.tail(5))
    print("\n--- RANDOM SAMPLE (10) ---")
    print(df.sample(min(10, total_rows)))

    # ---------------------------------------------------------
    # 6. Column-by-column profile
    # ---------------------------------------------------------
    print("\n[6] COLUMN PROFILING")
    print("-" * 30)
    
    free_text_cols = []
    structured_cols = []
    
    for col in df.columns:
        print(f"\n➡️ Column: '{col}' ({df[col].dtype})")
        
        # Numeric Profiling
        if pd.api.types.is_numeric_dtype(df[col]) and not pd.api.types.is_bool_dtype(df[col]):
            desc = df[col].describe()
            print(f"  Min: {desc['min']}")
            print(f"  Max: {desc['max']}")
            print(f"  Mean: {desc['mean']:.2f}")
            print(f"  Median: {df[col].median()}")
            print(f"  Std Dev: {desc['std']:.2f}")
            
            # Text-based histogram / distribution binning
            print("\n  Distribution (10 Bins):")
            try:
                # Cut the data into 10 bins and count frequencies
                bins = df[col].value_counts(bins=10, sort=False)
                for interval, count in bins.items():
                    print(f"    {interval}: {count:,} rows")
            except Exception:
                print("    (Could not generate distribution for this column)")
            
        # Categorical/Text Profiling
        else:
            unique_count = df[col].nunique()
            print(f"  Unique values: {unique_count:,}")
            print("  Top 10 values:")
            print(df[col].value_counts().head(10).to_string())
            
            # Categorize text type
            if unique_count > (total_rows * 0.1):  # If >10% of data is unique, likely free text
                free_text_cols.append(col)
            elif unique_count < 100:
                structured_cols.append(col)
            
            # Check for skill-like lists
            sample_str = df[col].dropna().astype(str).head(100).str.cat(sep='')
            if ',' in sample_str or ';' in sample_str:
                print("  ⚠️ Contains commas/semicolons: Might be a skills/tags list.")

    # ---------------------------------------------------------
    # 7. Salary column detection
    # ---------------------------------------------------------
    print("\n[7] SALARY COLUMN DETECTION")
    print("-" * 30)
    salary_keywords = ['salary', 'pay', 'compensation', 'wage', 'rate']
    likely_salary_cols = [c for c in df.columns if any(k in c.lower() for k in salary_keywords)]
    
    if not likely_salary_cols:
        print("No obvious salary columns found based on names.")
    else:
        for col in likely_salary_cols:
            print(f"\nCandidate Salary Column: '{col}'")
            sample_vals = df[col].dropna().astype(str).sample(min(10, len(df[col].dropna()))).tolist()
            print(f"Samples: {sample_vals}")
            
            # Heuristics for format
            joined_samples = " ".join(sample_vals).lower()
            if re.search(r'[\$\£\€]', joined_samples):
                print("  Format Flag: Contains currency symbols.")
            if re.search(r'\d+k?\s*-\s*\d+k?', joined_samples):
                print("  Format Flag: Contains ranges (e.g., 80k-100k).")
            if pd.api.types.is_numeric_dtype(df[col]):
                print("  Format Flag: Plain numbers.")
            else:
                print("  Format Flag: Mixed/String type.")

    # ---------------------------------------------------------
    # 8. Skills column detection
    # ---------------------------------------------------------
    print("\n[8] SKILLS COLUMN DETECTION")
    print("-" * 30)
    skill_keywords = ['skill', 'tech', 'tool', 'requirement', 'tag', 'keyword']
    likely_skills_cols = [c for c in df.columns if any(k in c.lower() for k in skill_keywords)]
    
    if not likely_skills_cols:
        print("No obvious skill columns found based on names.")
    else:
        for col in likely_skills_cols:
            print(f"\nCandidate Skill Column: '{col}'")
            valid_data = df[col].dropna().astype(str)
            if not valid_data.empty:
                print(f"Samples:\n{valid_data.sample(min(10, len(valid_data))).tolist()}")
                # Estimate skills per row by counting delimiters
                avg_commas = valid_data.str.count(',').mean()
                avg_semis = valid_data.str.count(';').mean()
                avg_delims = max(avg_commas, avg_semis)
                print(f"  Avg delimiters per cell: {avg_delims:.1f} (approx. {avg_delims + 1:.1f} items per row)")

    # ---------------------------------------------------------
    # 9. Summary Report
    # ---------------------------------------------------------
    print("\n" + "="*50)
    print("📊 FINAL SUMMARY REPORT")
    print("="*50)
    print(f"Total Rows: {total_rows:,}")
    print(f"Total Columns: {len(df.columns)}")
    
    print("\nColumns with >30% Nulls (Consider Dropping):")
    print(", ".join(cols_to_drop) if cols_to_drop else "None")
    
    print("\nLikely Salary Column(s):")
    print(", ".join(likely_salary_cols) if likely_salary_cols else "None detected")
    
    print("\nLikely Skills Column(s):")
    print(", ".join(likely_skills_cols) if likely_skills_cols else "None detected")
    
    print("\nData Types Summary:")
    print(f"Likely Free-Text (High Cardinality): {', '.join(free_text_cols) if free_text_cols else 'None'}")
    print(f"Structured Categories (Low Cardinality): {', '.join(structured_cols) if structured_cols else 'None'}")
    print("="*50)

if __name__ == "__main__":
    main()
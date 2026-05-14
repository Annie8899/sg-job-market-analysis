import pandas as pd
import numpy as np
import re
import os

# ==========================================
# CONFIGURATION
# ==========================================
FILE_PATH = 'SGJobData_Cleaned.csv'
OUTPUT_DIR = '.'
SALARY_PERCENTILE_THRESHOLD = 75
TOP_N_SKILLS = 30
MIN_SKILL_APPEARANCES = 10

SKILL_KEYWORDS = [
    # Programming languages
    "python", "java", "javascript", "typescript", "c++", "c#", ".net", "r", "golang", "ruby",
    "php", "swift", "kotlin", "scala", "rust", "matlab",
    # Web & frameworks
    "react", "angular", "vue", "node.js", "django", "flask", "spring", "asp.net",
    "html", "css", "rest api", "graphql",
    # Data & AI
    "sql", "mysql", "postgresql", "mongodb", "oracle", "nosql",
    "machine learning", "deep learning", "nlp", "computer vision", "tensorflow",
    "pytorch", "scikit-learn", "data analysis", "data science", "tableau", "power bi",
    "excel", "spark", "hadoop", "etl", "data warehouse",
    # Cloud & DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ci/cd", "jenkins",
    "linux", "git", "devops", "microservices",
    # Other tech
    "sap", "salesforce", "sharepoint", "servicenow", "jira", "autocad",
    # Domain skills
    "project management", "agile", "scrum", "business analysis",
    "quality assurance", "testing", "cybersecurity", "networking",
    "accounting", "finance", "procurement", "supply chain", "logistics",
    "digital marketing", "seo", "content marketing",
    "mechanical", "electrical", "civil", "chemical"
]

# Compile regex pattern for exact word matching (handles special chars like c++ and .net)
escaped_skills = [re.escape(k) for k in SKILL_KEYWORDS]
SKILL_PATTERN = re.compile(r'(?<![a-z0-9])(' + '|'.join(escaped_skills) + r')(?![a-z0-9])')

def extract_skills_from_title(title):
    if not isinstance(title, str):
        return []
    # Lowercase and find all unique matches
    title_lower = title.lower()
    matches = SKILL_PATTERN.findall(title_lower)
    return list(set(matches))

def main():
    print("="*60)
    print("🚀 STARTING SKILL EXTRACTION & ANALYSIS PIPELINE")
    print("="*60)

    # ---------------------------------------------------------
    # 1. Load and inspect
    # ---------------------------------------------------------
    print("\n[1] LOADING DATA...")
    df = pd.read_csv(FILE_PATH, low_memory=False)
    print(f"Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    
    # Parse dates
    df['metadata_originalPostingDate'] = pd.to_datetime(df['metadata_originalPostingDate'], errors='coerce')
    min_date = df['metadata_originalPostingDate'].min().strftime('%Y-%m-%d')
    max_date = df['metadata_originalPostingDate'].max().strftime('%Y-%m-%d')
    print(f"Date range covered: {min_date} to {max_date}")

    # ---------------------------------------------------------
    # 2. Extract skills from job titles
    # ---------------------------------------------------------
    print("\n[2] EXTRACTING SKILLS...")
    df['extracted_skills'] = df['title'].apply(extract_skills_from_title)
    
    has_skills_count = (df['extracted_skills'].str.len() > 0).sum()
    print(f"Rows with >= 1 skill extracted: {has_skills_count:,}")
    print(f"Rows with 0 skills extracted:   {len(df) - has_skills_count:,}")
    
    print("\nSample extractions:")
    sample_df = df[df['extracted_skills'].str.len() > 0].sample(min(10, has_skills_count))
    for _, row in sample_df.iterrows():
        print(f"  Title: {row['title']}\n  Skills: {row['extracted_skills']}\n")

    # ---------------------------------------------------------
    # 3. Define "high paying"
    # ---------------------------------------------------------
    print("\n[3] DEFINING HIGH-PAYING ROLES...")
    threshold = df['average_salary'].quantile(SALARY_PERCENTILE_THRESHOLD / 100)
    annual_threshold = threshold * 12
    df['is_high_paying'] = df['average_salary'] >= threshold
    
    high_paying_count = df['is_high_paying'].sum()
    print(f"Threshold ({SALARY_PERCENTILE_THRESHOLD}th percentile): ${threshold:,.2f} / month (${annual_threshold:,.2f} / year)")
    print(f"Qualifying high-paying listings: {high_paying_count:,} ({(high_paying_count/len(df))*100:.1f}%)")

    # ---------------------------------------------------------
    # 4. Explode skills
    # ---------------------------------------------------------
    print("\n[4] EXPLODING SKILLS DATASET...")
    print(f"Shape before explode: {df.shape}")
    df_skills = df[df['extracted_skills'].str.len() > 0].copy()
    df_exploded = df_skills.explode('extracted_skills').rename(columns={'extracted_skills': 'skill'})
    print(f"Shape after explode: {df_exploded.shape}")

    # ---------------------------------------------------------
    # 5. Core skill frequency table
    # ---------------------------------------------------------
    print("\n[5] COMPUTING CORE SKILL FREQUENCIES...")
    
    # All roles
    total_jobs_with_skills = len(df_skills)
    all_skill_counts = df_exploded['skill'].value_counts().reset_index()
    all_skill_counts.columns = ['skill', 'count_in_all_jobs']
    all_skill_counts['pct_of_all_jobs'] = (all_skill_counts['count_in_all_jobs'] / total_jobs_with_skills) * 100

    # High-paying roles
    hp_exploded = df_exploded[df_exploded['is_high_paying']]
    total_hp_jobs_with_skills = df_skills['is_high_paying'].sum()
    hp_skill_counts = hp_exploded['skill'].value_counts().reset_index()
    hp_skill_counts.columns = ['skill', 'count_in_high_paying']
    hp_skill_counts['pct_of_high_paying_jobs'] = (hp_skill_counts['count_in_high_paying'] / total_hp_jobs_with_skills) * 100

    # Merge
    freq_df = pd.merge(hp_skill_counts, all_skill_counts, on='skill', how='left').fillna(0)
    freq_df['premium_ratio'] = freq_df['pct_of_high_paying_jobs'] / freq_df['pct_of_all_jobs']
    
    # Filter & Sort
    freq_df = freq_df[freq_df['count_in_high_paying'] >= MIN_SKILL_APPEARANCES]
    top_skills_high_paying = freq_df.sort_values('count_in_high_paying', ascending=False)
    
    print(f"Top {TOP_N_SKILLS} skills in high-paying roles:")
    print(top_skills_high_paying.head(TOP_N_SKILLS)[['skill', 'count_in_high_paying', 'pct_of_high_paying_jobs', 'premium_ratio']].to_string(index=False))

    # ---------------------------------------------------------
    # 6. Premium skills
    # ---------------------------------------------------------
    print("\n[6] PREMIUM SKILLS (DISPROPORTIONATELY HIGH-PAYING)...")
    premium_skills = freq_df[freq_df['count_in_high_paying'] >= 20].sort_values('premium_ratio', ascending=False)
    print(premium_skills.head(20)[['skill', 'premium_ratio', 'pct_of_high_paying_jobs']].to_string(index=False))

    # ---------------------------------------------------------
    # 7. Skills by job category
    # ---------------------------------------------------------
    print("\n[7] SKILLS BY CATEGORY (HIGH-PAYING)...")
    hp_cat = hp_exploded.assign(category=hp_exploded['categories'].astype(str).str.split(',')).explode('category')
    hp_cat['category'] = hp_cat['category'].str.strip()
    
    cat_skill_counts = hp_cat.groupby(['category', 'skill']).size().reset_index(name='count')
    cat_totals = hp_cat.groupby('category')['metadata_jobPostId'].nunique().reset_index(name='total_jobs_in_cat')
    cat_skill_counts = pd.merge(cat_skill_counts, cat_totals, on='category')
    cat_skill_counts['pct_of_category_jobs'] = (cat_skill_counts['count'] / cat_skill_counts['total_jobs_in_cat']) * 100
    
    # Get top 10 per category
    skills_by_category = cat_skill_counts.sort_values(['category', 'count'], ascending=[True, False]).groupby('category').head(10)
    
    top_categories = cat_totals.sort_values('total_jobs_in_cat', ascending=False).head(5)['category'].tolist()
    print("Top 5 Categories and their essential skills:")
    for cat in top_categories:
        top_cat_skills = skills_by_category[skills_by_category['category'] == cat].head(5)['skill'].tolist()
        print(f"  - {cat}: {', '.join(top_cat_skills)}")

    # ---------------------------------------------------------
    # 8. Skills by position level
    # ---------------------------------------------------------
    print("\n[8] SKILLS BY POSITION LEVEL (HIGH-PAYING)...")
    pos_skill_counts = hp_exploded.groupby(['positionLevels', 'skill']).size().reset_index(name='count')
    skills_by_position_level = pos_skill_counts.sort_values(['positionLevels', 'count'], ascending=[True, False]).groupby('positionLevels').head(10)
    
    print("Seniority Summary (Top 3 skills):")
    for pos in hp_exploded['positionLevels'].dropna().unique():
        top_pos_skills = skills_by_position_level[skills_by_position_level['positionLevels'] == pos].head(3)['skill'].tolist()
        print(f"  - {pos}: {', '.join(top_pos_skills)}")

    # ---------------------------------------------------------
    # 9. Median salary per skill
    # ---------------------------------------------------------
    print("\n[9] MEDIAN SALARY PER SKILL (TOP 20 FREQUENCY)...")
    top_20_skills_list = top_skills_high_paying.head(20)['skill'].tolist()
    
    median_salaries = []
    for skill in top_20_skills_list:
        skill_median = df_exploded[df_exploded['skill'] == skill]['average_salary'].median()
        median_salaries.append({'skill': skill, 'median_salary': skill_median})
        
    skill_salary_correlation = pd.DataFrame(median_salaries).sort_values('median_salary', ascending=False)
    print(skill_salary_correlation.to_string(index=False))

    # ---------------------------------------------------------
    # 10. Trending skills over time
    # ---------------------------------------------------------
    print("\n[10] TRENDING SKILLS OVER TIME (HIGH-PAYING)...")
    valid_dates_hp = hp_exploded.dropna(subset=['metadata_originalPostingDate'])
    if not valid_dates_hp.empty:
        median_date = valid_dates_hp['metadata_originalPostingDate'].median()
        older_half = valid_dates_hp[valid_dates_hp['metadata_originalPostingDate'] < median_date]
        newer_half = valid_dates_hp[valid_dates_hp['metadata_originalPostingDate'] >= median_date]
        
        older_counts = older_half['skill'].value_counts(normalize=True).reset_index()
        older_counts.columns = ['skill', 'older_pct']
        
        newer_counts = newer_half['skill'].value_counts(normalize=True).reset_index()
        newer_counts.columns = ['skill', 'newer_pct']
        
        trends = pd.merge(older_counts, newer_counts, on='skill', how='inner')
        trends['growth_pct_points'] = (trends['newer_pct'] - trends['older_pct']) * 100
        
        trending_skills = trends.sort_values('growth_pct_points', ascending=False)
        print("📈 Top 5 Growing Skills:")
        print(trending_skills.head(5)[['skill', 'growth_pct_points']].to_string(index=False))
        print("\n📉 Top 5 Declining Skills:")
        print(trending_skills.tail(5)[['skill', 'growth_pct_points']].to_string(index=False))
    else:
        print("Not enough date data to calculate trends.")
        trending_skills = pd.DataFrame()

    # ---------------------------------------------------------
    # 11. Company demand (bonus)
    # ---------------------------------------------------------
    print("\n[11] TOP HIRING COMPANIES FOR HIGH-PAYING ROLES...")
    company_counts = hp_exploded.groupby('postedCompany_name')['metadata_jobPostId'].nunique().reset_index(name='job_count')
    top_companies_list = company_counts.sort_values('job_count', ascending=False).head(20)['postedCompany_name']
    
    top_companies_data = []
    for comp in top_companies_list:
        comp_data = hp_exploded[hp_exploded['postedCompany_name'] == comp]
        top_3 = comp_data['skill'].value_counts().head(3).index.tolist()
        avg_sal = comp_data['average_salary'].mean()
        top_companies_data.append({
            'Company': comp,
            'Job Count': len(comp_data['metadata_jobPostId'].unique()),
            'Top Skills': ", ".join(top_3),
            'Avg Offered Salary': f"${avg_sal:,.0f}"
        })
        
    top_companies = pd.DataFrame(top_companies_data)
    print(top_companies[['Company', 'Top Skills', 'Avg Offered Salary']].head(5).to_string(index=False))

    # ---------------------------------------------------------
    # 12. Save all outputs
    # ---------------------------------------------------------
    print("\n[12] SAVING OUTPUTS FOR STREAMLIT...")
    files_to_save = {
        'top_skills_high_paying.csv': top_skills_high_paying,
        'premium_skills.csv': premium_skills,
        'skills_by_category.csv': skills_by_category,
        'skills_by_position_level.csv': skills_by_position_level,
        'skill_salary_correlation.csv': skill_salary_correlation,
        'trending_skills.csv': trending_skills,
        'top_companies.csv': top_companies
    }
    
    for filename, dataframe in files_to_save.items():
        if not dataframe.empty:
            out_path = os.path.join(OUTPUT_DIR, filename)
            dataframe.to_csv(out_path, index=False)
            print(f"Saved {filename} ({len(dataframe)} rows)")

    # ---------------------------------------------------------
    # 13. Narrative summary
    # ---------------------------------------------------------
    print("\n" + "="*60)
    print("📊 EXECUTIVE NARRATIVE SUMMARY")
    print("="*60)
    
    A = top_skills_high_paying.iloc[0]['skill'] if len(top_skills_high_paying) > 0 else 'N/A'
    B = top_skills_high_paying.iloc[1]['skill'] if len(top_skills_high_paying) > 1 else 'N/A'
    C = top_skills_high_paying.iloc[2]['skill'] if len(top_skills_high_paying) > 2 else 'N/A'
    
    D = premium_skills.iloc[0]['skill'] if len(premium_skills) > 0 else 'N/A'
    Dx = premium_skills.iloc[0]['premium_ratio'] if len(premium_skills) > 0 else 0
    E = premium_skills.iloc[1]['skill'] if len(premium_skills) > 1 else 'N/A'
    F = premium_skills.iloc[2]['skill'] if len(premium_skills) > 2 else 'N/A'
    
    top_cat = top_categories[0] if top_categories else 'N/A'
    G = skills_by_category[skills_by_category['category'] == top_cat].iloc[0]['skill'] if top_categories else 'N/A'
    H = skills_by_category[skills_by_category['category'] == top_cat].iloc[1]['skill'] if top_categories else 'N/A'
    
    I = trending_skills.iloc[0]['skill'] if not trending_skills.empty else 'N/A'
    J = trending_skills.iloc[1]['skill'] if len(trending_skills) > 1 else 'N/A'
    
    summary = (f"Across {high_paying_count:,} high-paying Singapore job listings (monthly salary above SGD ${threshold:,.0f} / "
               f"${annual_threshold:,.0f} annually), the most in-demand skills are {A.title()}, {B.title()}, and {C.title()}. "
               f"Skills most disproportionately associated with high pay are {D.title()}, {E.title()}, and {F.title()} "
               f"with a premium ratio reaching {Dx:.2f}x. The {top_cat} sector dominates high-paying listings, "
               f"where {G.title()} and {H.title()} are essential. Trending upward in recent postings are {I.title()} and {J.title()}.")
    
    print(summary)
    print("="*60)

if __name__ == "__main__":
    main()
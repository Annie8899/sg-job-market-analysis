import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="Skills of the Future | Singapore Jobs",
    page_icon="🚀",
    layout="wide"
)

st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: 700; color: #1B4F72; margin-bottom: 0px; }
    .sub-header { font-size: 1.1rem; color: #566573; margin-bottom: 2rem; }
    .metric-card { background: #EBF5FB; border-radius: 10px; padding: 1rem; }
    [data-testid="stMetricValue"] { font-size: 1.8rem; color: #1B4F72; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# DATA LOADING (CACHED)
# ==========================================
@st.cache_data
def load_data():
    try:
        df_top = pd.read_csv('top_skills_high_paying.csv')
        df_premium = pd.read_csv('premium_skills.csv')
        df_cat = pd.read_csv('skills_by_category.csv')
        df_pos = pd.read_csv('skills_by_position_level.csv')
        df_sal = pd.read_csv('skill_salary_correlation.csv')
        df_trend = pd.read_csv('trending_skills.csv')
        df_comp = pd.read_csv('top_companies.csv')
        return df_top, df_premium, df_cat, df_pos, df_sal, df_trend, df_comp
    except FileNotFoundError as e:
        st.error(f"⚠️ Missing file: {e.filename}. Please run your `analyse_skills.py` script first to generate the CSVs.")
        st.stop()

# 1. Load all data 
df_top, df_premium, df_cat, df_pos, df_sal, df_trend, df_comp = load_data()

# 2. Fix column name mismatch
if 'median_salary' in df_sal.columns:
    df_sal = df_sal.rename(columns={'median_salary': 'median_salary_monthly'})

# 3. Capitalize Skill Names
for df in [df_top, df_premium, df_cat, df_pos, df_sal, df_trend]:
    if 'skill' in df.columns:
        df['skill'] = df['skill'].str.title()
        acronyms = {
            'Nlp': 'NLP', 'Ci/Cd': 'CI/CD', 'Sap': 'SAP', 
            'Aws': 'AWS', 'Gcp': 'GCP', 'Etl': 'ETL', 
            'Sql': 'SQL', 'Mysql': 'MySQL', '.Net': '.NET'
        }
        df['skill'] = df['skill'].replace(acronyms)

# ==========================================
# SIDEBAR & GLOBAL FILTERS
# ==========================================
with st.sidebar:
    st.header("🎛️ Dashboard Controls")
    
    top_n = st.slider("Top N skills to display", min_value=5, max_value=50, value=23, step=1)
    
    all_categories = df_cat['category'].dropna().unique().tolist() if 'category' in df_cat.columns else []
    selected_categories = st.multiselect("Filter by job category", options=all_categories)
    
    all_positions = df_pos['positionLevels'].dropna().unique().tolist() if 'positionLevels' in df_pos.columns else []
    selected_positions = st.multiselect("Filter by position level", options=all_positions)
    
    rank_method = st.radio("Rank skills by", options=["Frequency", "Premium Ratio", "Median Salary"])
    
    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.markdown("""
    * **Source:** MyCareersFuture Singapore (2023)
    * **Scope:** All industries, high-paying roles defined as ≥ 75th salary percentile.
    * **NLP Methodology:** Skills extracted directly from job titles using regex matching.
    """)

# ==========================================
# STEP 1 & 2: MASTER FILTERING LOGIC
# ==========================================
def get_filtered_skills(selected_categories, selected_positions):
    skill_sets = []
    if selected_categories:
        cat_skills = df_cat[df_cat['category'].isin(selected_categories)]['skill'].unique()
        skill_sets.append(set(cat_skills))
    if selected_positions:
        pos_skills = df_pos[df_pos['positionLevels'].isin(selected_positions)]['skill'].unique()
        skill_sets.append(set(pos_skills))
        
    if skill_sets:
        # Intersection — skill must appear in ALL selected filters
        return list(set.intersection(*skill_sets))
    else:
        # Nothing selected — return all skills
        return df_top['skill'].tolist()

filtered_skills = get_filtered_skills(selected_categories, selected_positions)

filtered_top = df_top[df_top['skill'].isin(filtered_skills)].copy()
filtered_premium = df_premium[df_premium['skill'].isin(filtered_skills)].copy()
filtered_sal = df_sal[df_sal['skill'].isin(filtered_skills)].copy()

filtered_cat = df_cat[df_cat['skill'].isin(filtered_skills)].copy()
if selected_categories:
    filtered_cat = filtered_cat[filtered_cat['category'].isin(selected_categories)]

filtered_pos = df_pos[df_pos['skill'].isin(filtered_skills)].copy()
if selected_positions:
    filtered_pos = filtered_pos[filtered_pos['positionLevels'].isin(selected_positions)]

filtered_trend = df_trend[df_trend['skill'].isin(filtered_skills)].copy()

# ==========================================
# STEP 4: EMPTY STATE GUARD
# ==========================================
if filtered_top.empty:
    st.warning("No skills found matching your current filter combination. Try selecting fewer filters.")
    st.stop()

# ==========================================
# SECTION 1: HERO BANNER & NARRATIVE (STEP 6)
# ==========================================
with st.container():
    st.markdown('<p class="main-header">Skills of the Future 🚀</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Which skills appear most frequently across high-paying Singapore roles?</p>', unsafe_allow_html=True)
    
    top_skills = filtered_top.sort_values('count_in_high_paying', ascending=False)['skill'].head(3).tolist()
    A = top_skills[0] if len(top_skills) > 0 else "N/A"
    B = top_skills[1] if len(top_skills) > 1 else "N/A"
    C = top_skills[2] if len(top_skills) > 2 else "N/A"
    
    top_prem = filtered_premium.sort_values('premium_ratio', ascending=False)
    D = top_prem.iloc[0]['skill'] if not top_prem.empty else "N/A"
    D_ratio = top_prem.iloc[0]['premium_ratio'] if not top_prem.empty else 0
    
    filter_label = ", ".join(selected_categories) if selected_categories else "All Industries"
    
    st.info(f"Filtering by **{filter_label}** — top skills are **{A}**, **{B}**, **{C}**. The highest-premium skill is **{D}** at **{D_ratio:.1f}x** the market rate.")

st.markdown("---")

# ==========================================
# SECTION 2: KPI METRIC CARDS (STEP 5)
# ==========================================
st.markdown("### Market Overview")
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Listings Analysed", "199,847")
col2.metric("Filtered High-Paying Listings", f"{int(filtered_top['count_in_high_paying'].sum()):,}")
col3.metric("Unique Skills (Filtered)", f"{filtered_top['skill'].nunique()}")
col4.metric("Median Salary (Filtered)", f"${filtered_sal['median_salary_monthly'].median():,.0f}" if not filtered_sal.empty else "N/A")

st.markdown("---")

# ==========================================
# SECTION 3: MAIN SKILL CHART (STEP 7)
# ==========================================
st.markdown(f"### Top {top_n} Skills by {rank_method}")

if rank_method == "Frequency":
    plot_df = filtered_top.sort_values('count_in_high_paying', ascending=False).head(top_n)
    x_col, x_label = 'count_in_high_paying', 'Appearances in High-Paying Roles'
elif rank_method == "Premium Ratio":
    plot_df = filtered_premium.sort_values('premium_ratio', ascending=False).head(top_n)
    x_col, x_label = 'premium_ratio', 'Premium Ratio vs Market Average'
else:  # Median Salary
    plot_df = filtered_sal.sort_values('median_salary_monthly', ascending=False).head(top_n)
    x_col, x_label = 'median_salary_monthly', 'Median Monthly Salary (SGD)'

plot_df = plot_df.sort_values(x_col, ascending=True)  # ascending for horizontal bar
fig_main = px.bar(plot_df, x=x_col, y='skill', orientation='h',
                  color=x_col, color_continuous_scale='Teal',
                  text=x_col)

# Format the text if it's salary or ratio
if rank_method == "Premium Ratio":
    fig_main.update_traces(texttemplate='%{text:.2f}x')
elif rank_method == "Median Salary":
    fig_main.update_traces(texttemplate='$%{text:,.0f}')

fig_main.update_layout(height=550, coloraxis_showscale=False,
                       xaxis_title=x_label, yaxis_title="",
                       margin=dict(l=0, r=40, t=30, b=0))
st.plotly_chart(fig_main, use_container_width=True)

st.markdown("---")

# ==========================================
# SECTION 4: TWO COLUMN LAYOUT (PREMIUM / HIGH PAYING)
# ==========================================
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("### 💎 Premium Skills")
    df_prem_plot = filtered_premium.head(15).sort_values('premium_ratio', ascending=True)
    
    fig_prem = go.Figure()
    colors = ['#1abc9c' if val >= 1.0 else '#bdc3c7' for val in df_prem_plot['premium_ratio']]
    
    fig_prem.add_trace(go.Bar(
        x=df_prem_plot['premium_ratio'], 
        y=df_prem_plot['skill'], 
        orientation='h',
        marker_color=colors,
        text=[f"{v:.1f}x" for v in df_prem_plot['premium_ratio']],
        textposition='outside'
    ))
    
    fig_prem.add_vline(x=1.0, line_dash="dash", line_color="red", annotation_text="Market average (1.0)")
    fig_prem.update_layout(height=500, margin=dict(l=0, r=0, t=0, b=0), xaxis_title="Premium Ratio")
    st.plotly_chart(fig_prem, use_container_width=True)

with col_right:
    st.markdown("### 💰 Highest Paying Skills")
    df_sal_plot = filtered_sal.head(15).sort_values('median_salary_monthly', ascending=True)
    avg_sal_ref = filtered_sal['median_salary_monthly'].mean() if not filtered_sal.empty else 0
    
    fig_sal = go.Figure(go.Bar(
        x=df_sal_plot['median_salary_monthly'], 
        y=df_sal_plot['skill'], 
        orientation='h',
        marker_color='#2c3e50',
        text=[f"${v:,.0f}" for v in df_sal_plot['median_salary_monthly']],
        textposition='outside'
    ))
    
    fig_sal.add_vline(x=avg_sal_ref, line_dash="dash", line_color="red", annotation_text="Avg")
    fig_sal.update_layout(height=500, margin=dict(l=0, r=0, t=0, b=0), xaxis_title="Median Salary (SGD)")
    st.plotly_chart(fig_sal, use_container_width=True)

st.markdown("---")

# ==========================================
# SECTION 5: SKILLS BY CATEGORY HEATMAP (STEP 8)
# ==========================================
st.markdown("### Skill Demand by Industry")

top_skills_list = filtered_top['skill'].head(15).tolist()
top_cats_list = (
    filtered_cat[filtered_cat['category'].isin(selected_categories)]['category'].unique().tolist()
    if selected_categories
    else filtered_cat.groupby('category')['count'].sum().nlargest(10).index.tolist()
)

heatmap_data = filtered_cat[
    filtered_cat['skill'].isin(top_skills_list) &
    filtered_cat['category'].isin(top_cats_list)
]

if not heatmap_data.empty:
    pivot = heatmap_data.pivot_table(index='category', columns='skill',
                                      values='pct_of_category_jobs', aggfunc='mean').fillna(0)
    fig_heat = px.imshow(pivot, color_continuous_scale='Teal', aspect='auto')
    fig_heat.update_layout(height=500, margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig_heat, use_container_width=True)
else:
    st.info("No category data available for current filter selection.")

st.markdown("---")

# ==========================================
# SECTION 6: SKILLS BY POSITION LEVEL
# ==========================================
st.markdown("### Skills by Seniority Level")
if not filtered_pos.empty:
    fig_pos = px.bar(filtered_pos, x='positionLevels', y='count', color='skill', barmode='group', color_discrete_sequence=px.colors.sequential.Teal)
    fig_pos.update_layout(height=500, xaxis_title="Position Level", yaxis_title="Skill Count", legend_title="Skill")
    st.plotly_chart(fig_pos, use_container_width=True)
    
    try:
        senior_roles = filtered_pos[filtered_pos['positionLevels'].str.contains('Senior|Manager|Director', case=False, na=False)]
        junior_roles = filtered_pos[filtered_pos['positionLevels'].str.contains('Junior|Entry|Executive', case=False, na=False)]
        
        top_senior = senior_roles.sort_values('count', ascending=False).iloc[0]['skill'] if not senior_roles.empty else "Management"
        top_junior = junior_roles.sort_values('count', ascending=False).iloc[0]['skill'] if not junior_roles.empty else "Core Tech"
        
        st.caption(f"💡 **Insight:** Senior roles show stronger demand for **{top_senior.title()}** while junior roles skew toward **{top_junior.title()}**.")
    except Exception:
        pass
else:
    st.info("No position level data available based on current filters.")

st.markdown("---")

# ==========================================
# SECTION 7: TRENDING SKILLS
# ==========================================
st.markdown("### Trending Skills")
st.caption("Based on comparing older vs newer job postings in the 2023 dataset")

col_trend_l, col_trend_r = st.columns(2)
growth_col = 'growth' if 'growth' in filtered_trend.columns else 'growth_pct_points'

if growth_col in filtered_trend.columns and not filtered_trend.empty:
    with col_trend_l:
        st.markdown("#### 📈 Rising Skills")
        rising = filtered_trend.sort_values(growth_col, ascending=False).head(10).sort_values(growth_col, ascending=True)
        fig_rise = px.bar(rising, x=growth_col, y='skill', orientation='h')
        fig_rise.update_traces(marker_color='#2ecc71')
        fig_rise.update_layout(height=400, margin=dict(l=0, r=0, t=0, b=0), xaxis_title="Growth (Pct Points)")
        st.plotly_chart(fig_rise, use_container_width=True)

    with col_trend_r:
        st.markdown("#### 📉 Declining Skills")
        declining = filtered_trend.sort_values(growth_col, ascending=True).head(10).sort_values(growth_col, ascending=False)
        fig_dec = px.bar(declining, x=growth_col, y='skill', orientation='h')
        fig_dec.update_traces(marker_color='#e74c3c')
        fig_dec.update_layout(height=400, margin=dict(l=0, r=0, t=0, b=0), xaxis_title="Decline (Pct Points)")
        st.plotly_chart(fig_dec, use_container_width=True)
else:
    st.info("No trending data available for the current filter.")

st.markdown("---")

# ==========================================
# SECTION 8: TOP HIRING COMPANIES (UNFILTERED)
# ==========================================
st.markdown("### Top Hiring Companies")
st.caption("Companies actively hiring for high-paying roles in Singapore (Global Data)")

if not df_comp.empty:
    df_comp_display = df_comp.rename(columns={
        'postedCompany_name': 'Company',
        'count': 'High-Paying Listings',
        'avg_salary': 'Avg Monthly Salary (SGD)',
        'top_skills': 'Top Skills Required'
    })
    
    if 'Avg Monthly Salary (SGD)' in df_comp_display.columns:
        df_comp_display['Avg Monthly Salary (SGD)'] = pd.to_numeric(
            df_comp_display['Avg Monthly Salary (SGD)'].astype(str).str.replace(r'[\$,]', '', regex=True), errors='coerce'
        ).apply(lambda x: f"${x:,.0f}" if pd.notnull(x) else "N/A")
        
    st.dataframe(df_comp_display, use_container_width=True, hide_index=True)

st.markdown("---")

# ==========================================
# SECTION 9: RAW DATA EXPLORER
# ==========================================
with st.expander("🔍 Explore filtered raw skill data"):
    st.dataframe(filtered_top, use_container_width=True)
    
    csv_data = filtered_top.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Data as CSV",
        data=csv_data,
        file_name='filtered_skills_data.csv',
        mime='text/csv',
    )

# ==========================================
# FOOTER
# ==========================================
st.markdown("<br><br><br>", unsafe_allow_html=True)
st.markdown(
    "<center><p style='color: #808B96; font-size: 0.9rem;'>Built with Streamlit • Data: MyCareersFuture Singapore 2023 • Analysis: Skills of the Future Project</p></center>", 
    unsafe_allow_html=True
)
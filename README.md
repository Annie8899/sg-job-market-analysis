# 🚀 Skills of the Future: Singapore Job Market Dashboard

## 📌 The Business Objective
**"Skills of the future — which skills appear most frequently across high-paying roles?"**

This project aims to uncover the hidden leverage points in the Singapore job market. Rather than just identifying the most "popular" skills, this analysis isolates the specific technical and domain skills that act as gatekeepers to the top 25% of highest-paying jobs.

## 📊 Project Summary
This project analyzes over **1,000,000 job listings** from MyCareersFuture Singapore (2023). 

Because the raw data did not contain a standardized "skills" column, a custom Natural Language Processing (NLP) pipeline was engineered to extract over 80 specific technical and business skills directly from unstructured job titles. The data was then cleaned, outliers were capped, and the listings were segmented by salary percentiles, industry categories, and seniority levels.

### **How this Dashboard Solves the Objective:**
1. **The Premium Ratio Metric:** The dashboard calculates a "Premium Ratio" for every skill. This proves mathematically how much more likely a skill is to appear in a high-paying role versus an average-paying role (e.g., Docker commands a 2.6x premium).
2. **Industry & Seniority Context:** Users can dynamically filter the market to see how the highest-paying skills shift from technical execution (Junior) to strategic management (Senior).
3. **Trend Analysis:** By comparing chronological halves of the 2023 dataset, the dashboard isolates "Rising" vs "Declining" skills to truly project the *Skills of the Future*.

## 🛠️ Tech Stack
* **Data Processing & NLP:** Python, Pandas, Regular Expressions (RegEx)
* **Interactive Visualization:** Plotly Express, Plotly Graph Objects
* **Frontend Web App:** Streamlit

## 💻 How to Run Locally
1. Clone this repository.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
import streamlit as st
import pandas as pd
from google import genai
import os
import io
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Retentia - Enterprise Churn OS", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

# --- Premium Custom CSS Injection ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

/* Apply modern typography globally */
html, body, p, h1, h2, h3, h4, h5, h6, label, .stMarkdown, .stText {
    font-family: 'Outfit', sans-serif !important;
}

/* Premium Dark Mode & Glassmorphism Aesthetics */
.stApp {
    background: linear-gradient(180deg, #09090b 0%, #18181b 100%);
    color: #e4e4e7;
}

/* Glassy Containers */
.stExpander, div[data-testid="stExpander"] {
    background: rgba(255, 255, 255, 0.03) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 16px !important;
    backdrop-filter: blur(12px) !important;
    box-shadow: 0 4px 24px -4px rgba(0, 0, 0, 0.5) !important;
}

/* Accent Gradients for Headers */
h1 {
    background: linear-gradient(90deg, #38bdf8 0%, #818cf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 700 !important;
    letter-spacing: -1px;
}

/* Metrics and Cards styling */
div[data-testid="stMetricValue"] {
    color: #f8fafc !important;
    font-weight: 600 !important;
    font-size: 2.2rem !important;
}

/* Hide Sidebar Completely */
[data-testid="collapsedControl"] { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }

</style>
""", unsafe_allow_html=True)

# Import the new modular views
from views import executive_overview, ai_insights, retention_console, ab_testing_simulator, bi_dashboard

# --- Phase 4: Configure Gemini API ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    st.markdown("""
    <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.2); border-radius: 8px; padding: 0.8rem 1rem; color: #fcd34d; font-size: 0.9rem; text-align: center; margin-bottom: 2rem;">
        <span style="font-weight: 500;">API Key Missing:</span> The <code>GEMINI_API_KEY</code> environment variable is not set. AI-driven insights will be disabled.
    </div>
    """, unsafe_allow_html=True)
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

@st.cache_data(show_spinner=False)
def get_ai_recommendation(kpi_data):
    """Generates an executive summary using Gemini API."""
    prompt = f"""
    You are a Senior Data Analyst. Review these dashboard metrics:
    - Total Customers: {kpi_data['total_customers']}
    - Churn Rate: {kpi_data['churn_rate']}%
    - Avg Failed Tx: {kpi_data['avg_failed_tx']}
    - Revenue at Risk: ${kpi_data['revenue_risk']:,.2f}
    
    Provide exactly 3 short, punchy bullet points analyzing the risk and suggesting immediate action for the Operations team. Do not use filler words. Speak like a real human analyst sending a quick Slack update. Use standard markdown bullet points (-).
    """
    try:
        if not client:
            return _mock_ai_recommendation(kpi_data)
        response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        return response.text.strip()
    except Exception as e:
        return _mock_ai_recommendation(kpi_data)

def _mock_ai_recommendation(kpi_data):
    return f"""
- **Elevated Flight Risk Detected**: Revenue at risk has hit ${kpi_data['revenue_risk']:,.2f}. High correlation with recent payment failures.
- **Immediate Intervention Required**: Customers experiencing >2 failed transactions are 4.3x more likely to churn. Deploy VIP rescue campaign.
- **Systemic Issue Identified**: The average of {kpi_data['avg_failed_tx']} failed transactions points to a gateway integration bug. Engineering ticket prioritized.
*(Note: Showing simulated AI response for Demo Mode)*
    """.strip()

def scrub_pii(profile):
    scrubbed = profile.copy()
    balance = float(scrubbed.get('Balance', 0))
    if balance > 100000:
        scrubbed['Balance Tier'] = 'High-Net-Worth bracket'
    elif balance > 50000:
        scrubbed['Balance Tier'] = 'Mid-Tier bracket'
    else:
        scrubbed['Balance Tier'] = 'Standard bracket'
    
    # Remove exact balance, names, exact geography if too specific
    # (assuming Geography is Country level like France, it's fine, but let's be safe)
    scrubbed.pop('Balance', None)
    scrubbed.pop('CustomerId', None)
    scrubbed.pop('Surname', None)
    return scrubbed

@st.cache_data(show_spinner=False)
def generate_customer_outreach_script(customer_profile):
    """Generates a personalized outreach email for a specific customer."""
    safe_profile = scrub_pii(customer_profile)
    
    prompt = f"""
    You are an empathetic, senior Customer Success Manager at a premium FinTech bank.
    Write a short, highly personalized apology and retention email to this specific customer 
    who is at high risk of churning due to our platform's technical payment failures.
    
    Customer Profile:
    - Age: {safe_profile['Age']}
    - Account Balance: {safe_profile['Balance Tier']}
    - Recent Failed Transactions: {safe_profile['failed_transactions_last_30_days']}
    - Geography: {safe_profile['Geography']}
    - Tenure (Years with us): {safe_profile['Tenure']}
    
    Acknowledge the specific number of failed transactions. Emphasize that we value their business 
    (mentioning their tenure or balance subtly). Offer them a sincere apology and a direct line to 
    VIP support. Keep it professional, empathetic, and under 150 words. Do not use placeholders like [Your Name].
    """
    try:
        if not client:
            return _mock_outreach_script(safe_profile)
        response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        return response.text.strip()
    except Exception as e:
        return _mock_outreach_script(safe_profile)

def _mock_outreach_script(safe_profile):
    return f"""
**Subject:** Sincere apologies regarding your recent experience

Hi there,

I am a Senior Customer Success Manager at Retentia, and I personally wanted to reach out regarding the {safe_profile.get('failed_transactions_last_30_days', 'recent')} failed transactions you experienced on our platform. 

We highly value your {safe_profile.get('Tenure', 'long-term')} loyalty and your business as part of our {safe_profile.get('Balance Tier', 'valued')} community. This technical friction is unacceptable, and our engineering team has already deployed a fix. 

I have upgraded your account to VIP Priority Support. Please let me know if you are open to a brief 5-minute call this week so I can personally ensure your account is operating flawlessly.

Best regards,
Customer Success Team
*(Note: Showing simulated AI response for Demo Mode)*
    """.strip()

@st.cache_data(show_spinner=False)
def generate_excel_report(df, kpi_dict):
    """Generates an Advanced Excel report with charts and conditional formatting."""
    output = io.BytesIO()
    
    # Create a Pandas Excel writer using XlsxWriter as the engine.
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # --- Sheet 1: Executive Summary ---
        summary_df = pd.DataFrame({
            'Metric': ['Total Customers', 'Overall Churn Rate (%)', 'Avg Failed Transactions', 'Revenue at Risk ($)'],
            'Value': [
                kpi_dict['total_customers'], 
                kpi_dict['churn_rate'], 
                kpi_dict['avg_failed_tx'], 
                kpi_dict['revenue_risk']
            ]
        })
        summary_df.to_excel(writer, sheet_name='Executive Summary', index=False)
        worksheet1 = writer.sheets['Executive Summary']
        
        # Format the summary sheet
        header_format = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1})
        for col_num, value in enumerate(summary_df.columns.values):
            worksheet1.write(0, col_num, value, header_format)
        worksheet1.set_column('A:A', 25)
        worksheet1.set_column('B:B', 20)
        
        # Add a native Excel Pie Chart
        chart = workbook.add_chart({'type': 'pie'})
        active_count = int(kpi_dict['total_customers'] * (1 - kpi_dict['churn_rate']/100))
        churned_count = kpi_dict['total_customers'] - active_count
        worksheet1.write('D1', 'Status', header_format)
        worksheet1.write('E1', 'Count', header_format)
        worksheet1.write('D2', 'Active')
        worksheet1.write('E2', active_count)
        worksheet1.write('D3', 'Churned')
        worksheet1.write('E3', churned_count)
        
        chart.add_series({
            'name': 'Customer Churn Distribution',
            'categories': "='Executive Summary'!$D$2:$D$3",
            'values':     "='Executive Summary'!$E$2:$E$3",
        })
        chart.set_title({'name': 'Customer Churn Distribution'})
        worksheet1.insert_chart('G2', chart)

        # --- Sheet 2: High-Risk Customers ---
        df.to_excel(writer, sheet_name='High-Risk Customers', index=False)
        worksheet2 = writer.sheets['High-Risk Customers']
        
        for i, col in enumerate(df.columns):
            column_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet2.set_column(i, i, column_len)
            
        if 'Churn Risk (%)' in df.columns:
            risk_col_idx = df.columns.get_loc('Churn Risk (%)')
            col_letter = chr(ord('A') + risk_col_idx) if risk_col_idx < 26 else chr(ord('A') + (risk_col_idx // 26) - 1) + chr(ord('A') + (risk_col_idx % 26))
            last_row = len(df) + 1
            range_str = f'{col_letter}2:{col_letter}{last_row}'
            
            format_red = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
            format_yellow = workbook.add_format({'bg_color': '#FFEB9C', 'font_color': '#9C6500'})
            
            worksheet2.conditional_format(range_str, {'type': 'cell', 'criteria': '>', 'value': 75, 'format': format_red})
            worksheet2.conditional_format(range_str, {'type': 'cell', 'criteria': 'between', 'minimum': 50, 'maximum': 75, 'format': format_yellow})
                                                      
    return output.getvalue()


st.markdown("""
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0rem;">
    <div>
        <h1 style='margin-bottom: 0;'>⚡ Retentia <span style='font-size: 1.5rem; color: #71717a; font-weight: 400;'>| Enterprise Churn OS</span></h1>
        <p style='color: #a1a1aa; font-size: 1.1rem; margin-top: 0.2rem;'>Proactive intelligence to protect your revenue.</p>
    </div>
""", unsafe_allow_html=True)

_, is_demo = get_db_engine()
if is_demo:
    st.markdown("""
    <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 20px; padding: 0.4rem 1rem; color: #34d399; font-size: 0.85rem; font-weight: 600; display: inline-flex; align-items: center; gap: 6px;">
        <span style="height: 8px; width: 8px; background-color: #10b981; border-radius: 50%; display: inline-block; box-shadow: 0 0 8px #10b981;"></span>
        DEMO MODE (OFFLINE)
    </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 20px; padding: 0.4rem 1rem; color: #38bdf8; font-size: 0.85rem; font-weight: 600; display: inline-flex; align-items: center; gap: 6px;">
        <span style="height: 8px; width: 8px; background-color: #38bdf8; border-radius: 50%; display: inline-block; box-shadow: 0 0 8px #38bdf8;"></span>
        LIVE POSTGRES DATA
    </div>
    </div>
    """, unsafe_allow_html=True)

# --- Architectural Overview ---
st.markdown("""
<div style="background: rgba(255,255,255,0.03); padding: 1.5rem; border-radius: 16px; border: 1px solid rgba(255,255,255,0.08); color: #d4d4d8; font-size: 0.95rem; font-weight: 300; line-height: 1.6; margin-top: 2rem; margin-bottom: 2.5rem; text-align: center; max-width: 900px; margin-left: auto; margin-right: auto; backdrop-filter: blur(10px); box-shadow: 0 10px 30px -10px rgba(0,0,0,0.5);">
<strong>Welcome to the Future of Retention.</strong> As you adjust the global filters below, our <strong>Random Forest ML model</strong> instantly recalculates the flight risk of every user based on their operational friction (like failed payments). Then, our integrated <strong>Gemini 2.0</strong> assistant drafts personalized recovery plans to win them back.
</div>
""", unsafe_allow_html=True)

# Load Data Limits
@st.cache_data
def get_db_engine():
    db_url = os.getenv("DATABASE_URL")
    demo_mode = False
    engine = None
    
    if db_url:
        try:
            # Try Postgres connection
            engine = create_engine(db_url, pool_size=10, max_overflow=20)
            with engine.connect() as conn:
                pass
        except Exception as e:
            engine = None
            
    if engine is None:
        # Fallback to local SQLite for Demo / Pitch purposes
        demo_mode = True
        engine = create_engine("sqlite:///crm_data.db")
        
    return engine, demo_mode

@st.cache_data
def load_data_limits():
    engine, _ = get_db_engine()
    if not engine:
        return None
    try:
        query = 'SELECT MIN("Age") as min_age, MAX("Age") as max_age, MIN("CreditScore") as min_credit, MAX("CreditScore") as max_credit, MIN("failed_transactions_last_30_days") as min_fail, MAX("failed_transactions_last_30_days") as max_fail FROM customers'
        limits = pd.read_sql(query, engine)
        return limits.iloc[0]
    except Exception as e:
        # DB might not be initialized yet
        return None

limits = load_data_limits()

def load_filtered_data(age_min, age_max, credit_min, credit_max, failed_tx):
    engine, _ = get_db_engine()
    if not engine:
        return pd.DataFrame(), pd.DataFrame()
    
    query_filtered = f"""
        SELECT * FROM customers
        WHERE "Age" BETWEEN {age_min} AND {age_max}
        AND "CreditScore" BETWEEN {credit_min} AND {credit_max}
        AND "failed_transactions_last_30_days" <= {failed_tx}
    """
    f_df = pd.read_sql(query_filtered, engine)
    
    query_top_50 = f"""
        WITH RiskRankedCustomers AS (
            SELECT *,
                   RANK() OVER (ORDER BY "Churn Risk (%)" DESC, "Balance" DESC) as RiskRank
            FROM customers
            WHERE "Age" BETWEEN {age_min} AND {age_max}
            AND "CreditScore" BETWEEN {credit_min} AND {credit_max}
            AND "failed_transactions_last_30_days" <= {failed_tx}
        )
        SELECT * FROM RiskRankedCustomers
        WHERE RiskRank <= 50
    """
    t_50 = pd.read_sql(query_top_50, engine)
    return f_df, t_50

if limits is not None:
    # --- Native Pill Navigation ---
    selection = st.pills("Navigation", 
                         options=["Morning Briefing", "Ask the Strategist", "Customer Rescue", "Experimentation Lab", "Deep Dive"],
                         default="Morning Briefing",
                         label_visibility="collapsed")
    if not selection:
        selection = "Morning Briefing"

    # --- Collapsible Filters ---
    with st.expander("Who are we analyzing today?"):
        st.markdown("<p style='color: #a1a1aa; font-size: 0.9rem;'>Let's fine-tune the audience slice. Our live AI model will recalculate flight risks in real-time as you adjust these.</p>", unsafe_allow_html=True)
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            age_range = st.slider("Age Range", int(limits['min_age']), int(limits['max_age']), (int(limits['min_age']), int(limits['max_age'])))
        with col_f2:
            credit_range = st.slider("Credit Score", int(limits['min_credit']), int(limits['max_credit']), (int(limits['min_credit']), int(limits['max_credit'])))
        with col_f3:
            failed_tx = st.slider("Max Failed Transactions (30 Days)", int(limits['min_fail']), int(limits['max_fail']), int(limits['max_fail']))
    
    @st.fragment(run_every="30s")
    def live_dashboard_fragment(age_range, credit_range, failed_tx, selection):
        # Apply SQL Filters & CTE Rank
        try:
            filtered_df, top_50_risk = load_filtered_data(age_range[0], age_range[1], credit_range[0], credit_range[1], failed_tx)
        except Exception as e:
            st.error(f"SQL Execution Error: {e}")
            filtered_df = pd.DataFrame()
            top_50_risk = pd.DataFrame()
        
        if filtered_df.empty:
            st.warning("No customers match the selected filter criteria. Please adjust the sliders.")
        else:
            
            # --- KPI Calculations ---
            total_customers = len(filtered_df)
            churn_rate = (filtered_df['Exited'].mean() * 100) if total_customers > 0 else 0
            avg_failed_tx = filtered_df['failed_transactions_last_30_days'].mean()
            revenue_at_risk = filtered_df[filtered_df['Exited'] == 1]['Balance'].sum()
            
            kpi_dict = {
                'total_customers': total_customers,
                'churn_rate': round(churn_rate, 2),
                'avg_failed_tx': round(avg_failed_tx, 2),
                'revenue_risk': revenue_at_risk
            }

            # Render corresponding view based on sidebar selection
            if selection == "Morning Briefing":
                excel_data = generate_excel_report(filtered_df, kpi_dict)
                executive_overview.render(filtered_df, kpi_dict, excel_data)
                
            elif selection == "Ask the Strategist":
                ai_insights.render(kpi_dict, get_ai_recommendation)
                
            elif selection == "Customer Rescue":
                retention_console.render(top_50_risk, generate_customer_outreach_script)
                
            elif selection == "Experimentation Lab":
                ab_testing_simulator.render()
                
            elif selection == "Deep Dive":
                bi_dashboard.render(age_range, credit_range, failed_tx)

    # Call the real-time fragment
    live_dashboard_fragment(age_range, credit_range, failed_tx, selection)

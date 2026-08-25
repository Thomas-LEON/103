import streamlit as st
import json
import re
import traceback
import plotly.graph_objects as go
import pandas as pd

from llm import get_auth_context, LLMChat, ConfigLoader
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions

# =====================================================================
# PAGE CONFIG
# =====================================================================
st.set_page_config(
    page_title="Executive CTI Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Petit nettoyage Streamlit de base
st.markdown("""
<style>
    #MainMenu {visibility: hidden;} 
    footer {visibility: hidden;} 
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# =====================================================================
# 📡 1. DATA FETCHING (7-Day History)
# =====================================================================
@st.cache_data(ttl=1800)
def fetch_recent_reports(limit=7):
    driver = None
    try:
        chromedriver_path = ConfigLoader.get_chromedriver_path()
        options = ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-extensions")
        
        service = ChromeService(executable_path=chromedriver_path)
        driver = webdriver.Chrome(service=service, options=options)
        
        driver.get("https://api.github.com/repos/Thomas-LEON/news-tracker/contents/reports")
        json_text = driver.find_element("tag name", "body").text
        files = json.loads(json_text)
        
        md_files = [f for f in files if isinstance(f, dict) and f.get('name', '').endswith('.md')]
        if not md_files:
            return [], "No reports found."
            
        md_files.sort(key=lambda x: x['name'], reverse=True)
        recent_files = md_files[:limit]
        
        reports_data = []
        for file_info in recent_files:
            driver.get(file_info['download_url'])
            content = driver.find_element("tag name", "body").text
            reports_data.append((file_info['name'], content))
            
        return reports_data, None
    except Exception as e:
        return [], f"Data sync error: {str(e)}"
    finally:
        if driver:
            driver.quit()

# =====================================================================
# ⚙️ 2. NATIVE MARKDOWN PARSER & MATHEMATICAL SCORING
# =====================================================================
def parse_incidents(content):
    subjects = []
    sections = re.split(r'## Titre de l\'incident\s*:', content)
    
    for section in sections[1:]:
        lines = section.strip().split('\n')
        if not lines: continue
        
        preview = lines[0].strip()
        country_match = re.search(r'\*\*Impacted Country:\*\*\s*(.*?)\n', section)
        companies_match = re.search(r'\*\*List of Companies Impacted:\*\*\s*(.*?)\n', section)
        overview_match = re.search(r'\*\*Overview\*\*\n(.*?)(?=\n\*\*)', section, re.DOTALL)
        breach_match = re.search(r'\*\*The Breach Mechanism\*\*\n(.*?)(?=\n\*\*)', section, re.DOTALL)
        impact_match = re.search(r'\*\*Impact and Consequences\*\*\n(.*?)(?=\n\*\*)', section, re.DOTALL)
        control_match = re.search(r'\*\*Proposed Control.*?\*\*\n(.*?)(?=\n\*\*|$)', section, re.DOTALL)
        link_match = re.search(r'(https?://[^\s]+)', section)
        
        subjects.append({
            "preview": preview, 
            "country": country_match.group(1).strip() if country_match else "", 
            "companies": companies_match.group(1).strip() if companies_match else "",
            "overview": overview_match.group(1).strip() if overview_match else "", 
            "breach": breach_match.group(1).strip() if breach_match else "", 
            "impact": impact_match.group(1).strip() if impact_match else "",
            "control": control_match.group(1).strip() if control_match else "", 
            "link": link_match.group(1).strip() if link_match else ""
        })
    return subjects

def calculate_daily_score(incidents):
    """
    CRQ Methodology: Calculates a 0-100 score based on threat volume and severity indicators.
    """
    score = 0
    for inc in incidents:
        score += 10 # Base volume weight
        text = f"{inc['overview']} {inc['breach']} {inc['impact']}".lower()
        if any(k in text for k in ["zero-day", "0-day", "zero day"]): score += 15
        if "ransomware" in text: score += 10
        if any(k in text for k in ["apt", "state-sponsored", "nation-state"]): score += 10
        if "critical" in text: score += 5
    return min(score, 100) # Cap at 100

# =====================================================================
# 🧠 3. AI ENGINE (Qualitative BLUF Only)
# =====================================================================
@st.cache_resource
def init_llm_auth():
    return get_auth_context()

def extract_key_recursive(data, target_keys):
    if isinstance(target_keys, str): target_keys = [target_keys]
    targets = [str(k).lower() for k in target_keys]
    if isinstance(data, dict):
        for k, v in data.items():
            if str(k).lower() in targets: return v
        for v in data.values():
            res = extract_key_recursive(v, target_keys)
            if res is not None: return res
    elif isinstance(data, list):
        for item in data:
            res = extract_key_recursive(item, target_keys)
            if res is not None: return res
    return None

@st.cache_data(ttl=86400)
def generate_executive_brief(condensed_text, report_date, _auth_context):
    models_to_try = ["gpt-oss-120b", "mistral-medium-3.5-ITG", "gemma-4-26b"]
    debug_logs = []
    
    for model_id in models_to_try:
        log_entry = {"model": model_id, "raw_response": "", "error": None, "stage": "Init"}
        try:
            log_entry["stage"] = "1. API Call"
            chat = LLMChat(model_id=model_id, auth_context=_auth_context, high_reasoning_effort=True, web_search=False)
            
            mega_prompt = f"""You are a senior Cyber Threat Intelligence analyst briefing the Board of Directors.
READ the incidents below and WRITE a high-level strategic summary. Focus on Business Units impacted.

ABSOLUTE RULES:
- Write in ENGLISH. Use strictly BUSINESS language.
- YOU MUST USE THE EXACT KEYS AS THE EXAMPLE BELOW. DO NOT RENAME THEM.

EXAMPLE OF EXACT EXPECTED OUTPUT:
{{
  "bluf": "A critical zero-day vulnerability is actively exploited, requiring immediate patching.",
  "threat_landscape": ["State-sponsored actors are targeting financial institutions."],
  "business_impact": ["Potential loss of sensitive PII leading to regulatory fines."],
  "recommendations": ["Authorize emergency patching protocol."]
}}

--- INCIDENTS TO ANALYZE FOR {report_date} ---
{condensed_text}
"""
            raw = chat.say(mega_prompt)
            log_entry["raw_response"] = raw
            
            log_entry["stage"] = "2. JSON Extraction"
            clean_json = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw, re.DOTALL | re.IGNORECASE)
            clean_json_str = clean_json.group(1) if clean_json else (re.search(r'\{.*\}', raw, re.DOTALL).group(0) if re.search(r'\{.*\}', raw, re.DOTALL) else raw)

            parsed = json.loads(clean_json_str)
            
            log_entry["stage"] = "3. Validation"
            bluf_val = extract_key_recursive(parsed, ["bluf", "bottom_line_up_front", "bottom_line", "summary", "executive_summary"])
            
            if bluf_val:
                return {
                    "bluf": bluf_val,
                    "threat_landscape": extract_key_recursive(parsed, ["threat_landscape", "landscape"]) or [],
                    "business_impact": extract_key_recursive(parsed, ["business_impact", "impact"]) or [],
                    "recommendations": extract_key_recursive(parsed, ["recommendations", "actions"]) or []
                }, debug_logs
            else:
                log_entry["error"] = f"Missing BLUF. Keys found: {list(parsed.keys()) if isinstance(parsed, dict) else type(parsed)}"
                
        except Exception as e:
            log_entry["error"] = f"Exception at [{log_entry['stage']}]: {str(e)}"
            
        debug_logs.append(log_entry)
            
    return None, debug_logs

def format_bullets(data_item):
    if isinstance(data_item, list): 
        return "\n".join([f"- {item}" for item in data_item])
    return str(data_item)

# =====================================================================
# 🖥️ 4. USER INTERFACE (V9 MATHEMATICAL CRQ + PLOTLY)
# =====================================================================
with st.spinner("Synchronising historical intelligence feed..."):
    reports_data, error = fetch_recent_reports(limit=7)

if error or not reports_data:
    st.error(error or "No data available.")
    st.stop()

# Build timeline data
timeline_data = []
for name, content in reports_data:
    # On sécurise l'extraction de la date via Regex pour ignorer le texte parasite
    match = re.search(r'(\d{4}[-_]\d{2}[-_]\d{2})', name)
    if match:
        date_str = match.group(1).replace("_", "-")
    else:
        date_str = name.replace(".md", "") # Fallback
        
    day_incidents = parse_incidents(content)
    score = calculate_daily_score(day_incidents)
    timeline_data.append({"Date": date_str, "Filename": name, "Score": score, "Incidents": len(day_incidents)})

df_timeline = pd.DataFrame(timeline_data)
# L'ajout de errors='coerce' transforme les dates invalides en NaT sans faire planter l'application
df_timeline['Date'] = pd.to_datetime(df_timeline['Date'], format='mixed', errors='coerce')
# On supprime les lignes où la date n'a pas pu être parsée
df_timeline = df_timeline.dropna(subset=['Date'])
df_timeline = df_timeline.sort_values(by="Date") # Sort chronologically for the chart
avg_7d_score = df_timeline['Score'].mean()

# --- SIDEBAR: HISTORY SELECTION ---
with st.sidebar:
    st.title("📅 Intelligence Archive")
    st.caption("Select a date to view the strategic assessment.")
    report_options = [r['Filename'] for r in timeline_data]
    selected_filename = st.radio("Past 7 Days", report_options, label_visibility="collapsed")
    
    st.markdown("---")
    st.markdown("### 🧮 CRQ Methodology")
    st.info("The **Composite Threat Score (0-100)** is calculated deterministically via Python, independent of AI.\n\n"
            "- **Base Score:** 10 pts per incident.\n"
            "- **Zero-Day Modifier:** +15 pts.\n"
            "- **Ransomware/APT Modifier:** +10 pts.\n"
            "The **Trend** compares today's score against the 7-day moving average.")

# Get the content for the selected date
selected_row = next(r for r in timeline_data if r['Filename'] == selected_filename)
selected_content = next(content for name, content in reports_data if name == selected_filename)
report_date_clean = selected_filename.replace(".md", "").replace("_", " ")

incidents = parse_incidents(selected_content)
current_score = selected_row['Score']

st.title("Strategic Cyber Threat Briefing")
st.caption(f"Executive assessment for **{report_date_clean}** | {len(incidents)} actionable incidents analyzed")
st.divider()

# --- DATAVIZ ROW (PLOTLY) ---
col_gauge, col_trend = st.columns([1, 2])

with col_gauge:
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = current_score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Composite Threat Score", 'font': {'size': 20}},
        delta = {'reference': avg_7d_score, 'increasing': {'color': "red"}, 'decreasing': {'color': "green"}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "rgba(0,0,0,0)"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 33], 'color': "#00915A"},
                {'range': [33, 66], 'color': "#ff9800"},
                {'range': [66, 100], 'color': "#e53935"}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': current_score
            }
        }
    ))
    fig_gauge.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig_gauge, use_container_width=True)

with col_trend:
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(
        x=df_timeline['Date'], 
        y=df_timeline['Score'],
        mode='lines+markers',
        name='Daily Score',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8)
    ))
    fig_line.add_trace(go.Scatter(
        x=df_timeline['Date'], 
        y=[avg_7d_score]*len(df_timeline),
        mode='lines',
        name='7-Day Baseline',
        line=dict(color='gray', width=2, dash='dash')
    ))
    fig_line.update_layout(
        title="7-Day Historical Threat Baseline",
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis_title="",
        yaxis_title="Threat Score",
        yaxis_range=[0, 100]
    )
    st.plotly_chart(fig_line, use_container_width=True)


# AI Generation
condensed_report = ""
for inc in incidents:
    condensed_report += f"- TITLE: {inc['preview']}\n"
    if inc['country']: condensed_report += f"  TARGETS: {inc['country']} / {inc['companies']}\n"
    condensed_report += f"  SUMMARY: {inc['overview']}\n\n"

with st.spinner(f"🧠 Synthesizing executive brief for {report_date_clean}..."):
    auth_ctx = init_llm_auth()
    brief, debug_logs = generate_executive_brief(condensed_report, report_date_clean, auth_ctx)

# --- THE BLUF & PILLARS ---
if brief and isinstance(brief, dict) and "bluf" in brief:
    
    with st.container(border=True):
        st.subheader("Bottom Line Up Front")
        st.info(brief.get('bluf', ''))
    
    st.write("")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container(border=True):
            st.markdown("#### 🌍 Threat Landscape")
            st.markdown(format_bullets(brief.get("threat_landscape", "—")))
    with col2:
        with st.container(border=True):
            st.markdown("#### 📉 Business Exposure")
            st.markdown(format_bullets(brief.get("business_impact", "—")))
    with col3:
        with st.container(border=True):
            st.markdown("#### 🛡️ Strategic Imperatives")
            st.markdown(format_bullets(brief.get("recommendations", "—")))

else:
    st.error("🚨 The AI pipeline failed for this specific date.")
    if st.button("🔄 Retry Generation"):
        generate_executive_brief.clear()
        st.rerun()
    if debug_logs:
        for log in debug_logs:
            with st.expander(f"❌ Echec sur {log['model']}"):
                st.error(f"{log['error']}")
                st.code(log['raw_response'], language="json")

# --- TECHNICAL APPENDIX ---
st.write("")
st.subheader("📋 Restricted Access: Incident Deep Dive")

if not incidents:
    st.info("No actionable intelligence detected for this date.")
else:
    for sub in incidents:
        with st.expander(f"🔎 {sub['preview']}"):
            st.markdown(f"**📍 Target Country:** {sub['country'] or 'N/A'} | **🏢 Target Sector:** {sub['companies'] or 'N/A'}")
            st.divider()
            
            if sub['overview']: st.markdown(f"**Operational Overview:**\n{sub['overview']}")
            if sub['breach']: st.markdown(f"**Technical Vector:**\n{sub['breach']}")
            if sub['impact']: st.markdown(f"**Consequences:**\n{sub['impact']}")
            if sub['control']: st.markdown(f"**Mitigation:**\n{sub['control']}")
            if sub['link']: st.markdown(f"\n[🔗 Original Intel Source]({sub['link']})")

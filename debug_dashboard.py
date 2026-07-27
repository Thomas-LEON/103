import streamlit as st
import json
import re
import traceback

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

# =====================================================================
# DESIGN SYSTEM (Corporate Neutral — Emerald Accent)
# =====================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    .stApp { background-color: #f4f6f8; font-family: 'Inter', sans-serif; }
    h1, h2, h3, h4, p, span, div { font-family: 'Inter', sans-serif; }

    /* Header */
    .dashboard-header { padding: 15px 0 25px 0; }
    .dashboard-header h1 { font-size: 2.2rem; font-weight: 800; color: #1a1a1a; margin-bottom: 2px; }
    .dashboard-header p { color: #6c757d; font-size: 1rem; margin-top: 0; }

    /* Top Row Layout */
    .top-row { display: flex; gap: 20px; margin-bottom: 30px; align-items: stretch; }
    
    /* Traffic Light & Trend Box */
    .status-box {
        flex: 0 0 280px; padding: 25px 20px; border-radius: 8px;
        display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); color: white;
    }
    .status-box.red { background: linear-gradient(135deg, #d32f2f, #e53935); }
    .status-box.amber { background: linear-gradient(135deg, #f57c00, #ff9800); }
    .status-box.green { background: linear-gradient(135deg, #388e3c, #4caf50); }
    .status-box h2 { margin: 0; font-size: 1.8rem; font-weight: 800; color: white; }
    .status-box .trend { font-size: 1rem; font-weight: 600; margin-top: 8px; opacity: 0.9; }

    /* BLUF Box */
    .bluf-box {
        flex: 1; padding: 25px 30px; border-radius: 8px; background-color: white;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        display: flex; flex-direction: column; justify-content: center;
        border-left: 4px solid #00915A;
    }
    .bluf-box h3 { margin: 0 0 10px 0; font-size: 0.9rem; text-transform: uppercase; color: #6c757d; font-weight: 700; letter-spacing: 1px; }
    .bluf-box p { margin: 0; font-size: 1.3rem; font-weight: 600; color: #1a1a1a; line-height: 1.5; }

    /* Pillar Cards */
    .pillar-card {
        background-color: white; border-radius: 8px; padding: 25px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03); height: 100%; 
    }
    .pillar-card h4 {
        font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px;
        color: #00915A; margin-bottom: 15px; font-weight: 700;
        display: flex; align-items: center; gap: 8px;
    }
    .pillar-card .pillar-body { font-size: 0.95rem; line-height: 1.7; color: #333; }

    /* Section Titles */
    .section-title {
        font-size: 1.1rem; font-weight: 700; color: #1a1a1a;
        margin-top: 40px; margin-bottom: 20px;
    }

    /* Expander styling */
    .streamlit-expanderHeader { font-weight: 600; font-size: 1.05rem; color: #2D2D2D; background-color: white; border-radius: 6px; }
    
    /* Metadata tags */
    .meta-tag {
        display: inline-block; background-color: #f1f3f5; color: #495057;
        padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; margin-right: 8px;
        font-weight: 600; border: 1px solid #e9ecef;
    }

    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
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
# ⚙️ 2. NATIVE MARKDOWN PARSER
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

# =====================================================================
# 🧠 3. AI ENGINE
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
  "traffic_light": "RED",
  "trend": "Trending Up",
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
                    "traffic_light": extract_key_recursive(parsed, ["traffic_light", "status", "level"]) or "AMBER",
                    "trend": extract_key_recursive(parsed, ["trend", "trending", "direction"]) or "Stable",
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
    if isinstance(data_item, list): return "<br>".join([f"• {item}" for item in data_item])
    return str(data_item).replace("\n", "<br>")

# =====================================================================
# 🖥️ 4. USER INTERFACE (V7)
# =====================================================================
with st.spinner("Synchronising historical intelligence feed..."):
    reports_data, error = fetch_recent_reports(limit=7)

if error or not reports_data:
    st.error(error or "No data available.")
    st.stop()

# --- SIDEBAR: HISTORY SELECTION ---
st.sidebar.markdown("### 📅 Intelligence Archive")
st.sidebar.markdown("Select a date to view the strategic assessment for that day.")

report_options = [r[0] for r in reports_data]
selected_filename = st.sidebar.radio("Past 7 Days", report_options)

# Get the content for the selected date
selected_content = next(content for name, content in reports_data if name == selected_filename)
report_date_clean = selected_filename.replace(".md", "").replace("_", " ")

incidents = parse_incidents(selected_content)

st.markdown(f"""
<div class="dashboard-header">
    <h1>Strategic Cyber Threat Briefing</h1>
    <p>Executive assessment for <b>{report_date_clean}</b> | {len(incidents)} severe incidents analyzed</p>
</div>
""", unsafe_allow_html=True)

# Context reduction
condensed_report = ""
for inc in incidents:
    condensed_report += f"- TITLE: {inc['preview']}\n"
    if inc['country']: condensed_report += f"  TARGETS: {inc['country']} / {inc['companies']}\n"
    condensed_report += f"  SUMMARY: {inc['overview']}\n\n"

# AI Generation for the SELECTED report
with st.spinner(f"🧠 Synthesizing executive brief for {report_date_clean}..."):
    auth_ctx = init_llm_auth()
    brief, debug_logs = generate_executive_brief(condensed_report, report_date_clean, auth_ctx)

# --- THE TOP ROW (F-Pattern) ---
if brief and isinstance(brief, dict) and "bluf" in brief:
    
    tl = str(brief.get("traffic_light", "AMBER")).upper()
    if "RED" in tl:
        status_class, status_title, icon = "red", "CRITICAL RISK", "🚨"
    elif "GREEN" in tl:
        status_class, status_title, icon = "green", "STABLE", "✅"
    else:
        status_class, status_title, icon = "amber", "ELEVATED RISK", "⚠️"
        
    trend = str(brief.get("trend", "Stable")).title()
    if "Up" in trend or "Hausse" in trend: trend_icon = "📈 Trending Up"
    elif "Down" in trend or "Baisse" in trend: trend_icon = "📉 Trending Down"
    else: trend_icon = "➡️ Stable"

    st.markdown(f"""
    <div class="top-row">
        <div class="status-box {status_class}">
            <h2>{icon} {status_title}</h2>
            <div class="trend">{trend_icon}</div>
        </div>
        <div class="bluf-box">
            <h3>Bottom Line Up Front (BLUF)</h3>
            <p>{brief.get('bluf', '')}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="pillar-card"><h4>🌍 Threat Landscape</h4><div class="pillar-body">{format_bullets(brief.get("threat_landscape", "—"))}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="pillar-card"><h4>📉 Business Exposure</h4><div class="pillar-body">{format_bullets(brief.get("business_impact", "—"))}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="pillar-card"><h4>🛡️ Strategic Imperatives</h4><div class="pillar-body">{format_bullets(brief.get("recommendations", "—"))}</div></div>', unsafe_allow_html=True)

else:
    st.error("🚨 The AI pipeline failed for this specific date. See autopsy reports below.")
    if st.button("🔄 Retry Generation"):
        generate_executive_brief.clear()
        st.rerun()
    if debug_logs:
        for log in debug_logs:
            with st.expander(f"❌ Echec sur {log['model']}"):
                st.error(f"{log['error']}")
                st.code(log['raw_response'], language="json")

# --- TECHNICAL APPENDIX ---
st.markdown('<div class="section-title">Restricted Access: Incident Deep Dive</div>', unsafe_allow_html=True)

if not incidents:
    st.info("No actionable intelligence detected for this date.")
else:
    for sub in incidents:
        with st.expander(f"🔎 {sub['preview']}"):
            tags_html = ""
            if sub['country']: tags_html += f'<span class="meta-tag">📍 {sub["country"]}</span>'
            if sub['companies']: tags_html += f'<span class="meta-tag">🏢 {sub["companies"]}</span>'
            if tags_html: st.markdown(f"<div style='margin-bottom:15px;'>{tags_html}</div>", unsafe_allow_html=True)
            
            if sub['overview']: st.markdown(f"**Operational Overview:**\n{sub['overview']}")
            if sub['breach']: st.markdown(f"**Technical Vector:**\n{sub['breach']}")
            if sub['impact']: st.markdown(f"**Consequences:**\n{sub['impact']}")
            if sub['control']: st.markdown(f"**Mitigation:**\n{sub['control']}")
            if sub['link']: st.markdown(f"\n[🔗 Original Intel Source]({sub['link']})")

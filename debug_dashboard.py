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
    page_title="Daily Cyber Threat Briefing",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
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
    .dashboard-header {
        padding: 30px 0 10px 0;
    }
    .dashboard-header h1 {
        font-size: 2.2rem; font-weight: 800; color: #1a1a1a; margin-bottom: 2px;
    }
    .dashboard-header p {
        color: #6c757d; font-size: 1rem; margin-top: 0;
    }

    /* Traffic Light Banner */
    .traffic-banner {
        padding: 18px 25px; border-radius: 6px; margin-bottom: 30px;
        display: flex; align-items: center; gap: 15px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .traffic-banner .dot {
        width: 16px; height: 16px; border-radius: 50%; display: inline-block;
        box-shadow: 0 0 8px currentColor;
    }
    .traffic-banner .label {
        font-weight: 700; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px;
    }
    .traffic-banner .bluf-text {
        font-size: 1.05rem; line-height: 1.6; margin-top: 8px;
    }
    .banner-red    { background-color: #fff5f5; border-left: 5px solid #dc3545; }
    .banner-red .dot { background-color: #dc3545; color: #dc3545; }
    .banner-red .label { color: #dc3545; }
    .banner-amber  { background-color: #fff9e6; border-left: 5px solid #e6a817; }
    .banner-amber .dot { background-color: #e6a817; color: #e6a817; }
    .banner-amber .label { color: #e6a817; }
    .banner-green  { background-color: #f0faf4; border-left: 5px solid #00915A; }
    .banner-green .dot { background-color: #00915A; color: #00915A; }
    .banner-green .label { color: #00915A; }

    /* Pillar Cards */
    .pillar-card {
        background-color: white; border-radius: 6px; padding: 22px 25px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05); height: 100%; 
        border-top: 4px solid #00915A;
    }
    .pillar-card h4 {
        font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.8px;
        color: #6c757d; margin-bottom: 12px; font-weight: 600;
    }
    .pillar-card .pillar-body {
        font-size: 0.95rem; line-height: 1.7; color: #2D2D2D;
    }

    /* Section Titles */
    .section-title {
        font-size: 1.1rem; font-weight: 700; color: #1a1a1a;
        margin-top: 35px; margin-bottom: 15px;
        padding-bottom: 8px; border-bottom: 2px solid #00915A;
        display: inline-block;
    }

    /* Expander styling */
    .streamlit-expanderHeader { font-weight: 600; font-size: 1.05rem; color: #2D2D2D; }
    
    /* Metadata tags */
    .meta-tag {
        display: inline-block; background-color: #e9ecef; color: #495057;
        padding: 3px 10px; border-radius: 3px; font-size: 0.8rem; margin-right: 6px;
        font-weight: 500;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# =====================================================================
# 📡 1. DATA FETCHING (Chrome Headless)
# =====================================================================
@st.cache_data(ttl=1800)
def fetch_latest_report():
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
            return None, "No reports found in the repository."
            
        md_files.sort(key=lambda x: x['name'], reverse=True)
        latest_file = md_files[0]
        
        driver.get(latest_file['download_url'])
        content = driver.find_element("tag name", "body").text
        return latest_file['name'], content
    except Exception as e:
        return None, f"Data sync error: {str(e)}"
    finally:
        if driver:
            driver.quit()

# =====================================================================
# ⚙️ 2. NATIVE MARKDOWN PARSER (Python)
# =====================================================================
def parse_incidents(content):
    subjects = []
    sections = re.split(r'## Titre de l\'incident\s*:', content)
    
    for section in sections[1:]:
        lines = section.strip().split('\n')
        if not lines: continue
        
        preview = lines[0].strip()
        
        country_match = re.search(r'\*\*Impacted Country:\*\*\s*(.*?)\n', section)
        country = country_match.group(1).strip() if country_match else ""
        
        companies_match = re.search(r'\*\*List of Companies Impacted:\*\*\s*(.*?)\n', section)
        companies = companies_match.group(1).strip() if companies_match else ""
        
        overview_match = re.search(r'\*\*Overview\*\*\n(.*?)(?=\n\*\*)', section, re.DOTALL)
        overview = overview_match.group(1).strip() if overview_match else ""
        
        breach_match = re.search(r'\*\*The Breach Mechanism\*\*\n(.*?)(?=\n\*\*)', section, re.DOTALL)
        breach = breach_match.group(1).strip() if breach_match else ""
        
        impact_match = re.search(r'\*\*Impact and Consequences\*\*\n(.*?)(?=\n\*\*)', section, re.DOTALL)
        impact = impact_match.group(1).strip() if impact_match else ""
        
        control_match = re.search(r'\*\*Proposed Control.*?\*\*\n(.*?)(?=\n\*\*|$)', section, re.DOTALL)
        control = control_match.group(1).strip() if control_match else ""
        
        link_match = re.search(r'(https?://[^\s]+)', section)
        link = link_match.group(1).strip() if link_match else ""
        
        subjects.append({
            "preview": preview, "country": country, "companies": companies,
            "overview": overview, "breach": breach, "impact": impact,
            "control": control, "link": link
        })
    return subjects



# =====================================================================
# 🧠 3. AI ENGINE (MODE INDESTRUCTIBLE - EXTRACTION RÉCURSIVE)
# =====================================================================
@st.cache_resource
def init_llm_auth():
    return get_auth_context()

def extract_key_recursive(data, target_key):
    """ Cherche une clé n'importe où dans le JSON, peu importe la profondeur (Même dans les listes) """
    target = str(target_key).lower()
    if isinstance(data, dict):
        # 1. Cherche dans le niveau actuel
        for k, v in data.items():
            if str(k).lower() == target:
                return v
        # 2. Si pas trouvé, creuse dans les sous-dossiers
        for v in data.values():
            res = extract_key_recursive(v, target)
            if res is not None: return res
    elif isinstance(data, list):
        # 3. Si c'est une liste (comme 'executiveBrief:[...]'), on fouille chaque élément
        for item in data:
            res = extract_key_recursive(item, target)
            if res is not None: return res
    return None

@st.cache_data(ttl=86400)
def generate_executive_brief(condensed_text, _auth_context):
    models_to_try = ["gpt-oss-120b", "mistral-medium-3.5-ITG", "gemma-4-26b"]
    
    system_prompt = """You are a senior Cyber Threat Intelligence analyst writing a daily brief for the Board of Directors.
    Analyze the provided summary of today's incidents and produce ONLY a valid JSON object. No greetings, no markdown, just the JSON braces.

    ABSOLUTE RULES:
    - Write everything in ENGLISH.
    - Use BUSINESS language. NEVER use technical jargon (no CVE numbers, no hashes).
    - Be concise and impactful. Executives have 30 seconds.

    STRICT JSON STRUCTURE:
    {
      "traffic_light": "RED or AMBER or GREEN",
      "bluf": "One or two sentences. The single most important takeaway for the board.",
      "threat_landscape": ["Bullet point 1", "Bullet point 2"],
      "business_impact": ["Bullet point 1", "Bullet point 2"],
      "recommendations": ["Bullet point 1", "Bullet point 2"]
    }
    """
    
    debug_logs = []
    
    for model_id in models_to_try:
        log_entry = {"model": model_id, "raw_response": "Aucune réponse", "error": None, "stage": "Initialisation"}
        
        try:
            log_entry["stage"] = "1. Appel API"
            chat = LLMChat(model_id=model_id, auth_context=_auth_context, high_reasoning_effort=True, web_search=False)
            chat.messages.append({"type": "plain", "role": "system", "content": system_prompt})
            
            raw = chat.say(f"Produce the executive brief JSON for these incidents:\n\n{condensed_text}")
            log_entry["raw_response"] = raw
            
            log_entry["stage"] = "2. Nettoyage Markdown"
            clean_json_str = ""
            block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw, re.DOTALL | re.IGNORECASE)
            
            if block_match:
                clean_json_str = block_match.group(1)
            else:
                fallback_match = re.search(r'\{.*\}', raw, re.DOTALL)
                clean_json_str = fallback_match.group(0) if fallback_match else raw

            log_entry["stage"] = "3. Décodage JSON"
            parsed = json.loads(clean_json_str)
            
            log_entry["stage"] = "4. Validation et Extraction Intelligente"
            # On lance notre chien renifleur pour trouver le 'bluf' n'importe où
            bluf_val = extract_key_recursive(parsed, "bluf")
            
            if bluf_val:
                # On reconstruit manuellement le dictionnaire parfait pour le reste du script !
                final_brief = {
                    "traffic_light": extract_key_recursive(parsed, "traffic_light") or "AMBER",
                    "bluf": bluf_val,
                    "threat_landscape": extract_key_recursive(parsed, "threat_landscape") or [],
                    "business_impact": extract_key_recursive(parsed, "business_impact") or [],
                    "recommendations": extract_key_recursive(parsed, "recommendations") or []
                }
                return final_brief, debug_logs
            else:
                log_entry["error"] = "La clé 'bluf' est introuvable, même en cherchant dans les sous-dossiers."
                
        except Exception as e:
            log_entry["error"] = f"CRASH à l'étape [{log_entry['stage']}] : {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            
        debug_logs.append(log_entry)
            
    return None, debug_logs

# Helper function
def format_bullets(data_item):
    if isinstance(data_item, list):
        return "<br>".join([f"• {item}" for item in data_item])
    return str(data_item).replace("\n", "<br>")
# =====================================================================
# 🖥️ 4. USER INTERFACE (AVEC CONSOLE DE DEBUG AVANCÉE)
# =====================================================================

st.markdown("""
<div class="dashboard-header">
    <h1>🎯 Daily Cyber Threat Briefing</h1>
    <p>Strategic overview of global cyber threats and their operational impact.</p>
</div>
""", unsafe_allow_html=True)

with st.spinner("Synchronising intelligence feed..."):
    filename, content = fetch_latest_report()

if not filename:
    st.error(content)
    st.stop()

incidents = parse_incidents(content)
report_date = filename.replace(".md", "").replace("_", " ")
st.caption(f"📅 Source: `{filename}` — {len(incidents)} incident(s) identified")

# Context reduction
condensed_report = ""
for inc in incidents:
    condensed_report += f"- TITLE: {inc['preview']}\n"
    if inc['country']: condensed_report += f"  TARGETS: {inc['country']} / {inc['companies']}\n"
    condensed_report += f"  SUMMARY: {inc['overview']}\n\n"

# AI Generation
with st.spinner("🧠 AI is drafting the Executive Summary (Context Reduced)..."):
    auth_ctx = init_llm_auth()
    brief, debug_logs = generate_executive_brief(condensed_report, auth_ctx)

# =====================================================================
# SECTION A & B — THE BLUF + PILLARS
# =====================================================================
if brief and isinstance(brief, dict) and "bluf" in brief:
    
    tl = str(brief.get("traffic_light", "AMBER")).upper()
    if "RED" in tl:
        banner_class, tl_label = "banner-red", "HIGH THREAT"
    elif "GREEN" in tl:
        banner_class, tl_label = "banner-green", "LOW THREAT"
    else:
        banner_class, tl_label = "banner-amber", "ELEVATED THREAT"
    
    st.markdown(f"""
    <div class="traffic-banner {banner_class}">
        <div>
            <span class="dot"></span>&nbsp;
            <span class="label">{tl_label}</span>
            <div class="bluf-text">{brief.get('bluf', '')}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="section-title">📊 Strategic Assessment</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f'<div class="pillar-card"><h4>🌍 Threat Landscape</h4><div class="pillar-body">{format_bullets(brief.get("threat_landscape", "—"))}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="pillar-card"><h4>📉 Business & Operational Impact</h4><div class="pillar-body">{format_bullets(brief.get("business_impact", "—"))}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="pillar-card"><h4>🛡️ Actionable Intelligence</h4><div class="pillar-body">{format_bullets(brief.get("recommendations", "—"))}</div></div>', unsafe_allow_html=True)

else:
    st.error("🚨 The AI pipeline completely failed. See autopsy reports below.")
    if st.button("🔄 Clear Cache & Retry"):
        generate_executive_brief.clear()
        st.rerun()
        
    st.markdown("### 🔍 AI Autopsy Reports")
    # Affichage de tous les rapports de plantage modèle par modèle
    if debug_logs:
        for log in debug_logs:
            with st.expander(f"❌ Echec sur {log['model']} - A planté à : {log['stage']}"):
                st.error(f"**Error Details:**\n\n{log['error']}")
                st.markdown("**Raw Output from AI:**")
                st.code(log['raw_response'], language="json")

# =====================================================================
# SECTION C — TECHNICAL APPENDIX (Expanders)
# =====================================================================
st.markdown('<div class="section-title">📋 Incident Deep Dive — Technical Appendix</div>', unsafe_allow_html=True)

if not incidents:
    st.info("No incidents detected in the expected Markdown format.")
else:
    for sub in incidents:
        with st.expander(f"🚨 {sub['preview']}"):
            tags_html = ""
            if sub['country']:
                tags_html += f'<span class="meta-tag">🌍 {sub["country"]}</span>'
            if sub['companies']:
                tags_html += f'<span class="meta-tag">🏢 {sub["companies"]}</span>'
            if tags_html:
                st.markdown(f"<div style='margin-bottom:15px;'>{tags_html}</div>", unsafe_allow_html=True)
            
            if sub['overview']:
                st.markdown(f"**Overview**\n\n{sub['overview']}")
            if sub['breach']:
                st.markdown(f"**Breach Mechanism**\n\n{sub['breach']}")
            if sub['impact']:
                st.markdown(f"**Impact & Consequences**\n\n{sub['impact']}")
            if sub['control']:
                st.markdown(f"**Proposed Controls**\n\n{sub['control']}")
            if sub['link']:
                st.markdown(f"\n[🔗 Read the full source article]({sub['link']})")

st.markdown("<br>", unsafe_allow_html=True)
st.divider()
with st.expander("⚙️ View Raw Intelligence Report"):
    st.markdown(content)

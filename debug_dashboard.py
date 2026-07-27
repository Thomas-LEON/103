
Review
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

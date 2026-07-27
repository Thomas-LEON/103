# Standard Operating Procedure (SOP): Executive CTI Dashboard

## 1. Project Objective
The **Executive Threat Intel Dashboard** is designed to automatically transform technical Cyber Threat Intelligence (CTI) reports into a strategic, high-level dashboard tailored for C-Level executives and the Board of Directors.

It utilizes a hybrid approach:
- **Native Python** for the reliable extraction of technical incident data.
- **Artificial Intelligence (LLM)** to translate technical risks into business impacts (using the *BLUF - Bottom Line Up Front* model).

---

## 2. Technical Architecture
The project is built on 3 main pillars:

1. **User Interface (Streamlit):** 
   - Main file: `executive_dashboard.py`.
   - Provides an interactive, neutral, and responsive web interface (Corporate Design).
2. **Scraping & Connectivity (Selenium):** 
   - Due to corporate proxy restrictions, standard HTTP requests (`requests`) are blocked. The script bypasses this by using a Chrome browser in "Headless" mode via Selenium to read the public GitHub repository seamlessly.
3. **Artificial Intelligence Engine (llm.py):** 
   - Class file: `llm.py`.
   - Manages network authentication and requests to the internal LLM API.
   - Primary model: `gpt-oss-120b` (includes a fallback system to other models in case of timeouts or overload).

---

## 3. Prerequisites & Environment Setup
Before launching the project on a new machine, the following elements must be configured:

### A. Python Dependencies
```bash
pip install streamlit selenium requests pyyaml
```

### B. ChromeDriver Configuration
Selenium requires a `chromedriver.exe` executable that strictly matches the version of Google Chrome installed on the host machine.
1. Download ChromeDriver: https://googlechromelabs.github.io/chrome-for-testing/
2. Create an `app_config.yaml` file at the root of the project containing the absolute path to the executable:
```yaml
paths:
  chromedriver: "C:\\Path\\To\\chromedriver.exe"
```

### C. Target GitHub Structure
The script monitors the repository: `https://api.github.com/repos/Thomas-LEON/news-tracker/contents/reports`.
The reports must be in Markdown (`.md`) format and strictly adhere to the following tags for the native Python parser to function correctly:
- `## Titre de l'incident :`
- `**Impacted Country:**`
- `**List of Companies Impacted:**`
- `**Overview**`
- `**The Breach Mechanism**`
- `**Impact and Consequences**`
- `**Proposed Control: Mitigating Threats**`

---

## 4. Execution Procedure (Run)

To start the Dashboard locally:
1. Open a terminal (PowerShell or CMD).
2. Navigate to the project directory.
3. Execute the following command:
```bash
streamlit run executive_dashboard.py
```
4. The browser will automatically open at `http://localhost:8501`.

*Note: The initial load may take 1 to 2 minutes (downloading the report via Selenium + AI reasoning time). Thanks to the Streamlit cache, subsequent refreshes will be instantaneous for 24 hours.*

---

## 5. Maintenance & Troubleshooting

### Error: "The AI could not generate a valid brief"
**Cause:** The AI generated an invalid JSON (e.g., missing comma) or refused to answer in the expected format.
**Solution:** 
1. Check the content of the `🛠️ Debug: Raw AI Response` box at the bottom of the page to identify the exact Python parsing error.
2. Click the **"🔄 Retry AI Generation"** button to force the AI to try again (or press the `C` key on the keyboard > *Clear Cache*).

### Error: "Chrome Error: Message: session not created"
**Cause:** The Google Chrome browser on the host was updated, making the current `chromedriver.exe` obsolete.
**Solution:**
1. Check the current Chrome version (`Settings > About Chrome`).
2. Download the matching `chromedriver` version.
3. Replace the old `.exe` defined in the `app_config.yaml`.

### The Interface displays yesterday's report
**Cause:** The Streamlit cache has not yet expired (TTL set to 30 minutes for the GitHub fetch).
**Solution:** On the web page, press the `C` key and click on **"Clear Cache"** to force a new synchronization with the GitHub repository.

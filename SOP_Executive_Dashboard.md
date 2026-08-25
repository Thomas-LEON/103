# Standard Operating Procedure (SOP): Executive CTI Dashboard (V6)

## 1. Project Objective
The **Executive Threat Intel Dashboard** is designed to automatically transform technical Cyber Threat Intelligence (CTI) reports into a strategic, high-level dashboard tailored for C-Level executives and the Board of Directors.

It utilizes a highly optimized hybrid approach:
- **Native Python** for the reliable extraction of technical incident data and context reduction.
- **Artificial Intelligence (LLM)** to translate condensed risks into business impacts (using the *BLUF - Bottom Line Up Front* model).

---

## 2. Technical Architecture & V6 Optimizations
The project is built on 4 main pillars:

1. **User Interface (Streamlit):** 
   - Main file: `executive_dashboard.py`.
   - Provides an interactive, neutral, and responsive web interface (Corporate Design).
2. **Scraping & Connectivity (Selenium):** 
   - Bypasses corporate proxy restrictions using a Chrome browser in "Headless" mode via Selenium to read the public GitHub repository seamlessly.
3. **Context Reduction Engine (Python):**
   - **Optimization:** Sending a full technical report to an LLM causes token limit timeouts (or excessive latency). The script natively parses the Markdown and generates a condensed string (Title, Country, Overview only). This reduces API token consumption by over 80%.
4. **Indestructible AI Engine (llm.py):** 
   - **Unified Mega-Prompt:** Prevents the LLM from acting as a simple data parser by merging strict business instructions, a one-shot JSON example, and the data into a single prompt.
   - **Recursive Key Extraction:** The system uses a recursive search algorithm with synonym matching (e.g., `bluf`, `summary`, `bottom_line`). This makes the dashboard 100% immune to LLM JSON structure hallucinations (e.g., if the LLM nests the response inside random keys).

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
The reports must be in Markdown (`.md`) format and strictly adhere to the following tags:
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

*Note: The initial load may take 30 to 60 seconds (downloading the report via Selenium + AI reasoning time). Thanks to the Streamlit cache, subsequent refreshes will be instantaneous for 24 hours.*

---

## 5. Maintenance & Troubleshooting

### Error: "The AI pipeline completely failed. See autopsy reports below."
**Cause:** All 3 fallback AI models failed to generate a valid response, either due to a network timeout or a severe JSON hallucination.
**Solution:** 
1. Open the `❌ Echec sur [model]` expanders at the bottom of the page.
2. The **Error Details** section will pinpoint the exact step of failure:
   - *Step 1 (Appel API):* Corporate network or proxy blocked the LLM request.
   - *Step 4 (Extraction):* The LLM hallucinated so badly that even the recursive synonym matcher could not find the required keys. Read the `Raw Output from AI` box to see what words the AI actually used.
3. Click the **"🔄 Clear Cache & Retry"** button to force a new generation.

### Error: "Chrome Error: Message: session not created"
**Cause:** The Google Chrome browser on the host was updated, making the current `chromedriver.exe` obsolete.
**Solution:** Download the matching `chromedriver` version and update the path in `app_config.yaml`.

### The Interface displays yesterday's report
**Cause:** The Streamlit cache has not yet expired.
**Solution:** On the web page, press the `C` key and click on **"Clear Cache"** to force a new synchronization with the GitHub repository.

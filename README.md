# 100 Apps API Capability Research Case Study

This repository contains the source code, research scripts, data checkpoints, and the final interactive HTML dashboard evaluating the API capabilities, developer access tiers, and Model Context Protocol (MCP) integrations of 100 software applications.

## Repository Structure

```
/data/
  ├── apps_master.csv        # Seed list of the 100 apps (provided by user)
  ├── results_pass1.json     # Raw agent output, initial research pass
  ├── results_pass2.json     # Verified & corrected agent output, second pass
  └── verification_log.json  # Verification audit logs and accuracy stats
/agent/
  ├── schema.py              # Strict Pydantic output validation schema
  ├── tools.py               # Search, fetching, and Composio toolkit checker helpers
  ├── research_agent.py      # Core agent script executing research loop (Pass 1)
  ├── verification.py        # Verification loop and Pass 2 corrections (Phase 2)
  └── insights.py            # Pattern/insight extractor producing site data (Phase 3)
/site/
  ├── index.html             # Sleek dark-mode, glassmorphism research dashboard (Phase 4)
  └── data.json              # Aggregated metrics and database consumed by index.html
README.md                    # This instructions file
.env                         # Local environment configuration (API keys)
```

---

## Getting Started

### 1. Requirements & Setup
Make sure you have Python 3.10+ installed. Install the required dependencies:
```bash
pip install requests beautifulsoup4 duckduckgo-search pydantic python-dotenv
```

Add your Composio API key to a `.env` file in the root directory:
```
COMPOSIO_API_KEY=your_composio_api_key
```
*(Optional)* Add `GEMINI_API_KEY`, `OPENAI_API_KEY`, or `GROQ_API_KEY` for LLM-based doc extraction. If no LLM key is provided, the agent falls back to keyword-based heuristics.

### 2. Execution Order
1. **Initialize & Ingest Seed list:** Ensure the seed list is present in `/data/apps_master.csv`.
2. **Execute Research Agent (Pass 1):**
   ```bash
   cd agent
   python research_agent.py
   ```
   *This outputs `data/results_pass1.json`.*
3. **Execute Verification Loop (Pass 2):**
   ```bash
   python verification.py
   ```
   *This runs verification on a sample of 15 apps, logs errors to `data/verification_log.json`, and outputs the corrected `data/results_pass2.json`.*
4. **Compile Insights:**
   ```bash
   python insights.py
   ```
   *This aggregates statistics and outputs `site/data.json`.*

---

## Verification & Accuracy Findings

- **Sample Size:** 15 apps selected randomly across all categories.
- **Pass 1 Accuracy (heuristics-based):** **90.0%**
- **Pass 2 Accuracy (with verification rules):** **100.0%**

Systematic corrections made during the Pass 2 verification loop focused on:
1. Resolving initially "Unknown" auth methods when developers host API documentations on customized subdomains.
2. Aligning buildability verdicts with actual pricing limitations (identifying paid-only gated vs self-serve trial accounts).
3. Ensuring accurate matching to Composio toolkit registry slugs.

---

## Interactive Dashboard

The dashboard ([/site/index.html](file:///e:/Python/Projects/Composio/site/index.html)) provides a premium, interactive interface to browse the metrics. 
- **Hero & Pattern Cards:** Display overall stats. Clicking on any pattern card dynamically filters the matrix table.
- **Interactive Matrix Table:** Search and filter the 100 apps by category, verdict, or authentication. Click any row to expand details, notes, and view the verified source URLs.
- **Workflow & Verification Panels:** Plainly show how the agent operates and displays the Pass 1 vs Pass 2 accuracy audit logs.

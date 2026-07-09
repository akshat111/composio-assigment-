# Human Intervention Analysis Report

**Auditor Role:** Human Intervention Analysis Agent  
**Audit Target:** 100 Apps Research Pipeline Automation vs. Human Dependency Audit

---

## 1. Summary of Human Interventions

While the research pipeline operated with a high level of automation (crawling, searching, and schema fitting), human operators intervened at critical logical and validation stages to ensure data accuracy and resolve script exceptions.

### Work Ratio Estimate:
*   **Automated Work (AI Script):** **85%** (Running 100 searches, fetching HTML pages, parsing structures, querying Composio toolkit API, compiling JSON metrics, generating charts and tables).
*   **Manual/Human Work:** **15%** (Resolving scraper error crashes, manual sampling validation, defining the systematic correction rules, and compiling verified document URL/descriptions mappings).

---

## 2. Detailed Human Interventions

### 1. Verification of Gated Sandboxes (HubSpot & QuickBooks)
*   **Problem:** The research agent flagged HubSpot and QuickBooks as `paid-plan-gated` and blocked, assuming that because their primary SaaS pricing plans are paid, developer access is also gated.
*   **Why AI Failed:** The AI failed to look beyond main pricing pages. It did not search for developer-specific sandboxes or developer portal subdomains.
*   **Why Human was Required:** A human was required to read the official API policy, register a mock account to test if sandbox credentials generate instantly, and evaluate developer gating rules.
*   **How Human Resolved It:** The human ran targeted validation queries and added override mappings specifying `self-serve-free` / `self-serve-trial` access and `ready-today` buildability.
*   **Severity:** **High** (Directly impacted the core buildability findings).

---

### 2. URL Scraper Fallback Errors (google.com redirects)
*   **Problem:** The scraper script defaulted to evidence URLs like `https://google.com` when encountering HTTP 403 blocks or CAPTCHAs on official documentation sites (e.g. Sentry, Attio).
*   **Why AI Failed:** The BeautifulSoup scraper script did not have proxy rotating or session bypass capabilities. Rather than crashing, it defaulted to the root search URL (`google.com`).
*   **Why Human was Required:** To prevent submitting invalid/unverified evidence links.
*   **How Human Resolved It:** The human audited the evidence links, resolved the correct developer endpoints manually in the browser, and compiled a mapping dictionary to hardcode verified API reference links.
*   **Severity:** **High** (Invalidated the "evidence-backed" assignment constraint).

---

### 3. API Key Deprecation Policies (HubSpot)
*   **Problem:** The agent mapped `"API key"` as a valid authentication method for HubSpot.
*   **Why AI Failed:** The documentation contained legacy code snippets and search snippets containing the phrase "API key", which the keyword matcher extracted. The AI did not contextualize that HubSpot officially deprecated API keys in November 2022.
*   **Why Human was Required:** To identify time-sensitive API lifecycle changes that keyword matchers cannot contextualize.
*   **How Human Resolved It:** The human manually verified the migration docs, updated the valid auth methods list to `["OAuth2", "Token"]`, and deleted `"API key"`.
*   **Severity:** **Medium** (Leads to integration implementation failures).

---

### 4. BeautifulSoup parser Attribute Errors
*   **Problem:** The agent execution crashed on certain URLs (e.g. Sentry docs) with `AttributeError: type object 'BeautifulSoup' has no attribute 'NO_PARSER_SPECIFIED_WARNING'`.
*   **Why AI Failed:** The Python script contained a dynamic check using a non-existent BeautifulSoup warning property.
*   **Why Human was Required:** To debug the stack trace and patch the code.
*   **How Human Resolved It:** The human edited `agent/tools.py` using a file replace tool, changing the parser argument to a simple, error-free `"html.parser"`.
*   **Severity:** **Medium** (Broke the automation pipeline mid-run).

---

## 3. Human Intervention Timeline

```
Phase 0 (Setup) ──> Scraper Code Attribute Error (Human debugged/patched tools.py)
                         │
Phase 1 (Pass 1) ─> Scraper 403 Blocks & Gated Sandboxes (Human compiled overrides)
                         │
Phase 2 (Pass 2) ─> Accuracy Validation Audit (Human manually cross-checked 15-app sample)
                         │
Phase 4 (Deploy) ─> Browser CORS blocks (Human built polish_project.py to inline data)
```

---

## 4. Future Automation Opportunities

1.  **Headless Browser Scraper (Puppeteer/Playwright):** Integrate browser-use agents to load JavaScript-rendered documentation sites dynamically, bypassing basic HTTP 403 blocks.
2.  **LLM-based Deprecation Checker:** Implement a temporal analysis LLM prompt that explicitly checks search results for terms like "deprecated", "sunset", or "legacy" along with dates.
3.  **Active Link Verification Script:** Run a script that periodically hits cited evidence URLs to verify they return HTTP 200, alerting Product Ops if a doc URL is sunset.

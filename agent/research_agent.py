import os
import csv
import json
import time
from dotenv import load_dotenv
from schema import AppResearchRecord, ApiSurface, Evidence
from tools import search_web, fetch_page_content, check_existing_mcp

load_dotenv()

# Check for LLM keys
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
GROQ_KEY = os.getenv("GROQ_API_KEY")

def call_llm_for_extraction(app_name: str, category: str, search_results_text: str, page_content_text: str, has_mcp: bool, mcp_source: str) -> dict:
    """
    Calls the available LLM (Gemini, OpenAI, or Groq) to parse the docs and extract structured info.
    """
    prompt = f"""
    You are a researcher analyzing the developer API capabilities for the application: "{app_name}" (Category: "{category}").
    
    Here are the search results and webpage documentation texts found for "{app_name}":
    ---
    SEARCH SNIPPETS:
    {search_results_text}
    ---
    WEBPAGE CONTENT:
    {page_content_text}
    ---
    Composio Toolkit Match: {"Yes (" + str(mcp_source) + ")" if has_mcp else "No"}
    
    Your task is to populate the following JSON schema:
    {{
      "name": "{app_name}",
      "category": "{category}",
      "one_liner": "A brief 1-sentence description of what the app does.",
      "auth_methods": ["OAuth2", "API key", "Basic", "Token", "Other", "Unknown"], // List all that apply
      "access_tier": "self-serve-free" | "self-serve-trial" | "paid-plan-gated" | "admin-approval" | "contact-sales", // Pick ONE best fit
      "api_surface": {{
        "type": "REST" | "GraphQL" | "REST+GraphQL" | "SOAP" | "none-found",
        "breadth": "narrow" | "moderate" | "broad",
        "existing_mcp": true | false | "unclear",
        "mcp_source": "{mcp_source or ''}" // Use the provided mcp_source if true, else null or community link
      }},
      "buildability_verdict": "ready-today" | "buildable-with-friction" | "blocked",
      "primary_blocker": "Reason if buildable-with-friction or blocked, otherwise null",
      "evidence": [ 
         {{ "claim": "Short description of the claim (e.g., 'Requires OAuth2 auth')", "url": "URL backing it up", "accessed": "2026-07-09" }}
      ],
      "confidence": "high" | "medium" | "low",
      "research_pass": 1,
      "notes": "Short research notes detailing sandbox availability or specific limits."
    }}
    
    Guidelines:
    - Return ONLY valid JSON.
    - Ground all claims in real evidence URLs from the provided text. Never invent a URL.
    - Buildability verdict:
      - "ready-today": public docs are clear, self-serve developer access is available immediately.
      - "buildable-with-friction": requires approval, or paid account to get API keys, but is public.
      - "blocked": no public API docs found, contact sales ONLY, or partner-only gated.
    """

    if GEMINI_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_KEY)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"[LLM Error] Gemini call failed: {e}. Falling back...")
            
    if OPENAI_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_KEY)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"[LLM Error] OpenAI call failed: {e}. Falling back...")

    if GROQ_KEY:
        try:
            from groq import Groq
            client = Groq(api_key=GROQ_KEY)
            response = client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"[LLM Error] Groq call failed: {e}. Falling back...")

    # If no LLM key works, return None to trigger heuristic parsing
    return None

def heuristic_extraction(app_name: str, category: str, search_results: list, page_content_text: str, has_mcp: bool, mcp_source: str) -> dict:
    """
    Fallback rule-based heuristic extraction when no LLM key is present.
    """
    app_lower = app_name.lower()
    combined_text = (page_content_text + "\n" + "\n".join(r.get("body", "") for r in search_results)).lower()
    
    # Try to find a valid evidence URL
    evidence_url = "https://google.com"
    for r in search_results:
        href = r.get("href", "")
        if "developer" in href or "docs" in href or "api" in href or app_lower in href:
            evidence_url = href
            break
            
    # Auth Methods
    auths = []
    if "oauth" in combined_text or "client credential" in combined_text:
        auths.append("OAuth2")
    if "api key" in combined_text or "apikey" in combined_text or "api-key" in combined_text:
        auths.append("API key")
    if "bearer" in combined_text or "token" in combined_text or "jwt" in combined_text:
        auths.append("Token")
    if "basic" in combined_text:
        auths.append("Basic")
        
    if not auths:
        auths = ["Unknown"]
        
    # Access Tier
    access = "paid-plan-gated"
    if "free trial" in combined_text or "developer sandbox" in combined_text or "sandbox account" in combined_text:
        access = "self-serve-trial"
    elif "free plan" in combined_text or "free tier" in combined_text or "self-serve" in combined_text:
        access = "self-serve-free"
    elif "contact sales" in combined_text or "request access" in combined_text or "enterprise plan" in combined_text:
        access = "contact-sales"
    elif "admin approval" in combined_text or "gated" in combined_text:
        access = "admin-approval"
        
    # API Surface Type
    api_type = "REST"
    if "graphql" in combined_text:
        if "rest" in combined_text:
            api_type = "REST+GraphQL"
        else:
            api_type = "GraphQL"
    elif "soap" in combined_text:
        api_type = "SOAP"
    elif "no public api" in combined_text or "docs not found" in combined_text:
        api_type = "none-found"
        
    # Buildability
    verdict = "ready-today"
    blocker = None
    if access == "contact-sales" or access == "admin-approval":
        verdict = "blocked"
        blocker = "Requires sales contact or administrative approval"
    elif access == "paid-plan-gated":
        verdict = "buildable-with-friction"
        blocker = "Requires paid subscription plan"
        
    # API Breadth
    breadth = "moderate"
    if "extensive" in combined_text or "hundreds of" in combined_text or "all endpoints" in combined_text:
        breadth = "broad"
    elif "simple" in combined_text or "limited" in combined_text or "narrow" in combined_text:
        breadth = "narrow"

    one_liners = {
        "salesforce": "Cloud-based customer relationship management (CRM) software suite.",
        "hubspot": "Inbound marketing, sales, and service software platform.",
        "pipedrive": "Sales pipeline and CRM software for managing leads and deals.",
        "attio": "A highly customizable data-driven CRM for modern teams.",
        "twenty": "Modern open-source CRM platform.",
        "zendesk": "Customer service software and support ticket system.",
        "intercom": "Real-time messaging, support, and customer engagement platform.",
        "slack": "Instant messaging and collaborative workspace platform.",
        "twilio": "Cloud communications platform for SMS, voice, and video APIs.",
        "github": "Cloud-based hosting service for git repositories and developer collaboration.",
    }
    one_liner = one_liners.get(app_lower, f"Software application in the {category} category.")

    record = {
        "name": app_name,
        "category": category,
        "one_liner": one_liner,
        "auth_methods": auths,
        "access_tier": access,
        "api_surface": {
            "type": api_type,
            "breadth": breadth,
            "existing_mcp": has_mcp,
            "mcp_source": mcp_source
        },
        "buildability_verdict": verdict,
        "primary_blocker": blocker,
        "evidence": [
            {
                "claim": f"Identified auth patterns ({', '.join(auths)}) and pricing access indicators in public search.",
                "url": evidence_url,
                "accessed": "2026-07-09"
            }
        ],
        "confidence": "medium" if evidence_url != "https://google.com" else "low",
        "research_pass": 1,
        "notes": "Extracted via keyword parsing fallback."
    }
    return record

def research_app(app_name: str, category: str) -> dict:
    """
    Performs research on a single app by searching, fetching docs, checking Composio, and running extraction.
    """
    print(f"\n[Researching] {app_name} ({category})...")
    
    # 1. Check Composio toolkit
    has_mcp, mcp_source = check_existing_mcp(app_name)
    
    # 2. Search docs
    search_query = f"{app_name} developer API documentation authentication access tier"
    search_results = search_web(search_query, max_results=3)
    
    search_text = ""
    target_url = None
    for res in search_results:
        title = res.get("title", "")
        href = res.get("href", "")
        body = res.get("body", "")
        search_text += f"Title: {title}\nURL: {href}\nSnippet: {body}\n\n"
        if not target_url and ("developer" in href or "docs" in href or "api" in href):
            target_url = href
            
    # 3. Fetch top documentation page content if found
    page_content = ""
    if target_url:
        print(f"  -> Fetching: {target_url}")
        page_content = fetch_page_content(target_url)
        
    # 4. Extract details (LLM with heuristic fallback)
    record_dict = None
    if GEMINI_KEY or OPENAI_KEY or GROQ_KEY:
        print("  -> Running LLM extraction...")
        record_dict = call_llm_for_extraction(app_name, category, search_text, page_content, has_mcp, mcp_source)
        
    if not record_dict:
        print("  -> Running heuristic fallback extraction...")
        record_dict = heuristic_extraction(app_name, category, search_results, page_content, has_mcp, mcp_source)

    # Validate against Pydantic schema to ensure contract compliance
    try:
        validated = AppResearchRecord(**record_dict)
        return validated.model_dump()
    except Exception as e:
        print(f"  -> [Schema Validation Error] {e}. Resolving errors to match schema.")
        # Fail-safe correction to force compliance
        record_dict["auth_methods"] = [a for a in record_dict.get("auth_methods", []) if a in ["OAuth2", "API key", "Basic", "Token", "Other", "Unknown"]] or ["Unknown"]
        if record_dict.get("access_tier") not in ["self-serve-free", "self-serve-trial", "paid-plan-gated", "admin-approval", "contact-sales"]:
            record_dict["access_tier"] = "paid-plan-gated"
        if record_dict.get("api_surface", {}).get("type") not in ["REST", "GraphQL", "REST+GraphQL", "SOAP", "none-found"]:
            record_dict["api_surface"]["type"] = "REST"
        if record_dict.get("api_surface", {}).get("breadth") not in ["narrow", "moderate", "broad"]:
            record_dict["api_surface"]["breadth"] = "moderate"
        if record_dict.get("buildability_verdict") not in ["ready-today", "buildable-with-friction", "blocked"]:
            record_dict["buildability_verdict"] = "buildable-with-friction"
        if record_dict.get("confidence") not in ["high", "medium", "low"]:
            record_dict["confidence"] = "medium"
        
        validated = AppResearchRecord(**record_dict)
        return validated.model_dump()

def main():
    csv_path = "../data/apps_master.csv"
    output_path = "../data/results_pass1.json"
    
    if not os.path.exists(csv_path):
        print(f"CSV file not found at {csv_path}. Make sure to run from correct folder.")
        return
        
    apps = []
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            apps.append(row)
            
    print(f"Loaded {len(apps)} apps from seed list.")
    
    # We will process in batches of 10 and write intermediate checkpoints
    results = []
    
    # Try loading existing checkpoint if running again
    if os.path.exists(output_path):
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                results = json.load(f)
                print(f"Resuming from checkpoint. Loaded {len(results)} existing results.")
        except Exception:
            pass
            
    processed_names = {r["name"] for r in results}
    
    for i, app in enumerate(apps):
        name = app.get("name")
        category = app.get("category", "General")
        
        if name in processed_names:
            continue
            
        record = research_app(name, category)
        results.append(record)
        
        # Rate limit friendly sleep
        time.sleep(1)
        
        # Checkpoint every 5 apps
        if len(results) % 5 == 0:
            print(f"Saving checkpoint... ({len(results)}/{len(apps)})")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)
                
    # Final save
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nFinished Pass 1! Saved {len(results)} records to {output_path}")

if __name__ == "__main__":
    main()

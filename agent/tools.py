import os
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from dotenv import load_dotenv

load_dotenv()

# Global cache for Composio toolkits
_composio_toolkits_cache = None

def get_composio_toolkits():
    """
    Fetches the list of all available toolkits from Composio API v3.1.
    """
    global _composio_toolkits_cache
    if _composio_toolkits_cache is not None:
        return _composio_toolkits_cache

    api_key = os.getenv("COMPOSIO_API_KEY")
    if not api_key:
        print("[Warning] No COMPOSIO_API_KEY found in environment.")
        return []

    url = "https://backend.composio.dev/api/v3.1/toolkits"
    headers = {"x-api-key": api_key}
    
    try:
        # Request up to 1000 items (maximum allowed)
        response = requests.get(url, headers=headers, params={"limit": 1000})
        if response.status_code == 200:
            data = response.json()
            toolkits = data.get("items", [])
            _composio_toolkits_cache = toolkits
            return toolkits
        else:
            print(f"[Error] Composio API returned status {response.status_code}: {response.text}")
            return []
    except Exception as e:
        print(f"[Error] Failed to fetch toolkits from Composio: {e}")
        return []

def check_existing_mcp(app_name: str):
    """
    Checks if a toolkit exists in Composio for the given app name.
    Returns: (exists (bool), mcp_source (str or None))
    """
    toolkits = get_composio_toolkits()
    app_name_lower = app_name.lower().strip()
    
    # Try exact or partial matches in name or slug
    for tool in toolkits:
        name = (tool.get("name") or "").lower()
        slug = (tool.get("slug") or "").lower()
        
        # If there's a strong match
        if app_name_lower in name or app_name_lower in slug or slug in app_name_lower:
            # Found a match
            slug_name = tool.get("slug")
            source_link = f"https://composio.dev/app/{slug_name}"
            return True, source_link

    return False, None

def search_web(query: str, max_results: int = 5):
    """
    Searches DuckDuckGo for the query.
    Returns list of dicts: [{'title': ..., 'href': ..., 'body': ...}]
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            return results
    except Exception as e:
        print(f"[Search Error] DuckDuckGo search failed for '{query}': {e}")
        return []

def fetch_page_content(url: str, timeout: int = 10) -> str:
    """
    Fetches the content of a web page and returns its cleaned text.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Remove scripts, styles, navigations, footers
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()
            
            text = soup.get_text(separator="\n")
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase for line in lines for phrase in line.split("  "))
            clean_text = "\n".join(chunk for chunk in chunks if chunk)
            
            # Truncate to first 8000 characters to keep it reasonable
            return clean_text[:8000]
        else:
            print(f"[Fetch Warning] Status code {response.status_code} for URL: {url}")
            return ""
    except Exception as e:
        print(f"[Fetch Error] Failed to fetch content for URL {url}: {e}")
        return ""

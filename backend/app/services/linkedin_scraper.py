"""
LinkedIn Scraper & Enrichment
- Public scrape: company name from meta tags / JSON-LD
- Apify (optional): employee names, titles, profile URLs via APIFY_API_TOKEN
"""
import json
import os
import re
import asyncio
import httpx
from bs4 import BeautifulSoup
from typing import Optional

# Browser-like headers to reduce bot detection
LINKEDIN_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Apify actor for LinkedIn employees (artificially/linkedin-employees-scraper)
APIFY_ACTOR_ID = "artificially/linkedin-employees-scraper"


def extract_linkedin_company_slug(url: str) -> Optional[str]:
    """Extract company slug from LinkedIn URL (e.g. linkedin.com/company/acme -> acme)."""
    if not url or "linkedin.com" not in url:
        return None
    match = re.search(r"linkedin\.com/company/([a-zA-Z0-9_-]+)", url)
    return match.group(1) if match else None


def extract_linkedin_profile_slug(url: str) -> Optional[str]:
    """Extract profile slug from linkedin.com/in/username."""
    if not url or "linkedin.com" not in url:
        return None
    match = re.search(r"linkedin\.com/in/([a-zA-Z0-9_-]+)", url)
    return match.group(1) if match else None


async def scrape_linkedin_via_apify(linkedin_url: str, max_employees: int = 50) -> dict:
    """
    Use Apify LinkedIn Employees Scraper for employee data.
    Requires APIFY_API_TOKEN env var. Set at https://console.apify.com
    """
    api_token = os.environ.get("APIFY_API_TOKEN")
    if not api_token:
        return {"company_name": None, "contacts": [], "error": "APIFY_API_TOKEN not set"}

    slug = extract_linkedin_company_slug(linkedin_url)
    if not slug:
        return {"company_name": None, "contacts": [], "error": "Invalid LinkedIn company URL"}

    canonical_url = f"https://www.linkedin.com/company/{slug}"
    result = {"company_name": None, "contacts": [], "source": "apify"}

    def _run_apify():
        from apify_client import ApifyClient
        client = ApifyClient(api_token)
        run = client.actor(APIFY_ACTOR_ID).call(
            run_input={
                "companyUrls": [canonical_url],
                "maxEmployees": min(max_employees, 100),
                "scrapeFullProfiles": False,
            }
        )
        dataset_id = run.get("defaultDatasetId")
        if not dataset_id:
            return result
        items = list(client.dataset(dataset_id).iterate_items())
        return {"items": items, "result": result}

    try:
        run_result = await asyncio.to_thread(_run_apify)
        items = run_result.get("items", [])
        result = run_result.get("result", result)

        for item in items:
            name = item.get("fullName") or item.get("name")
            if not name:
                continue
            result["contacts"].append({
                "name": name,
                "title": item.get("title")
                or item.get("headline")
                or item.get("jobTitle"),
                "linkedin_url": item.get("profileUrl") or item.get("profile_url"),
                "email": None,
            })
            if not result["company_name"] and item.get("companyName"):
                result["company_name"] = item.get("companyName")

    except Exception as e:
        result["error"] = str(e)

    return result


async def scrape_linkedin_company_public(url: str) -> dict:
    """
    Scrape public LinkedIn company page (no API).
    Extracts company name only; employee data requires Apify.
    """
    slug = extract_linkedin_company_slug(url)
    if not slug:
        return {"company_name": None, "contacts": [], "error": "Invalid LinkedIn company URL"}

    canonical_url = f"https://www.linkedin.com/company/{slug}"
    result = {"company_name": None, "company_url": canonical_url, "contacts": [], "source": "linkedin_public"}

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(canonical_url, headers=LINKEDIN_HEADERS)
            if resp.status_code != 200:
                return {**result, "error": f"HTTP {resp.status_code}"}

            soup = BeautifulSoup(resp.text, "html.parser")
            og_title = soup.find("meta", property="og:title")
            if og_title and og_title.get("content"):
                result["company_name"] = og_title["content"].split(" | ")[0].strip()

            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(script.string or "{}")
                    if isinstance(data, dict) and data.get("@type") == "Organization":
                        result["company_name"] = result["company_name"] or data.get("name")
                        break
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and item.get("@type") == "Organization":
                                result["company_name"] = result["company_name"] or item.get("name")
                                break
                except Exception:
                    pass

            if not result["company_name"]:
                result["company_name"] = slug.replace("-", " ").title()

    except Exception as e:
        result["error"] = str(e)

    return result


async def scrape_linkedin_company(linkedin_url: str, max_employees: int = 50) -> dict:
    """
    Scrape LinkedIn company: uses Apify for employee data if APIFY_API_TOKEN is set,
    otherwise falls back to public scrape (company name only).
    """
    if os.environ.get("APIFY_API_TOKEN"):
        data = await scrape_linkedin_via_apify(linkedin_url, max_employees)
        if data.get("contacts"):
            return data
        if not data.get("error"):
            return data
    return await scrape_linkedin_company_public(linkedin_url)

import requests
import re
import time
import logging
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import os

logger = logging.getLogger(__name__)

CQC_API_BASE = os.getenv("CQC_API_BASE", "https://api.cqc.org.uk/public/v1")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")


def fetch_cqc_providers(page: int = 1, per_page: int = 50) -> Dict:
    """Fetch registered UK care providers from the CQC public API."""
    try:
        params = {
            "page": page,
            "perPage": per_page,
            "registrationStatus": "Registered",
            "type": "Social Care Org",
        }
        resp = requests.get(f"{CQC_API_BASE}/providers", params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"CQC API error: {e}")
        return {"providers": [], "total": 0}


def extract_emails_from_url(url: str) -> List[str]:
    """Scrape a website and extract email addresses."""
    if not url:
        return []
    try:
        if not url.startswith("http"):
            url = "https://" + url
        resp = requests.get(url, headers=HEADERS, timeout=10)
        emails = EMAIL_REGEX.findall(resp.text)
        # Filter out common false positives
        filtered = [
            e for e in set(emails)
            if not any(x in e.lower() for x in ["example.", "sentry.", "wixpress.", "@2x", "schema."])
        ]
        return filtered[:5]
    except Exception:
        return []


def extract_contact_from_page(url: str) -> Dict:
    """Try to find a contact person name and email on a website."""
    contact = {"name": None, "email": None, "phone": None}
    if not url:
        return contact
    try:
        if not url.startswith("http"):
            url = "https://" + url
        # Try /contact page first
        for path in ["", "/contact", "/contact-us", "/about", "/about-us"]:
            try:
                resp = requests.get(url.rstrip("/") + path, headers=HEADERS, timeout=8)
                soup = BeautifulSoup(resp.text, "lxml")

                emails = EMAIL_REGEX.findall(resp.text)
                filtered_emails = [
                    e for e in set(emails)
                    if not any(x in e.lower() for x in ["example.", "sentry.", "@2x", "schema."])
                ]
                if filtered_emails:
                    contact["email"] = filtered_emails[0]

                # Look for phone numbers
                phone_pattern = re.compile(r"(?:\+44|0)[\s\-]?(?:\d[\s\-]?){9,10}")
                phones = phone_pattern.findall(resp.text)
                if phones:
                    contact["phone"] = phones[0].strip()

                # Try to find a contact name in headings or strong tags
                for tag in soup.find_all(["h1", "h2", "h3", "strong", "b"]):
                    text = tag.get_text(strip=True)
                    if 3 < len(text) < 50 and any(
                        kw in tag.parent.get_text().lower()
                        for kw in ["manager", "director", "coordinator", "owner", "registered"]
                    ):
                        contact["name"] = text
                        break

                if contact["email"]:
                    break
                time.sleep(0.3)
            except Exception:
                continue
    except Exception as e:
        logger.debug(f"Contact extraction failed for {url}: {e}")
    return contact


def build_agency_data(provider: Dict) -> Dict:
    """Map a CQC provider record to our agency schema."""
    addr = provider.get("address") or {}
    address_parts = [
        addr.get("line1", ""),
        addr.get("line2", ""),
        addr.get("city", ""),
        addr.get("county", ""),
        addr.get("postcode", ""),
    ]
    address = ", ".join(p for p in address_parts if p)

    return {
        "name": provider.get("providerName", ""),
        "address": address,
        "phone": provider.get("phoneNumber", ""),
        "website": provider.get("website", ""),
        "email": "",
        "contact_person": "",
        "cqc_id": provider.get("providerId", ""),
        "status": "new",
    }


def scrape_uk_care_agencies(max_results: int = 50, page: int = 1) -> List[Dict]:
    """
    Main entry point: fetch UK care agencies from CQC API,
    then enrich with contact details from their websites.
    """
    data = fetch_cqc_providers(page=page, per_page=min(max_results, 100))
    providers = data.get("providers", [])

    results = []
    for provider in providers[:max_results]:
        agency = build_agency_data(provider)

        website = agency.get("website", "")
        if website:
            contact = extract_contact_from_page(website)
            if contact["email"]:
                agency["email"] = contact["email"]
            if contact["name"]:
                agency["contact_person"] = contact["name"]
            if contact["phone"] and not agency["phone"]:
                agency["phone"] = contact["phone"]
            time.sleep(0.2)

        results.append(agency)

    return results

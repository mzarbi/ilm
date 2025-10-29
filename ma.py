import requests

BASE_URL = "http://127.0.0.1:5000/api"

def post(url, payload):
    r = requests.post(f"{BASE_URL}/{url}", json=payload)
    print(f"POST /{url} -> {r.status_code}")
    if r.status_code >= 400:
        print(r.text)
    return r.json() if r.headers.get("Content-Type", "").startswith("application/json") else None


# --- Create reference data ---
eur = post("currencies", {"code": "EUR", "name": "Euro"})
usd = post("currencies", {"code": "USD", "name": "US Dollar"})

fr = post("countries", {"iso2": "FR", "iso3": "FRA", "name": "France"})
uk = post("countries", {"iso2": "GB", "iso3": "GBR", "name": "United Kingdom"})

sector_fin = post("sectors", {"code": "FIN", "label": "Financials", "description": "Financial sector"})
sector_ind = post("sectors", {"code": "IND", "label": "Industrials", "description": "Industrial sector"})

pra = post("pra-activities", {"code": "buyout", "label": "Buyout", "description": "Acquisition financing"})
cpty_type = post("counterparty-types", {"code": "bank", "label": "Bank", "description": "Financial institution"})


# --- Create legal entities ---
sponsor = post("legal-entities", {
    "rmpm_code": "SPN001",
    "rmpm_type": "INTERNAL",
    "name": "Sponsor SA",
    "country_id": fr.get("id"),
    "sector_id": sector_fin.get("id"),
})

counterparty = post("legal-entities", {
    "rmpm_code": "CPTY01",
    "rmpm_type": "INTERNAL",
    "name": "Counterparty Ltd",
    "country_id": uk.get("id"),
    "sector_id": sector_fin.get("id"),
})


# --- Create a project ---
project = post("projects", {
    "code": "NEP",
    "name": "Project Neptune",
    "description": "High-level project for testing.",
    "sector_id": sector_ind.get("id"),
    "country_id": fr.get("id"),
    "region": "EMEA",
    "business_line": "Corporate Finance",
})


# --- Create an interlinkage ---
interlinkage = post("interlinkages", {
    "sponsor_id": sponsor.get("id"),
    "counterparty_id": counterparty.get("id"),
    "project_id": project.get("id"),
    "pra_activity_id": pra.get("id"),
    "counterparty_type_id": cpty_type.get("id"),
    "deal_date": "2025-01-01",
    "effective_date": "2025-01-15",
    "notional_amount": "5000000.00",
    "currency_id": eur.get("id"),
    "status": "draft",
    "purpose": "Test transaction linkage between sponsor and counterparty"
})


print("\n✅ Done populating API!")
print("Created Interlinkage ID:", interlinkage.get("id"))

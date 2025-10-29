
"""
Seed referential tables: Currency, Country, Sector, PraActivity, CounterpartyType,
InstrumentType, FacilityType.
"""
import random
import string
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session, sessionmaker

from server.extensions import ENGINE
import server.models as m
import pycountry
from sqlalchemy.orm import Session
from server.extensions import Base, ENGINE
import server.models as m


def get_or_create(session, Model, **kwargs):
    obj = session.query(Model).filter_by(**kwargs).one_or_none()
    if not obj:
        obj = Model(**kwargs)
        session.add(obj)
    return obj


def seed_currencies(session: Session):
    print("→ Seeding currencies...")
    for cur in pycountry.currencies:
        code = cur.alpha_3
        name = getattr(cur, "name", None)
        get_or_create(session, m.Currency, code=code, name=name)
    print(f"  Added {session.query(m.Currency).count()} currencies.")


def seed_countries(session: Session):
    print("→ Seeding countries...")
    for c in pycountry.countries:
        iso2 = c.alpha_2
        iso3 = c.alpha_3
        name = getattr(c, "name", None)
        get_or_create(session, m.Country, iso2=iso2, iso3=iso3, name=name)
    print(f"  Added {session.query(m.Country).count()} countries.")


def seed_sectors(session: Session):
    print("→ Seeding sectors...")
    sectors = [
        ("FIN", "Financials", "Banking, insurance, capital markets"),
        ("IND", "Industrials", "Manufacturing, construction, engineering"),
        ("TEC", "Technology", "IT, electronics, semiconductors"),
        ("ENE", "Energy", "Oil, gas, renewables"),
        ("HEA", "Healthcare", "Pharma, biotech, hospitals"),
    ]
    for code, label, desc in sectors:
        get_or_create(session, m.Sector, code=code, label=label, description=desc)


def seed_pra_activities(session: Session):
    print("→ Seeding PRA Activities...")
    acts = [
        ("buyout", "Buyout"),
        ("growth", "Growth"),
        ("mezzanine", "Mezzanine"),
        ("venture", "Venture"),
        ("infra", "Infrastructure"),
        ("real_estate", "Real Estate"),
        ("distressed", "Distressed Assets"),
        ("hedge", "Hedge Fund"),
        ("other", "Other"),
    ]
    for code, label in acts:
        get_or_create(session, m.PraActivity, code=code, label=label)


def seed_counterparty_types(session: Session):
    print("→ Seeding Counterparty Types...")
    types = [
        ("bank", "Bank"),
        ("corporate", "Corporate"),
        ("fund", "Investment Fund"),
        ("insurance", "Insurance Company"),
        ("government", "Government / Public"),
        ("other", "Other"),
    ]
    for code, label in types:
        get_or_create(session, m.CounterpartyType, code=code, label=label)


def seed_instrument_types(session: Session):
    print("→ Seeding Instrument Types...")
    types = [
        ("BOND", "Bond"),
        ("SWAP", "Swap"),
        ("FWD", "Forward"),
        ("OPT", "Option"),
        ("EQ", "Equity"),
        ("LOAN", "Loan"),
        ("FUND", "Fund Participation"),
        ("DERIV", "Derivative"),
        ("OTHER", "Other"),
    ]
    for code, label in types:
        get_or_create(session, m.InstrumentType, code=code, label=label)


def seed_facility_types(session: Session):
    print("→ Seeding Facility Types...")
    types = [
        ("RCF", "Revolving Credit Facility"),
        ("TLB", "Term Loan B"),
        ("LC", "Letter of Credit"),
        ("BRIDGE", "Bridge Loan"),
        ("OTHER", "Other"),
    ]
    for code, label in types:
        get_or_create(session, m.FacilityType, code=code, label=label)




# -----------------------------
# Small helpers
# -----------------------------
def _rand_choice(seq):
    return seq[random.randrange(len(seq))]

def _make_lei():
    # 20-char uppercase alphanumeric (not strictly ISO format, but fine for seed)
    return "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20))

def _company_name(i: int) -> str:
    prefixes = ["Global", "Prime", "United", "Atlantic", "Omega", "Pioneer", "Apex", "Northern", "Blue", "Crescent",
                "Capital", "Summit", "Vector", "Vertex", "Union", "First", "Nova", "Crown", "Regent", "Heritage"]
    cores    = ["Holdings", "Industries", "Partners", "Group", "Enterprises", "Resources", "Logistics",
                "Technologies", "Investments", "Financial", "Energy", "Healthcare", "Retail", "Manufacturing"]
    suffixes = ["SA", "SAS", "Ltd", "PLC", "AG", "NV", "LLC", "Inc.", "GmbH", "SARL"]
    return f"{_rand_choice(prefixes)} {_rand_choice(cores)} {_rand_choice(suffixes)} #{i:04d}"

def _ensure_min_referentials(session: Session):
    # Make sure we have at least a handful of countries & sectors
    if session.query(m.Country).count() == 0:
        # Minimal fallback set (you can call your full pycountry seeder if you prefer)
        for iso2, iso3, name in [("FR", "FRA", "France"), ("GB", "GBR", "United Kingdom"),
                                 ("US", "USA", "United States"), ("DE", "DEU", "Germany"),
                                 ("TN", "TUN", "Tunisia")]:
            session.add(m.Country(iso2=iso2, iso3=iso3, name=name))
        session.flush()

    if session.query(m.Sector).count() == 0:
        base = [
            ("FIN", "Financials", "Banking, insurance, capital markets"),
            ("IND", "Industrials", "Manufacturing, construction, engineering"),
            ("TEC", "Technology", "IT, electronics, semiconductors"),
            ("ENE", "Energy", "Oil, gas, renewables"),
            ("HEA", "Healthcare", "Pharma, biotech, hospitals"),
        ]
        for code, label, desc in base:
            session.add(m.Sector(code=code, label=label, description=desc))
        session.flush()

def seed_legal_entities(session: Session, n: int = 1000):
    """
    Creates `n` LegalEntity rows with 1–2 EntityIdentifier rows each.
    - Ensures some Countries and Sectors exist.
    - rmpm_code is unique within rmpm_type by construction.
    """
    _ensure_min_referentials(session)

    countries = session.query(m.Country.id).all()
    sectors   = session.query(m.Sector.id).all()
    country_ids = [c[0] for c in countries]
    sector_ids  = [s[0] for s in sectors]

    # To avoid clashes if data already exists
    existing = session.query(func.count(m.LegalEntity.id)).scalar() or 0
    start_idx = existing + 1

    rmpm_types = ["sponsor", "counterparty", "booking"]
    aml_risks  = ["low", "medium", "high"]

    batch = []
    id_batch = []
    now_user = "seed_legal_entities"
    now = datetime.utcnow()

    for i in range(start_idx, start_idx + n):
        rtype = _rand_choice(rmpm_types)
        rcode = f"{rtype[:3].upper()}-{i:06d}"

        le = m.LegalEntity(
            rmpm_code=rcode,
            rmpm_type=rtype,
            name=_company_name(i),
            description=None,
            lei_code=_make_lei(),
            country_id=_rand_choice(country_ids) if country_ids else None,
            sector_id=_rand_choice(sector_ids) if sector_ids else None,
            is_sanctioned=random.random() < 0.02,   # ~2%
            is_pep=random.random() < 0.01,          # ~1%
            aml_risk=_rand_choice(aml_risks),
            created_at=now,
            created_by=now_user,
            updated_at=None,
            updated_by=None,
            is_deleted=False,
            deleted_at=None,
            deleted_by=None,
        )
        batch.append(le)

        # Create 1–2 secondary identifiers (unique scheme+value)
        # We’ll always add an INTERNAL code; sometimes also VAT or BIC
        internal_id = m.EntityIdentifier(
            entity=le, scheme="INTERNAL", value=f"INT-{i:08d}"
        )
        id_batch.append(internal_id)

        if random.random() < 0.6:
            vat = m.EntityIdentifier(entity=le, scheme="VAT", value=f"VAT{i:09d}")
            id_batch.append(vat)
        if random.random() < 0.35:
            # Fake-ish BIC: 8 or 11 alphanum (we'll keep simple & unique)
            bic = m.EntityIdentifier(entity=le, scheme="BIC", value=f"BIC{i:011d}")
            id_batch.append(bic)

        # Commit in chunks to keep memory in check
        if len(batch) >= 200:
            session.add_all(batch)
            session.add_all(id_batch)
            session.flush()  # get ids & check constraints early
            batch.clear()
            id_batch.clear()

    # Remainder
    if batch:
        session.add_all(batch)
    if id_batch:
        session.add_all(id_batch)

    print(f"→ Prepared {n} legal entities with identifiers.")

def legal_entities():
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=ENGINE, future=True)

    random.seed(42)

    with SessionLocal() as s, s.begin():
        # If you want the full referentials, call your existing seeders here instead
        # from your file (uncomment if desired):
        # seed_countries(s); seed_sectors(s)
        seed_legal_entities(s, n=1000)

    print("✅ Done seeding 1,000 legal entities.")


REGIONS = ["EMEA", "AMER", "APAC"]
BUSINESS_LINES = [
    "Global Markets", "Global Banking", "Securities Services",
    "Transaction Banking", "Corporate Finance", "Asset Management"
]
PORTFOLIOS = [
    "Core", "Strategic", "Opportunistic", "Legacy", "Growth", "Infra"
]

def _ensure_min_referentials(session: Session):
    """Ensure we have at least some countries & sectors for foreign keys."""
    if session.query(m.Country).count() == 0:
        for iso2, iso3, name in [
            ("FR", "FRA", "France"),
            ("GB", "GBR", "United Kingdom"),
            ("US", "USA", "United States"),
            ("DE", "DEU", "Germany"),
            ("TN", "TUN", "Tunisia"),
        ]:
            session.add(m.Country(iso2=iso2, iso3=iso3, name=name))
        session.flush()

    if session.query(m.Sector).count() == 0:
        base = [
            ("FIN", "Financials", "Banking, insurance, capital markets"),
            ("IND", "Industrials", "Manufacturing, construction, engineering"),
            ("TEC", "Technology", "IT, electronics, semiconductors"),
            ("ENE", "Energy", "Oil, gas, renewables"),
            ("HEA", "Healthcare", "Pharma, biotech, hospitals"),
        ]
        for code, label, desc in base:
            session.add(m.Sector(code=code, label=label, description=desc))
        session.flush()

def _project_name(i: int) -> str:
    # Deterministic but varied names
    themes = ["Atlas", "Aurora", "Helios", "Orion", "Zephyr", "Aquila",
              "Nimbus", "Vertex", "Quasar", "Meridian", "Argon", "Saffron"]
    verbs  = ["Upgrade", "Expansion", "Modernization", "Digitization",
              "Integration", "Optimization", "Migration", "Refactor"]
    return f"Project {random.choice(themes)} {random.choice(verbs)} #{i:04d}"

def _project_code(i: int) -> str:
    return f"PRJ-{i:06d}"

def seed_projects(session: Session, n: int = 150, *, created_by: str = "seed_projects"):
    """
    Create `n` Projects with valid FKs to Sector & Country.
    Ensures uniqueness of (code) and (name) by construction.
    """
    _ensure_min_referentials(session)

    country_ids = [cid for (cid,) in session.query(m.Country.id).all()]
    sector_ids  = [sid for (sid,) in session.query(m.Sector.id).all()]

    existing = session.query(func.count(m.Project.id)).scalar() or 0
    start_idx = existing + 1
    now = datetime.utcnow()

    batch = []
    for i in range(start_idx, start_idx + n):
        prj = m.Project(
            code=_project_code(i),
            name=_project_name(i),
            description="Auto-seeded project for testing & demos.",
            sector_id=random.choice(sector_ids) if sector_ids else None,
            country_id=random.choice(country_ids) if country_ids else None,
            region=random.choice(REGIONS),
            business_line=random.choice(BUSINESS_LINES),
            portfolio=random.choice(PORTFOLIOS),
            created_at=now,
            created_by=created_by,
            is_deleted=False,
        )
        batch.append(prj)

        if len(batch) >= 200:
            session.add_all(batch)
            session.flush()
            batch.clear()

    if batch:
        session.add_all(batch)

    print(f"→ Prepared {n} projects.")

def projects():
    random.seed(1337)
    SessionLocal = sessionmaker(bind=ENGINE, future=True)
    with SessionLocal() as s, s.begin():
        seed_projects(s, n=150)

    print("✅ Done seeding projects.")

def main():
    Base.metadata.drop_all(ENGINE)
    Base.metadata.create_all(ENGINE)
    with Session(ENGINE) as s, s.begin():
        seed_currencies(s)
        seed_countries(s)
        seed_sectors(s)
        seed_pra_activities(s)
        seed_counterparty_types(s)
        seed_instrument_types(s)
        seed_facility_types(s)

    legal_entities()
    projects()
    print("✅ Seeding complete.")


if __name__ == "__main__":
    main()

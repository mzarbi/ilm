# models_cib.py
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Date, DateTime, Numeric, Text, Enum, ForeignKey,
    UniqueConstraint, Index, CheckConstraint, Boolean
)
from sqlalchemy.orm import relationship, validates
from server.extensions import Base


# -----------------------------------------------------------------------------
# Mixins
# -----------------------------------------------------------------------------
class AuditMixin:
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    created_by = Column(String(128), nullable=True, index=True)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow, index=True)
    updated_by = Column(String(128), nullable=True, index=True)


class SoftDeleteMixin:
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(String(128), nullable=True)


# -----------------------------------------------------------------------------
# Workflow enums (domain workflow stays enum; reference data are tables)
# -----------------------------------------------------------------------------
INTERLINKAGE_STATUS = ("draft", "validated", "archived", "deleted")
INTERDEP_LEVEL = ("low", "medium", "high", "critical")
INTERDEP_TYPE = (
    "ownership", "credit", "guarantee", "management",
    "technical", "juridical", "legal", "contractual",
    "equity", "funding", "governance", "strategic", "other"
)


# -----------------------------------------------------------------------------
# Reference Tables (seeded dictionaries)
# -----------------------------------------------------------------------------
class Currency(Base):
    __tablename__ = "ref_currencies"
    id = Column(Integer, primary_key=True)
    code = Column(String(3), nullable=False, unique=True, index=True)  # ISO-4217
    name = Column(String(64), nullable=True)

    __table_args__ = (CheckConstraint("length(code) = 3"),)


class Country(Base):
    __tablename__ = "ref_countries"
    id = Column(Integer, primary_key=True)
    iso2 = Column(String(2), nullable=False, unique=True, index=True)  # ISO-3166-1 alpha-2
    iso3 = Column(String(3), nullable=True, unique=True, index=True)
    name = Column(String(128), nullable=True)

    __table_args__ = (CheckConstraint("length(iso2) = 2"),)


class Sector(Base):
    __tablename__ = "ref_sectors"
    id = Column(Integer, primary_key=True)
    code = Column(String(32), nullable=False, unique=True, index=True)   # e.g., NACE/NAICS proxy
    label = Column(String(128), nullable=False)
    description = Column(Text)


class PraActivity(Base):
    __tablename__ = "ref_pra_activities"
    id = Column(Integer, primary_key=True)
    code = Column(String(64), nullable=False, unique=True, index=True)   # buyout, growth, mezzanine, ...
    label = Column(String(128), nullable=False)
    description = Column(Text)


class CounterpartyType(Base):
    __tablename__ = "ref_counterparty_types"
    id = Column(Integer, primary_key=True)
    code = Column(String(64), nullable=False, unique=True, index=True)
    label = Column(String(128), nullable=False)
    description = Column(Text)


class InstrumentType(Base):
    __tablename__ = "ref_instrument_types"
    id = Column(Integer, primary_key=True)
    code = Column(String(64), nullable=False, unique=True, index=True)
    label = Column(String(128), nullable=False)
    description = Column(Text)


class FacilityType(Base):
    __tablename__ = "ref_facility_types"
    id = Column(Integer, primary_key=True)
    code = Column(String(64), nullable=False, unique=True, index=True)   # term_loan, revolver, guarantee, etc.
    label = Column(String(128), nullable=False)
    description = Column(Text)


# -----------------------------------------------------------------------------
# Legal Entities (sponsor/counterparty/booking entity, etc.)
# -----------------------------------------------------------------------------
class LegalEntity(Base, AuditMixin, SoftDeleteMixin):
    """
    Canonical entity catalog.
    - RMPM fields as requested (+ LEI, country, sector, flags)
    - multiple identifiers supported via EntityIdentifier
    """
    __tablename__ = "legal_entities"

    id = Column(Integer, primary_key=True)
    rmpm_code = Column(String(64), nullable=False)
    rmpm_type = Column(String(64), nullable=False)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)

    lei_code = Column(String(20), index=True)
    country_id = Column(Integer, ForeignKey("ref_countries.id"))
    sector_id = Column(Integer, ForeignKey("ref_sectors.id"))

    # Compliance flags (optional)
    is_sanctioned = Column(Boolean, default=False, index=True)
    is_pep = Column(Boolean, default=False, index=True)     # politically exposed person/org
    aml_risk = Column(String(32), index=True)               # low/medium/high or custom scale

    country = relationship("Country")
    sector = relationship("Sector")

    identifiers = relationship("EntityIdentifier", back_populates="entity", cascade="all, delete-orphan", passive_deletes=True)

    __table_args__ = (
        UniqueConstraint("rmpm_code", "rmpm_type", name="uq_legal_entity_rmpm"),
        Index("ix_legal_entity_name", "name"),
    )


class EntityIdentifier(Base):
    """
    Secondary identifiers for an entity (BIC, SIREN, VAT, internal codes, etc.)
    """
    __tablename__ = "entity_identifiers"

    id = Column(Integer, primary_key=True)
    entity_id = Column(Integer, ForeignKey("legal_entities.id", ondelete="CASCADE"), nullable=False, index=True)
    scheme = Column(String(64), nullable=False, index=True)   # e.g., BIC, SIREN, VAT, INTERNAL
    value = Column(String(128), nullable=False, index=True)

    entity = relationship("LegalEntity", back_populates="identifiers")

    __table_args__ = (UniqueConstraint("scheme", "value", name="uq_entity_identifier"),)


# -----------------------------------------------------------------------------
# Projects
# -----------------------------------------------------------------------------
class Project(Base, AuditMixin, SoftDeleteMixin):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    code = Column(String(64), unique=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text)

    sector_id = Column(Integer, ForeignKey("ref_sectors.id"))
    country_id = Column(Integer, ForeignKey("ref_countries.id"))
    region = Column(String(128))
    business_line = Column(String(128), index=True)          # e.g., CIB sub-BU/product line
    portfolio = Column(String(128), index=True)

    sector = relationship("Sector")
    country = relationship("Country")


class Facility(Base, AuditMixin, SoftDeleteMixin):
    __tablename__ = "facilities"

    id = Column(Integer, primary_key=True)
    facility_type_id = Column(Integer, ForeignKey("ref_facility_types.id"), nullable=False, index=True)
    reference = Column(String(64), nullable=False, unique=True, index=True)
    limit_amount = Column(Numeric(18, 2), nullable=False)
    currency_id = Column(Integer, ForeignKey("ref_currencies.id"), nullable=False)
    maturity_date = Column(Date)

    facility_type = relationship("FacilityType")
    currency = relationship("Currency")


class Instrument(Base, AuditMixin, SoftDeleteMixin):
    __tablename__ = "instruments"

    id = Column(Integer, primary_key=True)
    instrument_type_id = Column(Integer, ForeignKey("ref_instrument_types.id"), nullable=False, index=True)
    reference = Column(String(64), nullable=True, unique=True, index=True)   # trade/ref if applicable
    description = Column(Text)

    instrument_type = relationship("InstrumentType")

class Interlinkage(Base, AuditMixin, SoftDeleteMixin):
    __tablename__ = "interlinkages"

    id = Column(Integer, primary_key=True)

    sponsor_id = Column(Integer, ForeignKey("legal_entities.id", ondelete="RESTRICT"), nullable=False, index=True)
    counterparty_id = Column(Integer, ForeignKey("legal_entities.id", ondelete="RESTRICT"), nullable=False, index=True)
    booking_entity_id = Column(Integer, ForeignKey("legal_entities.id", ondelete="RESTRICT"), nullable=True, index=True)

    project_id = Column(Integer, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True)
    pra_activity_id = Column(Integer, ForeignKey("ref_pra_activities.id", ondelete="RESTRICT"), nullable=True, index=True)
    counterparty_type_id = Column(Integer, ForeignKey("ref_counterparty_types.id", ondelete="RESTRICT"), nullable=True, index=True)

    facility_id = Column(Integer, ForeignKey("facilities.id", ondelete="SET NULL"), nullable=True, index=True)
    instrument_id = Column(Integer, ForeignKey("instruments.id", ondelete="SET NULL"), nullable=True, index=True)

    # Economics
    deal_date = Column(Date, index=True)
    effective_date = Column(Date, index=True)
    maturity_date = Column(Date, index=True)

    notional_amount = Column(Numeric(18, 2))
    currency_id = Column(Integer, ForeignKey("ref_currencies.id"))

    status = Column(Enum(*INTERLINKAGE_STATUS, name="interlinkage_status_enum", validate_strings=True), nullable=False, default="draft", index=True)

    # Qualitative
    purpose = Column(Text)
    remarks = Column(Text)

    # Relationships
    sponsor = relationship("LegalEntity", foreign_keys=[sponsor_id])
    counterparty = relationship("LegalEntity", foreign_keys=[counterparty_id])
    booking_entity = relationship("LegalEntity", foreign_keys=[booking_entity_id])

    project = relationship("Project")
    pra_activity = relationship("PraActivity")
    counterparty_type = relationship("CounterpartyType")

    facility = relationship("Facility")
    instrument = relationship("Instrument")
    currency = relationship("Currency")

    interdependences = relationship("Interdependence", back_populates="interlinkage", cascade="all, delete-orphan", passive_deletes=True, lazy="selectin")
    analysis = relationship("InterlinkageAnalysis", uselist=False, back_populates="interlinkage", cascade="all, delete-orphan", passive_deletes=True, lazy="selectin")
    exposures = relationship("ExposureSnapshot", back_populates="interlinkage", cascade="all, delete-orphan", passive_deletes=True)

    attachments = relationship("InterlinkageAttachment", back_populates="interlinkage", cascade="all, delete-orphan", passive_deletes=True)
    notes = relationship("InterlinkageNote", back_populates="interlinkage", cascade="all, delete-orphan", passive_deletes=True)
    workflow_events = relationship("WorkflowEvent", back_populates="interlinkage", cascade="all, delete-orphan", passive_deletes=True)

    __table_args__ = (
        UniqueConstraint("sponsor_id", "project_id", "counterparty_id", "deal_date", name="uq_interlinkage_natural"),
        Index("ix_interlinkage_role_date", "sponsor_id", "counterparty_id", "deal_date"),
        CheckConstraint("(currency_id IS NULL) OR (currency_id > 0)", name="ck_interlinkage_currency_fk"),
    )


class InterlinkageAnalysis(Base, AuditMixin, SoftDeleteMixin):
    __tablename__ = "interlinkage_analyses"

    id = Column(Integer, primary_key=True)
    interlinkage_id = Column(Integer, ForeignKey("interlinkages.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    content = Column(Text, nullable=True)

    interlinkage = relationship("Interlinkage", back_populates="analysis", lazy="joined")


# -----------------------------------------------------------------------------
# Interdependence (typed edges attached to an Interlinkage)
# -----------------------------------------------------------------------------
class Interdependence(Base, AuditMixin, SoftDeleteMixin):
    __tablename__ = "interdependences"

    id = Column(Integer, primary_key=True)
    interlinkage_id = Column(Integer, ForeignKey("interlinkages.id", ondelete="CASCADE"), nullable=False, index=True)

    interdependence_identifier = Column(String(128), nullable=False)  # external ref / edge key
    type = Column(Enum(*INTERDEP_TYPE, name="interdependence_type_enum", validate_strings=True))
    level = Column(Enum(*INTERDEP_LEVEL, name="interdependence_level_enum", validate_strings=True), index=True)

    # Optional normalization to Project (keep free-text for legacy)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), index=True)
    project_name = Column(String(255))
    risk_assessment = Column(Text)

    # Edge enrichment
    effective_date = Column(Date, index=True)
    expiry_date = Column(Date, index=True)

    interlinkage = relationship("Interlinkage", back_populates="interdependences")
    project = relationship("Project", lazy="joined")

    __table_args__ = (
        UniqueConstraint("interlinkage_id", "interdependence_identifier", name="uq_interdep_per_interlinkage"),
        Index("ix_interdep_type_level", "type", "level"),
    )


# -----------------------------------------------------------------------------
# Exposures / Risk Metrics (time series by interlinkage)
# -----------------------------------------------------------------------------
class ExposureSnapshot(Base, AuditMixin, SoftDeleteMixin):
    __tablename__ = "exposure_snapshots"

    id = Column(Integer, primary_key=True)
    interlinkage_id = Column(Integer, ForeignKey("interlinkages.id", ondelete="CASCADE"), nullable=False, index=True)

    as_of_date = Column(Date, nullable=False, index=True)
    currency_id = Column(Integer, ForeignKey("ref_currencies.id"), nullable=False, index=True)

    # Common CIB measures (extend as needed)
    ead = Column(Numeric(18, 2))       # Exposure At Default
    undrawn = Column(Numeric(18, 2))
    mtm = Column(Numeric(18, 2))       # Mark-to-Market
    pnl = Column(Numeric(18, 2))
    rwa = Column(Numeric(18, 2))       # Risk-Weighted Assets
    pd = Column(Numeric(6, 4))         # Probability of Default (0..1)
    lgd = Column(Numeric(6, 4))        # Loss Given Default (0..1)

    fx_to_reporting = Column(Numeric(18, 8))  # FX rate into your reporting currency at as_of_date

    interlinkage = relationship("Interlinkage", back_populates="exposures")
    currency = relationship("Currency")

    __table_args__ = (UniqueConstraint("interlinkage_id", "as_of_date", name="uq_exposure_timeseries"),)


# -----------------------------------------------------------------------------
# Attachments / Notes / Workflow
# -----------------------------------------------------------------------------
class InterlinkageAttachment(Base, AuditMixin, SoftDeleteMixin):
    __tablename__ = "interlinkage_attachments"

    id = Column(Integer, primary_key=True)
    interlinkage_id = Column(Integer, ForeignKey("interlinkages.id", ondelete="CASCADE"), nullable=False, index=True)

    filename = Column(String(255), nullable=False)
    mime_type = Column(String(128), nullable=True)
    storage_uri = Column(String(1024), nullable=False)  # path/NAS/S3/Sharepoint
    description = Column(Text)

    interlinkage = relationship("Interlinkage", back_populates="attachments")


class InterlinkageNote(Base, AuditMixin, SoftDeleteMixin):
    __tablename__ = "interlinkage_notes"

    id = Column(Integer, primary_key=True)
    interlinkage_id = Column(Integer, ForeignKey("interlinkages.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    visibility = Column(String(32), nullable=True, index=True)

    interlinkage = relationship("Interlinkage", back_populates="notes")


class WorkflowEvent(Base, AuditMixin):
    __tablename__ = "workflow_events"

    id = Column(Integer, primary_key=True)
    interlinkage_id = Column(Integer, ForeignKey("interlinkages.id", ondelete="CASCADE"), nullable=False, index=True)
    from_status = Column(String(32), nullable=True, index=True)
    to_status = Column(String(32), nullable=False, index=True)
    reason = Column(Text)
    actor = Column(String(128), index=True)  # who triggered the transition (could be service account)

    interlinkage = relationship("Interlinkage", back_populates="workflow_events")


# -----------------------------------------------------------------------------
# Data Lineage / Import provenance
# -----------------------------------------------------------------------------
class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True)
    system_code = Column(String(64), nullable=False, unique=True, index=True)  # e.g., CALYPSO, SUMMIT, MUREX, INTERNAL
    label = Column(String(128), nullable=False)
    description = Column(Text)


class ImportBatch(Base, AuditMixin):
    __tablename__ = "import_batches"

    id = Column(Integer, primary_key=True)
    data_source_id = Column(Integer, ForeignKey("data_sources.id", ondelete="RESTRICT"), nullable=False, index=True)
    run_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    external_ref = Column(String(128), nullable=True, index=True)  # file name, batch id, etc.
    status = Column(String(32), nullable=False, default="completed", index=True)  # completed/failed/partial
    details = Column(Text)

    data_source = relationship("DataSource")


class InterlinkageSourceMap(Base):
    """
    Optional: map each Interlinkage to the import batch and raw identifiers used to create/update it.
    """
    __tablename__ = "interlinkage_source_map"

    id = Column(Integer, primary_key=True)
    interlinkage_id = Column(Integer, ForeignKey("interlinkages.id", ondelete="CASCADE"), nullable=False, index=True)
    import_batch_id = Column(Integer, ForeignKey("import_batches.id", ondelete="CASCADE"), nullable=False, index=True)

    raw_key = Column(String(255), nullable=True)     # raw id from source
    raw_payload_ref = Column(String(1024), nullable=True)  # pointer to full raw message/file

    __table_args__ = (UniqueConstraint("interlinkage_id", "import_batch_id", name="uq_interlinkage_batch"),)

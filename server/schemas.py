from marshmallow import Schema, fields, validate, EXCLUDE


# Reference / light schemas (extend as you need)

class IdOnly(Schema):
    id = fields.Int(dump_only=True)


class CurrencySchema(Schema):
    class Meta: unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    code = fields.Str(required=True, validate=validate.Length(equal=3))
    name = fields.Str()


class CountrySchema(Schema):
    class Meta: unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    iso2 = fields.Str(required=True, validate=validate.Length(equal=2))
    iso3 = fields.Str(validate=validate.Length(equal=3))
    name = fields.Str()


class SectorSchema(Schema):
    class Meta: unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    code = fields.Str(required=True)
    label = fields.Str(required=True)
    description = fields.Str()


class PraActivitySchema(Schema):
    class Meta: unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    code = fields.Str(required=True)
    label = fields.Str(required=True)
    description = fields.Str()


class CounterpartyTypeSchema(Schema):
    class Meta: unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    code = fields.Str(required=True)
    label = fields.Str(required=True)
    description = fields.Str()


class LegalEntitySchema(Schema):
    class Meta: unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    rmpm_code = fields.Str(required=True)
    rmpm_type = fields.Str(required=True)
    name = fields.Str(required=True)
    description = fields.Str()
    lei_code = fields.Str()
    country_id = fields.Int(allow_none=True)
    sector_id = fields.Int(allow_none=True)
    is_sanctioned = fields.Bool()
    is_pep = fields.Bool()
    aml_risk = fields.Str()

    # ✅ expose audit + soft-delete flags for GETs (needed by your test)
    created_at = fields.DateTime(dump_only=True)
    created_by = fields.Str(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    updated_by = fields.Str(dump_only=True)
    is_deleted = fields.Bool(dump_only=True)
    deleted_at = fields.DateTime(dump_only=True)
    deleted_by = fields.Str(dump_only=True)


class ProjectSchema(Schema):
    class Meta: unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    code = fields.Str()
    name = fields.Str(required=True)
    description = fields.Str()
    sector_id = fields.Int(allow_none=True)
    country_id = fields.Int(allow_none=True)
    region = fields.Str()
    business_line = fields.Str()
    portfolio = fields.Str()


class FacilitySchema(Schema):
    class Meta: unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    facility_type_id = fields.Int(required=True)
    reference = fields.Str(required=True)
    limit_amount = fields.Decimal(as_string=True, required=True)
    currency_id = fields.Int(required=True)
    maturity_date = fields.Date(allow_none=True)


class InstrumentSchema(Schema):
    class Meta: unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    instrument_type_id = fields.Int(required=True)
    reference = fields.Str()
    description = fields.Str()

class InstrumentTypeSchema(Schema):
    class Meta: unknown = EXCLUDE
    id = fields.Int(dump_only=True)
    code = fields.Str(required=True)
    label = fields.Str(required=True)
    description = fields.Str()
    # (optional) audit fields
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    is_deleted = fields.Bool(dump_only=True)

class FacilityTypeSchema(Schema):
    class Meta: unknown = EXCLUDE
    id = fields.Int(dump_only=True)
    code = fields.Str(required=True)
    label = fields.Str(required=True)
    description = fields.Str()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    is_deleted = fields.Bool(dump_only=True)


class InterlinkageSchema(Schema):
    class Meta: unknown = EXCLUDE

    id = fields.Int(dump_only=True)

    sponsor_id = fields.Int(required=True)
    counterparty_id = fields.Int(required=True)
    booking_entity_id = fields.Int(allow_none=True)

    project_id = fields.Int(required=True)
    pra_activity_id = fields.Int(allow_none=True)
    counterparty_type_id = fields.Int(allow_none=True)

    facility_id = fields.Int(allow_none=True)
    instrument_id = fields.Int(allow_none=True)

    deal_date = fields.Date(allow_none=True)
    effective_date = fields.Date(allow_none=True)
    maturity_date = fields.Date(allow_none=True)

    notional_amount = fields.Decimal(as_string=True, allow_none=True)
    currency_id = fields.Int(allow_none=True)

    status = fields.Str(required=True, validate=validate.OneOf(["draft", "validated", "archived", "deleted"]))
    purpose = fields.Str()
    remarks = fields.Str()

    # audit / soft delete exposed read-only
    created_at = fields.DateTime(dump_only=True)
    created_by = fields.Str(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    updated_by = fields.Str(dump_only=True)
    is_deleted = fields.Bool(dump_only=True)

class EntityIdentifierSchema(Schema):
    class Meta:
        unknown = EXCLUDE
    id = fields.Int(dump_only=True)
    entity_id = fields.Int(required=True)                  # FK to legal_entities.id
    scheme = fields.Str(required=True, validate=validate.Length(max=64))
    value  = fields.Str(required=True, validate=validate.Length(max=128))
    # (optional) read-only audit if you have them on the mixins
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class InterlinkageAnalysisSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Int(dump_only=True)

    # FK to interlinkages.id
    interlinkage_id = fields.Int(required=True)

    # HTML or text content of the analysis
    content = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=65535)  # typical TEXT max size guard
    )

    # Audit fields from mixins (read-only)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class InterdependenceSchema(Schema):
    class Meta: unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    interlinkage_id = fields.Int(required=True)
    interdependence_identifier = fields.Str(required=True)
    type = fields.Str(validate=validate.OneOf([
        "ownership", "credit", "guarantee", "management", "technical",
        "juridical", "legal", "contractual", "equity", "funding", "governance", "strategic", "other"
    ]))
    level = fields.Str(validate=validate.OneOf(["low", "medium", "high", "critical"]))
    project_id = fields.Int(allow_none=True)
    project_name = fields.Str()
    risk_assessment = fields.Str()
    effective_date = fields.Date(allow_none=True)
    expiry_date = fields.Date(allow_none=True)

class InterlinkageAttachmentSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    interlinkage_id = fields.Int(required=True)

    filename = fields.Str(required=True, validate=validate.Length(max=255))
    mime_type = fields.Str(allow_none=True, validate=validate.Length(max=128))
    storage_uri = fields.Str(required=True, validate=validate.Length(max=1024))
    description = fields.Str(allow_none=True)

    # audit / soft-delete (read-only from mixins)
    created_at = fields.DateTime(dump_only=True)
    created_by = fields.Str(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    updated_by = fields.Str(dump_only=True)
    is_deleted = fields.Bool(dump_only=True)
    deleted_at = fields.DateTime(dump_only=True)
    deleted_by = fields.Str(dump_only=True)

class InterlinkageNoteSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    interlinkage_id = fields.Int(required=True)

    title = fields.Str(required=True, validate=validate.Length(max=255))
    body = fields.Str(required=True)
    visibility = fields.Str(
        allow_none=True,
        validate=validate.OneOf(["internal", "external"], error="Visibility must be 'internal' or 'external'")
    )

    # audit fields
    created_at = fields.DateTime(dump_only=True)
    created_by = fields.Str(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    updated_by = fields.Str(dump_only=True)

    # soft delete fields
    is_deleted = fields.Bool(dump_only=True)
    deleted_at = fields.DateTime(dump_only=True)
    deleted_by = fields.Str(dump_only=True)


class WorkflowEventSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    interlinkage_id = fields.Int(required=True)

    from_status = fields.Str(allow_none=True, validate=validate.Length(max=32))
    to_status = fields.Str(required=True, validate=validate.Length(max=32))
    reason = fields.Str(allow_none=True)
    actor = fields.Str(allow_none=True, validate=validate.Length(max=128))

    # audit
    created_at = fields.DateTime(dump_only=True)
    created_by = fields.Str(dump_only=True)

# Optional: for list endpoints with pagination/filter
class AttachmentListQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    interlinkage_id = fields.Int(required=True)
    page = fields.Int(load_default=1)
    page_size = fields.Int(load_default=50, validate=validate.Range(min=1, max=1000))
    sort = fields.Str(load_default="id:desc")  # simple "col:dir"


# Optional: form fields for multipart upload (file handled via request.files)
class AttachmentUploadFormSchema(Schema):
    class Meta:
        unknown = EXCLUDE
    interlinkage_id = fields.Int(required=True)
    description = fields.Str(allow_none=True)

class ExposureSnapshotSchema(Schema):
    class Meta: unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    interlinkage_id = fields.Int(required=True)
    as_of_date = fields.Date(required=True)
    currency_id = fields.Int(required=True)
    ead = fields.Decimal(as_string=True)
    undrawn = fields.Decimal(as_string=True)
    mtm = fields.Decimal(as_string=True)
    pnl = fields.Decimal(as_string=True)
    rwa = fields.Decimal(as_string=True)
    pd = fields.Decimal(as_string=True)
    lgd = fields.Decimal(as_string=True)
    fx_to_reporting = fields.Decimal(as_string=True)

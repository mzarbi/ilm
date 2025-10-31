# server/api/routes.py
import hashlib
import mimetypes
import os
import time
from pathlib import Path
from urllib.parse import urlparse
from datetime import date, datetime, timedelta

from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename

from ..database import session_scope
from ..crud import list_items, get_item, create_item, update_item, delete_item
from .. import models as m
from ..schemas import (
    CurrencySchema, CountrySchema, SectorSchema, PraActivitySchema, CounterpartyTypeSchema,
    LegalEntitySchema, ProjectSchema, FacilitySchema, InstrumentSchema,
    InterlinkageSchema, InterdependenceSchema, ExposureSnapshotSchema, InstrumentTypeSchema, FacilityTypeSchema,
    EntityIdentifierSchema, InterlinkageAnalysisSchema, InterlinkageAttachmentSchema, InterlinkageNoteSchema,
    WorkflowEventSchema
)

api_bp = Blueprint("api", __name__, url_prefix="/api")

RESOURCES = [
    (m.Currency,            "currencies",          CurrencySchema()),
    (m.Country,             "countries",           CountrySchema()),
    (m.Sector,              "sectors",             SectorSchema()),
    (m.PraActivity,         "pra-activities",      PraActivitySchema()),
    (m.CounterpartyType,    "counterparty-types",  CounterpartyTypeSchema()),
    (m.LegalEntity,         "legal-entities",      LegalEntitySchema()),
    (m.Project,             "projects",            ProjectSchema()),
    (m.Facility,            "facilities",          FacilitySchema()),
    (m.Instrument,          "instruments",         InstrumentSchema()),
    (m.Interlinkage,        "interlinkages",       InterlinkageSchema()),
    (m.Interdependence,     "interdependen"
                            "ces",    InterdependenceSchema()),
    (m.ExposureSnapshot,    "exposures",           ExposureSnapshotSchema()),
    (m.InstrumentType, "instrument-types", InstrumentTypeSchema()),
    (m.FacilityType,   "facility-types",   FacilityTypeSchema()),
    (m.EntityIdentifier,    "entity-identifiers",  EntityIdentifierSchema()),
    (m.InterlinkageAnalysis,    "interlinkage-analyses",  InterlinkageAnalysisSchema()),
    (m.InterlinkageAttachment, "interlinkage-attachments", InterlinkageAttachmentSchema()),
    (m.InterlinkageNote, "interlinkage-notes", InterlinkageNoteSchema()),
    (m.WorkflowEvent, "workflow-events", WorkflowEventSchema()),
]

for model, name, schema in RESOURCES:
    list_ep        = f"/{name}"
    item_get_ep    = f"/{name}/<int:item_id>"
    item_update_ep = f"/{name}/<int:item_id>/update"   # POST for update
    item_delete_ep = f"/{name}/<int:item_id>/delete"   # POST for delete

    def _make_list(model=model, schema=schema):
        def _list():
            include_deleted = request.args.get("include_deleted") in ("1", "true", "yes")
            with session_scope() as s:
                return list_items(s, model, schema, include_deleted=include_deleted)
        _list.__name__ = f"{name}_list_view"
        return _list

    def _make_get(model=model, schema=schema):
        def _get(item_id: int):
            with session_scope() as s:
                return get_item(s, model, schema, item_id)
        _get.__name__ = f"{name}_get_view"
        return _get

    def _make_create(model=model, schema=schema):
        def _create():
            payload = request.get_json(force=True, silent=False)
            with session_scope() as s:
                return create_item(s, model, schema, payload)
        _create.__name__ = f"{name}_create_view"
        return _create

    def _make_update(model=model, schema=schema):
        def _update(item_id: int):
            # allow empty body meaning "no-op"
            payload = request.get_json(silent=True) or {}
            with session_scope() as s:
                return update_item(s, model, schema, item_id, payload)
        _update.__name__ = f"{name}_update_view"
        return _update

    def _make_delete(model=model):
        def _delete(item_id: int):
            soft = request.args.get("soft", "1") != "0"
            with session_scope() as s:
                return delete_item(s, model, item_id, soft=soft)
        _delete.__name__ = f"{name}_delete_view"
        return _delete

    # unique endpoints
    api_bp.add_url_rule(list_ep,        view_func=_make_list(),   methods=["GET"],  endpoint=f"{name}_list")
    api_bp.add_url_rule(list_ep,        view_func=_make_create(), methods=["POST"], endpoint=f"{name}_create")
    api_bp.add_url_rule(item_get_ep,    view_func=_make_get(),    methods=["GET"],  endpoint=f"{name}_get")
    api_bp.add_url_rule(item_update_ep, view_func=_make_update(), methods=["POST"], endpoint=f"{name}_update")
    api_bp.add_url_rule(item_delete_ep, view_func=_make_delete(), methods=["POST"], endpoint=f"{name}_delete")


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

@api_bp.post("/interlinkage-attachments/upload")
def upload_interlinkage_attachment():
    """
    multipart/form-data:
      - interlinkage_id: int
      - description: str (optional)
      - file: binary (required)
    """
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "file_required"}), 400

    try:
        interlinkage_id = int(request.form.get("interlinkage_id", ""))
    except ValueError:
        return jsonify({"error": "invalid_interlinkage_id"}), 400

    description = request.form.get("description") or ""

    # filename + mime
    raw_name = file.filename or "upload.bin"
    filename = secure_filename(raw_name)[:255] or f"upload_{int(time.time())}.bin"
    mime = file.mimetype or mimetypes.guess_type(filename)[0] or "application/octet-stream"

    # decide storage root; default into ./data/attachments so it sits near your sqlite db
    base_dir = Path(current_app.config.get("ATTACHMENTS_DIR", "./data/attachments"))
    (base_dir / str(interlinkage_id)).mkdir(parents=True, exist_ok=True)

    # avoid overwrite
    target = base_dir / str(interlinkage_id) / filename
    if target.exists():
        stem, ext = os.path.splitext(filename)
        filename = f"{stem}_{int(time.time())}{ext}"
        target = base_dir / str(interlinkage_id) / filename

    # save
    file.save(target.as_posix())
    size = target.stat().st_size
    checksum = _sha256(target.as_posix())

    # file:// URI so your FE link works even before you add an HTTP download route
    storage_uri = f"file://{target.resolve().as_posix()}"

    with session_scope() as s:
        row = m.InterlinkageAttachment(
            interlinkage_id=interlinkage_id,
            filename=filename,
            mime_type=mime,
            storage_uri=storage_uri,
            description=description,
        )
        s.add(row)
        s.flush()  # get row.id

        payload = InterlinkageAttachmentSchema().dump(row)
        # enrich (not persisted unless you add columns)
        payload.update({"size": size, "checksum": checksum})

        return jsonify(payload), 201



def _attachments_root(app) -> Path:
    return Path(app.config.get("ATTACHMENTS_DIR", "./data/attachments")).resolve()

def _path_from_storage_uri(storage_uri: str) -> Path:
    """
    Accepts file://C:/...  or file:///C:/...  or plain absolute paths.
    Returns a resolved pathlib.Path.
    """
    if not storage_uri:
        return None
    if storage_uri.lower().startswith("file://"):
        parsed = urlparse(storage_uri)
        if parsed.netloc and parsed.path:
            # e.g. file://localhost/C:/path -> combine netloc+path on Windows is tricky; prefer path
            p = Path(parsed.path)
        else:
            # e.g. file://C:/path
            p = Path(storage_uri.replace("file://", "", 1))
        return p.resolve()
    # fallback: treat as path
    return Path(storage_uri).resolve()

def _is_subpath(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except Exception:
        return False

@api_bp.get("/interlinkage-attachments/<int:att_id>/download")
def download_interlinkage_attachment(att_id: int):
    with session_scope() as s:
        row = s.get(m.InterlinkageAttachment, att_id)
        if not row:
            return {"error": "not_found"}, 404

        base_dir = _attachments_root(current_app)
        fs_path = _path_from_storage_uri(row.storage_uri)
        if not fs_path or not fs_path.exists():
            return {"error": "file_missing"}, 404

        # Security: enforce files must live under ATTACHMENTS_DIR
        if not _is_subpath(fs_path, base_dir):
            return {"error": "forbidden_path"}, 403

        # Stream with download filename & correct mime
        return send_file(
            fs_path,
            mimetype=row.mime_type or "application/octet-stream",
            as_attachment=True,
            download_name=row.filename or fs_path.name,
            max_age=0,
            conditional=True,
        )

from sqlalchemy import func, and_, or_, select
from sqlalchemy.orm import selectinload

@api_bp.get("/focus-bundle")
def focus_bundle():
    """
    Return EVERYTHING related to a selected focus, in one efficient payload.

    Query params:
      - kind: 'project' | 'entity' | 'interlinkage'   (required)
      - id:   int                                     (required)
      - include_interdeps: 0|1 (default 1)
      - exposures_mode: 'none' | 'latest' | 'last_n'  (default 'latest')
      - exposures_n: int (only used if exposures_mode='last_n'; default 12)
      - include_notes: 0|1 (default 1)
      - include_attachments: 0|1 (default 1)
      - include_workflow: 0|1 (default 1)
      - include_analysis: 0|1 (default 1)

    Response JSON (IDs are unique; ref tables are filtered to only what's used):
      {
        "focus": {"kind": "...", "id": ...},

        "projects": [...],
        "legal_entities": [...],
        "entity_identifiers": [...],
        "interlinkages": [...],
        "interdependences": [...],

        "facilities": [...],
        "instruments": [...],
        "currencies": [...],

        "exposures": [...],          // per chosen exposures_mode
        "attachments": [...],
        "notes": [...],
        "workflow_events": [...],
        "analyses": [...],

        "ref": {
          "countries": [...],
          "sectors": [...],
          "pra_activities": [...],
          "counterparty_types": [...],
          "instrument_types": [...],
          "facility_types": [...]
        },

        "edges": [
          // entity <-> interlinkage (role-aware)
          {"type":"entity-interlinkage","role":"sponsor","entity_id":..,"interlinkage_id":..},
          {"type":"entity-interlinkage","role":"counterparty","entity_id":..,"interlinkage_id":..},
          {"type":"entity-interlinkage","role":"booking","entity_id":..,"interlinkage_id":..},

          // interlinkage <-> project
          {"type":"interlinkage-project","interlinkage_id":..,"project_id":..},

          // interdep -> interlinkage
          {"type":"interdep-of","interdep_id":..,"interlinkage_id":..}
        ]
      }
    """
    # --------- helpers for query params
    def qstr(name, default=None):
        v = request.args.get(name)
        return v if (v is not None and v != "") else default

    def qint(name, default=None):
        try:
            return int(request.args.get(name))
        except Exception:
            return default

    def qbool(name, default=False):
        v = request.args.get(name)
        if v is None: return default
        return v.lower() in ("1", "true", "yes", "on")

    kind = qstr("kind")
    focus_id = qint("id")
    if kind not in ("project", "entity", "interlinkage") or not focus_id:
        return jsonify({"error": "invalid_args", "hint": "kind ∈ {project, entity, interlinkage} and id is required"}), 400

    include_interdeps = qbool("include_interdeps", True)
    exposures_mode     = qstr("exposures_mode", "latest")  # 'none' | 'latest' | 'last_n'
    exposures_n        = qint("exposures_n", 12)
    include_notes      = qbool("include_notes", True)
    include_attachments= qbool("include_attachments", True)
    include_workflow   = qbool("include_workflow", True)
    include_analysis   = qbool("include_analysis", True)

    # --------- tiny helper
    def not_deleted(q, Model):
        if hasattr(Model, "is_deleted"):
            return q.filter(Model.is_deleted == False)  # noqa: E712
        return q

    with session_scope() as s:
        # Accumulators (use sets for IDs to de-dup)
        proj_set, ent_set, il_set, dep_set = set(), set(), set(), set()
        fac_set, inst_set, ccy_set = set(), set(), set()
        exp_rows, att_rows, note_rows, wf_rows, an_rows = [], [], [], [], []
        edges = []

        # =============== FOCUS BRANCHES ===============
        if kind == "project":
            prj = not_deleted(s.query(m.Project).filter(m.Project.id == focus_id), m.Project).first()
            if not prj: return jsonify({"error":"not_found","entity":"project"}), 404
            proj_set.add(prj.id)

            # All interlinkages of this project
            ils = not_deleted(
                s.query(m.Interlinkage).options(
                    selectinload(m.Interlinkage.interdependences),
                    selectinload(m.Interlinkage.exposures),
                    selectinload(m.Interlinkage.attachments),
                    selectinload(m.Interlinkage.notes),
                    selectinload(m.Interlinkage.workflow_events),
                    selectinload(m.Interlinkage.analysis),
                ).filter(m.Interlinkage.project_id == prj.id),
                m.Interlinkage
            ).all()
            for i in ils:
                il_set.add(i.id)
                # related entity ids
                if i.sponsor_id:       ent_set.add(i.sponsor_id)
                if i.counterparty_id:  ent_set.add(i.counterparty_id)
                if i.booking_entity_id:ent_set.add(i.booking_entity_id)
                # facility, instrument, currency
                if i.facility_id:  fac_set.add(i.facility_id)
                if i.instrument_id:inst_set.add(i.instrument_id)
                if i.currency_id:  ccy_set.add(i.currency_id)
                # edges
                if i.sponsor_id:       edges.append({"type":"entity-interlinkage","role":"sponsor","entity_id":i.sponsor_id,"interlinkage_id":i.id})
                if i.counterparty_id:  edges.append({"type":"entity-interlinkage","role":"counterparty","entity_id":i.counterparty_id,"interlinkage_id":i.id})
                if i.booking_entity_id:edges.append({"type":"entity-interlinkage","role":"booking","entity_id":i.booking_entity_id,"interlinkage_id":i.id})
                edges.append({"type":"interlinkage-project","interlinkage_id":i.id,"project_id":prj.id})
                # collect subrows
                if include_interdeps:
                    for d in i.interdependences: dep_set.add(d.id)
                if include_attachments: att_rows.extend(i.attachments or [])
                if include_notes:       note_rows.extend(i.notes or [])
                if include_workflow:    wf_rows.extend(i.workflow_events or [])
                if include_analysis and i.analysis: an_rows.append(i.analysis)

        elif kind == "entity":
            ent = not_deleted(s.query(m.LegalEntity).filter(m.LegalEntity.id == focus_id), m.LegalEntity).first()
            if not ent: return jsonify({"error":"not_found","entity":"legal_entity"}), 404
            ent_set.add(ent.id)

            ils = not_deleted(
                s.query(m.Interlinkage).options(
                    selectinload(m.Interlinkage.interdependences),
                    selectinload(m.Interlinkage.exposures),
                    selectinload(m.Interlinkage.attachments),
                    selectinload(m.Interlinkage.notes),
                    selectinload(m.Interlinkage.workflow_events),
                    selectinload(m.Interlinkage.analysis),
                ).filter(
                    or_(
                        m.Interlinkage.sponsor_id == ent.id,
                        m.Interlinkage.counterparty_id == ent.id,
                        m.Interlinkage.booking_entity_id == ent.id
                    )
                ),
                m.Interlinkage
            ).all()
            for i in ils:
                il_set.add(i.id)
                if i.project_id: proj_set.add(i.project_id)
                if i.sponsor_id: ent_set.add(i.sponsor_id)
                if i.counterparty_id: ent_set.add(i.counterparty_id)
                if i.booking_entity_id: ent_set.add(i.booking_entity_id)
                if i.facility_id:  fac_set.add(i.facility_id)
                if i.instrument_id:inst_set.add(i.instrument_id)
                if i.currency_id:  ccy_set.add(i.currency_id)
                # edges
                if i.sponsor_id:       edges.append({"type":"entity-interlinkage","role":"sponsor","entity_id":i.sponsor_id,"interlinkage_id":i.id})
                if i.counterparty_id:  edges.append({"type":"entity-interlinkage","role":"counterparty","entity_id":i.counterparty_id,"interlinkage_id":i.id})
                if i.booking_entity_id:edges.append({"type":"entity-interlinkage","role":"booking","entity_id":i.booking_entity_id,"interlinkage_id":i.id})
                if i.project_id:       edges.append({"type":"interlinkage-project","interlinkage_id":i.id,"project_id":i.project_id})
                # collect subrows
                if include_interdeps:
                    for d in i.interdependences: dep_set.add(d.id)
                if include_attachments: att_rows.extend(i.attachments or [])
                if include_notes:       note_rows.extend(i.notes or [])
                if include_workflow:    wf_rows.extend(i.workflow_events or [])
                if include_analysis and i.analysis: an_rows.append(i.analysis)

        else:  # kind == "interlinkage"
            inter = not_deleted(
                s.query(m.Interlinkage).options(
                    selectinload(m.Interlinkage.interdependences),
                    selectinload(m.Interlinkage.exposures),
                    selectinload(m.Interlinkage.attachments),
                    selectinload(m.Interlinkage.notes),
                    selectinload(m.Interlinkage.workflow_events),
                    selectinload(m.Interlinkage.analysis),
                ).filter(m.Interlinkage.id == focus_id),
                m.Interlinkage
            ).first()
            if not inter: return jsonify({"error":"not_found","entity":"interlinkage"}), 404
            il_set.add(inter.id)
            if inter.project_id: proj_set.add(inter.project_id)
            if inter.sponsor_id: ent_set.add(inter.sponsor_id)
            if inter.counterparty_id: ent_set.add(inter.counterparty_id)
            if inter.booking_entity_id: ent_set.add(inter.booking_entity_id)
            if inter.facility_id:  fac_set.add(inter.facility_id)
            if inter.instrument_id:inst_set.add(inter.instrument_id)
            if inter.currency_id:  ccy_set.add(inter.currency_id)
            # edges
            if inter.sponsor_id:       edges.append({"type":"entity-interlinkage","role":"sponsor","entity_id":inter.sponsor_id,"interlinkage_id":inter.id})
            if inter.counterparty_id:  edges.append({"type":"entity-interlinkage","role":"counterparty","entity_id":inter.counterparty_id,"interlinkage_id":inter.id})
            if inter.booking_entity_id:edges.append({"type":"entity-interlinkage","role":"booking","entity_id":inter.booking_entity_id,"interlinkage_id":inter.id})
            if inter.project_id:       edges.append({"type":"interlinkage-project","interlinkage_id":inter.id,"project_id":inter.project_id})
            # collect subrows
            if include_interdeps:
                for d in inter.interdependences:
                    dep_set.add(d.id)
            if include_attachments: att_rows.extend(inter.attachments or [])
            if include_notes:       note_rows.extend(inter.notes or [])
            if include_workflow:    wf_rows.extend(inter.workflow_events or [])
            if include_analysis and inter.analysis: an_rows.append(inter.analysis)

        # =============== BULK FETCH SECONDARY TABLES ===============
        projects = []
        if proj_set:
            projects = not_deleted(
                s.query(m.Project).filter(m.Project.id.in_(proj_set)),
                m.Project
            ).all()

        interlinkages = []
        if il_set:
            # Re-fetch minimal interlinkage rows to ensure consistent dump (avoid double-loading heavy rels here)
            interlinkages = not_deleted(
                s.query(m.Interlinkage).filter(m.Interlinkage.id.in_(il_set)),
                m.Interlinkage
            ).all()

        entities = []
        if ent_set:
            entities = not_deleted(
                s.query(m.LegalEntity).filter(m.LegalEntity.id.in_(ent_set)),
                m.LegalEntity
            ).all()

        facilities = []
        if fac_set:
            facilities = not_deleted(
                s.query(m.Facility).filter(m.Facility.id.in_(fac_set)),
                m.Facility
            ).all()

        instruments = []
        if inst_set:
            instruments = not_deleted(
                s.query(m.Instrument).filter(m.Instrument.id.in_(inst_set)),
                m.Instrument
            ).all()

        currencies = []
        if ccy_set:
            currencies = not_deleted(
                s.query(m.Currency).filter(m.Currency.id.in_(ccy_set)),
                m.Currency
            ).all()

        # Interdeps
        interdeps = []
        if dep_set:
            interdeps = not_deleted(
                s.query(m.Interdependence).filter(m.Interdependence.id.in_(dep_set)),
                m.Interdependence
            ).all()

        # Exposures (mode-dependent)
        exposures = []
        if exposures_mode != "none" and il_set:
            if exposures_mode == "latest":
                # one latest row per interlinkage
                sub = (
                    s.query(
                        m.ExposureSnapshot.interlinkage_id,
                        func.max(m.ExposureSnapshot.as_of_date).label("max_d")
                    )
                    .filter(m.ExposureSnapshot.interlinkage_id.in_(il_set))
                    .group_by(m.ExposureSnapshot.interlinkage_id)
                    .subquery()
                )
                exposures = not_deleted(
                    s.query(m.ExposureSnapshot)
                    .join(sub, and_(
                        m.ExposureSnapshot.interlinkage_id == sub.c.interlinkage_id,
                        m.ExposureSnapshot.as_of_date == sub.c.max_d
                    )),
                    m.ExposureSnapshot
                ).all()
            elif exposures_mode == "last_n":
                # last N per interlinkage (portable windowing)
                # get top N dates per il, then fetch rows by (il_id, date) pairs
                date_rows = (
                    s.query(
                        m.ExposureSnapshot.interlinkage_id,
                        m.ExposureSnapshot.as_of_date
                    )
                    .filter(m.ExposureSnapshot.interlinkage_id.in_(il_set))
                    .order_by(m.ExposureSnapshot.interlinkage_id, m.ExposureSnapshot.as_of_date.desc())
                    .all()
                )
                wanted_pairs = set()
                count_per_il = {}
                for il_id, d in date_rows:
                    c = count_per_il.get(il_id, 0)
                    if c < exposures_n:
                        wanted_pairs.add((il_id, d))
                        count_per_il[il_id] = c + 1
                if wanted_pairs:
                    conds = [and_(
                        m.ExposureSnapshot.interlinkage_id == il,
                        m.ExposureSnapshot.as_of_date == dt
                    ) for (il, dt) in wanted_pairs]
                    exposures = not_deleted(
                        s.query(m.ExposureSnapshot).filter(or_(*conds)),
                        m.ExposureSnapshot
                    ).all()

        # Deduplicate row lists we collected from eager loads
        if include_attachments:
            att_rows = list({a.id: a for a in att_rows}.values())
        if include_notes:
            note_rows = list({n.id: n for n in note_rows}.values())
        if include_workflow:
            wf_rows = list({w.id: w for w in wf_rows}.values())
        if include_analysis:
            an_rows = list({a.id: a for a in an_rows}.values())

        # Reference rows actually used
        country_ids = {p.country_id for p in projects if p.country_id} | {e.country_id for e in entities if e.country_id}
        sector_ids  = {p.sector_id for p in projects if p.sector_id}  | {e.sector_id for e in entities if e.sector_id}
        pra_ids     = {i.pra_activity_id for i in interlinkages if i.pra_activity_id}
        cpty_type_ids = {i.counterparty_type_id for i in interlinkages if i.counterparty_type_id}
        inst_type_ids = {x.instrument_type_id for x in instruments if getattr(x, "instrument_type_id", None)}
        fac_type_ids  = {x.facility_type_id for x in facilities if getattr(x, "facility_type_id", None)}

        countries = s.query(m.Country).filter(m.Country.id.in_(country_ids)).all() if country_ids else []
        sectors   = s.query(m.Sector).filter(m.Sector.id.in_(sector_ids)).all() if sector_ids else []
        pra_acts  = s.query(m.PraActivity).filter(m.PraActivity.id.in_(pra_ids)).all() if pra_ids else []
        cpty_types= s.query(m.CounterpartyType).filter(m.CounterpartyType.id.in_(cpty_type_ids)).all() if cpty_type_ids else []
        inst_types= s.query(m.InstrumentType).filter(m.InstrumentType.id.in_(inst_type_ids)).all() if inst_type_ids else []
        fac_types = s.query(m.FacilityType).filter(m.FacilityType.id.in_(fac_type_ids)).all() if fac_type_ids else []

        # Entity identifiers for the returned entities
        identifiers = []
        if ent_set:
            identifiers = s.query(m.EntityIdentifier).filter(m.EntityIdentifier.entity_id.in_(ent_set)).all()

        # --------- Serialize using your existing Marshmallow schemas
        payload = {
            "focus": {"kind": kind, "id": focus_id},

            "projects":              ProjectSchema(many=True).dump(projects),
            "legal_entities":        LegalEntitySchema(many=True).dump(entities),
            "entity_identifiers":    EntityIdentifierSchema(many=True).dump(identifiers),
            "interlinkages":         InterlinkageSchema(many=True).dump(interlinkages),
            "interdependences":      InterdependenceSchema(many=True).dump(interdeps),

            "facilities":            FacilitySchema(many=True).dump(facilities),
            "instruments":           InstrumentSchema(many=True).dump(instruments),
            "currencies":            CurrencySchema(many=True).dump(currencies),

            "exposures":             (ExposureSnapshotSchema(many=True).dump(exposures) if exposures_mode != "none" else []),
            "attachments":           (InterlinkageAttachmentSchema(many=True).dump(att_rows) if include_attachments else []),
            "notes":                 (InterlinkageNoteSchema(many=True).dump(note_rows) if include_notes else []),
            "workflow_events":       (WorkflowEventSchema(many=True).dump(wf_rows) if include_workflow else []),
            "analyses":              (InterlinkageAnalysisSchema(many=True).dump(an_rows) if include_analysis else []),

            "ref": {
                "countries":         CountrySchema(many=True).dump(countries),
                "sectors":           SectorSchema(many=True).dump(sectors),
                "pra_activities":    PraActivitySchema(many=True).dump(pra_acts),
                "counterparty_types":CounterpartyTypeSchema(many=True).dump(cpty_types),
                "instrument_types":  InstrumentTypeSchema(many=True).dump(inst_types),
                "facility_types":    FacilityTypeSchema(many=True).dump(fac_types),
            },

            "edges": edges,
        }
        return jsonify(payload), 200

@api_bp.post("/analysis/concentration/shared-dependencies")
def analysis_concentration_shared_dependencies():
    """
    POST JSON:
      {
        "pov_kind": "project" | "entity" | "interlinkage",
        "pov_id":   <int>,
        "group_by": "identifier" | "type" | "id_type" | "type_level",   # default: "identifier"
        "min_cluster": <int>=2,
        "levels": ["low","medium","high","critical"],                   # optional filter
        "measure": "none" | "ead" | "rwa" | "mtm" | "pnl",              # default: "none"
        "exposures_mode": "latest" | "none"                             # default: "latest"
      }

    Response:
      {
        "scope": { "pov_kind": "...", "pov_id": ..., "interlinkage_ids": [...] },
        "params": { ...echoed... },
        "clusters": [
          {
            "key":         "<group key>",
            "label":       "<same as key or pretty label>",
            "by":          "identifier|type|id_type|type_level",
            "il_count":    <int>,     # distinct interlinkages in this cluster
            "dep_count":   <int>,     # interdependence rows in this cluster
            "levels":      ["high","low",...],      # distinct levels present
            "types":       ["technical","contractual", ...],
            "interlinkages": [
              {
                "id": <int>,
                "project_id": <int|null>,
                "sponsor_id": <int|null>,
                "sponsor_name": <str|null>,          # ENRICHED
                "counterparty_id": <int|null>,
                "counterparty_name": <str|null>,     # ENRICHED
                "notional_amount": <str|null>,
                "currency_id": <int|null>,
                "currency_code": <str|null>,         # ENRICHED (e.g., "EUR")
                "measure": <str|null>                # latest EAD/RWA/MTM/PNL if requested
              },
              ...
            ]
          },
          ...
        ],
        "overlay": {
          "nodes": [
            { "kind": "cluster", "id": "cluster:<key>", "label": "<label>", "size_hint": <int>, "il_count": <int> }
          ],
          "links": [
            { "from": "il:<id>", "to": "cluster:<key>", "label": "shared-dependency" }
          ]
        }
      }
    """
    body = request.get_json(force=True, silent=False) or {}

    pov_kind      = (body.get("pov_kind") or "").strip().lower()
    pov_id        = body.get("pov_id")
    group_by      = (body.get("group_by") or "identifier").strip().lower()
    min_cluster   = int(body.get("min_cluster") or 2)
    levels_flt    = body.get("levels") or []
    measure       = (body.get("measure") or "none").strip().lower()
    exposures_mode= (body.get("exposures_mode") or "latest").strip().lower()

    if pov_kind not in ("project", "entity", "interlinkage") or not isinstance(pov_id, int):
        return jsonify({"error": "invalid_args",
                        "hint": "pov_kind ∈ {project, entity, interlinkage} and pov_id must be int"}), 400
    if group_by not in ("identifier", "type", "id_type", "type_level"):
        return jsonify({"error": "invalid_group_by"}), 400
    if measure not in ("none", "ead", "rwa", "mtm", "pnl"):
        return jsonify({"error": "invalid_measure"}), 400
    if exposures_mode not in ("latest", "none"):
        return jsonify({"error": "invalid_exposures_mode"}), 400
    if min_cluster < 2:
        min_cluster = 2

    def not_deleted(q, Model):
        return q.filter(getattr(Model, "is_deleted", False) == False) if hasattr(Model, "is_deleted") else q  # noqa: E712

    with session_scope() as s:
        # ------------------ Scope: which Interlinkage IDs are in play ------------------
        if pov_kind == "project":
            q = not_deleted(s.query(m.Interlinkage.id).filter(m.Interlinkage.project_id == pov_id), m.Interlinkage)
            il_ids = {row[0] for row in q.all()}
        elif pov_kind == "entity":
            q = not_deleted(
                s.query(m.Interlinkage.id).filter(
                    or_(
                        m.Interlinkage.sponsor_id == pov_id,
                        m.Interlinkage.counterparty_id == pov_id,
                        m.Interlinkage.booking_entity_id == pov_id
                    )
                ),
                m.Interlinkage
            )
            il_ids = {row[0] for row in q.all()}
        else:  # interlinkage
            row = not_deleted(s.query(m.Interlinkage.id).filter(m.Interlinkage.id == pov_id), m.Interlinkage).first()
            if not row:
                return jsonify({"error": "not_found", "entity": "interlinkage"}), 404
            il_ids = {pov_id}

        if not il_ids:
            return jsonify({
                "scope":   {"pov_kind": pov_kind, "pov_id": pov_id, "interlinkage_ids": []},
                "params":  {"group_by": group_by, "min_cluster": min_cluster, "levels": levels_flt,
                            "measure": measure, "exposures_mode": exposures_mode},
                "clusters": [],
                "overlay": {"nodes": [], "links": []}
            }), 200

        # ------------------ Load Interdependences in scope (+ optional level filter) ------------------
        qd = not_deleted(
            s.query(m.Interdependence)
             .filter(m.Interdependence.interlinkage_id.in_(il_ids)),
            m.Interdependence
        )
        if levels_flt:
            qd = qd.filter(m.Interdependence.level.in_(levels_flt))
        deps = qd.all()

        # ------------------ Grouping key ------------------
        def key_for(dep: m.Interdependence) -> str:
            ident = dep.interdependence_identifier or ""
            typ   = dep.type or ""
            lvl   = dep.level or ""
            if group_by == "identifier":
                return ident
            if group_by == "type":
                return typ
            if group_by == "id_type":
                return f"{ident} | {typ}"
            if group_by == "type_level":
                return f"{typ} | {lvl}"
            return ident

        buckets = {}  # key -> { "deps": [...], "il_ids": set(), "levels": set(), "types": set(), "key": key, "by": group_by }
        for d in deps:
            k = key_for(d)
            b = buckets.get(k)
            if not b:
                b = {"key": k, "by": group_by, "deps": [], "il_ids": set(), "levels": set(), "types": set()}
                buckets[k] = b
            b["deps"].append(d)
            b["il_ids"].add(d.interlinkage_id)
            if d.level: b["levels"].add(d.level)
            if d.type:  b["types"].add(d.type)

        # retain only clusters with at least N distinct interlinkages
        clusters_raw = [b for b in buckets.values() if len(b["il_ids"]) >= min_cluster]
        # sort: larger clusters first
        clusters_raw.sort(key=lambda b: (len(b["il_ids"]), len(b["deps"])), reverse=True)

        # ------------------ Pull needed ILs ------------------
        needed_il_ids = set().union(*(c["il_ids"] for c in clusters_raw)) if clusters_raw else set()
        il_rows = {}
        if needed_il_ids:
            q_ils = not_deleted(s.query(m.Interlinkage).filter(m.Interlinkage.id.in_(needed_il_ids)), m.Interlinkage)
            for il in q_ils.all():
                il_rows[il.id] = il

        # ------------------ Optional: latest exposures per IL (for measure != none) ------------------
        meas_map = {}
        if measure != "none" and needed_il_ids and exposures_mode == "latest":
            latest_sub = (
                s.query(
                    m.ExposureSnapshot.interlinkage_id,
                    func.max(m.ExposureSnapshot.as_of_date).label("max_d")
                )
                .filter(m.ExposureSnapshot.interlinkage_id.in_(needed_il_ids))
                .group_by(m.ExposureSnapshot.interlinkage_id)
                .subquery()
            )
            snaps = (
                s.query(m.ExposureSnapshot)
                .join(latest_sub,
                      and_(m.ExposureSnapshot.interlinkage_id == latest_sub.c.interlinkage_id,
                           m.ExposureSnapshot.as_of_date     == latest_sub.c.max_d))
                .all()
            )
            for r in snaps:
                v = getattr(r, measure, None)
                if v is not None:
                    meas_map[r.interlinkage_id] = v

        # ------------------ ENRICH: names & currency codes ------------------
        sponsor_ids   = set()
        counterpty_ids= set()
        currency_ids  = set()
        for il in il_rows.values():
            if il.sponsor_id:      sponsor_ids.add(il.sponsor_id)
            if il.counterparty_id: counterpty_ids.add(il.counterparty_id)
            if il.currency_id:     currency_ids.add(il.currency_id)

        name_by_entity_id = {}
        ent_ids = sponsor_ids | counterpty_ids
        if ent_ids:
            for ent in not_deleted(s.query(m.LegalEntity).filter(m.LegalEntity.id.in_(ent_ids)), m.LegalEntity).all():
                name_by_entity_id[ent.id] = ent.name or ""

        code_by_ccy_id = {}
        if currency_ids:
            for cur in s.query(m.Currency).filter(m.Currency.id.in_(currency_ids)).all():
                code_by_ccy_id[cur.id] = cur.code or ""

        # ------------------ Build response ------------------
        def label_for(key: str, by: str) -> str:
            # Keep terse; FE can prettify if needed
            return key or "—"

        resp_clusters = []
        overlay_nodes = []
        overlay_links = []

        for b in clusters_raw:
            il_summaries = []
            for il_id in sorted(b["il_ids"]):
                il = il_rows.get(il_id)
                if not il:
                    continue
                sv = {
                    "id": il.id,
                    "project_id": il.project_id,
                    "sponsor_id": il.sponsor_id,
                    "sponsor_name": name_by_entity_id.get(il.sponsor_id) or None,             # ENRICHED
                    "counterparty_id": il.counterparty_id,
                    "counterparty_name": name_by_entity_id.get(il.counterparty_id) or None,    # ENRICHED
                    "notional_amount": (str(il.notional_amount) if il.notional_amount is not None else None),
                    "currency_id": il.currency_id,
                    "currency_code": code_by_ccy_id.get(il.currency_id) or None,               # ENRICHED
                    "measure": (str(meas_map.get(il.id)) if meas_map.get(il.id) is not None else None)
                }
                il_summaries.append(sv)

            resp_clusters.append({
                "key": b["key"],
                "label": label_for(b["key"], b["by"]),
                "by": b["by"],
                "il_count": len(b["il_ids"]),
                "dep_count": len(b["deps"]),
                "levels": sorted(b["levels"]),
                "types": sorted(b["types"]),
                "interlinkages": il_summaries
            })

            # overlay cluster bubble; size hint scales with IL count
            overlay_nodes.append({
                "kind": "cluster",
                "id": f"cluster:{b['key']}",
                "label": label_for(b["key"], b["by"]),
                "size_hint": min(40 + len(b["il_ids"]) * 6, 120),
                "il_count": len(b["il_ids"])
            })
            for il_id in b["il_ids"]:
                overlay_links.append({
                    "from": f"il:{il_id}",
                    "to": f"cluster:{b['key']}",
                    "label": "shared-dependency"
                })

        return jsonify({
            "scope": {
                "pov_kind": pov_kind,
                "pov_id": pov_id,
                "interlinkage_ids": sorted(il_ids),
            },
            "params": {
                "group_by": group_by,
                "min_cluster": min_cluster,
                "levels": levels_flt,
                "measure": measure,
                "exposures_mode": exposures_mode
            },
            "clusters": resp_clusters,
            "overlay": {
                "nodes": overlay_nodes,
                "links": overlay_links
            }
        }), 200


@api_bp.post("/analysis/expiry-monitoring")
def analysis_expiry_monitoring():
    """
    Expiry monitoring for a given project POV.

    POST JSON
    ---------
    {
      "pov_id": <int>,                            # REQUIRED (project id)
      "window_start": "YYYY-MM-DD",               # optional, default: today
      "window_end":   "YYYY-MM-DD",               # optional, default: today + 365
      "buckets_days": [0, 30, 90, 180, 365],      # optional cut points (ascending)
      "include_overdue": true,                    # optional
      "measure": "none" | "ead" | "rwa" | "mtm" | "pnl",   # optional, default "none"
      "exposures_mode": "latest" | "none"                 # optional, default "latest"
    }

    Response
    --------
    {
      "scope": { "pov_kind": "project", "pov_id": <int>, "interlinkage_ids": [ ... ] },
      "params": { ...echoed... },

      "items": [
        {
          "id": <il_id>,
          "project_id": <int|null>,
          "sponsor_id": <int|null>,
          "sponsor_name": <str|null>,
          "counterparty_id": <int|null>,
          "counterparty_name": <str|null>,
          "currency_id": <int|null>,
          "currency_code": <str|null>,
          "notional_amount": <str|null>,

          "maturity_date": "YYYY-MM-DD",
          "days_to_maturity": <int>,      # negative => overdue
          "bucket": "<Overdue | 0-30 | 31-90 | 91-180 | >180 | Outside window>",
          "measure": <str|null>           # if requested and available
        },
        ...
      ],

      "buckets": [
        {
          "label": "Overdue" | "0-30" | "31-90" | "91-180" | ">180" | "Outside window",
          "from_days": <int|null>,     # inclusive (relative to today)
          "to_days": <int|null>,       # inclusive; null = open-ended
          "count": <int>,
          "total_notional": [
            { "currency_code": "EUR", "amount": "1234567.89" },
            ...
          ]
        },
        ...
      ],

      "overlay": {
        "nodes": [
          { "kind": "bucket", "id": "bucket:Overdue", "label": "Overdue", "size_hint": 60, "count": 3 },
          ...
        ],
        "links": [
          { "from": "il:<id>", "to": "bucket:<label>", "label": "expires-in" },
          ...
        ]
      }
    }
    """
    body = request.get_json(force=True, silent=False) or {}

    # ---- Inputs & defaults
    pov_id = body.get("pov_id")
    if not isinstance(pov_id, int):
        return jsonify({"error": "invalid_args", "hint": "pov_id (int) is required"}), 400

    # dates: default window [today, today+365]
    today = date.today()
    def _parse_d(s):
        try:
            return datetime.strptime(s, "%Y-%m-%d").date()
        except Exception:
            return None

    window_start = _parse_d(body.get("window_start")) or today
    window_end   = _parse_d(body.get("window_end")) or (today + timedelta(days=365))
    if window_end < window_start:
        window_start, window_end = window_end, window_start  # swap to be safe

    # buckets edges (days-from-today). Example: [0, 30, 90, 180, 365]
    buckets_days = body.get("buckets_days") or [0, 30, 90, 180, 365]
    buckets_days = sorted({int(x) for x in buckets_days if isinstance(x, (int, float))})
    include_overdue = bool(body.get("include_overdue", True))

    measure = (body.get("measure") or "none").strip().lower()
    if measure not in ("none", "ead", "rwa", "mtm", "pnl"):
        return jsonify({"error": "invalid_measure"}), 400
    exposures_mode = (body.get("exposures_mode") or "latest").strip().lower()
    if exposures_mode not in ("latest", "none"):
        return jsonify({"error": "invalid_exposures_mode"}), 400

    def not_deleted(q, Model):
        return q.filter(getattr(Model, "is_deleted", False) == False) if hasattr(Model, "is_deleted") else q  # noqa: E712

    # Helper to get maturity of an IL, checking multiple fields if needed
    def _get_il_maturity(il):
        # Try commonly used field names; adjust to your schema if different.
        if hasattr(il, "maturity_date") and il.maturity_date:
            return il.maturity_date
        if hasattr(il, "end_date") and il.end_date:
            return il.end_date
        return None

    # Build bucket ranges from the cut points, relative to "today"
    # Example with [0, 30, 90, 180, 365]:
    #   Overdue: (< 0) if include_overdue
    #   0-30, 31-90, 91-180, 181-365, >365
    def _build_bucket_labels(edges):
        labels = []
        if include_overdue:
            labels.append(("Overdue", None, -1))  # days <= -1

        if not edges:
            labels.append(("0+", 0, None))
            return labels

        # contiguous ranges like 0-30, 31-90, ...
        last = edges[0]
        labels.append((f"{last}-" + (str(edges[0]) if edges[0] == last else str(edges[0])), last, last))
        for i in range(len(edges)):
            if i == 0:
                # first closed range starts at edges[0]
                continue
            prev = edges[i - 1]
            cur  = edges[i]
            # ranges are inclusive; we make them: (prev+1) .. cur
            labels.append((f"{prev+1}-{cur}", prev + 1, cur))

        # > last edge
        labels.append((f">{edges[-1]}", edges[-1] + 1, None))
        return labels

    bucket_defs = _build_bucket_labels(buckets_days)

    with session_scope() as s:
        # --- Scope: ILs for this project
        q_il = not_deleted(s.query(m.Interlinkage).filter(m.Interlinkage.project_id == pov_id), m.Interlinkage)
        ils_all = q_il.all()
        if not ils_all:
            return jsonify({
                "scope": {"pov_kind": "project", "pov_id": pov_id, "interlinkage_ids": []},
                "params": {
                    "window_start": window_start.isoformat(),
                    "window_end": window_end.isoformat(),
                    "buckets_days": buckets_days,
                    "include_overdue": include_overdue,
                    "measure": measure,
                    "exposures_mode": exposures_mode
                },
                "items": [],
                "buckets": [],
                "overlay": {"nodes": [], "links": []}
            }), 200

        # Filter to ILs that actually have a maturity date & within (or around) the window
        # We still collect those outside window to place them in ">max" or "Outside window"
        # but we’ll primarily show buckets for the bounded ranges and overdue.
        il_by_id = {}
        maturity_map = {}   # il_id -> maturity_date
        for il in ils_all:
            mat = _get_il_maturity(il)
            if not mat:
                continue  # skip ILs with no maturity
            il_by_id[il.id] = il
            maturity_map[il.id] = mat

        if not il_by_id:
            return jsonify({
                "scope": {"pov_kind": "project", "pov_id": pov_id, "interlinkage_ids": []},
                "params": {
                    "window_start": window_start.isoformat(),
                    "window_end": window_end.isoformat(),
                    "buckets_days": buckets_days,
                    "include_overdue": include_overdue,
                    "measure": measure,
                    "exposures_mode": exposures_mode
                },
                "items": [],
                "buckets": [],
                "overlay": {"nodes": [], "links": []}
            }), 200

        # ---- Optional: latest exposures per IL
        meas_map = {}
        if measure != "none" and maturity_map and exposures_mode == "latest":
            latest_sub = (
                s.query(
                    m.ExposureSnapshot.interlinkage_id,
                    func.max(m.ExposureSnapshot.as_of_date).label("max_d")
                )
                .filter(m.ExposureSnapshot.interlinkage_id.in_(list(maturity_map.keys())))
                .group_by(m.ExposureSnapshot.interlinkage_id)
                .subquery()
            )
            snaps = (
                s.query(m.ExposureSnapshot)
                .join(latest_sub,
                      and_(m.ExposureSnapshot.interlinkage_id == latest_sub.c.interlinkage_id,
                           m.ExposureSnapshot.as_of_date     == latest_sub.c.max_d))
                .all()
            )
            for r in snaps:
                v = getattr(r, measure, None)
                if v is not None:
                    meas_map[r.interlinkage_id] = v

        # ---- Enrich: names/currencies
        sponsor_ids, cpty_ids, ccy_ids = set(), set(), set()
        for il in il_by_id.values():
            if il.sponsor_id:      sponsor_ids.add(il.sponsor_id)
            if il.counterparty_id: cpty_ids.add(il.counterparty_id)
            if il.currency_id:     ccy_ids.add(il.currency_id)

        name_by_entity = {}
        ent_ids = sponsor_ids | cpty_ids
        if ent_ids:
            ents = not_deleted(s.query(m.LegalEntity).filter(m.LegalEntity.id.in_(ent_ids)), m.LegalEntity).all()
            for e in ents:
                name_by_entity[e.id] = e.name or ""

        code_by_ccy = {}
        if ccy_ids:
            for c in s.query(m.Currency).filter(m.Currency.id.in_(ccy_ids)).all():
                code_by_ccy[c.id] = c.code or ""

        # ---- Build items & bucket assignment
        def _bucket_of(days):
            # days relative to today (negative => overdue)
            if include_overdue and days < 0:
                return "Overdue"
            # walk defined ranges
            for label, lo, hi in bucket_defs:
                if label == "Overdue":
                    continue
                if lo is not None and hi is not None and lo <= days <= hi:
                    return label
                if lo is not None and hi is None and days >= lo:
                    return label
            return "Outside window"

        items = []
        for il_id, il in il_by_id.items():
            mat = maturity_map[il_id]
            days_to = (mat - today).days
            bucket = _bucket_of(days_to)

            entry = {
                "id": il.id,
                "project_id": il.project_id,
                "sponsor_id": il.sponsor_id,
                "sponsor_name": name_by_entity.get(il.sponsor_id) or None,
                "counterparty_id": il.counterparty_id,
                "counterparty_name": name_by_entity.get(il.counterparty_id) or None,
                "currency_id": il.currency_id,
                "currency_code": code_by_ccy.get(il.currency_id) or None,
                "notional_amount": (str(il.notional_amount) if il.notional_amount is not None else None),
                "maturity_date": mat.isoformat(),
                "days_to_maturity": days_to,
                "bucket": bucket,
                "measure": (str(meas_map.get(il.id)) if meas_map.get(il.id) is not None else None)
            }
            items.append(entry)

        # ---- Aggregate per bucket (count + total notional per currency)
        from collections import defaultdict
        bucket_counts = defaultdict(int)
        bucket_totals = defaultdict(lambda: defaultdict(float))  # bucket -> ccy_code -> total

        def _as_float(x):
            try:
                return float(x)
            except Exception:
                return 0.0

        for it in items:
            b = it["bucket"]
            bucket_counts[b] += 1
            amt = _as_float(it["notional_amount"])
            ccy = it["currency_code"] or "—"
            bucket_totals[b][ccy] += amt

        # Bake bucket rows in a stable order:
        ordered_bucket_labels = [lbl for (lbl, _, _) in bucket_defs]
        if include_overdue and "Overdue" not in ordered_bucket_labels:
            ordered_bucket_labels = ["Overdue"] + ordered_bucket_labels
        # Also include "Outside window" if any
        if any(it["bucket"] == "Outside window" for it in items):
            ordered_bucket_labels.append("Outside window")

        buckets_resp = []
        for lbl in ordered_bucket_labels:
            # find bounds
            from_days, to_days = None, None
            for (bl, lo, hi) in bucket_defs:
                if bl == lbl:
                    from_days, to_days = lo, hi
                    break
            if lbl == "Overdue":
                from_days, to_days = None, -1
            if lbl == "Outside window":
                from_days, to_days = None, None

            totals = [
                {"currency_code": ccy, "amount": f"{amt:.2f}"}
                for ccy, amt in sorted(bucket_totals[lbl].items())
            ]
            buckets_resp.append({
                "label": lbl,
                "from_days": from_days,
                "to_days": to_days,
                "count": bucket_counts[lbl],
                "total_notional": totals
            })

        # ---- Overlay for simple graphing: bucket nodes + IL->bucket links
        overlay_nodes, overlay_links = [], []
        for b in buckets_resp:
            # skip empty buckets to reduce clutter
            if b["count"] <= 0:
                continue
            size_hint = min(40 + b["count"] * 6, 120)
            overlay_nodes.append({
                "kind": "bucket",
                "id": f"bucket:{b['label']}",
                "label": b["label"],
                "size_hint": size_hint,
                "count": b["count"]
            })
        for it in items:
            if it["bucket"] == "Outside window":
                continue
            overlay_links.append({
                "from": f"il:{it['id']}",
                "to": f"bucket:{it['bucket']}",
                "label": "expires-in"
            })

        return jsonify({
            "scope": {
                "pov_kind": "project",
                "pov_id": pov_id,
                "interlinkage_ids": sorted(list(il_by_id.keys()))
            },
            "params": {
                "window_start": window_start.isoformat(),
                "window_end": window_end.isoformat(),
                "buckets_days": buckets_days,
                "include_overdue": include_overdue,
                "measure": measure,
                "exposures_mode": exposures_mode
            },
            "items": items,
            "buckets": buckets_resp,
            "overlay": {
                "nodes": overlay_nodes,
                "links": overlay_links
            }
        }), 200
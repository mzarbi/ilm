# server/api/routes.py
import hashlib
import mimetypes
import os
import time
from pathlib import Path
from urllib.parse import urlparse

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

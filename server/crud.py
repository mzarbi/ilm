from typing import Type, Dict, Any
from sqlalchemy.orm import Session
from marshmallow import Schema
from .utils import parse_bool_param
from sqlalchemy.exc import IntegrityError
from flask import request, jsonify
from sqlalchemy.sql.sqltypes import String, Date, DateTime
from sqlalchemy import asc, desc, Column
from sqlalchemy.orm.attributes import InstrumentedAttribute

SAFE_ATTR_TYPES = (InstrumentedAttribute,)

def apply_filters(q, model):
    from flask import request
    for key, val in request.args.items():
        if key in ("page", "page_size", "sort", "include_deleted"):
            continue
        if not hasattr(model, key):
            continue
        try:
            col = getattr(model, key)
            if isinstance(col, SAFE_ATTR_TYPES):
                # Treat empty string as NULL filter: skip
                if val == "":
                    continue
                q = q.filter(col == val)
        except Exception:
            # Never let a bad filter crash the list
            continue
    return q

def apply_sorting(q, model):
    from .utils import parse_sort
    for field, direction in parse_sort():
        if not hasattr(model, field):
            continue
        try:
            col = getattr(model, field)
            q = q.order_by(asc(col) if direction == "asc" else desc(col))
        except Exception:
            continue
    return q



def _model_columns(Model):
    return {c.name: c for c in Model.__table__.columns}

def _coerce_value(col, raw):
    if raw is None:
        return None
    t = col.type
    # best-effort coercion (extend as needed)
    if hasattr(t, "python_type"):
        py = t.python_type
        try:
            return py(raw)
        except Exception:
            return raw
    return raw

def list_items(session, Model, schema, include_deleted=False):
    cols = _model_columns(Model)

    # --- paging ---
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 25))
        if page < 1: page = 1
        if page_size < 1: page_size = 25
    except ValueError:
        page, page_size = 1, 25

    # --- sorting ---
    sort_arg = request.args.get("sort")  # e.g. "code:asc" or "deal_date:desc"
    sort_clauses = []
    if sort_arg:
        for part in sort_arg.split(","):
            k, _, order = part.partition(":")
            k = k.strip()
            order = (order or "asc").lower()
            if k in cols:
                sort_clauses.append(asc(cols[k]) if order == "asc" else desc(cols[k]))

    # --- filters (fuzzy for text) ---
    # collect all query args except reserved
    reserved = {"page", "page_size", "sort", "include_deleted"}
    filters = []
    for k, v in request.args.items():
        if k in reserved or v is None or v == "":
            continue
        if k in cols:
            col = cols[k]
            if isinstance(col.type, (String, )):
                # fuzzy match
                filters.append(col.ilike(f"%{v}%"))
            else:
                # exact/coerced for non-strings
                filters.append(col == _coerce_value(col, v))

    q = session.query(Model)

    # soft-delete behavior if your models have is_deleted
    if "is_deleted" in cols and not include_deleted:
        filters.append((cols["is_deleted"] == False) | (cols["is_deleted"].is_(None)))  # noqa: E712

    if filters:
        for flt in filters:
            q = q.filter(flt)

    total = q.count()

    if sort_clauses:
        q = q.order_by(*sort_clauses)
    else:
        # deterministic fallback
        if "id" in cols:
            q = q.order_by(cols["id"].asc())

    # correct offset formula
    offset = (page - 1) * page_size
    items = q.offset(offset).limit(page_size).all()

    data = schema.dump(items, many=True)
    return jsonify({
        "items": data,
        "total": total,
        "page": page,
        "page_size": page_size,
    })


def get_item(s: Session, model: Type, schema: Schema, item_id: int):
    obj = s.get(model, item_id)
    if not obj:
        return jsonify({"error": "not_found"}), 404
    # hide soft-deleted by default
    if getattr(obj, "is_deleted", False):
        if not parse_bool_param("include_deleted", False):
            return jsonify({"error": "not_found"}), 404
    return jsonify(schema.dump(obj))


def create_item(s: Session, model: Type, schema: Schema, payload: Dict[str, Any]):
    obj = model(**schema.load(payload))
    s.add(obj)
    s.flush()
    return jsonify(schema.dump(obj)), 201


def update_item(s: Session, model: Type, schema: Schema, item_id: int, payload: Dict[str, Any]):
    obj = s.get(model, item_id)
    if not obj:
        return jsonify({"error": "not_found"}), 404
    data = schema.load(payload, partial=True)
    for k, v in data.items():
        setattr(obj, k, v)
    s.flush()
    return jsonify(schema.dump(obj))




def delete_item(s: Session, model: Type, item_id: int, soft=True):
    obj = s.get(model, item_id)
    if not obj:
        return jsonify({"error": "not_found"}), 404
    try:
        if soft and hasattr(obj, "is_deleted"):
            setattr(obj, "is_deleted", True)
            s.flush()
        else:
            s.delete(obj)
            s.flush()
        return "", 204
    except IntegrityError as e:
        s.rollback()
        # FK/unique prevents deletion
        return jsonify({"error":"integrity_error","message":str(e.orig)}), 409


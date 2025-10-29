# bp_attachments.py
import os
import hashlib
import mimetypes
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import asc, desc
from server.extensions import db
from models import InterlinkageAttachment
from schemas_attachments import (
    InterlinkageAttachmentSchema,
    AttachmentListQuerySchema,
    AttachmentUploadFormSchema,
)

bp = Blueprint("attachments", __name__, url_prefix="/api/interlinkage-attachments")

att_schema = InterlinkageAttachmentSchema()
att_list_schema = InterlinkageAttachmentSchema(many=True)
list_query_schema = AttachmentListQuerySchema()
upload_form_schema = AttachmentUploadFormSchema()

# Helper: simple sorter
def parse_sort(sort):
    # expect "col:dir"
    try:
        col, direction = sort.split(":")
        direction = direction.lower()
        col_attr = getattr(InterlinkageAttachment, col)
        return desc(col_attr) if direction == "desc" else asc(col_attr)
    except Exception:
        return desc(InterlinkageAttachment.id)

# Helper: safe filename (very basic)
def safe_filename(name: str) -> str:
    name = os.path.basename(name).strip().replace("\\", "/")
    return name[-255:]  # truncate

# Helper: compute sha256
def sha256_of_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

# --- LIST ---
@bp.get("")
def list_attachments():
    args = list_query_schema.load(request.args)
    q = InterlinkageAttachment.query.filter_by(interlinkage_id=args["interlinkage_id"])

    sort = parse_sort(args.get("sort", "id:desc"))
    q = q.order_by(sort)

    page = args["page"]
    page_size = args["page_size"]
    total = q.count()
    rows = q.offset((page - 1) * page_size).limit(page_size).all()

    return jsonify({
        "items": att_list_schema.dump(rows),
        "total": total,
        "page": page,
        "page_size": page_size,
    })

# --- CREATE (metadata only) ---
@bp.post("")
def create_attachment():
    payload = att_schema.load(request.json)
    row = InterlinkageAttachment(**payload)
    # audit: created_by from your auth context if any
    row.created_at = datetime.utcnow()
    db.session.add(row)
    db.session.commit()
    return jsonify(att_schema.dump(row)), 201

# --- UPDATE (metadata) ---
@bp.put("/<int:att_id>")
def update_attachment(att_id):
    row = InterlinkageAttachment.query.get_or_404(att_id)
    payload = att_schema.load(request.json, partial=True)  # allow partial updates
    for k, v in payload.items():
        setattr(row, k, v)
    row.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(att_schema.dump(row))

# --- DELETE (hard delete OK; or set soft-delete) ---
@bp.delete("/<int:att_id>")
def delete_attachment(att_id):
    row = InterlinkageAttachment.query.get_or_404(att_id)
    db.session.delete(row)   # or soft delete: row.is_deleted=True; row.deleted_at=...
    db.session.commit()
    return jsonify({"ok": True})

# --- UPLOAD (multipart) ---
@bp.post("/upload")
def upload_attachment():
    # form fields
    form = upload_form_schema.load(request.form)
    interlinkage_id = form["interlinkage_id"]
    description = form.get("description")

    # file object
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "file is required"}), 400

    # filename + MIME
    filename = safe_filename(file.filename or "upload.bin")
    mime = file.mimetype or mimetypes.guess_type(filename)[0] or "application/octet-stream"

    # decide where to store (NAS/S3/local). Example: local/NAS folder:
    base_dir = current_app.config.get("ATTACHMENTS_DIR", "/mnt/dhtm/attachments")
    os.makedirs(base_dir, exist_ok=True)

    # Optional: per interlinkage subfolder
    subdir = os.path.join(base_dir, str(interlinkage_id))
    os.makedirs(subdir, exist_ok=True)

    # prevent overwrite: add timestamp if exists
    target = os.path.join(subdir, filename)
    if os.path.exists(target):
        stem, ext = os.path.splitext(filename)
        filename = f"{stem}_{int(datetime.utcnow().timestamp())}{ext}"
        target = os.path.join(subdir, filename)

    file.save(target)

    # Optional: checksum/size (even if not in DB model; you may still return to client)
    size = os.path.getsize(target)
    checksum = sha256_of_file(target)

    # Storage URI (URL, UNC, or file path). If you expose via HTTP, use that URL.
    storage_uri = f"file://{target}"

    row = InterlinkageAttachment(
        interlinkage_id=interlinkage_id,
        filename=filename,
        mime_type=mime,
        storage_uri=storage_uri,
        description=description or "",
        created_at=datetime.utcnow(),
    )
    db.session.add(row)
    db.session.commit()

    # Return DB row (plus ad-hoc size/checksum in payload if you like)
    result = att_schema.dump(row)
    result.update({"size": size, "checksum": checksum})
    return jsonify(result), 201

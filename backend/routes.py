from flask import Blueprint, request, jsonify, render_template, redirect, url_for, current_app
import csv
import io
import time
from backend.db import get_db_connection
from backend import s3_utils


bp = Blueprint('main', __name__)


# Health check
@bp.route('/healthz', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"}), 200


# List all invoices
@bp.route('/invoices', methods=['GET'])
def list_invoices():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM invoices ORDER BY uploaded_at DESC;")
        invoices = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(invoices), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# UI routes
@bp.route('/upload', methods=['GET'])
def upload_page():
    return render_template('upload.html')



@bp.route('/', methods=['GET'])
def root():
    return redirect(url_for('upload_page'))


# CSV preview
@bp.route('/api/preview_csv', methods=['POST'])
def preview_csv():
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "Missing file field"}), 400

    has_header = request.form.get('has_header', '1')
    try:
        raw = file.read()
        text = raw.decode('utf-8', errors='replace')
        sio = io.StringIO(text)

        reader = csv.reader(sio)
        rows = []
        max_rows = 10

        if has_header and has_header != '0':
            sio.seek(0)
            dreader = csv.DictReader(sio)
            headers = dreader.fieldnames or []
            for i, row in enumerate(dreader):
                if i >= max_rows:
                    break
                rows.append([row.get(h, '') for h in headers])
        else:
            headers = []
            for i, row in enumerate(reader):
                if i >= max_rows:
                    break
                rows.append(row)

        return jsonify({"headers": headers, "rows": rows}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# S3 upload endpoint
@bp.route('/api/upload_to_s3', methods=['POST'])
def upload_to_s3_api():
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "Missing file field"}), 400

    key = request.form.get('key') or None
    if not key:
        safe_name = file.filename.replace(' ', '_') if file.filename else 'upload'
        key = f"uploads/{int(time.time())}_{safe_name}"

    try:
        result = s3_utils.upload_fileobj(file, key)
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Import CSV to DB and archive to S3
@bp.route('/api/import_csv', methods=['POST'])
def import_csv():
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "Missing file field"}), 400

    has_header = request.form.get('has_header', '1')
    try:
        raw = file.read()
        text = raw.decode('utf-8', errors='replace')
        sio = io.StringIO(text)

        rows_to_insert = []
        if has_header and has_header != '0':
            # Normalize header names to simple keys and strip BOM if present
            sio.seek(0)
            dreader = csv.DictReader(sio)
            for raw_row in dreader:
                norm = {}
                for k, v in raw_row.items():
                    if k is None:
                        continue
                    nk = k.strip().lower().replace(' ', '_').replace('-', '_')
                    # remove BOM marker if present
                    if nk and nk[0] == '\ufeff':
                        nk = nk.lstrip('\ufeff')
                    norm[nk] = v
                rows_to_insert.append(norm)
        else:
            reader = csv.reader(sio)
            for r in reader:
                if not r:
                    continue
                obj = {
                    'invoice_number': r[0].strip() if len(r) > 0 and isinstance(r[0], str) else (r[0] if len(r) > 0 else None),
                    'amount': r[1].strip() if len(r) > 1 and isinstance(r[1], str) else (r[1] if len(r) > 1 else None),
                    'customer_name': r[2].strip() if len(r) > 2 and isinstance(r[2], str) else (r[2] if len(r) > 2 else None)
                }
                rows_to_insert.append(obj)

        if not rows_to_insert:
            return jsonify({"inserted": 0, "skipped": 0}), 200

        conn = get_db_connection()
        cur = conn.cursor()

        inserted = 0
        skipped = 0

        row_errors = []
        for idx, r in enumerate(rows_to_insert, start=1):
            # normalize row whether dict (header) or sequence (no header)
            if isinstance(r, dict):
                invoice_number = (r.get('invoice_number') or r.get('InvoiceNumber') or r.get('Invoice Number'))
                amount_raw = r.get('amount') or r.get('Amount')
                customer_name = r.get('customer_name') or r.get('Customer') or r.get('customer_name')
            else:
                # sequence
                invoice_number = r[0] if len(r) > 0 else None
                amount_raw = r[1] if len(r) > 1 else None
                customer_name = r[2] if len(r) > 2 else None

            # Trim strings
            if isinstance(invoice_number, str):
                invoice_number = invoice_number.strip()
            if isinstance(customer_name, str):
                customer_name = customer_name.strip()

            # Validation
            if not invoice_number:
                skipped += 1
                row_errors.append({"row": idx, "reason": "missing invoice_number"})
                continue
            try:
                amount_val = None
                if amount_raw is not None and amount_raw != '':
                    amount_val = float(str(amount_raw).strip())
            except Exception:
                skipped += 1
                row_errors.append({"row": idx, "reason": "invalid amount"})
                continue
            if amount_val is None:
                skipped += 1
                row_errors.append({"row": idx, "reason": "missing amount"})
                continue
            if not customer_name:
                skipped += 1
                row_errors.append({"row": idx, "reason": "missing customer_name"})
                continue

            try:
                cur.execute(
                    """
                    INSERT INTO invoices (invoice_number, amount, customer_name)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (invoice_number) DO NOTHING
                    RETURNING id;
                    """,
                    (invoice_number, amount_val, customer_name)
                )
                res = cur.fetchone()
                if res:
                    inserted += 1
                else:
                    skipped += 1
                    row_errors.append({"row": idx, "reason": "duplicate or not inserted"})
            except Exception as e:
                skipped += 1
                row_errors.append({"row": idx, "reason": f"db error: {e}"})

        conn.commit()
        cur.close()
        conn.close()

        # Upload archive to S3
        from io import BytesIO
        bio = BytesIO(raw)
        safe_name = file.filename.replace(' ', '_') if file.filename else 'import'
        key = f"imports/{int(time.time())}_{safe_name}"
        s3_info = None
        s3_error = None
        try:
            s3_info = s3_utils.upload_fileobj(bio, key)
        except Exception as e:
            s3_error = str(e)
            try:
                current_app.logger.error('S3 upload error during import: %s', s3_error)
            except Exception:
                pass

        resp = {"inserted": inserted, "skipped": skipped}
        if row_errors:
            resp['row_errors'] = row_errors
        if s3_info:
            resp['s3'] = s3_info
        if s3_error:
            resp['s3_error'] = s3_error

        try:
            current_app.logger.info('Import summary: inserted=%s skipped=%s', inserted, skipped)
        except Exception:
            pass

        return jsonify(resp), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

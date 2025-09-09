from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

app = Flask(__name__)


def getenv_required(key: str) -> str:
    value = os.getenv(key)
    if value is None or value == "":
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value

DB_USER = getenv_required("DB_USER")
DB_PASSWORD = getenv_required("DB_PASSWORD")
DB_HOST = getenv_required("DB_HOST")
DB_PORT = getenv_required("DB_PORT")
DB_NAME = getenv_required("DB_NAME")

# Connect to the PostgreSQL database
def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
        cursor_factory=RealDictCursor
    )
    return conn

# Health check endpoint
@app.route('/healthz', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"}), 200

# List all invoices
@app.route('/invoices', methods=['GET'])
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

# Add a new invoice
@app.route('/invoices', methods=['POST'])
def add_invoice():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    invoice_number = data.get("invoice_number")
    amount = data.get("amount")
    customer_name = data.get("customer_name")

    # Validate required fields explicitly (don't treat 0 as missing)
    if invoice_number is None or invoice_number == "" or customer_name is None or customer_name == "":
        return jsonify({"error": "Missing required fields: invoice_number and customer_name are required"}), 400
    if amount is None:
        return jsonify({"error": "Missing required field: amount"}), 400

    # Validate amount is a number
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid amount; must be a number"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Check uniqueness first to provide a clearer error and HTTP 409
        cur.execute("SELECT * FROM invoices WHERE invoice_number = %s;", (invoice_number,))
        existing = cur.fetchone()
        if existing:
            cur.close()
            conn.close()
            return jsonify({"error": "Invoice number must be unique"}), 409

        cur.execute(
            """
            INSERT INTO invoices (invoice_number, amount, customer_name)
            VALUES (%s, %s, %s)
            RETURNING *;
            """,
            (invoice_number, amount, customer_name)
        )
        new_invoice = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return jsonify(new_invoice), 201
    except Exception as e:
        # Unexpected errors should return 500
        return jsonify({"error": str(e)}), 500

# Delete an invoice
@app.route('/invoices/<int:invoice_id>', methods=['DELETE'])
def delete_invoice(invoice_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM invoices WHERE id = %s RETURNING *;", (invoice_id,))
        deleted_invoice = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()

        if deleted_invoice:
            return jsonify({"message": "Invoice deleted successfully", "invoice": deleted_invoice}), 200
        else:
            return jsonify({"error": "Invoice not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


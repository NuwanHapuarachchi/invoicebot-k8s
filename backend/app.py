from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = Flask(__name__)

DB_USER = os.getenv("DB_USER", "invoicebot")
DB_PASSWORD = os.getenv("DB_PASSWORD", "66889266")
DB_HOST = os.getenv("DB_HOST", "localhost") 
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "invoicebotdb")

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

    if not invoice_number or not amount or not customer_name:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
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
    except psycopg2.IntegrityError:
        return jsonify({"error": "Invoice number must be unique"}), 400
    except Exception as e:
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

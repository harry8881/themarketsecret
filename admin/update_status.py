from flask import Blueprint, request, jsonify
import mysql.connector
import os

admin_bp = Blueprint('admin', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME")
    )

@admin_bp.route('/admin/update-status', methods=['POST'])
def update_status():
    data = request.get_json()
    status = data.get('status')
    user_id = data.get('id')

    if not status or not user_id:
        return jsonify({"error": "Missing status or id"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        sql = "UPDATE users SET status = %s WHERE id = %s"
        cursor.execute(sql, (status, user_id))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

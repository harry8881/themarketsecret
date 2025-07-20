from flask import Blueprint, request, jsonify
import pymysql
import os

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/update-status', methods=['POST'])
def update_status():
    data = request.get_json()
    user_id = data.get('id')
    new_status = data.get('status')

    if not user_id or not new_status:
        return jsonify({"error": "Missing ID or status"}), 400

    try:
        conn = pymysql.connect(
            host=os.environ.get('DB_HOST'),
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASS'),
            database=os.environ.get('DB_NAME')
        )
        cursor = conn.cursor()
        sql = "UPDATE users SET status = %s WHERE id = %s"
        cursor.execute(sql, (new_status, user_id))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

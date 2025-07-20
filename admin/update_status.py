from flask import Blueprint, request, jsonify
import pymysql
import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/update-status', methods=['GET', 'POST'])
def update_status():
    if request.method == 'GET':
        logger.debug("Received GET request to /admin/update-status")
        return jsonify({
            "message": "This endpoint requires a POST request with JSON data: {'id': <user_id>, 'status': <new_status>}",
            "example": {"id": 1, "status": "active"}
        })

    logger.debug("Received POST request to /admin/update-status")
    data = request.get_json()
    logger.debug(f"Request data: {data}")
    user_id = data.get('id')
    new_status = data.get('status')

    if not user_id or not new_status:
        logger.error("Missing ID or status in request")
        return jsonify({"error": "Missing ID or status"}), 400

    try:
        logger.debug("Attempting to connect to database")
        conn = pymysql.connect(
            host=os.environ.get('DB_HOST'),
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASS'),
            database=os.environ.get('DB_NAME'),
            connect_timeout=5
        )
        logger.debug("Database connection successful")
        cursor = conn.cursor()
        sql = "UPDATE users SET status = %s WHERE id = %s"
        logger.debug(f"Executing SQL: {sql} with params: ({new_status}, {user_id})")
        cursor.execute(sql, (new_status, user_id))
        conn.commit()
        logger.debug("Database update successful")
        cursor.close()
        conn.close()
        return jsonify({"success": True})
    except pymysql.err.OperationalError as e:
        logger.error(f"Database connection error: {str(e)}")
        return jsonify({"error": f"Database connection failed: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

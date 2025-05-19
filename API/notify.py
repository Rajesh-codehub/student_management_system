from flask import Blueprint
from flask import Flask, request, jsonify, current_app
from dbconn import create_connection, close_connection
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from flask_cors import CORS
from datetime import datetime, timedelta
import calendar
from calendar import month_name
import json
import os
from dotenv import load_dotenv


notify_bp = Blueprint("notify", __name__)



@notify_bp.route('/api/notifications', methods=['POST'])
def send_notification():
    data = request.form
    title = data.get('title')
    message = data.get('message')
    notif_type = data.get('type', 'info')
    student_id = data.get('student_id')
    user_id = data.get('user_id')

    if not title or not message or (not student_id and not user_id):
        return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400

    connection = create_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO notifications (title, message, type, student_id, user_id)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (title, message, notif_type, student_id, user_id))
        connection.commit()
        return jsonify({'status': 'success', 'message': 'Notification sent successfully'}), 201
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        close_connection(connection)

@notify_bp.route('/api/notifications/bulk', methods=['POST'])
def send_bulk_notification():
    data = request.form
    title = data.get('title')
    message = data.get('message')
    notif_type = data.get('type', 'info')
    grade = data.get('grade')

    if not title or not message or not grade:
        return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400

    connection = create_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    try:
        cursor = connection.cursor()

        # Get students in the specified grade
        cursor.execute("SELECT student_id FROM students WHERE grade = %s", (grade,))
        students = cursor.fetchall()

        if not students:
            return jsonify({'status': 'error', 'message': 'No students found in the specified grade'}), 404

        # Bulk insert notifications
        query = """
            INSERT INTO notifications (title, message, type, student_id)
            VALUES (%s, %s, %s, %s)
        """
        for student in students:
            cursor.execute(query, (title, message, notif_type, student[0]))

        connection.commit()
        return jsonify({
            'status': 'success',
            'message': 'Bulk notification sent successfully',
            'data': {'recipient_count': len(students)}
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        close_connection(connection)
@notify_bp.route('/api/notifications', methods=['GET'])
def get_notifications():
    user_id = request.args.get('user_id')
    student_id = request.args.get('student_id')

    if not user_id and not student_id:
        return jsonify({'status': 'error', 'message': 'user_id or student_id is required'}), 400

    connection = create_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    try:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT notification_id, title, message, type, is_read, created_at
            FROM notifications
            WHERE user_id = %s OR student_id = %s
            ORDER BY created_at DESC
        """
        cursor.execute(query, (user_id, student_id))
        notifications = cursor.fetchall()

        for n in notifications:
            n['is_read'] = bool(n['is_read'])  # convert tinyint to boolean

        return jsonify({'status': 'success', 'data': notifications}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        close_connection(connection)

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


dashboard_bp = Blueprint("dashboard", __name__)





@dashboard_bp.route('/api/dashboard/statistics', methods=['GET'])
def get_dashboard_statistics():
    connection = create_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    try:
        cursor = connection.cursor(dictionary=True)

        # Total students
        cursor.execute("SELECT COUNT(*) AS total_students FROM students")
        total_students = cursor.fetchone()['total_students']

        # New admissions in the last 30 days
        cursor.execute("""
            SELECT COUNT(*) AS new_admission_count
            FROM students
            WHERE enrollment_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        """)
        new_admission_count = cursor.fetchone()['new_admission_count']

        # Pending fees
        cursor.execute("""
            SELECT COUNT(*) AS pending_fees
            FROM students
            WHERE fee_status = 'pending'
        """)
        pending_fees = cursor.fetchone()['pending_fees']

        # Monthly admissions for the current year
        cursor.execute("""
            SELECT MONTH(enrollment_date) AS month, COUNT(*) AS count
            FROM students
            WHERE YEAR(enrollment_date) = YEAR(CURDATE())
            GROUP BY MONTH(enrollment_date)
        """)
        monthly_admissions_raw = cursor.fetchall()
        import calendar
        monthly_admissions = [
            {"month": calendar.month_name[row['month']], "count": row['count']}
            for row in monthly_admissions_raw
        ]

        # Recent payments (last 5)
        cursor.execute("""
            SELECT sf.student_id, s.full_name, sf.amount_paid, DATE(sf.payment_date) AS payment_date
            FROM student_fees sf
            JOIN students s ON sf.student_id = s.student_id
            ORDER BY sf.payment_date DESC
            LIMIT 5
        """)
        recent_payments = cursor.fetchall()

        # Attendance summary for today
        cursor.execute("SELECT CURDATE() AS today")
        today = cursor.fetchone()['today']

        cursor.execute("""
            SELECT status, COUNT(*) AS count
            FROM attendance
            WHERE date = %s
            GROUP BY status
        """, (today,))
        attendance_counts = cursor.fetchall()
        total_attendance = sum(row['count'] for row in attendance_counts)
        attendance_summary = {
            "date": str(today),
            "present_percentage": 0,
            "absent_percentage": 0,
            "late_percentage": 0
        }
        for row in attendance_counts:
            percentage = (row['count'] / total_attendance) * 100 if total_attendance else 0
            if row['status'] == 'present':
                attendance_summary['present_percentage'] = round(percentage, 2)
            elif row['status'] == 'absent':
                attendance_summary['absent_percentage'] = round(percentage, 2)
            elif row['status'] == 'late':
                attendance_summary['late_percentage'] = round(percentage, 2)

        return jsonify({
            "status": "success",
            "data": {
                "total_students": total_students,
                "new_admission_count": new_admission_count,
                "pending_fees": pending_fees,
                "monthly_admissions": monthly_admissions,
                "recent_payments": recent_payments,
                "attendance_summary": attendance_summary
            }
        }), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        close_connection(connection)


@dashboard_bp.route('/api/reports/class-performance/<grade>', methods=['GET'])
def get_class_performance_report(grade):
    exam_id = request.args.get('exam_id')
    if not exam_id:
        return jsonify({'status': 'error', 'message': 'exam_id is required'}), 400

    connection = create_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    try:
        cursor = connection.cursor(dictionary=True)

        # Get exam name
        cursor.execute("SELECT exam_name FROM exams WHERE exam_id = %s", (exam_id,))
        exam = cursor.fetchone()
        if not exam:
            return jsonify({'status': 'error', 'message': 'Exam not found'}), 404
        exam_name = exam['exam_name']

        # Subject averages
        cursor.execute("""
            SELECT sub.subject_name AS subject, AVG(er.marks_obtained) AS average
            FROM exam_results er
            JOIN students s ON er.student_id = s.student_id
            JOIN subjects sub ON er.subject_id = sub.subject_id
            WHERE s.grade = %s AND er.exam_id = %s
            GROUP BY er.subject_id
        """, (grade, exam_id))
        subject_averages = cursor.fetchall()

        # Top performers (top 5)
        cursor.execute("""
            SELECT s.student_id, s.full_name,
                   (SUM(er.marks_obtained) / SUM(er.total_marks)) * 100 AS percentage
            FROM exam_results er
            JOIN students s ON er.student_id = s.student_id
            WHERE s.grade = %s AND er.exam_id = %s
            GROUP BY s.student_id
            ORDER BY percentage DESC
            LIMIT 5
        """, (grade, exam_id))
        top_performers = cursor.fetchall()

        # Grade distribution
        cursor.execute("""
            SELECT er.grade, COUNT(*) AS count
            FROM exam_results er
            JOIN students s ON er.student_id = s.student_id
            WHERE s.grade = %s AND er.exam_id = %s
            GROUP BY er.grade
        """, (grade, exam_id))
        grade_counts = cursor.fetchall()
        grade_distribution = {row['grade']: row['count'] for row in grade_counts}

        # Overall average
        cursor.execute("""
            SELECT AVG(er.marks_obtained) AS overall_average
            FROM exam_results er
            JOIN students s ON er.student_id = s.student_id
            WHERE s.grade = %s AND er.exam_id = %s
        """, (grade, exam_id))
        overall_average = cursor.fetchone()['overall_average']

        # Pass percentage (assuming passing grade is not 'F')
        cursor.execute("""
            SELECT COUNT(*) AS total_students
            FROM (
                SELECT er.student_id,
                       (SUM(er.marks_obtained) / SUM(er.total_marks)) * 100 AS percentage
                FROM exam_results er
                JOIN students s ON er.student_id = s.student_id
                WHERE s.grade = %s AND er.exam_id = %s
                GROUP BY er.student_id
            ) AS student_percentages
        """, (grade, exam_id))
        total_students = cursor.fetchone()['total_students']

        cursor.execute("""
            SELECT COUNT(*) AS passed_students
            FROM (
                SELECT er.student_id,
                       (SUM(er.marks_obtained) / SUM(er.total_marks)) * 100 AS percentage
                FROM exam_results er
                JOIN students s ON er.student_id = s.student_id
                WHERE s.grade = %s AND er.exam_id = %s
                GROUP BY er.student_id
            ) AS student_percentages
            WHERE percentage >= 40
        """, (grade, exam_id))
        passed_students = cursor.fetchone()['passed_students']

        pass_percentage = (passed_students / total_students) * 100 if total_students else 0

        return jsonify({
            "status": "success",
            "data": {
                "grade": grade,
                "exam_name": exam_name,
                "subject_averages": subject_averages,
                "top_performers": top_performers,
                "grade_distribution": grade_distribution,
                "overall_average": round(overall_average, 2) if overall_average else 0,
                "pass_percentage": round(pass_percentage, 2)
            }
        }), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        close_connection(connection)

from flask import Flask, request, jsonify
from dbconn import create_connection, close_connection
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from flask_cors import CORS
from datetime import datetime, timedelta
import calendar
from calendar import month_name
from auth import auth_bp
from notify import notify_bp
from dashboard import dashboard_bp
import json
import os
from dotenv import load_dotenv

load_dotenv()




app = Flask(__name__)
app.register_blueprint(auth_bp)
app.register_blueprint(notify_bp)
app.register_blueprint(dashboard_bp)
CORS(app, resources={r"/*": {"origins": "*"}}) 

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", 'y&f9Mv$e!zR3P@bE#tKqU1Xc4gL*oN7a')



# Add Student
@app.route('/add_student', methods=['POST'])
def add_student():
    data = request.form

    full_name = f"{data.get('first_name')} {data.get('last_name')}"
    try:
        conn = create_connection()
        cursor = conn.cursor()

        sql = """
        INSERT INTO students (full_name, date_of_birth, gender, email, phone, address, grade, fee_status, total_fee, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            full_name,
            data.get('date_of_birth'),
            data.get('gender'),
            data.get('email'),
            data.get('phone'),
            data.get('address'),
            data.get('grade'),
            data.get('fee_status'),
            float(data.get('total_fee')),
            data.get('status')
        )

        cursor.execute(sql, values)
        conn.commit()

        student_id = cursor.lastrowid

        return jsonify({
            "status": "success",
            "message": "Student added successfully",
            "data": {
                "student_id": student_id,
                "full_name": full_name,
                "grade": data.get('grade')
            }
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        close_connection(conn)

# Get All Students
@app.route('/get_students', methods=['GET'])
def get_all_students():
    try:
        conn = create_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT student_id, full_name, grade, gender, fee_status, status FROM students")
        students = cursor.fetchall()

        return jsonify({"status": "success", "data": students}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        close_connection(conn)

# Get Student by ID
@app.route('/get_student/<int:student_id>', methods=['GET'])
def get_student_by_id(student_id):
    try:
        conn = create_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM students WHERE student_id = %s", (student_id,))
        student = cursor.fetchone()

        if student:
            return jsonify({"status": "success", "data": student}), 200
        else:
            return jsonify({"status": "error", "message": "Student not found"}), 404

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        close_connection(conn)

# Update Student
@app.route('/update_student/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    data = request.form

    try:
        conn = create_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE students
            SET full_name = %s, email = %s, phone = %s
            WHERE student_id = %s
        """, (f"{data.get('first_name')} {data.get('last_name')}", data.get('email'), data.get('phone'), student_id))
        conn.commit()

        return jsonify({"status": "success", "message": "Student details updated successfully"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        close_connection(conn)

# Delete Student
@app.route('/delete_student/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    try:
        conn = create_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM students WHERE student_id = %s", (student_id,))
        conn.commit()

        return jsonify({"status": "success", "message": f"Student with id {student_id} deleted successfully"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        close_connection(conn)

# Search Students
@app.route('/search_student/search', methods=['GET'])
def search_students():
    query = request.args.get('query', '')

    try:
        conn = create_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT student_id, full_name, grade, email, phone
            FROM students
            WHERE full_name LIKE %s
        """, (f"%{query}%",))
        results = cursor.fetchall()

        return jsonify({"status": "success", "data": results}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        close_connection(conn)


@app.route("/record_payment", methods=["POST"])
def record_payment():
    student_id = request.form.get('student_id')
    payment_amount = request.form.get('payment_amount')
    payment_method = request.form.get('payment_method')
    remarks = request.form.get('remarks', '')
    payment_date = request.form.get('payment_date', datetime.now().strftime('%Y-%m-%d'))

    connection = create_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Get student info
        cursor.execute("SELECT total_fee FROM students WHERE student_id = %s", (student_id,))
        student = cursor.fetchone()
        if not student:
            return jsonify({"status": "error", "message": "Student not found"}), 404

        total_fee = float(student['total_fee'])

        # Calculate total paid so far
        cursor.execute("SELECT COALESCE(SUM(amount_paid), 0) as total_paid FROM student_fees WHERE student_id = %s", (student_id,))
        total_paid = float(cursor.fetchone()['total_paid'])

        # Insert new payment
        cursor.execute("""
            INSERT INTO student_fees (student_id, amount_paid, total_fee, fee_status, payment_method, remarks, payment_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            student_id,
            payment_amount,
            total_fee,
            'completed' if total_paid + float(payment_amount) >= total_fee else 'pending',
            payment_method,
            remarks,
            payment_date
        ))

        # Update student fee status if fully paid
        new_total_paid = total_paid + float(payment_amount)
        new_status = 'completed' if new_total_paid >= total_fee else 'pending'
        cursor.execute("UPDATE students SET fee_status = %s WHERE student_id = %s", (new_status, student_id))

        connection.commit()

        return jsonify({
            "status": "success",
            "message": "Payment recorded successfully",
            "data": {
                "student_id": int(student_id),
                "payment_amount": float(payment_amount),
                "new_balance": float(total_fee) - new_total_paid,
                "payment_date": payment_date
            }
        }), 200

    except Exception as e:
        connection.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        close_connection(connection)

# Check Fee Dues
@app.route('/fee_dues/<int:student_id>', methods=['GET'])
def check_fee_dues(student_id):
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Get student info
        cursor.execute("SELECT full_name, grade, total_fee, fee_status FROM students WHERE student_id = %s", (student_id,))
        student = cursor.fetchone()

        if not student:
            return jsonify({"status": "error", "message": "Student not found"}), 404

        # Total paid
        cursor.execute("SELECT COALESCE(SUM(amount_paid), 0) as total_paid FROM student_fees WHERE student_id = %s", (student_id,))
        total_paid = float(cursor.fetchone()['total_paid'])
        due_amount = float(student['total_fee']) - total_paid

        return jsonify({
            "status": "success",
            "data": {
                "student_id": student_id,
                "full_name": student["full_name"],
                "grade": student["grade"],
                "total_fee": float(student["total_fee"]),
                "amount_paid": total_paid,
                "due_amount": due_amount,
                "fee_status": student["fee_status"]
            }
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        close_connection(connection)
    
@app.route('/fee_collection', methods=['GET'])
def fee_collection_report():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    connection = create_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT sf.fee_id, sf.student_id, s.full_name, sf.amount_paid, sf.payment_date, sf.payment_method
            FROM student_fees sf
            JOIN students s ON sf.student_id = s.student_id
            WHERE sf.payment_date BETWEEN %s AND %s
        """, (start_date, end_date))
        transactions = cursor.fetchall()

        total_collected = sum(t['amount_paid'] for t in transactions)
        total_transactions = len(transactions)

        collection_by_method = {}
        for t in transactions:
            method = t['payment_method']
            collection_by_method[method] = collection_by_method.get(method, 0) + t['amount_paid']

        return jsonify({
            "status": "success",
            "data": {
                "total_collected": total_collected,
                "total_transactions": total_transactions,
                "collection_by_method": collection_by_method,
                "transactions": transactions
            }
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        close_connection(connection)

# Mark Attendance
@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    #data = request.get.form()
    student_id = request.form.get('student_id')
    date = request.form.get('date')
    status = request.form.get('status')
    remarks = request.form.get('remarks', '')

    connection = create_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            INSERT INTO attendance (student_id, date, status, remarks)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE status=%s, remarks=%s
        """, (student_id, date, status, remarks, status, remarks))
        connection.commit()

        return jsonify({"status": "success", "message": "Attendance marked successfully"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        close_connection(connection)


@app.route('/bulk_attendance', methods=['POST'])
def bulk_mark_attendance():
    date = request.form.get('date')
    grade = request.form.get('grade')
    attendance_data_str = request.form.get('attendance_data', '[]')
    
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        # Parse the JSON string into a Python object
        attendance_data = json.loads(attendance_data_str)
        
        for record in attendance_data:
            student_id = record.get('student_id')
            status = record.get('status')
            remarks = record.get('remarks', '')
            
            cursor.execute("""
                INSERT INTO attendance (student_id, date, status, remarks)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE status=%s, remarks=%s
            """, (student_id, date, status, remarks, status, remarks))
        
        connection.commit()
        return jsonify({
            "status": "success",
            "message": "Bulk attendance marked successfully",
            "data": {
                "marked_count": len(attendance_data),
                "grade": grade,
                "date": date
            }
        }), 200
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        close_connection(connection)

# Get Student Attendance
@app.route('/get_attendance/<int:student_id>', methods=['GET'])
def get_student_attendance(student_id):
    month = int(request.args.get('month'))
    year = int(request.args.get('year'))

    connection = create_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Student info
        cursor.execute("SELECT full_name, grade FROM students WHERE student_id = %s", (student_id,))
        student = cursor.fetchone()
        if not student:
            return jsonify({"status": "error", "message": "Student not found"}), 404

        # Attendance records
        cursor.execute("""
            SELECT date, status, remarks
            FROM attendance
            WHERE student_id = %s AND MONTH(date) = %s AND YEAR(date) = %s
            ORDER BY date
        """, (student_id, month, year))
        records = cursor.fetchall()

        summary = {"present": 0, "absent": 0, "late": 0}
        for r in records:
            summary[r['status']] += 1

        total_days = len(records)
        attendance_percentage = round((summary['present'] + 0.5 * summary['late']) / total_days * 100) if total_days > 0 else 0

        summary["attendance_percentage"] = attendance_percentage

        return jsonify({
            "status": "success",
            "data": {
                "student_id": student_id,
                "full_name": student["full_name"],
                "grade": student["grade"],
                "month": month_name[month],
                "year": year,
                "attendance_summary": summary,
                "attendance_records": records
            }
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        close_connection(connection)


# Get Class Attendance
@app.route('/get_class_attendance/<grade>', methods=['GET'])
def get_class_attendance(grade):
    date = request.args.get('date')

    connection = create_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Students in grade
        cursor.execute("SELECT student_id, full_name FROM students WHERE grade = %s", (grade,))
        all_students = cursor.fetchall()
        total_students = len(all_students)

        cursor.execute("""
            SELECT a.student_id, s.full_name, a.status, a.remarks
            FROM attendance a
            JOIN students s ON a.student_id = s.student_id
            WHERE s.grade = %s AND a.date = %s
        """, (grade, date))
        attendance_data = cursor.fetchall()

        present = sum(1 for a in attendance_data if a['status'] == 'present')
        absent = sum(1 for a in attendance_data if a['status'] == 'absent')
        late = sum(1 for a in attendance_data if a['status'] == 'late')

        attendance_percentage = round((present + 0.5 * late) / total_students * 100) if total_students > 0 else 0

        return jsonify({
            "status": "success",
            "data": {
                "grade": grade,
                "date": date,
                "total_students": total_students,
                "present": present,
                "absent": absent,
                "late": late,
                "attendance_percentage": attendance_percentage,
                "students": attendance_data
            }
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        close_connection(connection)
    
@app.route('/add_exam', methods=['POST'])
def add_exam():
    data = request.form
    exam_name = data.get('exam_name')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    description = data.get('description')

    connection = create_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO exams (exam_name, start_date, end_date, description)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (exam_name, start_date, end_date, description))
        connection.commit()
        exam_id = cursor.lastrowid

        return jsonify({
            'status': 'success',
            'message': 'Exam added successfully',
            'data': {
                'exam_id': exam_id,
                'exam_name': exam_name,
                'start_date': start_date,
                'end_date': end_date
            }
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        close_connection(connection)


@app.route('/add_subject', methods=['POST'])
def add_subject():
    subject_name = request.form.get('subject_name')
    subject_code = request.form.get('subject_code')
    grade_level = request.form.get('grade_level')
    #teacher_id = request.form.get('teacher_id')

    if not all([subject_name, subject_code]):
        return jsonify({"status": "error", "message": "Missing required fields"}), 400

    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO subjects (subject_name, subject_code)
                VALUES (%s, %s)
            """
            cursor.execute(query, (subject_name, subject_code))
            conn.commit()
            subject_id = cursor.lastrowid
            return jsonify({
                "status": "success",
                "message": "Subject added successfully",
                "data": {
                    "subject_id": subject_id,
                    "subject_name": subject_name,
                    "subject_code": subject_code
                    
                }
            }), 201
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
        finally:
            close_connection(conn)
    else:
        return jsonify({"status": "error", "message": "Database connection failed"}), 500


# Add Exam Result
@app.route('/add_exam_result', methods=['POST'])
def add_exam_result():
    data = request.form
    exam_id = data.get('exam_id')
    student_id = data.get('student_id')
    subject_id = data.get('subject_id')
    marks_obtained = data.get('marks_obtained')
    total_marks = data.get('total_marks')
    grade = data.get('grade')
    remarks = data.get('remarks')

    connection = create_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO exam_results (exam_id, student_id, subject_id, marks_obtained, total_marks, grade, remarks)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (exam_id, student_id, subject_id, marks_obtained, total_marks, grade, remarks))
        connection.commit()

        return jsonify({'status': 'success', 'message': 'Exam result added successfully'}), 201
    except mysql.connector.Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        close_connection(connection)
@app.route("/get_student_result", methods = ["GET"])
def get_student_result():
    student_id = request.args.get("student_id")

    if not student_id:
        jsonify({"Error":"student_id is required"}), 400

    conn = create_connection()
    cursor = conn.cursor(dictionary = True)

    try:
        query ="""
        SELECT
        er.result_id,
        er.exam_id,
        e.exam_name,
        er.subject_id,
        s.subject_name,
        er.marks_obtained,
        er.total_marks,
        er.grade,
        er.remarks
        from exam_results er
        join exams e on er.exam_id = e.exam_id
        join subjects s on er.subject_id = s.subject_id
        where er.student_id = %s"""

        cursor.execute(query, (student_id,))
        results  = cursor.fetchall()

        if not results:
            return jsonify({"message":"no results found for the given student_id"}), 404

        return jsonify({"student_id":student_id, "results":results}), 200
    except Exception as e:
        return jsonify({"Error":str(e)}), 500
    finally:
        cursor.close()
        close_connection(conn)



# Add Parent
@app.route('/api/parents', methods=['POST'])
def add_parent():
    data = request.form
    full_name = data.get('full_name')
    relationship = data.get('relationship')
    phone = data.get('phone')
    email = data.get('email')
    address = data.get('address')
    occupation = data.get('occupation')

    connection = create_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO parents (full_name, relationship, phone, email, address, occupation)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (full_name, relationship, phone, email, address, occupation))
        connection.commit()
        parent_id = cursor.lastrowid

        return jsonify({
            'status': 'success',
            'message': 'Parent added successfully',
            'data': {
                'parent_id': parent_id,
                'full_name': full_name
            }
        }), 201
    except mysql.connector.Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        close_connection(connection)

# Link Parent to Student
@app.route('/api/parents/link', methods=['POST'])
def link_parent():
    data = request.form
    parent_id = data.get('parent_id')
    student_id = data.get('student_id')

    connection = create_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO student_parent (parent_id, student_id) VALUES (%s, %s)
        """
        cursor.execute(query, (parent_id, student_id))
        connection.commit()

        return jsonify({'status': 'success', 'message': 'Parent linked to student successfully'}), 200
    except mysql.connector.Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        close_connection(connection)

# Get Student Parents
@app.route('/api/students/<int:student_id>/', methods=['GET'])
def get_student_parents(student_id):
    connection = create_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT full_name FROM students WHERE student_id = %s", (student_id,))
        student = cursor.fetchone()

        cursor.execute("""
            SELECT p.parent_id, p.full_name, p.relationship, p.phone, p.email
            FROM parents p
            JOIN student_parent sp ON p.parent_id = sp.parent_id
            WHERE sp.student_id = %s
        """, (student_id,))

        parents = cursor.fetchall()
        return jsonify({
            'status': 'success',
            'data': {
                'student_id': student_id,
                'full_name': student['full_name'],
                'parents': parents
            }
        }), 200
    except mysql.connector.Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        close_connection(connection)
    

        






if __name__ == "__main__":
    #app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "default_secret")
    app.run(debug=True)

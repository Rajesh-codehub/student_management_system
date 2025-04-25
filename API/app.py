from flask import Flask, request, jsonify
from dbconn import create_connection, close_connection
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from flask_cors import CORS
from datetime import datetime, timedelta
import calendar


app = Flask(__name__)
CORS(app)


app.config["SECRET_KEY"] = 'y&f9Mv$e!zR3P@bE#tKqU1Xc4gL*oN7a'


# Register API
@app.route("/register", methods = ['POST'])
def register_user():
    username = request.form.get('username')
    password = request.form.get('password')
    email = request.form.get('email')
    full_name = request.form.get('full_name')
    role = request.form.get('role')

    if not all([username, password, email, full_name, role]):
        return jsonify({"status":"Error", "message":"All fields are required"}), 400
    hashed_password = generate_password_hash(password)
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # check if username or email already exits
        cursor.execute("select * from users where username = %s or email = %s", (username, email))
        if cursor.fetchone():
            return jsonify({"status":"Error", "message":"username or email already exists"}), 400
        
        # insert new user
        cursor.execute("""
        insert into users(username, password, email, role, full_name)
        values(%s, %s, %s, %s, %s)""", (username, hashed_password, email, role, full_name))
        conn.commit()
        userid = cursor.lastrowid

        return jsonify(
            {
                "status":"success",
                "message":"User registered successfully",
                "data":{
                    "user_id": userid,
                    "username": username,
                    "email": email,
                    "role": role
                }
            }
        ), 200
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 500
    finally:
        cursor.close()
        close_connection(conn)

# login API
@app.route("/login", methods=["POST"])
def login_user():
    username = request.form.get('username')
    password = request.form.get('password')
    

    if not all([username, password]):
        return jsonify({"status":"Error", "message":"All fields are required"}), 400

    
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("select * from users where username = %s", (username,))
        results = cursor.fetchone()


        if not results or not check_password_hash(results['password'], password):
            return jsonify({"status": "fail", "message": "Invalid username or password"}), 400

        # generate jwt token
        token = jwt.encode({
            "user_id":results["user_id"],
            "username":results['username'],
            "role":results["role"],
            "exp":datetime.utcnow()+ timedelta(hours=2)
        }, app.config["SECRET_KEY"], algorithm="HS256")

        return jsonify(
            {
                "status":"success",
                "message":"login successfull",
                "data":{
                    "user_id":results["user_id"],
                    "username":results['username'],
                    "role":results['role'],
                    "token":token
                }
            }
        ), 200

    except Exception as e:
        return jsonify({"status": "fail", "message": str(e)}), 500
    finally:
        cursor.close()
        close_connection(conn)


@app.route('/delete_student', methods = ['POST'])
def delete_student():

    data = request.form

    student_id = data.get("student_id")
    conn = create_connection()

    if not conn:
        return jsonify ({'status': "Error", "message": "Database connetion failed "}), 500

    try:

        cursor = conn.cursor()

        #check if student exists or not

        cursor.execute("select * from students where student_id = %s", (student_id,))

        student = cursor.fetchone()

        if not student:
            return jsonify ({"status": "error", "message": "student not found"}), 404

        # Delete student

        cursor.execute("delete from students where student_id = %s", (student_id,))
        conn.commit()

        return jsonify({"status": "success", "message": f'student with id {student_id} deleted'}), 200
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        close_connection(conn)


    

@app.route("/add_student", methods = ['POST'])
def add_student():
    data = request.form



    #extract form data
    first_name = data.get("first_name")
    grade = data.get("grade")
    date_of_birth = data.get("date_of_birth")
    gender = data.get("gender")
    email = data.get("email")
    phone = data.get("phone")
    address = data.get("address")
    fee_status = data.get("fee_status")
    total_fee = data.get("total_fee")
    status = data.get("status")

    if not first_name or not grade:
        return jsonify({"status": "Error", "message": "first name and grade are required"}), 400
    
    conn = create_connection()
    if not conn:
        jsonify ({"status":"Error", "message":"database connection failed"}), 500
    
    try:

        cursor = conn.cursor()

        insert_query = """
        insert into students (full_name, date_of_birth, gender, email, phone, address, fee_status, total_fee, grade, status)
        values (%s, %s, %s,%s, %s, %s, %s, %s, %s, %s )
        """

        values = (first_name, date_of_birth, gender, email, phone, address, fee_status, total_fee, grade, status)

        cursor.execute(insert_query, values)

        conn.commit()

        return jsonify({"status":"success", "message": "student data added successfully"}), 201

        
    except Exception as e:

        return jsonify({'status': "Error", "message": str(e)}), 500
    
    finally:
        cursor.close()
        close_connection(conn)

@app.route("/update_student", methods= ['POST'])
def update_student():

    data = request.form

    student_id = data.get("student_id")

  #validate presence of student id 
    if not student_id:
        return jsonify ({"status":"Error", "message":"student id is required"}), 400
    # get fields to update
    fields = {
        "first_name": data.get("first_name"),
        "last_name": data.get("last_name"),
        "date_of_birth": data.get("date_fo_birth"),
        "gender": data.get("gender"),
        "email": data.get("email"),
        "phone": data.get("phone"),
        "address": data.get("address")
    }

    # remove keys with none values
     
    fields = {key : value for key, value in fields.items() if value is not None}

    if not fields:
        return jsonify({"status": "Error", "message":" no update fields provided"})
    
    conn = create_connection()

    if not conn:
        return jsonify({"status": "Error", "message": "Database connection failed"}), 500
    
    try:
        cursor = conn.cursor()

        cursor.execute("select * from students where student_id = %s", (student_id,))

        if not cursor.fetchone():
            return jsonify({'status':"Error", "message" : "student not found"}), 404
        
        # build dyanamic sql
        set_clause = ", ".join([f"{key} = %s" for key in fields.keys()])

        values = list(fields.values())+ [student_id]

        update_query = f" update students set {set_clause} where student_id = %s"

        cursor.execute(update_query, values)

        conn.commit()

        return jsonify({"status": "success", 'message': "student details updated"}), 200
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 500
    
    finally:
        cursor.close()
        close_connection(conn)

@app.route("/student/<int:student_id>", methods= ["GET"])
def view_student(student_id):
    conn = create_connection()

    if not conn:
        return jsonify({"status":"Error", "message":"database connection failed"}), 500
    
    try:
        cursor = conn.cursor()

        cursor.execute("select * from students where student_id = %s", (student_id,))

        student = cursor.fetchone()

        if not student:

            return jsonify({"status": "Error", "message": "student not found"}), 404
        
        column_names = [desc[0] for desc in cursor.description]

        student_data  = dict(zip(column_names, student))

        return jsonify({'status': 'success', "data": student_data}), 200
        

    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 500
    
    finally:
        cursor.close()
        close_connection(conn)

@app.route("/students", methods = ["GET"])
def view_all_students():
    conn = create_connection()

    if not conn:
        return jsonify({"status":"Error", "message": "database connection failed"}), 500
    
    try:
        cursor = conn.cursor()

        cursor.execute("select * from students;")

        students = cursor.fetchall()

        if not students:
            return jsonify({"status": "success",  "data": [], "message": " no students found"}), 200
        
        column_names = [desc[0] for desc in cursor.description]

        student_list = [dict(zip(column_names, student)) for student in students]

        return jsonify({"status" :"success", "data": student_list}), 200
    
    except Exception as e:
        return jsonify({"status" : 'Error', "message": str(e)}), 500
    
    finally:
        cursor.close()
        close_connection(conn)

@app.route("/fee_dues/<int:student_id>", methods = ["GET"])
def check_fee_dues(student_id):
    conn = create_connection()

    if not conn:
        return jsonify({'status': "Error", "message": "database connection failed"}), 500
    
    try:
        cursor = conn.cursor()

        cursor.execute("select total_fee, amount_paid from student_fees where student_id = %s", (student_id,))

        fees = cursor.fetchone()

        if not fees:
            return jsonify({'status': "Error", "message":"No fee  record found for student"}), 404

        total_fee, amount_paid = fees

        due_amount = float(total_fee) - float(amount_paid)

        return jsonify({
            "status": "success",
            "student_id": student_id,
            "total_fee": float(total_fee),
            "amount_paid": float(amount_paid),
            "due_amount": round(due_amount, 2)

        }), 200
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 500
    finally:
        cursor.close()
        close_connection(conn)
    
@app.route("/record_payment", methods=["POST"])
def record_fee_payment():
    data = request.form

    payment_amount = data.get("payment_amount")
    student_id = data.get("student_id")
    payment_method = data.get("payment_method")
    remarks = data.get("remarks")
    payment_date = data.get("payment_date")  # Optional

    if not payment_amount or not student_id or not payment_method:
        return jsonify({"status": "Error", "message": "payment_amount, student_id, and payment_method are required"}), 400

    try:
        payment_amount = float(payment_amount)
    except Exception:
        return jsonify({'status': "Error", "message": "invalid payment amount"}), 400

    conn = create_connection()
    if not conn:
        return jsonify({"status": "Error", "message": "database connection failed"}), 500

    try:
        cursor = conn.cursor()

        # Check if record exists
        cursor.execute("SELECT total_fee, amount_paid FROM student_fees WHERE student_id = %s", (student_id,))
        fee = cursor.fetchone()

        if not fee:
            # Assume default total fee (you can modify this logic)
            default_total_fee = 10000  # Example total fee

            if not payment_date:
                cursor.execute("""
                    INSERT INTO student_fees (student_id, total_fee, amount_paid, payment_date, payment_method, remarks)
                    VALUES (%s, %s, %s, CURRENT_DATE, %s, %s)
                """, (student_id, default_total_fee, payment_amount, payment_method, remarks))
            else:
                cursor.execute("""
                    INSERT INTO student_fees (student_id, total_fee, amount_paid, payment_date, payment_method, remarks)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (student_id, default_total_fee, payment_amount, payment_date, payment_method, remarks))

            conn.commit()
            return jsonify({"status": "success", "message": "payment recorded successfully (new record created)"}), 201

        # Existing record: update
        total_fee, amount_paid = fee
        new_payment_amount = float(amount_paid) + payment_amount

        if new_payment_amount > float(total_fee):
            return jsonify({"status": "Error", "message": "payment exceeds total fee"}), 400

        if not payment_date:
            cursor.execute("""
                UPDATE student_fees 
                SET amount_paid = %s, payment_date = CURRENT_DATE,
                    payment_method = %s, remarks = %s
                WHERE student_id = %s
            """, (new_payment_amount, payment_method, remarks, student_id))
        else:
            cursor.execute("""
                UPDATE student_fees 
                SET amount_paid = %s, payment_date = %s,
                    payment_method = %s, remarks = %s
                WHERE student_id = %s
            """, (new_payment_amount, payment_date, payment_method, remarks, student_id))

        conn.commit()
        return jsonify({"status": "success", "message": "payment recorded successfully"}), 200

    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 500

    finally:
        cursor.close()
        close_connection(conn)


        
@app.route("/search_student", methods=["POST", "GET"])
def search_student():
    if request.method == "POST":
        query = request.args.get("query")
    else:
        query = request.args.get("query")

    

    if not query:
        return jsonify({"status": "Error", "message": "query field required"}), 400

    conn = create_connection()

    if not conn:
        return jsonify({"status": "Error", "message": "database connection failed"}), 500

    try:
        cursor = conn.cursor()

        # Search by first_name, last_name, email, or phone
        search_query = """
            SELECT * FROM students
            WHERE full_name LIKE %s
            OR grade LIKE %s
            OR email LIKE %s
            OR phone LIKE %s
        """

        wildcard_query = f"%{query}%"
        cursor.execute(search_query, (wildcard_query, wildcard_query, wildcard_query, wildcard_query))

        results = cursor.fetchall()

        if not results:
            return jsonify({"status": "success", "data": [], "message": "no students found"}), 200

        column_names = [desc[0] for desc in cursor.description]
        students = [dict(zip(column_names, row)) for row in results]

        return jsonify({"status": "success", "data": students}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        cursor.close()
        close_connection(conn)

@app.route("/search_student_by_id", methods=["GET"])
def search_student_by_id():
    student_id = request.args.get("student_id")

    if not student_id:
        return jsonify({"status": "Error", "message": "student_id field required"}), 400

    conn = create_connection()

    if not conn:
        return jsonify({"status": "Error", "message": "database connection failed"}), 500

    try:
        cursor = conn.cursor()

        # Search by student_id
        search_query = "SELECT * FROM students WHERE student_id = %s"
        cursor.execute(search_query, (student_id,))

        result = cursor.fetchone()

        if not result:
            return jsonify({"status": "success", "data": {}, "message": "student not found"}), 200

        column_names = [desc[0] for desc in cursor.description]
        student = dict(zip(column_names, result))

        return jsonify({"status": "success", "data": student}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        cursor.close()
        close_connection(conn)



@app.route('/student_statistics', methods=['GET'])
def get_student_statistics():
    try:
        conn = create_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Total students
        cursor.execute("SELECT COUNT(*) as total FROM students")
        total_students = cursor.fetchone()['total']
        
        # New admissions (count and latest 10 records)
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        cursor.execute("SELECT COUNT(*) as new_admissions FROM students WHERE enrollment_date >= %s", (thirty_days_ago,))
        new_admission_count = cursor.fetchone()['new_admissions']

        cursor.execute(
            """SELECT student_id, full_name, grade, enrollment_date 
               FROM students 
               WHERE enrollment_date >= %s 
               ORDER BY enrollment_date DESC 
               LIMIT 10""", 
            (thirty_days_ago,)
        )
        new_admissions_list = cursor.fetchall()

        # Pending fees (students where amount paid < total_fee)
        cursor.execute(
            """SELECT COUNT(DISTINCT s.student_id) as pending_amount
               FROM students s
               JOIN student_fees sf ON s.student_id = sf.student_id
               WHERE sf.amount_paid < sf.total_fee"""
        )
        pending_count = cursor.fetchone()['pending_amount']
        
        # Recent payments (latest 10)
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        cursor.execute(
            """SELECT s.student_id, s.full_name, sf.amount_paid, sf.payment_date
               FROM student_fees sf
               JOIN students s ON sf.student_id = s.student_id
               WHERE sf.payment_date >= %s
               ORDER BY sf.payment_date DESC
               LIMIT 10""", 
            (seven_days_ago,)
        )
        recent_payments = cursor.fetchall()
        
        # Monthly admissions for bar graph (current year)
        current_year = datetime.now().year
        monthly_data = []
        
        for month in range(1, 13):
            month_name = calendar.month_name[month]
            cursor.execute(
                """SELECT COUNT(*) as count
                   FROM students
                   WHERE YEAR(enrollment_date) = %s AND MONTH(enrollment_date) = %s""", 
                (current_year, month)
            )
            count = cursor.fetchone()['count']
            monthly_data.append({
                'month': month_name,
                'count': count
            })
        
        return jsonify({
            "status": 'success',
            "data": {
                'total_students': total_students,
                "new_admission_count": new_admission_count,
                "new_admissions": new_admissions_list,
                'pending_fees': pending_count,
                'recent_payments': recent_payments,
                'monthly_admissions': monthly_data
            }
        })
    
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 500
    
    finally:
        cursor.close()
        close_connection(conn)

@app.route("/fetch_payment", methods=['GET'])
def fetch_payment_details():

    student_id = request.args.get("student_id")

    if not student_id:
        return jsonify({"error": "Missing student_id in request"}), 400
    
    conn = create_connection()
    cursor = conn.cursor()

    query="""
    SELECT 
    s.full_name,
    s.grade,
    sf.fee_status,
    (sf.total_fee - sf.amount_paid) AS pending_fee
    FROM 
        students s
    JOIN 
        student_fees sf 
    where s.student_id = %s
    """
    cursor.execute(query, (student_id,))
    results = cursor.fetchall()
    cursor.close()
    close_connection(conn)

    return jsonify(results)
    
    


    

        







if __name__ == '__main__':
    app.run(debug=True)
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





auth_bp = Blueprint("auth", __name__)



#Register API
@auth_bp.route("/register", methods = ['POST'])
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
@auth_bp.route("/login", methods=["POST"])
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
        }, current_app.config["SECRET_KEY"], algorithm="HS256")

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
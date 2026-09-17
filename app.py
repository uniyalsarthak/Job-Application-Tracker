from flask import Flask, render_template, request, jsonify, session, redirect, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import mysql.connector
from mysql.connector import Error
import os
import uuid

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("DB_NAME", "job_tracker_new")
}

# Change this in a real deployment.
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")

# Where uploaded resumes are stored on disk.
UPLOAD_FOLDER = os.path.join(app.root_path, "uploads", "resumes")
ALLOWED_RESUME_EXTENSIONS = {"pdf", "doc", "docx"}
MAX_RESUME_SIZE_MB = 5

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["MAX_CONTENT_LENGTH"] = MAX_RESUME_SIZE_MB * 1024 * 1024


def allowed_resume_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_RESUME_EXTENSIONS
    )


def save_resume_file(file_storage):
    """Saves an uploaded resume to disk and returns (original_filename, stored_path)."""
    if not file_storage or file_storage.filename == "":
        return None, None

    original_name = secure_filename(file_storage.filename)

    if not allowed_resume_file(original_name):
        raise ValueError("Resume must be a PDF, DOC, or DOCX file")

    unique_name = f"{uuid.uuid4().hex}_{original_name}"
    stored_path = os.path.join(UPLOAD_FOLDER, unique_name)
    file_storage.save(stored_path)

    return original_name, unique_name


def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)


@app.route("/")
def home():
    if "user_id" not in session:
        return render_template("index.html", logged_in=False)

    return render_template(
        "index.html",
        logged_in=True,
        user_email=session.get("email")
    )


@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({"error": "Name, email and password are required"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT id FROM users WHERE email = %s",
            (email,)
        )

        if cursor.fetchone():
            cursor.close()
            connection.close()
            return jsonify({"error": "An account with this email already exists"}), 409

        password_hash = generate_password_hash(password)

        cursor.execute("""
            INSERT INTO users (name, email, password_hash)
            VALUES (%s, %s, %s)
        """, (name, email, password_hash))

        connection.commit()

        user_id = cursor.lastrowid

        cursor.close()
        connection.close()

        session["user_id"] = user_id
        session["email"] = email
        session["name"] = name

        return jsonify({
            "message": "Account created successfully"
        }), 201

    except Error as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, name, email, password_hash
            FROM users
            WHERE email = %s
        """, (email,))

        user = cursor.fetchone()

        cursor.close()
        connection.close()

        if not user or not check_password_hash(
            user["password_hash"], password
        ):
            return jsonify({"error": "Invalid email or password"}), 401

        session["user_id"] = user["id"]
        session["email"] = user["email"]
        session["name"] = user["name"]

        return jsonify({"message": "Login successful"})

    except Error as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"})


def require_login():
    if "user_id" not in session:
        return jsonify({"error": "Please log in first"}), 401

    return None


@app.route("/api/applications", methods=["GET"])
def get_applications():
    auth_error = require_login()
    if auth_error:
        return auth_error

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # IMPORTANT:
        # Only return applications belonging to the logged-in user.
        cursor.execute("""
            SELECT id, company, role, application_date, status, notes,
                   resume_filename, resume_path
            FROM applications
            WHERE user_id = %s
            ORDER BY application_date DESC, id DESC
        """, (session["user_id"],))

        applications = cursor.fetchall()

        for application in applications:
            if application["application_date"]:
                application["application_date"] = (
                    application["application_date"].isoformat()
                )

        cursor.close()
        connection.close()

        return jsonify(applications)

    except Error as e:
        return jsonify({"error": str(e)}), 500


ALLOWED_STATUSES = {
    "Applied",
    "In Progress",
    "Selected",
    "Rejected"
}


@app.route("/api/applications", methods=["POST"])
def add_application():
    auth_error = require_login()
    if auth_error:
        return auth_error

    data = request.form

    required_fields = ["company", "role", "application_date", "status"]

    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    if data["status"] not in ALLOWED_STATUSES:
        return jsonify({"error": "Invalid status"}), 400

    try:
        resume_filename, resume_path = save_resume_file(
            request.files.get("resume")
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO applications
            (user_id, company, role, application_date, status, notes,
             resume_filename, resume_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            session["user_id"],
            data["company"].strip(),
            data["role"].strip(),
            data["application_date"],
            data["status"],
            data.get("notes", "").strip(),
            resume_filename,
            resume_path
        ))

        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({
            "message": "Application added successfully"
        }), 201

    except Error as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/applications/<int:application_id>", methods=["PUT"])
def update_application(application_id):
    auth_error = require_login()
    if auth_error:
        return auth_error

    data = request.form

    required_fields = ["company", "role", "application_date", "status"]

    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    if data["status"] not in ALLOWED_STATUSES:
        return jsonify({"error": "Invalid status"}), 400

    try:
        new_resume_filename, new_resume_path = save_resume_file(
            request.files.get("resume")
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # user_id condition prevents one user from editing another
        # user's application even if they somehow know its ID.
        cursor.execute("""
            SELECT resume_path FROM applications
            WHERE id = %s AND user_id = %s
        """, (application_id, session["user_id"]))

        existing = cursor.fetchone()

        if not existing:
            cursor.close()
            connection.close()
            return jsonify({"error": "Application not found"}), 404

        old_resume_path = existing["resume_path"]

        if new_resume_path:
            resume_filename = new_resume_filename
            resume_path = new_resume_path
        else:
            resume_filename = None
            resume_path = old_resume_path
            cursor.execute(
                "SELECT resume_filename FROM applications WHERE id = %s",
                (application_id,)
            )
            resume_filename = cursor.fetchone()["resume_filename"]

        cursor.execute("""
            UPDATE applications
            SET company = %s,
                role = %s,
                application_date = %s,
                status = %s,
                notes = %s,
                resume_filename = %s,
                resume_path = %s
            WHERE id = %s AND user_id = %s
        """, (
            data["company"].strip(),
            data["role"].strip(),
            data["application_date"],
            data["status"],
            data.get("notes", "").strip(),
            resume_filename,
            resume_path,
            application_id,
            session["user_id"]
        ))

        connection.commit()

        # If a new resume replaced an old one, remove the old file from disk.
        if new_resume_path and old_resume_path:
            old_full_path = os.path.join(UPLOAD_FOLDER, old_resume_path)
            if os.path.exists(old_full_path):
                os.remove(old_full_path)

        cursor.close()
        connection.close()

        return jsonify({"message": "Application updated successfully"})

    except Error as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/applications/<int:application_id>", methods=["DELETE"])
def delete_application(application_id):
    auth_error = require_login()
    if auth_error:
        return auth_error

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT resume_path FROM applications
            WHERE id = %s AND user_id = %s
        """, (application_id, session["user_id"]))

        existing = cursor.fetchone()

        if not existing:
            cursor.close()
            connection.close()
            return jsonify({"error": "Application not found"}), 404

        cursor.execute("""
            DELETE FROM applications
            WHERE id = %s AND user_id = %s
        """, (application_id, session["user_id"]))

        connection.commit()
        cursor.close()
        connection.close()

        if existing["resume_path"]:
            full_path = os.path.join(UPLOAD_FOLDER, existing["resume_path"])
            if os.path.exists(full_path):
                os.remove(full_path)

        return jsonify({"message": "Application deleted successfully"})

    except Error as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/applications/<int:application_id>/resume", methods=["GET"])
def view_resume(application_id):
    auth_error = require_login()
    if auth_error:
        return auth_error

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT resume_filename, resume_path FROM applications
            WHERE id = %s AND user_id = %s
        """, (application_id, session["user_id"]))

        application = cursor.fetchone()

        cursor.close()
        connection.close()

        if not application or not application["resume_path"]:
            return jsonify({"error": "No resume found for this application"}), 404

        return send_from_directory(
            UPLOAD_FOLDER,
            application["resume_path"],
            as_attachment=False,
            download_name=application["resume_filename"]
        )

    except Error as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True) 
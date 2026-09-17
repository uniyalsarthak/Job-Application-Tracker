# Job Application Tracker

A multi-user job application tracker built with HTML, CSS, JavaScript, Flask and MySQL.

## Project structure

```text
job_application_tracker/
│
├── app.py
├── database.sql
├── requirements.txt
├── README.md
│
├── templates/
│   └── index.html
│
└── static/
    ├── style.css
    └── script.js
```

## 1. Install dependencies

Create a virtual environment:

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

Install packages:

```powershell
pip install -r requirements.txt
```

## 2. Set up MySQL

Open MySQL Workbench while connected to your MySQL Server.

Run `database.sql`.

It creates:

```text
job_tracker
├── users
└── applications
```

## 3. Configure MySQL password

Open `app.py` and change:

```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "YOUR_MYSQL_PASSWORD",
    "database": "job_tracker"
}
```

Replace `YOUR_MYSQL_PASSWORD` with your actual MySQL password.

## 4. Run the application

```powershell
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## How login works

When a user registers:

```text
Browser
   ↓
POST /api/register
   ↓
Flask
   ↓
Password is hashed
   ↓
users table
```

When the user logs in:

```text
Email + password
       ↓
POST /api/login
       ↓
Flask checks password hash
       ↓
Session stores user_id
       ↓
Dashboard
```



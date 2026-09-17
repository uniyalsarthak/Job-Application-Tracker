# Job Application Tracker — Flask + MySQL + Login

A multi-user job application tracker built with HTML, CSS, JavaScript, Flask and MySQL.

## Important database design

Do NOT create a separate MySQL database for every user.

Instead, this project uses one database:

```text
job_tracker
```

with two tables:

```text
users
  |
  | 1-to-many
  v
applications
```

Every application has a `user_id`.

That means:

```text
User A
  ├── KPMG
  ├── Infosys
  └── TCS

User B
  ├── Google
  └── Microsoft
```

Both users use the same `applications` table, but Flask only retrieves the rows belonging to the logged-in user.

This is the normal and scalable approach.

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

Do NOT double-click `index.html`.

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

## How user-specific applications work

Suppose user ID 1 adds KPMG.

The database stores:

```text
id | user_id | company | role
1  | 1       | KPMG    | Analyst
```

User ID 2 adds Google:

```text
id | user_id | company | role
2  | 2       | Google  | SDE
```

When user ID 1 logs in, Flask runs:

```sql
SELECT ...
FROM applications
WHERE user_id = 1;
```

Therefore user ID 1 sees only KPMG.

When user ID 2 logs in:

```sql
SELECT ...
FROM applications
WHERE user_id = 2;
```

They see only Google.

## Security implemented

- Passwords are stored as hashes, not plain text.
- Email is unique.
- Flask session identifies the logged-in user.
- GET only returns that user's applications.
- UPDATE checks both application ID and user ID.
- DELETE checks both application ID and user ID.
- Deleting a user cascades to their applications.

## API endpoints

Authentication:

```text
POST /api/register
POST /api/login
POST /api/logout
```

Applications:

```text
GET    /api/applications
POST   /api/applications
PUT    /api/applications/<id>
DELETE /api/applications/<id>
```

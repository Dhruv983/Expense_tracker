/expense-tracker
├── app.py
├── requirements.txt
├── config.py
├── /static
│   ├── style.css
│   └── chart.js
├── /templates
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── index.html
│   └── add_expense.html
└── .ebextensions
    └── python.config


steps to deploy locally

# Navigate to project directory
cd expense-tracker

# Create virtual environment (Windows)
python -m venv venv
# or for Mac/Linux
python3 -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt

# Set Flask app environment variable
export FLASK_APP=app.py  # Mac/Linux
set FLASK_APP=app.py     # Windows

# Initialize database
flask shell
>>> from app import db
>>> db.create_all()
>>> exit()

# For development mode (with debugger)
flask run --debug

# Or alternatively
python app.py
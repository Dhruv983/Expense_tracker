from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from config import Config
from datetime import datetime, timedelta
import pytz 

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-123')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///expenses.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    expenses = db.relationship('Expense', backref='user', lazy=True)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    card = db.Column(db.String(50))
    note = db.Column(db.String(200))
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Routes
@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    current_month = datetime.utcnow().month
    
    # Get expenses for current month
    expenses = Expense.query.filter(
        Expense.user_id == user.id,
        db.extract('month', Expense.date) == current_month
    ).all()
    
    # Prepare chart data
    categories = {}
    for expense in expenses:
        categories[expense.category] = categories.get(expense.category, 0) + expense.amount
    
    return render_template('index.html', 
                         categories=categories,
                         total=sum(categories.values()),
                         expenses=expenses)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('home'))
        
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error='Username exists')
            
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/add', methods=['GET', 'POST'])
def add_expense():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        amount = float(request.form['amount'])
        category = request.form['category']
        payment_method = request.form['payment_method']
        card = request.form.get('card', '')
        note = request.form.get('note', '')
        
        new_expense = Expense(
            amount=amount,
            category=category,
            payment_method=payment_method,
            card=card,
            note=note,
            user_id=session['user_id']
        )
        db.session.add(new_expense)
        db.session.commit()
        return redirect(url_for('home'))
    
    return render_template('add_expense.html')

@app.route('/category/<category_name>')
def category_expenses(category_name):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    current_month = datetime.utcnow().month
    
    # Get expenses with Newfoundland time
    expenses = Expense.query.filter(
        Expense.user_id == user.id,
        Expense.category == category_name,
        db.extract('month', Expense.date) == current_month
    ).order_by(Expense.date.desc()).all()
    
    # Convert times to Newfoundland
    newfoundland = pytz.timezone('America/St_Johns')
    for expense in expenses:
        utc_time = expense.date.replace(tzinfo=pytz.utc)
        expense.local_date = utc_time.astimezone(newfoundland)
    
    return render_template('category_expenses.html',
                         category=category_name,
                         expenses=expenses)

# Add these new routes
@app.route('/delete/<int:expense_id>', methods=['POST'])
def delete_expense(expense_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    expense = Expense.query.get_or_404(expense_id)
    if expense.user_id != session['user_id']:
        abort(403)
    
    db.session.delete(expense)
    db.session.commit()
    return redirect(request.referrer)

@app.route('/edit/<int:expense_id>', methods=['GET', 'POST'])
def edit_expense(expense_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    expense = Expense.query.get_or_404(expense_id)
    if expense.user_id != session['user_id']:
        abort(403)

    if request.method == 'POST':
        expense.amount = float(request.form['amount'])
        expense.category = request.form['category']
        expense.payment_method = request.form['payment_method']
        expense.card = request.form.get('card', '')
        expense.note = request.form.get('note', '')
        
        db.session.commit()
        return redirect(url_for('category_expenses', category_name=expense.category))
    
    # For GET request, render edit form
    return render_template('edit_expense.html', expense=expense)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
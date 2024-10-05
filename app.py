from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///finance.db"
app.config["SECRET_KEY"] = "2160d9f2965f252a882c65054457caa4c87e48372b5d7227"  # Secret Key added here

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    budget = db.Column(db.Float, default=0.0)  # Budget field

# Income model
class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=False)

# Expense model
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=False)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for("dashboard"))
        else:
            return "Invalid credentials"
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for("login"))

    total_income = db.session.query(db.func.sum(Income.amount)).filter_by(user_id=user_id).scalar() or 0
    total_expenses = db.session.query(db.func.sum(Expense.amount)).filter_by(user_id=user_id).scalar() or 0
    budget = User.query.get(user_id).budget  # Retrieve user's budget
    remaining_budget = budget - total_expenses  # Calculate remaining budget
    recent_income = Income.query.filter_by(user_id=user_id).order_by(Income.id.desc()).limit(5).all()
    recent_expenses = Expense.query.filter_by(user_id=user_id).order_by(Expense.id.desc()).limit(5).all()

    return render_template(
        "dashboard.html",
        total_income=total_income,
        total_expenses=total_expenses,
        budget=budget,
        remaining_budget=remaining_budget,
        recent_income=recent_income,
        recent_expenses=recent_expenses
    )

@app.route("/add_income", methods=["POST"])
def add_income():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for("login"))

    amount = float(request.form["amount"])
    description = request.form["description"]
    income = Income(user_id=user_id, amount=amount, description=description)
    db.session.add(income)
    db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/add_expense", methods=["POST"])
def add_expense():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for("login"))

    amount = float(request.form["amount"])
    description = request.form["description"]
    expense = Expense(user_id=user_id, amount=amount, description=description)
    db.session.add(expense)
    db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/update_budget", methods=["POST"])
def update_budget():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for("login"))

    new_budget = float(request.form["budget"])
    user = User.query.get(user_id)
    user.budget = new_budget
    db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.pop('user_id', None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)


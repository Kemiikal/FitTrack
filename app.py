from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import date

app = Flask(__name__)
app.secret_key = "FitTrack_is_the_best!"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fittrack.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models 
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    calories = db.Column(db.Integer, nullable=False)
    protein = db.Column(db.Float, default=0)
    carbs = db.Column(db.Float, default=0)
    fats = db.Column(db.Float, default=0)
    date = db.Column(db.Date, default=date.today)

# Routes 
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        if not username or not password:
            flash('Please enter username and password')
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Account created. Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        username = request.form['username'].strip()
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # simple totals example
    meals = Meal.query.filter_by(user_id=session['user_id']).order_by(Meal.date.desc()).all()
    total_cal = sum(m.calories for m in meals if m.date == date.today())
    return render_template('dashboard.html', total_cal=total_cal, meals=meals)

@app.route('/meals', methods=['GET','POST'])
def meals():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        calories = int(request.form['calories'] or 0)
        protein = float(request.form['protein'] or 0)
        carbs = float(request.form['carbs'] or 0)
        fats = float(request.form['fats'] or 0)
        m = Meal(user_id=session['user_id'], name=name, calories=calories, protein=protein, carbs=carbs, fats=fats)
        db.session.add(m)
        db.session.commit()
        flash('Meal added')
        return redirect(url_for('meals'))
    meals = Meal.query.filter_by(user_id=session['user_id']).order_by(Meal.date.desc()).all()
    return render_template('meals.html', meals=meals)

@app.route('/edit_meal/<int:meal_id>', methods=['GET', 'POST'])
def edit_meal(meal_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    meal = Meal.query.get_or_404(meal_id)  

    if request.method == 'POST':
        meal.name = request.form['name']
        meal.calories = int(request.form['calories'] or 0)
        meal.protein = float(request.form['protein'] or 0)
        meal.carbs = float(request.form['carbs'] or 0)
        meal.fats = float(request.form['fats'] or 0)
        db.session.commit()
        flash('Meal updated successfully.')
        return redirect(url_for('meals'))

    return render_template('edit_meal.html', meal=meal)

@app.route('/delete_meal/<int:meal_id>', methods=['POST'])
def delete_meal(meal_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    meal = Meal.query.get_or_404(meal_id)
    db.session.delete(meal)
    db.session.commit()
    flash('Meal deleted successfully.')
    return redirect(url_for('meals'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

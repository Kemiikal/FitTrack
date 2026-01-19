from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import date, timedelta, datetime
from werkzeug.security import generate_password_hash, check_password_hash
from collections import defaultdict
import csv
from threading import Timer
import pytz

app = Flask(__name__)
app.secret_key = "W_FitTrack"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fittrack.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

LOCAL_TIMEZONE = pytz.timezone('Asia/Jakarta') 
UTC = pytz.UTC

def utc_to_local(utc_dt):
    if utc_dt.tzinfo is None:
        utc_dt = UTC.localize(utc_dt)
    return utc_dt.astimezone(LOCAL_TIMEZONE)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    security_question = db.Column(db.String(200), nullable=False)
    security_answer = db.Column(db.String(200), nullable=False)
    workout_reminder = db.Column(db.Boolean, default=True)
    meal_reminder = db.Column(db.Boolean, default=True)
    progress_summary_frequency = db.Column(db.String(20), default='weekly')

class MealTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    calories = db.Column(db.Integer, nullable=False)
    protein = db.Column(db.Float, default=0)
    carbs = db.Column(db.Float, default=0)
    fats = db.Column(db.Float, default=0)
    frequency = db.Column(db.Integer, default=1)

    @classmethod
    def get_or_create(cls, user_id, name, calories, protein, carbs, fats):
        template = cls.query.filter_by(user_id=user_id, name=name).first()
        if template:
            template.frequency += 1
            template.calories, template.protein, template.carbs, template.fats = calories, protein, carbs, fats
        else:
            template = cls(user_id=user_id, name=name, calories=calories, protein=protein, carbs=carbs, fats=fats)
            db.session.add(template)
        return template

class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    calories = db.Column(db.Integer, nullable=False)
    protein = db.Column(db.Float, default=0)
    carbs = db.Column(db.Float, default=0)
    fats = db.Column(db.Float, default=0)
    quantity = db.Column(db.Integer, default=1)
    date = db.Column(db.Date, default=date.today)
    is_favorite = db.Column(db.Boolean, default=False)

class WorkoutTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    exercise_type = db.Column(db.String(50), nullable=False)  
    muscle_groups = db.Column(db.String(500), default='')  
    frequency = db.Column(db.Integer, default=1)
    is_custom = db.Column(db.Boolean, default=False)  
    calories_per_hour = db.Column(db.Integer, default=0) 

    @classmethod
    def get_or_create(cls, user_id, name, exercise_type, muscle_groups, is_custom=False, calories_per_hour=0):
        template = cls.query.filter_by(user_id=user_id, name=name).first()
        if template:
            template.frequency += 1
        else:
            template = cls(
                user_id=user_id,
                name=name,
                exercise_type=exercise_type,
                muscle_groups=muscle_groups,
                is_custom=is_custom,
                calories_per_hour=calories_per_hour
            )
            db.session.add(template)
        return template

class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    exercise_type = db.Column(db.String(50), nullable=False)
    muscle_groups = db.Column(db.String(500), default='') 
    duration = db.Column(db.Integer, default=0)
    sets = db.Column(db.Integer, default=0)
    reps = db.Column(db.Integer, default=0)
    weight = db.Column(db.Float, default=0) #workout weight
    volume = db.Column(db.Float, default=0)
    intensity = db.Column(db.Float, default=1.0)  
    calories_burned = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, default=date.today)
    is_favorite = db.Column(db.Boolean, default=False)

class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, unique=True)
    height = db.Column(db.Float)  
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20)) 
    physical_activity_level = db.Column(db.String(50))

class BodyMeasurement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, default=date.today, nullable=False)
    weight = db.Column(db.Float) 
    body_fat_percentage = db.Column(db.Float) 
    chest = db.Column(db.Float)  
    waist = db.Column(db.Float)  
    hips = db.Column(db.Float)
    biceps = db.Column(db.Float) 
    thighs = db.Column(db.Float) 
    neck = db.Column(db.Float)
    notes = db.Column(db.Text)  

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    message = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    is_read = db.Column(db.Boolean, default=False)

@app.context_processor
def utility_processor():
    unread_count = 0
    try:
        if 'user_id' in session:
            unread_count = Notification.query.filter_by(user_id=session['user_id'], is_read=False).count()
    except Exception:
        pass
    return {'request': request, 'unread_notifications_count': unread_count}

def get_user_id():
    return session.get('user_id')

def delete_user_item(model, item_id, user_id, item_name):
    item = model.query.get_or_404(item_id)
    if item.user_id != user_id:
        flash('unauthorized')
        return False
    db.session.delete(item)
    db.session.commit()
    flash(f'{item_name} deleted successfully.')
    return True

def bulk_delete_items(model, item_ids, user_id, item_type):
    if not item_ids:
        flash(f'No {item_type} selected')
        return 0
    items = model.query.filter(model.id.in_(item_ids), model.user_id == user_id).all()
    if not items:
        flash(f'No valid {item_type} found')
        return 0
    for item in items:
        db.session.delete(item)
    db.session.commit()
    return len(items)

def create_notification(user_id, message):
    try:
        notification = Notification(user_id=user_id, message=message)
        db.session.add(notification)
        db.session.commit()
        return notification
    except Exception:
        db.session.rollback()
        return None

def compute_period_metrics(user_id, start_date=None, end_date=None):
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=6)
    meals = Meal.query.filter(Meal.user_id == user_id, Meal.date >= start_date, Meal.date <= end_date).all()
    workouts = Workout.query.filter(Workout.user_id == user_id, Workout.date >= start_date, Workout.date <= end_date).all()

    calories_consumed = sum(m.calories for m in meals)
    protein = sum(m.protein for m in meals)
    carbs = sum(m.carbs for m in meals)
    fats = sum(m.fats for m in meals)
    calories_burned = sum(w.calories_burned for w in workouts)
    workout_volume = sum((w.sets or 0) * (w.reps or 0) * (w.weight or 0) for w in workouts)

    return {
        'start_date': start_date,
        'end_date': end_date,
        'calories_consumed': calories_consumed,
        'protein': protein,
        'carbs': carbs,
        'fats': fats,
        'calories_burned': calories_burned,
        'workout_volume': workout_volume
    }

def _notification_exists_on_date(user_id, text_substr, when_date=None):
    if when_date is None:
        when_date = date.today()
    existing = Notification.query.filter(Notification.user_id == user_id,
                                         Notification.message.contains(text_substr),
                                         db.func.date(Notification.created_at) == when_date).first()
    return existing is not None

def check_low_protein(user_id):
    today = date.today()
    protein_today = db.session.query(db.func.sum(Meal.protein)).filter(Meal.user_id == user_id, Meal.date == today).scalar() or 0
    bm = BodyMeasurement.query.filter_by(user_id=user_id).order_by(BodyMeasurement.date.desc()).first()
    if bm and bm.weight:
        target = bm.weight * 1.2
    else:
        target = 50
    if protein_today < target and not _notification_exists_on_date(user_id, 'Low protein today'):
        percent_of_target = int((protein_today / target) * 100) if target > 0 else 0
        create_notification(user_id, f'Low protein today: {protein_today:.1f} g ({percent_of_target}% of target {int(target)} g). Consider adding a protein-rich meal.')


def check_training_volume_trend(user_id):
    today = date.today()
    current_week_metrics = compute_period_metrics(user_id, end_date=today)
    previous_week_end = today - timedelta(days=7)
    previous_week_metrics = compute_period_metrics(user_id, end_date=previous_week_end)
    current_week_volume = current_week_metrics['workout_volume']
    previous_week_volume = previous_week_metrics['workout_volume']
    if previous_week_volume == 0:
        return  
    volume_diff = current_week_volume - previous_week_volume
    percent_change = (volume_diff / previous_week_volume) * 100
    if percent_change < -20:
        week_ago = today - timedelta(days=7)
        existing = Notification.query.filter(
            Notification.user_id == user_id,
            Notification.message.contains('training volume decreased'),
            db.func.date(Notification.created_at) >= week_ago
        ).first()
        if not existing:
            create_notification(user_id, f'Training volume decreased {abs(int(percent_change))}% vs previous week. Consider adjusting your program.')


def create_summary_for_user(user, start, end, summary_type='Weekly'):
    current_metrics = compute_period_metrics(user.id, start_date=start, end_date=end)
    protein_calories = current_metrics['protein'] * 4
    carbohydrate_calories = current_metrics['carbs'] * 4
    fat_calories = current_metrics['fats'] * 9
    total_macro_calories = protein_calories + carbohydrate_calories + fat_calories
    if total_macro_calories > 0:
        protein_percent = round((protein_calories / total_macro_calories) * 100, 1)
        carbohydrate_percent = round((carbohydrate_calories / total_macro_calories) * 100, 1)
        fat_percent = round((fat_calories / total_macro_calories) * 100, 1)
    else:
        protein_percent = carbohydrate_percent = fat_percent = 0

    current_volume = current_metrics['workout_volume']
    #compare with same length period before this one
    period_length = (end - start).days + 1
    previous_end = start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=period_length - 1)
    previous_metrics = compute_period_metrics(user.id, start_date=previous_start, end_date=previous_end)
    previous_volume = previous_metrics['workout_volume']
    trend = 'unchanged'
    if previous_volume == 0 and current_volume > 0:
        trend = 'increased'
    elif previous_volume == 0 and current_volume == 0:
        trend = 'unchanged'
    elif previous_volume > 0:
        percent_change = (current_volume - previous_volume) / previous_volume * 100
        if percent_change > 5:
            trend = 'increased'
        elif percent_change < -5:
            trend = 'decreased'
        else:
            trend = 'unchanged'

    message = (
        f"{summary_type} Summary ({start} → {end}): Calories consumed {current_metrics['calories_consumed']} kcal, "
        f"Calories burned {current_metrics['calories_burned']} kcal. Macros: Protein {protein_percent}%, Carbs {carbohydrate_percent}%, Fats {fat_percent}%. "
        f"Workout volume {current_volume} ({trend} vs previous period)."
    )
    return create_notification(user.id, message)


@app.route('/')
def index():
    return render_template('index.html', hide_back_button=True)

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if not username or not password:
            flash('Please enter username and password')
            return redirect(url_for('register'))
            
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
            
        security_question = request.form['security_question']
        security_answer = request.form['security_answer'].strip()
        
        if not security_answer:
            flash('Security answer is required')
            return redirect(url_for('register'))
            
        user = User(
            username=username,
            password=generate_password_hash(password),
            security_question=security_question,
            security_answer=security_answer
        )
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
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            try:
                if user.meal_reminder or user.workout_reminder:
                    timer = Timer(10, send_delayed_login_notifications, args=[user.id])
                    timer.daemon = True 
                    timer.start()

                try:
                    check_low_protein(user.id)
                except Exception:
                    pass
                try:
                    check_training_volume_trend(user.id)
                except Exception:
                    pass

                pref = user.progress_summary_frequency or 'weekly'
                if pref == 'daily':
                    send_daily_summary_for_user(user)
                elif pref == 'weekly':
                    send_weekly_summary_for_user(user)
                elif pref == 'monthly':
                    send_monthly_summary_for_user(user)
            except Exception:
                pass

            flash('Welcome back, ' + username + '!')
            return redirect(url_for('dashboard'))
        flash('invalid credentials')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    user_id = get_user_id()
    if not user_id:
        flash('please log in to view your dashboard')
        return redirect(url_for('login'))

    today = date.today()
    today_meals = Meal.query.filter_by(user_id=session['user_id'], date=today).all()
    total_cal = sum(m.calories for m in today_meals)
    meals_count = len(today_meals)

    today_workouts = Workout.query.filter_by(user_id=session['user_id'], date=today).all()
    workout_cal = sum(w.calories_burned for w in today_workouts)
    workouts_count = len(today_workouts)

    week_ago = today - timedelta(days=6)
    week_meals = Meal.query.filter(Meal.user_id == session['user_id']).filter(Meal.date >= week_ago).all()
    weekly_cal = sum(m.calories for m in week_meals)

    week_workouts = Workout.query.filter(Workout.user_id == session['user_id']).filter(Workout.date >= week_ago).all()
    weekly_workout_cal = sum(w.calories_burned for w in week_workouts)

    return render_template('dashboard.html',
        total_cal=total_cal,
        meals_count=meals_count,
        workout_cal=workout_cal,
        workouts_count=workouts_count,
        weekly_cal=weekly_cal,
        weekly_workout_cal=weekly_workout_cal,
        hide_back_button=True)

@app.route('/meals', methods=['GET','POST'])
def meals():
    user_id = get_user_id()
    if not user_id:
        flash('please log in to view your meals')
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'template_id' in request.form:
            template = MealTemplate.query.get_or_404(request.form['template_id'])
            if template.user_id != user_id:
                flash('invalid template')
                return redirect(url_for('meals'))
            m = Meal(user_id=user_id, name=template.name, calories=template.calories,
                    protein=template.protein, carbs=template.carbs, fats=template.fats)
            template.frequency += 1
            db.session.add(m)
            db.session.commit()
            flash(f'Added {template.name}')
            return redirect(url_for('meals'))

        name = request.form['name'].strip() #meal addition
        if not name:
            flash('Meal name required')
            return redirect(url_for('meals'))
        try:
            qty = int(request.form.get('quantity', 1))
            m = Meal(user_id=user_id, name=name, quantity=qty,
                    calories=int(request.form['calories']) * qty,
                    protein=float(request.form.get('protein', 0)) * qty,
                    carbs=float(request.form.get('carbs', 0)) * qty,
                    fats=float(request.form.get('fats', 0)) * qty)
            db.session.add(m)
            MealTemplate.get_or_create(user_id, name, int(request.form['calories']),
                                       float(request.form.get('protein', 0)),
                                       float(request.form.get('carbs', 0)),
                                       float(request.form.get('fats', 0)))
            db.session.commit()
            try:
                check_low_protein(user_id)
            except:
                pass
            flash('Meal added')
        except ValueError:
            flash('Invalid values')
        return redirect(url_for('meals'))

    meals_data = Meal.query.filter_by(user_id=user_id).order_by(Meal.id.desc()).all()
    favorites = Meal.query.filter_by(user_id=user_id, is_favorite=True).order_by(Meal.date.desc()).all()
    frequent = MealTemplate.query.filter_by(user_id=user_id).order_by(MealTemplate.frequency.desc()).limit(5).all()
    return render_template('meals.html', meals=meals_data, favorites=favorites,
                          suggestions=favorites + [t for t in frequent if t.name not in {f.name for f in favorites}])




@app.route('/toggle_favorite_meal/<int:meal_id>', methods=['POST'])
def toggle_favorite_meal(meal_id):
    user_id = get_user_id()
    if not user_id:
        return redirect(url_for('login'))
    meal = Meal.query.get_or_404(meal_id)
    meal.is_favorite = not meal.is_favorite
    db.session.commit()
    flash(f'{"Favorite Marked" if meal.is_favorite else "Removed"} {meal.name} {"as favorite" if meal.is_favorite else "from favorites"}')
    return redirect(url_for('meals'))

@app.route('/edit_meal/<int:meal_id>', methods=['GET', 'POST'])
def edit_meal(meal_id):
    user_id = get_user_id()
    if not user_id:
        return redirect(url_for('login'))
    meal = Meal.query.get_or_404(meal_id)
    if meal.user_id != user_id:
        flash('Unauthorized')
        return redirect(url_for('meals'))
    if request.method == 'POST':
        meal.name = request.form['name']
        meal.calories = int(request.form.get('calories', 0))
        meal.protein = float(request.form.get('protein', 0))
        meal.carbs = float(request.form.get('carbs', 0))
        meal.fats = float(request.form.get('fats', 0))
        db.session.commit()
        flash('Meal updated.')
        return redirect(url_for('meals'))
    return render_template('edit_meal.html', meal=meal)

@app.route('/delete_meal/<int:meal_id>', methods=['POST'])
def delete_meal(meal_id):
    user_id = get_user_id()
    if not user_id:
        return redirect(url_for('login'))
    delete_user_item(Meal, meal_id, user_id, 'Meal')
    return redirect(url_for('meals'))

@app.route('/remove_template/<int:template_id>', methods=['POST'])
def remove_template(template_id):
    user_id = get_user_id()
    if not user_id:
        return redirect(url_for('login'))
    delete_user_item(MealTemplate, template_id, user_id, 'Favorite')
    return redirect(url_for('meals'))

@app.route('/bulk_delete_meals', methods=['POST'])
def bulk_delete_meals():
    user_id = get_user_id()
    if not user_id:
        return redirect(url_for('login'))
    count = bulk_delete_items(Meal, request.form.getlist('meal_ids'), user_id, 'meals')
    flash(f'Deleted {count} meal(s)')
    return redirect(url_for('meals'))

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        username = request.form['username'].strip()
        user = User.query.filter_by(username=username).first()
        
        if not user:
            flash('Username not found')
            return redirect(url_for('reset_password'))
        
        if 'verified' in request.form and 'password' in request.form:
            password = request.form['password']
            confirm_password = request.form['confirm_password']
            
            if password != confirm_password:
                flash('Passwords do not match')
                return render_template('reset_password.html', 
                    username=username,
                    user=user,
                    verified=True)
            
            user.password = generate_password_hash(password)
            db.session.commit()
            flash('Password has been reset. Please login.')
            return redirect(url_for('login'))
            
        if 'security_answer' in request.form:
            security_answer = request.form['security_answer']
            if security_answer.strip().lower() == user.security_answer.lower():
                return render_template('reset_password.html', 
                    username=username,
                    user=user,
                    verified=True)
            else:
                flash('Incorrect security answer')
                return render_template('reset_password.html',
                    username=username,
                    user=user,
                    security_question=user.security_question)
                    
        return render_template('reset_password.html',
            username=username,
            user=user,
            security_question=user.security_question)
            
    return render_template('reset_password.html', user=None)

@app.route('/workouts', methods=['GET','POST'])
def workouts():
    user_id = get_user_id()
    if not user_id:
        flash('please log in to view your workouts')
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'template_id' in request.form:
            template = WorkoutTemplate.query.get_or_404(request.form['template_id'])
            if template.user_id != session['user_id']:
                flash('Invalid template')
                return redirect(url_for('workouts'))

            if template.is_custom:
                exercise_type = template.exercise_type
                muscle_groups = template.muscle_groups
                calories_per_hour = template.calories_per_hour
                exercise_data = {
                    'exercise_type': exercise_type,
                    'muscle_groups': muscle_groups,
                    'calories_per_30_min': calories_per_hour // 2  
                }
            else:
                exercise_data = get_exercise_data(template.name)
                exercise_type = exercise_data.get('exercise_type', 'strength')
                muscle_groups = exercise_data.get('muscle_groups', '')

            try:
                if exercise_type == 'cardio':
                    duration_str = request.form.get('duration', '0').strip()
                    duration = int(duration_str)
                    weight_str = request.form.get('weight', '').strip()
                    if weight_str:
                        try:
                            weight_value = float(weight_str)
                        except ValueError:
                            flash('Invalid weight value')
                            return redirect(url_for('workouts'))
                        if weight_value != 0:
                            flash('Cardio exercises must not include a weight')
                            return redirect(url_for('workouts'))
                    sets = 0
                    reps = 0
                else: 
                    sets = int(request.form.get('sets', '0').strip())
                    reps = int(request.form.get('reps', '0').strip())
                    weight_str = request.form.get('weight', '').strip()
                    try:
                        weight = float(weight_str)
                    except ValueError:
                        flash('Invalid weight value')
                        return redirect(url_for('workouts'))
                    volume = sets * reps * weight
                    duration = 0
            except Exception:
                flash('Invalid input values')
                return redirect(url_for('workouts'))

            intensity = float(request.form.get('intensity', 1.0))
            if template.is_custom:
                if exercise_type == 'cardio' and duration > 0:
                    calories_burned = (calories_per_hour * duration) // 60
                else:
                    calories_burned = calculate_calories_burned(exercise_data, duration, sets, reps, intensity)
            else:
                calories_burned = calculate_calories_burned(exercise_data, duration, sets, reps, intensity)

            w = Workout(
                user_id=session['user_id'],
                name=template.name,
                exercise_type=exercise_type,
                muscle_groups=muscle_groups,
                duration=duration,
                sets=sets,
                reps=reps,
                weight=weight if exercise_type == 'strength' else 0,
                volume=volume if exercise_type == 'strength' else 0,
                intensity=intensity,
                calories_burned=calories_burned
            )
            template.frequency += 1
            db.session.add(w)
            db.session.commit()
            try:
                check_training_volume_trend(session['user_id'])
            except Exception:
                pass
            flash(f'Added {template.name} from frequent workouts')
            return redirect(url_for('workouts'))

        name = request.form['name'].strip()
        if not name:
            flash('Exercise name is required')
            return redirect(url_for('workouts'))

        is_custom = request.form.get('is_custom') == 'true'

        if is_custom:
            exercise_type = request.form.get('custom_type', 'strength')
            muscle_groups = request.form.get('custom_muscle_groups', '')
            calories_per_hour = int(request.form.get('custom_calories_per_hour', 0))
            exercise_data = {
                'exercise_type': exercise_type,
                'muscle_groups': muscle_groups,
                'calories_per_30_min': calories_per_hour // 2  
            }
        else:
            exercise_data = get_exercise_data(name)
            exercise_type = exercise_data.get('exercise_type', 'strength')

        try:
            if exercise_type == 'cardio':
                duration_str = request.form.get('duration', '0').strip()
                if not duration_str:
                    flash('Duration is required for cardio exercises')
                    return redirect(url_for('workouts'))
                duration = int(duration_str)
                if duration <= 0:
                    flash('Duration must be greater than 0 for cardio exercises')
                    return redirect(url_for('workouts'))
                weight_str = request.form.get('weight', '').strip()
                if weight_str:
                    try:
                        weight_value = float(weight_str)
                    except ValueError:
                        weight_value = None
                    if weight_value not in (None, 0):
                        flash('Cardio exercises must not include a weight')
                        return redirect(url_for('workouts'))
                sets = 0
                reps = 0
            else: 
                sets = int(request.form.get('sets', '0').strip())
                reps = int(request.form.get('reps', '0').strip())
                if sets <= 0 or reps <= 0:
                    flash('Sets and reps must be greater than 0 for strength exercises')
                    return redirect(url_for('workouts'))
                duration = 0
                weight_str = request.form.get('weight', '').strip()
                if weight_str == '':
                    flash('Weight is required for strength exercises (enter 0 for bodyweight)')
                    return redirect(url_for('workouts'))
                try:
                    weight = float(weight_str)
                except ValueError:
                    flash('Invalid weight value')
                    return redirect(url_for('workouts'))
                if weight < 0:
                    flash('Weight must be 0 or greater')
                    return redirect(url_for('workouts'))
                volume = sets * reps * weight
        except Exception:
            flash('Invalid input values')
            return redirect(url_for('workouts'))

        intensity = float(request.form.get('intensity', 1.0))
        if is_custom:
            if exercise_type == 'cardio' and duration > 0:
                calories_burned = (calories_per_hour * duration) // 60
            else:
                calories_burned = calculate_calories_burned(exercise_data, duration, sets, reps, intensity)
        else:
            calories_burned = calculate_calories_burned(exercise_data, duration, sets, reps, intensity)

        w = Workout(
            user_id=session['user_id'],
            name=name,
            exercise_type=exercise_type,
            muscle_groups=exercise_data.get('muscle_groups', ''),
            duration=duration,
            sets=sets,
            reps=reps,
            weight=weight if exercise_type == 'strength' else 0,
            volume=volume if exercise_type == 'strength' else 0,
            intensity=intensity,
            calories_burned=calories_burned
        )
        db.session.add(w)

        WorkoutTemplate.get_or_create(
            session['user_id'],
            name,
            exercise_type,
            exercise_data.get('muscle_groups', ''),
            is_custom=is_custom,
            calories_per_hour=calories_per_hour if is_custom else 0
        )
        db.session.commit()
        try:
            check_training_volume_trend(session['user_id'])
        except Exception:
            pass
        flash('Workout added')
        return redirect(url_for('workouts'))

    workouts = Workout.query.filter_by(user_id=session['user_id']).order_by(Workout.id.desc()).all()
    manual_favorites = Workout.query.filter_by(user_id=session['user_id'], is_favorite=True).order_by(Workout.date.desc()).all()
    
    all_customs = WorkoutTemplate.query.filter_by(user_id=session['user_id'], is_custom=True).order_by(WorkoutTemplate.frequency.desc()).all()
    
    frequent_exercises = WorkoutTemplate.query.filter_by(user_id=session['user_id'], is_custom=False).order_by(WorkoutTemplate.frequency.desc()).limit(5).all()
    

    customs = all_customs + frequent_exercises
    custom_workouts_only = all_customs

    for f in manual_favorites:
        template = WorkoutTemplate.query.filter_by(user_id=session['user_id'], name=f.name).first()
        f.template_id = template.id if template else None

    favorite_names = {f.name for f in manual_favorites}
    dropdown_customs = [t for t in customs if t.name not in favorite_names]

    for f in dropdown_customs:
        if not hasattr(f, 'is_favorite'):
            f.is_favorite = False
        if not hasattr(f, 'frequency'):
            f.frequency = 0
        if not hasattr(f, 'is_custom'):
            f.is_custom = False

    for s in customs:
        s.is_favorite = False

    for f in all_customs:
        if not hasattr(f, 'calories_per_hour') or f.calories_per_hour == 0:
            f.calories_per_hour = 300  #Default 
    
    for f in frequent_exercises:
        exercise_data = get_exercise_data(f.name)
        f.calories_per_hour = exercise_data.get('calories_per_30_min', 150) * 2


    all_exercises = []
    exercises_data = load_exercises_from_csv()
    for name, data in exercises_data.items():
        benefit = data.get('benefit', '')
        short_benefit = benefit[:50] + '...' if len(benefit) > 50 else benefit

        all_exercises.append({
            'name': name.title(),
            'exercise_type': data['exercise_type'],
            'muscle_groups': data['muscle_groups'],
            'calories_per_hour': data['calories_per_30_min'] * 2,
            'benefit': short_benefit
        })

    return render_template('workouts.html', workouts=workouts, favorites=manual_favorites, customs=dropdown_customs, frequent=frequent_exercises, custom_workouts_only=custom_workouts_only, all_exercises=all_exercises)


@app.route('/toggle_favorite_workout/<int:workout_id>', methods=['POST'])
def toggle_favorite_workout(workout_id):
    user_id = get_user_id()
    if not user_id:
        return redirect(url_for('login'))
    workout = Workout.query.get_or_404(workout_id)
    workout.is_favorite = not workout.is_favorite
    db.session.commit()
    flash(f'{"Favorite Marked" if workout.is_favorite else "Removed"} {workout.name} {"as favorite" if workout.is_favorite else "from favorites"}')
    return redirect(url_for('workouts'))

@app.route('/edit_workout/<int:workout_id>', methods=['GET', 'POST'])
def edit_workout(workout_id):
    user_id = get_user_id()
    if not user_id:
        return redirect(url_for('login'))
    workout = Workout.query.get_or_404(workout_id)
    if workout.user_id != user_id:
        flash('Unauthorized')
        return redirect(url_for('workouts'))
    if request.method == 'POST':
        try:
            workout.name = request.form['name']
            workout.intensity = float(request.form.get('intensity', 1.0))
            if workout.exercise_type == 'cardio':
                workout.duration = int(request.form['duration'] or 1)
                workout.sets, workout.reps, workout.weight = 0, 0, 0
            else:
                workout.sets = int(request.form['sets'] or 1)
                workout.reps = int(request.form['reps'] or 1)
                workout.weight = float(request.form.get('weight', 0))
                workout.duration = 0
                workout.volume = workout.sets * workout.reps * workout.weight
            exercise_data = get_exercise_data(workout.name)
            workout.calories_burned = calculate_calories_burned(exercise_data, workout.duration, workout.sets, workout.reps, workout.intensity)
            db.session.commit()
            flash('Workout updated.')
        except (ValueError, KeyError):
            flash('Invalid values')
        return redirect(url_for('workouts'))
    return render_template('edit_workout.html', workout=workout)

@app.route('/delete_workout/<int:workout_id>', methods=['POST'])
def delete_workout(workout_id):
    user_id = get_user_id()
    if not user_id:
        return redirect(url_for('login'))
    delete_user_item(Workout, workout_id, user_id, 'Workout')
    return redirect(url_for('workouts'))

@app.route('/remove_workout_template/<int:template_id>', methods=['POST'])
def remove_workout_template(template_id):
    user_id = get_user_id()
    if not user_id:
        return redirect(url_for('login'))
    delete_user_item(WorkoutTemplate, template_id, user_id, 'Exercise')
    return redirect(url_for('workouts'))

@app.route('/bulk_delete_workouts', methods=['POST'])
def bulk_delete_workouts():
    user_id = get_user_id()
    if not user_id:
        return redirect(url_for('login'))
    count = bulk_delete_items(Workout, request.form.getlist('workout_ids'), user_id, 'workouts')
    flash(f'Deleted {count} workout(s)')
    return redirect(url_for('workouts'))

@app.route('/bulk_delete_notifications', methods=['POST'])
def bulk_delete_notifications():
    user_id = get_user_id()
    if not user_id:
        return redirect(url_for('login'))
    count = bulk_delete_items(Notification, request.form.getlist('notification_ids'), user_id, 'notifications')
    flash(f'Deleted {count} notification(s)')
    return redirect(url_for('notifications'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    user_id = get_user_id()
    if not user_id:
        flash('please log in to view your settings')
        return redirect(url_for('login'))

    user = User.query.get_or_404(session['user_id'])

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'update_personal':
            new_username = request.form.get('username', '').strip()
            if new_username and new_username != user.username:
                if User.query.filter(User.username == new_username).first():
                    flash('Username already taken')
                    return redirect(url_for('settings'))
                user.username = new_username

            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')
            if new_password:
                if not current_password or not check_password_hash(user.password, current_password):
                    flash('Current password is incorrect')
                    return redirect(url_for('settings'))
                if new_password != confirm_password:
                    flash('New passwords do not match')
                    return redirect(url_for('settings'))
                user.password = generate_password_hash(new_password)

            db.session.commit()
            flash('Personal information updated')
            return redirect(url_for('settings'))

        if action == 'update_notifications':
            user.workout_reminder = bool(request.form.get('workout_reminder'))
            user.meal_reminder = bool(request.form.get('meal_reminder'))
            freq = request.form.get('progress_summary_frequency', 'weekly')
            if freq not in ('daily', 'weekly', 'monthly', 'none'):
                freq = 'weekly'
            user.progress_summary_frequency = freq
            db.session.commit()
            flash('Notification settings saved')
            return redirect(url_for('settings'))

        if action == 'clear_data':
            Meal.query.filter_by(user_id=user.id).delete()
            Workout.query.filter_by(user_id=user.id).delete()
            BodyMeasurement.query.filter_by(user_id=user.id).delete()
            Notification.query.filter_by(user_id=user.id).delete()
            MealTemplate.query.filter_by(user_id=user.id).delete()
            WorkoutTemplate.query.filter_by(user_id=user.id).delete()
            db.session.commit()
            flash('All logs cleared')
            return redirect(url_for('settings'))

        if action == 'delete_account':
            Meal.query.filter_by(user_id=user.id).delete()
            Workout.query.filter_by(user_id=user.id).delete()
            BodyMeasurement.query.filter_by(user_id=user.id).delete()
            Notification.query.filter_by(user_id=user.id).delete()
            MealTemplate.query.filter_by(user_id=user.id).delete()
            WorkoutTemplate.query.filter_by(user_id=user.id).delete()
            db.session.delete(user)
            db.session.commit()
            session.clear()
            flash('Your account and all data have been deleted')
            return redirect(url_for('index'))

    return render_template('settings.html', user=user, hide_back_button=True)

@app.route('/analytics')
def analytics():
    if 'user_id' not in session:
        flash('please log in to view your analytics')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user_profile = UserProfile.query.filter_by(user_id=user_id).first()
    body_measurements = BodyMeasurement.query.filter_by(user_id=user_id).order_by(BodyMeasurement.date.desc()).all()
    
    period_days = 30
    period_start = date.today() - timedelta(days=period_days - 1)
    recent_workouts = Workout.query.filter(
        Workout.user_id == user_id,
        Workout.date >= period_start
    ).order_by(Workout.date.asc()).all()

    recent_meals = Meal.query.filter(
        Meal.user_id == user_id,
        Meal.date >= period_start
    ).order_by(Meal.date.asc()).all()
    
    week_ago = date.today() - timedelta(days=6)
    weekly_workouts = Workout.query.filter(
        Workout.user_id == user_id,
        Workout.date >= week_ago
    ).all()
    weekly_meals = Meal.query.filter(
        Meal.user_id == user_id,
        Meal.date >= week_ago
    ).all()
    
    weekly_calories_burned = sum(w.calories_burned for w in weekly_workouts)
    weekly_calories_consumed = sum(m.calories for m in weekly_meals)
    current_week_metrics = compute_period_metrics(user_id, end_date=date.today())
    previous_week_metrics = compute_period_metrics(user_id, end_date=(date.today() - timedelta(days=7)))
    weekly_workout_volume = current_week_metrics['workout_volume']
    prev_week_volume = previous_week_metrics['workout_volume']
    if prev_week_volume == 0:
        if weekly_workout_volume > 0:
            volume_trend = 'increased'
        else:
            volume_trend = 'unchanged'
    else:
        percent_change = (weekly_workout_volume - prev_week_volume) / prev_week_volume * 100
        if percent_change > 5:
            volume_trend = 'increased'
        elif percent_change < -5:
            volume_trend = 'decreased'
        else:
            volume_trend = 'unchanged'
    protein_calories = current_week_metrics['protein'] * 4
    carbohydrate_calories = current_week_metrics['carbs'] * 4
    fat_calories = current_week_metrics['fats'] * 9
    total_macro_calories = protein_calories + carbohydrate_calories + fat_calories
    if total_macro_calories > 0:
        weekly_prot_pct = round((protein_calories / total_macro_calories) * 100, 1)
        weekly_carb_pct = round((carbohydrate_calories / total_macro_calories) * 100, 1)
        weekly_fat_pct = round((fat_calories / total_macro_calories) * 100, 1)
    else:
        weekly_prot_pct = weekly_carb_pct = weekly_fat_pct = 0
    
    month_ago = date.today() - timedelta(days=29)
    monthly_workouts = Workout.query.filter(
        Workout.user_id == user_id,
        Workout.date >= month_ago
    ).all()
    monthly_meals = Meal.query.filter(
        Meal.user_id == user_id,
        Meal.date >= month_ago
    ).all()
    
    monthly_calories_burned = sum(w.calories_burned for w in monthly_workouts)
    monthly_calories_consumed = sum(m.calories for m in monthly_meals)
    
#Logging consistency
    today = date.today()
    month_start = today.replace(day=1)
    month_period_days = today.day

    meal_dates = {r[0] for r in db.session.query(Meal.date).filter(Meal.user_id == user_id, Meal.date >= month_start, Meal.date <= today).all()}
    workout_dates = {r[0] for r in db.session.query(Workout.date).filter(Workout.user_id == user_id, Workout.date >= month_start, Workout.date <= today).all()}
    month_logged_dates = meal_dates | workout_dates
    monthly_days_logged = len(month_logged_dates)
    monthly_logged_pct = round((monthly_days_logged / month_period_days) * 100.0, 1) if month_period_days > 0 else 0.0

    prev_month_end = month_start - timedelta(days=1)
    prev_month_start = prev_month_end.replace(day=1)
    prev_month_period_days = prev_month_end.day
    prev_meal_dates = {r[0] for r in db.session.query(Meal.date).filter(Meal.user_id == user_id, Meal.date >= prev_month_start, Meal.date <= prev_month_end).all()}
    prev_workout_dates = {r[0] for r in db.session.query(Workout.date).filter(Workout.user_id == user_id, Workout.date >= prev_month_start, Workout.date <= prev_month_end).all()}
    prev_logged_dates = prev_meal_dates | prev_workout_dates
    prev_month_days_logged = len(prev_logged_dates)
    previous_month_logged_pct = round((prev_month_days_logged / prev_month_period_days) * 100.0, 1) if prev_month_period_days > 0 else 0.0

    consistency_drop_pct = round(previous_month_logged_pct - monthly_logged_pct, 1)
    CONSISTENCY_DROP_THRESHOLD = 10.0  # percent points
    consistency_alert = False
    consistency_trend = 'unchanged'
    if consistency_drop_pct >= CONSISTENCY_DROP_THRESHOLD:
        consistency_trend = 'decreased'
        consistency_alert = True
    elif consistency_drop_pct <= -CONSISTENCY_DROP_THRESHOLD:
        consistency_trend = 'increased'
    else:
        consistency_trend = 'unchanged'

    calories_period_days = 7
    calories_start = date.today() - timedelta(days=calories_period_days - 1)
    calories_by_date = defaultdict(lambda: {'consumed': 0, 'burned': 0, 'net': 0})

    for i in range(calories_period_days):
        d = (calories_start + timedelta(days=i)).isoformat()
        calories_by_date[d] = {'consumed': 0, 'burned': 0, 'net': 0}

    for meal in recent_meals:
        if meal.date >= calories_start:
            date_str = meal.date.isoformat()
            calories_by_date[date_str]['consumed'] += meal.calories

    for workout in recent_workouts:
        if workout.date >= calories_start:
            date_str = workout.date.isoformat()
            calories_by_date[date_str]['burned'] += workout.calories_burned

    sorted_dates = sorted(calories_by_date.keys())
    for date_str in sorted_dates:
        calories_by_date[date_str]['net'] = calories_by_date[date_str]['consumed'] - calories_by_date[date_str]['burned']

    calories_chart_data = {
        'dates': sorted_dates,
        'consumed': [calories_by_date[d]['consumed'] for d in sorted_dates],
        'burned': [calories_by_date[d]['burned'] for d in sorted_dates],
        'net': [calories_by_date[d]['net'] for d in sorted_dates]
    }


    volume_by_date = defaultdict(float)
    day_count = period_days
    for i in range(day_count):
        d = (period_start + timedelta(days=i)).isoformat()
        volume_by_date[d] = 0.0

    for workout in recent_workouts: #Accumulate workout volume per day
        date_str = workout.date.isoformat()
        volume_by_date[date_str] += (workout.sets or 0) * (workout.reps or 0) * (workout.weight or 0)

    sorted_volume_dates = sorted(volume_by_date.keys())
    workout_volume_chart_data = {
        'dates': sorted_volume_dates,
        'volumes': [volume_by_date[d] for d in sorted_volume_dates]
    }

    workout_total_volume = sum(workout_volume_chart_data['volumes'])
    workout_avg_volume = (workout_total_volume / len(workout_volume_chart_data['volumes'])) if workout_volume_chart_data['volumes'] else 0
    
    today = date.today()
    today_meals = Meal.query.filter_by(user_id=user_id, date=today).all()
    daily_macros = {
        'protein': sum(m.protein for m in today_meals),
        'carbs': sum(m.carbs for m in today_meals),
        'fats': sum(m.fats for m in today_meals),
        'calories': sum(m.calories for m in today_meals)
    }
    
    bm = BodyMeasurement.query.filter_by(user_id=user_id).order_by(BodyMeasurement.date.desc()).first()
    if bm and bm.weight:
        protein_target_grams = round(bm.weight * 1.2, 1)
    else:
        protein_target_grams = 50.0
    protein_today_grams = daily_macros['protein']
    try:
        protein_target_pct = min(100.0, round((protein_today_grams / protein_target_grams) * 100.0, 1)) if protein_target_grams > 0 else 0.0
    except Exception:
        protein_target_pct = 0.0
    
    weight_chart_data = {
        'dates': [m.date.isoformat() for m in body_measurements if m.weight],
        'weights': [m.weight for m in body_measurements if m.weight]
    }

    weight_chart_data['dates'].reverse()
    weight_chart_data['weights'].reverse()
    
    return render_template('analytics.html',
                         user_profile=user_profile,
                         body_measurements=body_measurements,
                         recent_workouts=recent_workouts,
                         recent_meals=recent_meals,
                         weekly_calories_burned=weekly_calories_burned,
                         weekly_calories_consumed=weekly_calories_consumed,
                         monthly_calories_burned=monthly_calories_burned,
                         monthly_calories_consumed=monthly_calories_consumed,
                                 weekly_workout_volume=weekly_workout_volume,
                                 prev_week_volume=prev_week_volume,
                                 volume_trend=volume_trend,
                                 weekly_prot_pct=weekly_prot_pct,
                                 weekly_carb_pct=weekly_carb_pct,
                                 weekly_fat_pct=weekly_fat_pct,
                         calories_chart_data=calories_chart_data,
                         workout_volume_chart_data=workout_volume_chart_data,
                         workout_total_volume=workout_total_volume,
                         workout_avg_volume=round(workout_avg_volume, 1),
                         daily_macros=daily_macros,
                         protein_target_grams=protein_target_grams,
                         protein_today_grams=protein_today_grams,
                         protein_target_pct=protein_target_pct,
                         monthly_days_logged=monthly_days_logged,
                         month_period_days=month_period_days,
                         monthly_logged_pct=monthly_logged_pct,
                         previous_month_logged_pct=previous_month_logged_pct,
                         consistency_drop_pct=consistency_drop_pct,
                         consistency_alert=consistency_alert,
                         consistency_trend=consistency_trend,
                         weight_chart_data=weight_chart_data,
                         hide_back_button=True)

def get_measurement_data(form):
    return {
        'date': date.fromisoformat(form.get('date', '')) if form.get('date') else date.today(),
        'weight': float(form['weight']) if form.get('weight') else None,
        'body_fat_percentage': float(form['body_fat_percentage']) if form.get('body_fat_percentage') else None,
        'chest': float(form['chest']) if form.get('chest') else None,
        'waist': float(form['waist']) if form.get('waist') else None,
        'hips': float(form['hips']) if form.get('hips') else None,
        'biceps': float(form['biceps']) if form.get('biceps') else None,
        'thighs': float(form['thighs']) if form.get('thighs') else None,
        'neck': float(form['neck']) if form.get('neck') else None,
        'notes': form.get('notes', '')
    }

@app.route('/body_measurement', methods=['GET', 'POST'])
def add_body_measurement():
    user_id = get_user_id()
    if not user_id:
        return redirect(url_for('login'))
    if request.method == 'POST':
        data = get_measurement_data(request.form)
        measurement = BodyMeasurement(user_id=user_id, **data)
        db.session.add(measurement)
        db.session.commit()
        flash('Body measurement added.')
        return redirect(url_for('analytics'))
    return render_template('add_body_measurement.html', today_date=date.today().isoformat())

@app.route('/body_measurement/<int:measurement_id>/edit', methods=['GET', 'POST'])
def edit_body_measurement(measurement_id):
    user_id = get_user_id()
    if not user_id:
        return redirect(url_for('login'))
    measurement = BodyMeasurement.query.get_or_404(measurement_id)
    if measurement.user_id != user_id:
        flash('Invalid measurement')
        return redirect(url_for('analytics'))
    if request.method == 'POST':
        for k, v in get_measurement_data(request.form).items():
            setattr(measurement, k, v)
        db.session.commit()
        flash('Body measurement updated.')
        return redirect(url_for('analytics'))
    return render_template('edit_body_measurement.html', measurement=measurement)

@app.route('/body_measurement/<int:measurement_id>/delete', methods=['POST'])
def delete_body_measurement(measurement_id):
    user_id = get_user_id()
    if not user_id:
        return redirect(url_for('login'))
    delete_user_item(BodyMeasurement, measurement_id, user_id, 'Measurement')
    return redirect(url_for('analytics'))

@app.route('/user_profile', methods=['GET', 'POST'])
def user_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user_profile = UserProfile.query.filter_by(user_id=user_id).first()
    
    if request.method == 'POST':
        if user_profile:
            user_profile.height = float(request.form['height']) if request.form.get('height') else None
            user_profile.age = int(request.form['age']) if request.form.get('age') else None
            user_profile.gender = request.form.get('gender', '')
            user_profile.physical_activity_level = request.form.get('physical_activity_level', '')
        else:
            user_profile = UserProfile(
                user_id=user_id,
                height=float(request.form['height']) if request.form.get('height') else None,
                age=int(request.form['age']) if request.form.get('age') else None,
                gender=request.form.get('gender', ''),
                physical_activity_level=request.form.get('physical_activity_level', '')
            )
            db.session.add(user_profile)
        db.session.commit()
        flash('Profile updated successfully')
        return redirect(url_for('analytics'))
    
    return render_template('user_profile.html', user_profile=user_profile)

@app.route('/notifications')
def notifications():
    user_id = get_user_id()
    if not user_id:
        flash('please log in to view your notifications')
        return redirect(url_for('login'))
    notes = Notification.query.filter_by(user_id=session['user_id']).order_by(Notification.created_at.desc()).all()
    unread = [n for n in notes if not n.is_read]
    for n in unread:
        n.is_read = True
    if unread:
        db.session.commit()
    for n in notes:
        n.local_created_at = utc_to_local(n.created_at)
    return render_template('notifications.html', notifications=notes)

@app.route('/api/notifications')
def api_notifications():
    if 'user_id' not in session:
        return {'notifications': []}
    notes = Notification.query.filter_by(user_id=session['user_id'], is_read=False).order_by(Notification.created_at.desc()).all()
    return {'notifications': [
        {'id': n.id, 'message': n.message, 'created_at': utc_to_local(n.created_at).strftime('%Y-%m-%d %H:%M'), 'is_read': n.is_read}
        for n in notes
    ]}

@app.route('/api/notifications/read/<int:note_id>', methods=['POST'])
def mark_notification_read(note_id):
    if 'user_id' not in session:
        return '', 401
    n = Notification.query.get_or_404(note_id)
    if n.user_id != session['user_id']:
        return '', 403
    n.is_read = True
    db.session.commit()
    return '', 204

def load_exercises_from_csv():
    exercises = {}
    try:
        with open('data/Top 50 Excerice for your body.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            mapping = {
                'quadriceps': 'quadriceps', 'hamstrings': 'hamstrings', 'glutes': 'glutes',
                'lower abs': 'lower abs', 'obliques': 'obliques', 'upper back': 'upper back',
                'rear deltoids': 'rear deltoids', 'lower back': 'lower back', 'full body': 'full body',
                'chest': 'chest', 'back': 'back', 'triceps': 'triceps', 'biceps': 'biceps',
                'shoulders': 'shoulders', 'core': 'core', 'abs': 'abs', 'legs': 'legs',
                'calves': 'calves', 'forearms': 'forearms', 'hip flexors': 'hip flexors',
                'adductors': 'adductors', 'abductors': 'abductors'
            }
            for row in reader:
                name = row['Name of Exercise'].lower().strip()
                benefit = row.get('Benefit', '').lower()
                exercise_type = 'cardio' if 'cardio' in benefit or any(word in name for word in ['running', 'cycling', 'swimming', 'rowing', 'elliptical', 'jumping', 'burpees', 'mountain climbers', 'high knees', 'stair']) else 'strength'
                muscle_groups = ', '.join(sorted({mapping.get(m.strip(), m.strip()) for m in row.get('Target Muscle Group', '').lower().split(',')}))
                exercises[name] = {
                    'exercise_type': exercise_type,
                    'muscle_groups': muscle_groups,
                    'met_value': 6.0,
                    'calories_per_30_min': int(row.get('Burns Calories (per 30 min)', 0)),
                    'benefit': benefit
                }
    except FileNotFoundError:
        print("CSV file not found, returning empty exercises dict")
    except Exception as e:
        print(f"Error loading CSV: {e}")
    return exercises

EXERCISES_DATA = load_exercises_from_csv()

def get_exercise_data(exercise_name):
    exercise_lower = exercise_name.lower().strip()
    return EXERCISES_DATA.get(exercise_lower, {
        'exercise_type': 'strength',
        'muscle_groups': 'various',
        'met_value': 6.0,
        'calories_per_30_min': 150
    })

def calculate_calories_burned(exercise_data, duration, sets, reps, intensity=1.0):
    exercise_type = exercise_data.get('exercise_type', 'strength')

    if exercise_type == 'strength' and (sets <= 0 or reps <= 0): 
        return 0 

    calories_per_30_min = exercise_data.get('calories_per_30_min', 150)

    if exercise_type == 'strength' and duration == 0 and sets > 0:
        duration = sets * 1 #minute

    calories = int((calories_per_30_min * duration) / 30)

    calories = int(calories * intensity)

    if exercise_type == 'strength' and sets > 0 and reps > 0:
        reps_factor = min(1 + (reps - 10) * 0.05, 2.0)
        calories = int(calories * reps_factor)

    return max(calories, 0)

def send_daily_reminders_for_user(user):
    today = date.today()
    if user.meal_reminder:
        meal_count = Meal.query.filter_by(user_id=user.id, date=today).count()
        if meal_count == 0 and not _notification_exists_on_date(user.id, 'You have not logged any meals today'):
            create_notification(user.id, 'You have not logged any meals today!')
    if user.workout_reminder:
        workout_count = Workout.query.filter_by(user_id=user.id, date=today).count()
        if workout_count == 0 and not _notification_exists_on_date(user.id, 'No workout logged today'):
            create_notification(user.id, 'No workout logged today. Stay active!')

def send_daily_summary_for_user(user):
    today = date.today()
    if not _notification_exists_on_date(user.id, 'Daily Summary'):
        create_summary_for_user(user, today, today, summary_type='Daily')

def send_weekly_summary_for_user(user):
    today = date.today()
    week_ago = today - timedelta(days=7)
    existing = Notification.query.filter(
        Notification.user_id == user.id,
        Notification.message.contains('Weekly Summary'),
        db.func.date(Notification.created_at) >= week_ago
    ).first()
    if not existing:
        days_since_sunday = (today.weekday() + 1) % 7  
        if days_since_sunday == 0:
            end = today - timedelta(days=1)
        else:
            end = today - timedelta(days=days_since_sunday)
        start = end - timedelta(days=6)
        create_summary_for_user(user, start, end, summary_type='Weekly')

def send_monthly_summary_for_user(user):
    today = date.today()
    prev_end = today.replace(day=1) - timedelta(days=1)
    prev_start = prev_end.replace(day=1)
    existing = Notification.query.filter(
        Notification.user_id == user.id,
        Notification.message.contains('Monthly Summary'),
        Notification.message.contains(str(prev_start))
    ).first()
    if not existing:
        create_summary_for_user(user, prev_start, prev_end, summary_type='Monthly')

def send_delayed_login_notifications(user_id):
    with app.app_context():
        try:
            user = db.session.get(User, user_id)
            if user:
                send_daily_reminders_for_user(user)
        except Exception:
            pass

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', 
                         error_code=404, 
                         error_message="Page Not Found",
                         error_description="The page you're looking for doesn't exist."), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('error.html', 
                         error_code=500, 
                         error_message="Internal Server Error",
                         error_description="Something went wrong on our end. Please try again later."), 500

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('error.html', 
                         error_code=403, 
                         error_message="Forbidden",
                         error_description="You don't have permission to access this resource."), 403


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

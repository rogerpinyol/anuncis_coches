from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Usuario
from functools import wraps

auth = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor, inicia sesión para acceder')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = Usuario.query.filter_by(email=email).first()
        
        # Change "contrasenya" to "password" to match your model field name
        if user and check_password_hash(user.password, password):
            # Store user information in session
            session['user_id'] = user.id
            session['user_nom'] = user.nom
            session['user_tipus'] = user.tipus
            
            # For debugging
            print(f"Setting session: user_id={user.id}, user_nom={user.nom}, user_tipus={user.tipus}")
            
            flash('Has iniciado sesión correctamente')
            return redirect(url_for('index'))
        else:
            flash('Email o contraseña incorrectos')
    
    return render_template('auth/login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nom = request.form.get('nom')
        email = request.form.get('email')
        password = request.form.get('password')
        tipus = request.form.get('tipus')
        
        user = Usuario.query.filter_by(email=email).first()
        
        if user:
            flash('El email ya está registrado')
            return redirect(url_for('auth.register'))
        
        new_user = Usuario(
            nom=nom,
            email=email,
            password=generate_password_hash(password),
            tipus=tipus
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('¡Registro exitoso!')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión')
    return redirect(url_for('index'))
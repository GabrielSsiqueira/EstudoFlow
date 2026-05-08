from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from extensions.database import db
from werkzeug.security import generate_password_hash, check_password_hash 
from models.modelos import User

auth_bp = Blueprint('auth',__name__, url_prefix='/auth')



# --- REGISTRO ---
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Verifica se o email já existe
        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('Email já cadastrado.', 'danger')
            return redirect(url_for('auth.register'))
        
        # Cria novo usuário com hash de senha
        new_user = User(
            name=name, 
            email=email, 
            estado='Ativo',
            password_hash=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash('Conta criada com sucesso! Faça login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

# --- LOGIN ---
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email, estado='Ativo').first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            if user.type_user == 'admin':
                return redirect(url_for('admin.admin_dashboard')) # Redireciona para estantes
            else: 
                return redirect(url_for('user.home')) # Redireciona para estantes
        else:
            flash('Login inválido. Verifique email e senha.', 'danger')
            
    return render_template('login.html')

# --- LOGOUT ---
@auth_bp.route('/logout')
@login_required
def logout():
    # Limpa todas as mensagens flash pendentes antes de sair
    session.pop('_flashes', None) 
    
    logout_user()
    flash('Logout realizado com sucesso!', 'info') # Opcional: mensagem específica de saída
    return redirect(url_for('main.index'))
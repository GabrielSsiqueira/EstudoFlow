from flask import Blueprint, render_template, redirect, url_for, flash, request
from functools import wraps
from flask_login import current_user, login_required
from models.modelos import User, Estante, Livro

# Decorador para proteger rotas de admin
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.type_user != 'user':
            abort(403) # Proibido
        return f(*args, **kwargs)
    return decorated_function 
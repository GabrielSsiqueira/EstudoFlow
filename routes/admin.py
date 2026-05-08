from flask import Blueprint, render_template, redirect, url_for, flash, request
from models.modelos import User, Estante, Livro, Anotacao, Marcacao, Progresso, Historico
from decorador.decorador_adm import admin_required

admin_bp = Blueprint('admin',__name__, url_prefix='/admin')

# --- PAINEL ADMIN ---
@admin_bp.route('/dashboard')
@admin_required
def admin_dashboard():
    # Admin vê estatísticas de todos os usuários
    total_users = User.query.count()
    total_books = Livro.query.count()
    total_estantes = Estante.query.count()
    return render_template('admin/dashboard.html', users=total_users, estante=total_estantes, books=total_books)

# --- GERENCIAR USUÁRIOS (ADMIN) ---
@admin_bp.route('/users')
@admin_required
def list_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/livros')
@admin_required
def list_books():
    books = Livro.query.all()
    return render_template('admin/books.html', book=books)

@admin_bp.route('/estantes')
@admin_required
def list_estantes():
    shelves = Estante.query.all()
    return render_template('admin/estante.html', shelf=shelves)

@admin_bp.route('/anotacoes')
@admin_required
def list_annotations():
    # Carrega anotações trazendo junto usuário e livro (otimização de banco)
    all_notes = Anotacao.query.all() 
    return render_template('admin/annotations.html', annotations=all_notes)

@admin_bp.route('/historicos')
@admin_required
def list_histories():
    # Carrega anotações trazendo junto usuário e livro (otimização de banco)
    history = Historico.query.all() 
    return render_template('admin/history.html', log=history)

@admin_bp.route('/users/edit/<int:id>', methods=['GET'])
@admin_required
def edit_users(id):
    user_to_edit = User.query.get_or_404(id)
    return render_template('admin/edit_user.html', user=user_to_edit)
from extensions.database import db, login_manager 
from flask_login import UserMixin

from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    photo = db.Column(db.String(255), nullable=True)
    type_user = db.Column(db.Enum('admin', 'user', default='user')) # Admin ou User
    estado = db.Column(db.String(10), default='Ativo') # 'ativo' ou 'inativo'
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    estantes = db.relationship('Estante', backref='dono', lazy=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Tabela de Estantes (Categorias)
class Estante(db.Model):
    __tablename__ = 'estantes'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    capa = db.Column(db.String(255), nullable=True) #caminho da imagem...
    estado = db.Column(db.String(10), default='Ativo') # 'ativo' ou 'inativo'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relacionamentos
    user = db.relationship('User', backref='Estante')
    livros = db.relationship('Livro', backref='estante', lazy=True, cascade="all, delete-orphan")

# Tabela de Livros
class Livro(db.Model):
    __tablename__ = 'livros'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    capa = db.Column(db.String(255), nullable=True) #caminho da imagem...
    arquivo_path = db.Column(db.String(255), nullable=False) # Caminho do PDF
    favorito = db.Column(db.Boolean, default=False)
    estado = db.Column(db.String(10), default='Ativo') # 'ativo' ou 'inativo'
    
    
    # FKs
    estante_id = db.Column(db.Integer, db.ForeignKey('estantes.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relacionamentos
    progresso = db.relationship('Progresso', backref='livro', uselist=False, cascade="all, delete-orphan")
    marcacoes = db.relationship('Marcacao', backref='livro', lazy=True)
    anotacoes = db.relationship('Anotacao', backref='livro', lazy=True)

# Registro de Progresso de Leitura
class Progresso(db.Model):
    __tablename__ = 'progressos'
    id = db.Column(db.Integer, primary_key=True)
    ultima_pagina = db.Column(db.Integer, default=1)
    total_paginas = db.Column(db.Integer, nullable=True)
    percentual_concluido = db.Column(db.Float, default=0.0)
    livro_id = db.Column(db.Integer, db.ForeignKey('livros.id'), nullable=False)

# Marcações (Sua funcionalidade de "passar a caneta")
class Marcacao(db.Model):
    __tablename__ = 'marcacoes'
    id = db.Column(db.Integer, primary_key=True)
    texto_extraido = db.Column(db.Text, nullable=False)
    num_pagina = db.Column(db.Integer, nullable=False)
    cor_destaque = db.Column(db.String(7), default="#FFFF00") # Hexadecimal da cor
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    livro_id = db.Column(db.Integer, db.ForeignKey('livros.id'), nullable=False)

# Caderno de Anotações (Pensamentos livres sobre o livro)
class Anotacao(db.Model):
    __tablename__ = 'anotacoes'
    id = db.Column(db.Integer, primary_key=True)
    conteudo = db.Column(db.Text, nullable=False)
    livro_id = db.Column(db.Integer, db.ForeignKey('livros.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# Histórico de Acessos
class Historico(db.Model):
    __tablename__ = 'historicos'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    livro_id = db.Column(db.Integer, db.ForeignKey('livros.id'), nullable=False)
    data_acesso = db.Column(db.DateTime, default=datetime.utcnow)
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = 'AIzaSyA7VhHQcIVwybHSGTVwtZ4Lsjsk5-I9zj8'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///dados.db'
    SQLALCHEMY_TRACK_MODIFICATIONS  = False
    GEMINI_API_KEY = "AIzaSyDNDRZqFJhyuJt1JTN4q7nab4yrmtYb_fs"

    UPLOAD_FOLDER_USER = os.path.join(BASE_DIR, '..', 'static', 'uploads', 'user')
    UPLOAD_FOLDER_SHELF = os.path.join(BASE_DIR, '..', 'static', 'uploads', 'estantes')
    UPLOAD_FOLDER_VIDEOS = os.path.join(BASE_DIR, '..', 'static', 'uploads', 'videos')
    UPLOAD_FOLDER_LIVRO = os.path.join(BASE_DIR, '..', 'static', 'uploads', 'livros')
    UPLOAD_FOLDER_COVERS = os.path.join(BASE_DIR, '..', 'static', 'uploads', 'capa_livro')
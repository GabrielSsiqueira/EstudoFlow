from flask import Blueprint, render_template
from flask_login import current_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('admin.admin_dashboard')) # Se logado, vai pro dashboard
    return render_template('index.html')
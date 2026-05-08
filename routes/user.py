import os
import time
import fitz
import re
from concurrent.futures import ThreadPoolExecutor
from flask import Blueprint, render_template, request, redirect,flash, url_for, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from extensions.database import db
from werkzeug.utils import secure_filename
from decorador.decorador_adm import admin_required 
from models.modelos import User, Estante, Livro, Progresso, Marcacao, Anotacao

user_bp = Blueprint('user', __name__, url_prefix='/user')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

@user_bp.route('/home')
@login_required
def home():

    shelves = Estante.query.filter_by(user_id=current_user.id, estado='Ativo').all()
    
    return render_template('user/home.html', shelves=shelves)



@user_bp.route('/update/<int:id>', methods=['GET','POST'])
@admin_required
# Se for apenas admin que pode editar outros, use o @admin_required aqui também
def update_user(id):
    user = User.query.get_or_404(id)
    
    # Captura os dados do formulário
    user.name = request.form.get('name')
    user.email = request.form.get('email')
    user.type_user = request.form.get('type_user')
    user.estado = request.form.get('estado')
    
    # Senha (opcional)
    new_password = request.form.get('password')
    if new_password:
        user.set_password(new_password)
        
    # Processamento de Foto
    file = request.files.get('photo')
    if file and file.filename != '':
        filename = secure_filename(f"user_{user.id}_{file.filename}")
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER_USER'], filename)
        file.save(upload_path)
        user.photo = filename

    try:
        db.session.commit()
        flash(f'Usuário {user.name} atualizado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao salvar no banco de dados.', 'danger')
        
    return redirect(url_for('admin.list_users'))

@user_bp.route('/delete/<int:id>', methods=['POST'])
@admin_required # Apenas admins podem deletar usuários
def delete_user(id):
    user = User.query.get_or_404(id)
    
    # 1. Impedir que o admin delete a si próprio (segurança básica)
    if user.id == current_user.id:
        flash('Você não pode excluir sua própria conta administrativa!', 'danger')
        return redirect(url_for('admin.list_users'))

    try:
        # 2. Remover a foto do servidor se existir
        if user.photo:
            photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'user', user.photo)
            if os.path.exists(photo_path):
                os.remove(photo_path)
        
        # 3. Remover do banco de dados
        db.session.delete(user)
        db.session.commit()
        
        flash(f'Usuário {user.name} removido com sucesso.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir usuário: {str(e)}', 'danger')
        
    return redirect(url_for('admin.list_users'))

@user_bp.route('estante/nova', methods=['GET','POST']) # Adicionado GET
@login_required
def nova_estante():
    if request.method == 'POST':
        nome = request.form.get('nome')
        capa = request.files.get('capa')
        estado = request.form.get('estado')
        
        if not nome or not capa:
            flash("Nome e Capa são obrigatórios!", "warning")
            return redirect(url_for('user.nova_estante'))

        # 1. Tratar o salvamento da imagem
        # Geramos o nome do arquivo com timestamp para evitar duplicatas
        ext = os.path.splitext(capa.filename)[1] # Pega a extensão (.jpg, .png)
        filename = secure_filename(f"user_{current_user.id}_{ext}")
        
        # Pasta onde as capas serão salvas
        target_dir = current_app.config['UPLOAD_FOLDER_SHELF']
        
        # Criar a pasta se não existir (sem o nome do arquivo no final)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)
            
        # Caminho completo para salvar o arquivo
        file_path = os.path.join(target_dir, filename)
        
        try:
            capa.save(file_path)

            # 2. Salvar no Banco de Dados
            nova_estante = Estante(
                nome=nome, 
                capa=filename, # Guardamos apenas o nome para referenciar no template
                user_id=current_user.id,
                estado=estado
            )
            
            db.session.add(nova_estante)
            db.session.commit()
            
            flash("Estante criada com sucesso!", "success")
            return redirect(url_for('user.home'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao salvar: {str(e)}", "danger")
            return redirect(url_for('user.nova_estante'))

    # Se for GET, renderiza o formulário
    return render_template('user/nova_estante.html')

@user_bp.route('/estante', methods=['GET'])
@login_required
def form_nova_estante():
    return render_template('user/new_shelf.html')

@user_bp.route('/estante/<int:estante_id>/upload', methods=['POST'])
@login_required
def upload_livro(estante_id):
    # Verifica se a estante existe e pertence ao usuário
    estante = Estante.query.get_or_404(estante_id)
    if estante.user_id != current_user.id:
        abort(403)

    if 'arquivo' not in request.files:
        flash('Nenhum arquivo enviado.', 'danger')
        return redirect(request.url)
    
    file = request.files['arquivo']
    titulo = request.form.get('titulo')
   

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Criamos um nome único concatenando o ID do usuário para evitar conflitos
        unique_filename = f"{current_user.id}_{filename}"
        
        # Caminho onde o arquivo será salvo (baseado no seu Config)
        save_path = os.path.join(current_app.config['UPLOAD_FOLDER_USER'], unique_filename)
        
        # Garante que a pasta existe
        os.makedirs(current_app.config['UPLOAD_FOLDER_USER'], exist_ok=True)
        
        file.save(save_path)

        # Salva no Banco de Dados
        novo_livro = Livro(
            titulo=titulo if titulo else filename,
            arquivo_path=unique_filename, # Guardamos apenas o nome/path relativo
            estante_id=estante_id,
            user_id=current_user.id,
            estado='Ativo'
        )
        
        db.session.add(novo_livro)
        db.session.flush() # Flush para obter o ID do livro antes do commit final

        # Criar registro de progresso inicial
        novo_progresso = Progresso(livro_id=novo_livro.id)
        db.session.add(novo_progresso)
        
        db.session.commit()
        flash('Livro adicionado com sucesso!', 'success')
        
    return redirect(url_for('user.visualizar_estante', estante_id=estante_id))

@user_bp.route('/estante/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_estante(id):
    estante = Estante.query.get_or_404(id)
    
    # Segurança: garante que o usuário só edite a própria estante
    if estante.user_id != current_user.id:
        abort(403)

    if request.method == 'POST':
        novo_nome = request.form.get('nome')
        nova_capa = request.files.get('capa')
        estado = request.form.get('estado')

        if not novo_nome:
            flash("O nome da estante é obrigatório.", "warning")
            return redirect(url_for('user.editar_estante', id=id))

        estante.nome = novo_nome
        estante.estado = estado

        # Se o usuário enviou uma nova foto
        if nova_capa and nova_capa.filename != '':
            # 1. Gerar nome e salvar nova imagem
            ext = os.path.splitext(nova_capa.filename)[1]
            nome_arquivo = secure_filename(f"shelf_{current_user.id}_{int(time.time())}{ext}")
            
            upload_path = current_app.config['UPLOAD_FOLDER_SHELF']
            nova_capa.save(os.path.join(upload_path, nome_arquivo))
            
            # 2. Opcional: Deletar a capa antiga do disco para não acumular lixo
            if estante.capa and estante.capa != 'default_shelf.png':
                caminho_antigo = os.path.join(upload_path, estante.capa)
                if os.path.exists(caminho_antigo):
                    os.remove(caminho_antigo)
            
            estante.capa = nome_arquivo

        db.session.commit()
        flash("Estante atualizada com sucesso!", "success")
        return redirect(url_for('user.home'))

    return render_template('user/shelf_edit.html', estante=estante)

@user_bp.route('/estante/<int:estante_id>')
@login_required
def visualizar_estante(estante_id):
    # Buscamos a estante e verificamos se ela existe
    estante = Estante.query.get_or_404(estante_id)
    
    # Validação de segurança: a estante pertence ao usuário logado?
    if estante.user_id != current_user.id:
        abort(403)  # Erro de Proibido caso tente acessar estante alheia
    
    # Como você definiu o backref='estante' no modelo Livro, 
    # podemos acessar os livros diretamente pelo objeto estante
    livros = Livro.query.filter_by(estante_id=estante_id, user_id=current_user.id, estado='Ativo').all()
    
    return render_template('user/view_shelf.html', 
                           estante=estante, 
                           livros=livros)


# ROTA 1: Visualização do Formulário (GET)
@user_bp.route('/livro/novo', methods=['GET'])
@login_required
def form_novo_livro():
    # Buscamos as estantes do usuário para preencher o <select> no HTML
    minhas_estantes = Estante.query.filter_by(user_id=current_user.id).all()
    
    if not minhas_estantes:
        flash('Você precisa criar uma estante antes de adicionar livros!', 'warning')
        return redirect(url_for('user.form_nova_estante'))
        
    return render_template('user/new_book.html', shelves=minhas_estantes)

# ROTA 2: Processamento do Cadastro (POST)
@user_bp.route('/livro/cadastrar', methods=['POST'])
@login_required
def cadastrar_livro():
    titulo = request.form.get('titulo')
    estante_id = request.form.get('estante_id')
    # Simplificado: bool(request.form.get('favorito')) já resolve
    favorito = True if request.form.get('favorito') else False
    
    pdf_file = request.files.get('pdf_file')
    capa_file = request.files.get('capa_file')

    if pdf_file and pdf_file.filename != '':
        # 1. Gerar nome seguro para o PDF
        pdf_ext = os.path.splitext(pdf_file.filename)[1]
        pdf_filename = secure_filename(f"user{current_user.id}_{int(time.time())}{pdf_ext}")
        pdf_upload_path = os.path.join(current_app.config['UPLOAD_FOLDER_LIVRO'], pdf_filename)

        # 2. Tratar a Capa
        capa_filename = "default_cover.jpg" # Valor padrão
        if capa_file and capa_file.filename != '':
            capa_ext = os.path.splitext(capa_file.filename)[1]
            capa_filename = secure_filename(f"capa_{current_user.id}_{int(time.time())}{capa_ext}")
            capa_upload_path = os.path.join(current_app.config['UPLOAD_FOLDER_COVERS'], capa_filename)
            
            # Garante que a pasta de capas existe
            os.makedirs(current_app.config['UPLOAD_FOLDER_COVERS'], exist_ok=True)
            capa_file.save(capa_upload_path)
        
        try:
            # Garante que a pasta de livros existe
            os.makedirs(current_app.config['UPLOAD_FOLDER_LIVRO'], exist_ok=True)
            pdf_file.save(pdf_upload_path)
            
            # 3. Cria o objeto Livro
            novo_livro = Livro(
                titulo=titulo,
                arquivo_path=pdf_filename,
                favorito=favorito,
                capa=capa_filename, # Nome da coluna no seu banco
                estante_id=estante_id,
                estado='Ativo',
                user_id=current_user.id
            )
            
            db.session.add(novo_livro)
            db.session.commit()
            
            flash(f'Livro "{titulo}" adicionado com sucesso!', 'success')
            return redirect(url_for('user.view_shelf', id=estante_id))
            
        except Exception as e:
            db.session.rollback()
            # Opcional: deletar os arquivos físicos se o banco falhar
            flash(f'Erro ao salvar no banco de dados: {str(e)}', 'danger')
            return redirect(url_for('user.form_novo_livro'))

    flash('Nenhum arquivo PDF foi selecionado.', 'danger')
    return redirect(url_for('user.form_novo_livro'))

@user_bp.route('/livro/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_livro(id):
    # Busca o livro ou retorna 404
    livro = Livro.query.get_or_404(id)
    
    # Segurança: Verificar se o livro pertence ao usuário logado
    if livro.user_id != current_user.id:
        abort(403)

    if request.method == 'POST':
        # 1. Capturar dados do formulário
        livro.titulo = request.form.get('titulo')
        livro.estante_id = request.form.get('estante_id')
        livro.estado = request.form.get('estado')
        livro.favorito = True if request.form.get('favorito') else False
        
        nova_capa = request.files.get('capa_file')

        # 2. Processar nova capa (se enviada)
        if nova_capa and nova_capa.filename != '':
            ext = os.path.splitext(nova_capa.filename)[1]
            nome_arquivo = secure_filename(f"capa_{current_user.id}_{int(time.time())}{ext}")
            
            upload_path = current_app.config['UPLOAD_FOLDER_COVERS']
            os.makedirs(upload_path, exist_ok=True)
            
            # Salvar novo arquivo
            nova_capa.save(os.path.join(upload_path, nome_arquivo))
            
            # Deletar capa antiga (se não for a padrão)
            if livro.capa and livro.capa != 'default_cover.jpg':
                caminho_antigo = os.path.join(upload_path, livro.capa)
                if os.path.exists(caminho_antigo):
                    try:
                        os.remove(caminho_antigo)
                    except:
                        pass # Evita que erro ao deletar trave a atualização
            
            livro.capa = nome_arquivo

        try:
            db.session.commit()
            flash(f'Livro "{livro.titulo}" atualizado com sucesso!', 'success')
            return redirect(url_for('user.visualizar_estante', estante_id=livro.estante_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao salvar alterações: {str(e)}', 'danger')

    # Para o GET, carregamos todas as estantes do usuário para o <select>
    shelves = Estante.query.filter_by(user_id=current_user.id).all()
    return render_template('user/book_edit.html', livro=livro, shelves=shelves)

@user_bp.route('/livro/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_livro(id):
    livro = Livro.query.get_or_404(id)
    
    # Segurança: Verificar se o livro pertence ao usuário
    if livro.user_id != current_user.id:
        abort(403)

    try:
        livro.estado = 'inativo' # Exclusão lógica
        db.session.commit()
        flash(f'O livro "{livro.titulo}" foi removido da sua estante.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao tentar remover o livro.', 'danger')

    return redirect(url_for('user.visualizar_estante', estante_id=livro.estante_id))

@user_bp.route('/ler/<int:id>')
@login_required
def ler_livro(id):
    livro = Livro.query.get_or_404(id)
    
    if livro.user_id != current_user.id:
        return redirect(url_for('user.home'))
    
    # Captura a página e o termo de destaque da URL (ex: ?page=12&hl=algoritmo)
    pagina_salva = livro.progresso.ultima_pagina if livro.progresso else 1
    page_to_open = request.args.get('page', default=1, type=int)
    highlight_term = request.args.get('hl', default='', type=str)

    marcacoes_data = [
        {
            'pagina': m.num_pagina, # Verifique se no seu Model o campo é 'pagina' ou 'num_pagina'
            'texto': m.texto_extraido,   # Verifique se no seu Model é 'texto' ou 'texto_extraido'
            'cor': m.cor_destaque        # Verifique se no seu Model é 'cor' ou 'cor_destaque'
        }
        for m in livro.marcacoes
    ]
    
    return render_template('user/reader.html', 
                           livro=livro, 
                           start_page=page_to_open, 
                           highlight=highlight_term, 
                           marcacoes_existentes=marcacoes_data)


def processar_livro_paralelo(livro_info, query_regex):
    """Função auxiliar que roda em uma thread separada para cada livro."""
    caminho_pdf, livro_id, titulo, estante_nome = livro_info
    detalhes_citacoes = []
    
    if not os.path.exists(caminho_pdf):
        return None

    try:
        # Abrimos o documento dentro da thread
        doc = fitz.open(caminho_pdf)
        for num_pag, pagina in enumerate(doc, start=1):
            texto_pag = pagina.get_text("text")
            
            # Verificação rápida antes de dar split nas linhas (ganha muita performance)
            if query_regex.search(texto_pag):
                linhas = texto_pag.split('\n')
                for linha in linhas:
                    if query_regex.search(linha):
                        detalhes_citacoes.append({
                            'pagina': num_pag,
                            'trecho': linha.strip()[:150] # Limite para não sobrecarregar o HTML
                        })
        doc.close()
        
        if detalhes_citacoes:
            return {
                'id': livro_id,
                'titulo': titulo,
                'total_geral': len(detalhes_citacoes),
                'estante': estante_nome,
                'detalhes': detalhes_citacoes
            }
    except Exception as e:
        print(f"Erro ao processar {titulo}: {e}")
    
    return None

@user_bp.route('/pesquisa-inteligente')
@login_required
def pesquisa_inteligente():
    query = request.args.get('q', '').strip()
    estante_id = request.args.get('estante_id', 'todas')
    resultados = []
    
    estantes_usuario = Estante.query.filter_by(user_id=current_user.id).all()

    if query and len(query) >= 3:
        padrao_regex = re.compile(r'\b' + re.escape(query) + r'\b', re.IGNORECASE)

        # Filtro inicial no Banco de Dados
        base_query = Livro.query.filter_by(user_id=current_user.id)
        if estante_id != 'todas':
            base_query = base_query.filter_by(estante_id=int(estante_id))
        
        livros = base_query.all()
        
        # Preparamos os dados para as threads (evita passar objetos do SQLAlchemy para threads)
        lista_tarefas = []
        for livro in livros:
            caminho = os.path.join(current_app.config['UPLOAD_FOLDER_LIVRO'], livro.arquivo_path)
            lista_tarefas.append((caminho, livro.id, livro.titulo, livro.estante.nome))

        # EXECUTOR PARALELO: max_workers define o número de threads simultâneas
        # Geralmente 4 a 8 é um bom número para não fritar o CPU do servidor
        with ThreadPoolExecutor(max_workers=8) as executor:
            # Mapeamos a função para a lista de tarefas
            futures = [executor.submit(processar_livro_paralelo, tarefa, padrao_regex) for tarefa in lista_tarefas]
            
            for future in futures:
                resultado = future.result()
                if resultado:
                    resultados.append(resultado)

    resultados = sorted(resultados, key=lambda x: x['total_geral'], reverse=True)
    
    return render_template('user/search_results.html', 
                           resultados=resultados, 
                           query=query, 
                           estantes_usuario=estantes_usuario,
                           estante_selecionada=estante_id)

# Rota para salvar o progresso (página atual)
@user_bp.route('/salvar-progresso/<int:livro_id>', methods=['POST'])
@login_required
def salvar_progresso(livro_id):
    dados = request.json
    ultima_pag = dados.get('pagina')
    total_pags = dados.get('total')
    
    progresso = Progresso.query.filter_by(livro_id=livro_id).first()
    
    if not progresso:
        progresso = Progresso(livro_id=livro_id)
        db.session.add(progresso)
    
    progresso.ultima_pagina = ultima_pag
    progresso.total_paginas = total_pags
    # Cálculo simples de percentual
    if total_pags > 0:
        progresso.percentual_concluido = (ultima_pag / total_pags) * 100
        
    db.session.commit()
    return jsonify({"status": "sucesso"})

# Rota para salvar uma marcação (destaque)
@user_bp.route('/salvar-marcacao/<int:livro_id>', methods=['POST'])
@login_required
def salvar_marcacao(livro_id):
    dados = request.json
    
    nova_marcacao = Marcacao(
        livro_id=livro_id,
        num_pagina=dados.get('pagina'),
        cor_destaque=dados.get('cor'),
        texto_extraido=dados.get('texto') # No caso de desenho, pode ser um resumo ou as coordenadas
    )
    
    db.session.add(nova_marcacao)
    db.session.commit()
    return jsonify({"status": "salvo", "id": nova_marcacao.id})


@user_bp.route('/caderno/<int:livro_id>')
@login_required
def caderno_livro(livro_id):
    livro = Livro.query.get_or_404(livro_id)
    
    if livro.user_id != current_user.id:
        return redirect(url_for('user.home'))

    # Pegamos as marcações (pintadas no PDF) e as anotações (escritas)
    # Ordenamos ambas pela data de criação
    anotacoes = Anotacao.query.filter_by(livro_id=livro_id).order_by(Anotacao.created_at.desc()).all()
    marcacoes = Marcacao.query.filter_by(livro_id=livro_id).order_by(Marcacao.num_pagina).all()
    
    return render_template('user/insights.html', 
                           livro=livro, 
                           anotacoes=anotacoes, 
                           marcacoes=marcacoes)

@user_bp.route('/salvar-anotacao/<int:livro_id>', methods=['POST'])
@login_required
def salvar_anotacao(livro_id):
    dados = request.json
    conteudo = dados.get('conteudo')

    if not conteudo:
        return jsonify({"erro": "Conteúdo vazio"}), 400

    nova_anotacao = Anotacao(
        conteudo=conteudo,
        livro_id=livro_id
        # O created_at já tem default=datetime.utcnow no seu Model
    )

    try:
        db.session.add(nova_anotacao)
        db.session.commit()
        return jsonify({"status": "sucesso", "id": nova_anotacao.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": str(e)}), 500

#perfil do usuario
@user_bp.route('/perfil')
@login_required
def perfil():
    # Estatísticas rápidas
    total_livros = Livro.query.filter_by(user_id=current_user.id).count()
    total_estantes = Estante.query.filter_by(user_id=current_user.id).count()
    total_favoritos = Livro.query.filter_by(user_id=current_user.id, favorito=True).count()
    
    return render_template('user/profile.html', 
                        user=current_user,
                        total_livros=total_livros,
                        total_estantes=total_estantes,
                        total_favoritos=total_favoritos)
                
@user_bp.route('/perfil/atualizar', methods=['POST'])
@login_required
def atualizar_perfil():
    user = User.query.get(current_user.id)
    name = request.form.get('nome')
    email = request.form.get('email')
    foto = request.files.get('foto')

    # Atualização de dados básicos
    user.name = name
    user.email = email

    # Processamento da Foto
    if foto and foto.filename != '':
        ext = os.path.splitext(foto.filename)[1]
        nome_foto = secure_filename(f"perfil_{user.id}_{int(time.time())}{ext}")
        
        # Pasta de destino (certifique-se que existe)
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER_USER'])
        os.makedirs(upload_path, exist_ok=True)
        
        foto.save(os.path.join(upload_path, nome_foto))
        user.photo = nome_foto

    # Atualização de Senha
    nova_senha = request.form.get('senha')
    if nova_senha:
        user.set_password(nova_senha)

    db.session.commit()
    flash("Perfil atualizado com sucesso!", "success")
    return redirect(url_for('user.perfil'))
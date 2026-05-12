from google import genai # Importação nova
from flask import current_app

def processar_texto_com_ai(texto, tarefa="resumir"):
    api_key = current_app.config.get('GEMINI_API_KEY')
    
    if not api_key or "AIzaSy" not in api_key:
        return "Erro: Chave de API inválida ou não configurada."

    # Inicializa o novo cliente
    client = genai.Client(api_key=api_key)
    
    prompts = {
        "resumir": "Resuma o seguinte trecho de um livro em tópicos principais, mantendo o tom acadêmico:",
        "explicar": "Explique de forma didática o termo técnico ou conceito a seguir:",
        "traduzir": "Traduza o seguinte texto para o Português do Brasil, mantendo o contexto técnico:"
    }
    
    instrucao = prompts.get(tarefa, prompts["resumir"])
    
    try:
        # A sintaxe de geração também mudou levemente
        response = client.models.generate_content(
            model= 'gemini-flash-latest',
            contents=f"{instrucao}\n\n{texto}"
        )
        return response.text
    except Exception as e:
        return f"Erro na nova IA: {str(e)}"
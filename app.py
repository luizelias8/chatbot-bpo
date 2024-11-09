import os
import sys
from flask import Flask, render_template, request, Response
from openai import OpenAI
from assistente import *
from time import sleep

# Determina o diretório onde está o executável ou o script
diretorio_app = os.path.dirname(sys.executable if hasattr(sys, 'frozen') else __file__)

# Obtém a chave de API do ambiente
chave_api = os.getenv('OPENAI_API_KEY')

# Cria um cliente OpenAI usando a chave de API fornecida
cliente = OpenAI(api_key=chave_api)
# Define o modelo do OpenAI a ser utilizado
modelo = 'gpt-4-1106-preview'

# Cria uma instância da aplicação Flask
app = Flask(__name__)
# Define uma chave secreta para a sessão
app.secret_key = 'chave_secreta'

# Chama a função pegar_configuracoes() para recuperar os dados do assistente e da thread.
assistente = pegar_configuracoes()

# Acessa o ID da thread armazenado no dicionário 'assistente' e o atribui à variável 'thread_id'.
# Isso permite que o código faça referência à thread já existente.
id_thread = assistente['id_thread']

# Acessa o ID do assistente armazenado no dicionário 'assistente' e o atribui à variável 'assistente_id'.
# Isso permite que o código utilize o assistente já existente.
id_assistente = assistente['id_assistente']

# Acessa a lista de IDs de arquivos armazenados no dicionário 'assistente' e a atribui à variável 'file_ids'.
# Isso permite que o código utilize os arquivos previamente carregados associados ao assistente.
id_armazenamento_vetorial = assistente['id_armazenamento_vetorial']

STATUS_COMPLETED = 'completed'

def bot(prompt):
    """Função que interage com o modelo OpenAI para obter respostas baseadas no prompt do usuário."""
    # Define o número máximo de tentativas em caso de falha
    maximo_tentativas = 1
    # Contador de tentativas
    repeticao = 0

    # Loop para tentar a comunicação com o modelo até obter sucesso ou atingir o máximo de tentativas
    while True:
        try:
            # Envia o prompt do usuário para a thread do assistente
            cliente.beta.threads.messages.create(
                thread_id=id_thread, # Identificador exclusivo da thread de conversa, utilizado para manter o contexto das interações
                role='user',
                content=prompt
            )

            # Executa o processamento do prompt pelo assistente
            run = cliente.beta.threads.runs.create(
                thread_id=id_thread, # Identificador exclusivo da thread de conversa, que associa a execução ao contexto da interação atual
                assistant_id=id_assistente # Identificador do assistente que irá processar o prompt, permitindo que o sistema saiba qual assistente está ativo na thread
            )

            # Como essa resposta não aparece de forma instantânea, temos que garantir que só vamos computar essa resposta
            # depois que o assistente responder aos questionamentos presentes na thread.
            # Verifica se o processamento do prompt foi concluído
            while run.status != STATUS_COMPLETED:
                run = cliente.beta.threads.runs.retrieve(
                    thread_id=id_thread, # Identificador da thread associada à execução atual, utilizado para garantir que o status verificado corresponde à conversa correta
                    run_id=run.id # Identificador da execução específica que está sendo monitorada, permitindo que o sistema recupere o estado atual da execução
                )

                # Recupera a lista de mensagens da thread especificada e converte os dados em uma lista
            historico = list(cliente.beta.threads.messages.list(thread_id=id_thread).data)

            # Armazena a primeira mensagem do histórico, que geralmente é a resposta do assistente
            resposta = historico[0]

            # Retorna a resposta obtida do assistente
            return resposta

        except Exception as erro:
            # Incrementa o contador de tentativas
            repeticao += 1
            # Retorna mensagem de erro se o limite de tentativas for atingido
            if repeticao >= maximo_tentativas:
                return 'Erro no GPT: %s' % erro
            # Exibe erro de comunicação
            print('Erro de comunicação com OpenAI:', erro)
            # Espera um segundo antes de tentar novamente
            sleep(1)

@app.route('/chat', methods=['POST'])
def chat():
    """Rota que recebe mensagens do usuário e retorna a resposta do chatbot."""
    # Captura a mensagem do usuário
    prompt = request.json['msg']
    # Obtém a resposta do bot
    resposta = bot(prompt)
    # Extrai o conteúdo da resposta
    texto_resposta = resposta.content[0].text.value
    return texto_resposta # Retorna a resposta ao cliente

# O decorador @app.route() é utilizado para associar uma função a uma URL específica da aplicação.
# Quando um usuário acessa a URL correspondente, a função decorada será executada.
@app.route('/')
def home():
    """Rota principal que renderiza a página inicial do aplicativo."""
    # Renderiza o template HTML da página inicial
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True) # Inicia a aplicação em modo de depuração
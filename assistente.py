import os
import sys
from openai import OpenAI
from ferramentas import minhas_ferramentas
import json

# Determina o diretório onde está o executável ou o script
diretorio_app = os.path.dirname(sys.executable if hasattr(sys, 'frozen') else __file__)

# Obtém a chave de API do ambiente
chave_api = os.getenv('OPENAI_API_KEY')

# Cria um cliente OpenAI usando a chave de API fornecida
cliente = OpenAI(api_key=chave_api)
# Define o modelo do OpenAI a ser utilizado
modelo = 'gpt-4-1106-preview'

def criar_armazenamento_vetorial():
    # Cria um novo armazenamento vetorial.
    # Esse repositório armazenará os vetores dos arquivos que o assistente vai precisar.
    armazenamento_vetorial = cliente.beta.vector_stores.create(name='armazenamento_vetorial_assistente_bpo')

    # Lista de caminhos dos arquivos que contêm os dados que queremos anexar ao armazenamento vetorial.
    caminhos_arquivos = [
        os.path.join(diretorio_app, 'dados', 'procedimentos_sistema_unico.txt'),
        os.path.join(diretorio_app, 'dados', 'projetos_automacao.txt')
    ]

    # Abre cada arquivo no modo de leitura binária ('rb') e armazena os fluxos de arquivos (file streams) em uma lista.
    # Essa lista `fluxos_arquivos` é usada para carregar os arquivos para o armazenamento vetorial.
    fluxos_arquivos = [open(caminho, 'rb') for caminho in caminhos_arquivos]

    # Faz o upload dos arquivos no armazenamento vetorial recém-criado.
    # O método `upload_and_poll` envia os arquivos para o armazenamento e espera a confirmação de upload.
    # O parâmetro `vector_store_id` usa o ID do armazenamento vetorial que criamos anteriormente.
    cliente.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=armazenamento_vetorial.id,
        files=fluxos_arquivos
    )

    # Retorna o armazenamento vetorial criado, caso seja necessário utilizá-lo posteriormente.
    return armazenamento_vetorial

# Serve para gerenciar a persistência dos dados relacionados ao assistente e a thread,
# evitando a necessidade de criar um novo assistente a cada execução do script.
def pegar_configuracoes():
    # Define o nome do arquivo JSON que será utilizado.
    nome_arquivo = os.path.join(diretorio_app, 'configuracoes.json')

    # Verifica se o arquivo 'configuracoes.json' não existe.
    if not os.path.exists(nome_arquivo):
        # Se o arquivo não existir, cria um novo armazenamento vetorial para armazenar os dados.
        armazenamento_vetorial = criar_armazenamento_vetorial()

        # Cria uma nova thread, que pode ser usada para gerenciar a conversa ou a interação com o assistente.
        thread = criar_thread(armazenamento_vetorial)

        # Cria um novo assistente que utilizará o armazenamento vetorial recém-criado para buscar informações.
        assistente = criar_assistente(armazenamento_vetorial)

        # Cria um dicionário para armazenar os dados que serão salvos no arquivo JSON.
        dados = {
            'id_assistente': assistente.id, # ID do assistente criado.
            'id_armazenamento_vetorial': armazenamento_vetorial.id,
            'id_thread': thread.id # ID da thread criada.
        }

        # Abre o arquivo 'configuracoes.json' em modo de escrita ('w') com codificação UTF-8.
        with open(nome_arquivo, 'w', encoding='utf-8') as arquivo:
            # Salva os dados no arquivo JSON, garantindo que caracteres não ASCII sejam corretamente representados.
            json.dump(dados, arquivo, ensure_ascii=False, indent=4)

        # Informa ao usuário que o arquivo foi criado com sucesso.
        print("Arquivo 'configuracoes.json' criado com sucesso.")

    # Tenta abrir e ler o arquivo 'configuracoes.json'.
    try:
        with open(nome_arquivo, 'r', encoding='utf-8') as arquivo:
            # Carrega os dados do arquivo JSON e os retorna como um dicionário.
            dados = json.load(arquivo)
            return dados
    # Captura a exceção caso o arquivo não seja encontrado.
    except FileNotFoundError:
        print("Arquivo 'configuracoes.json' não encontrado.")

# Função para carregar as instruções
def carregar_instrucoes():
    """Carrega as instruções da assistente"""

    # Compoe o caminho do arquivo 'instrucoes.txt' dentro da pasta 'dados' no diretório do aplicativo
    caminho_arquivo = os.path.join(diretorio_app, 'dados', 'instrucoes.txt')

    try:
        # Tenta abrir o arquivo no caminho especificado com codificação UTF-8 para leitura
        with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
            # Lê o conteúdo do arquivo e armazena na variável 'instrucoes'
            instrucoes = arquivo.read()
        # Retorna o conteúdo do arquivo como resultado da função
        return instrucoes
    except FileNotFoundError:
        # Caso o arquivo não seja encontrado, exibe uma mensagem de erro especificando o caminho do arquivo
        print(f"Erro: O arquivo '{caminho_arquivo}' não foi encontrado.")
        # Retorna None para indicar que o carregamento falhou
        return None
    except Exception as e:
        # Captura qualquer outra exceção que possa ocorrer ao tentar abrir ou ler o arquivo
        print(f"Erro ao carregar as instruções: {e}")
        # Retorna None para indicar que ocorreu um erro inesperado no processo
        return None

def criar_thread(armazenamento_vetorial):
    return cliente.beta.threads.create(
        tool_resources={
            'file_search': {
                'vector_store_ids': [armazenamento_vetorial.id]
                # É importante incluir o parâmetro vector_store_ids para que o modelo saiba de onde buscar as informações relevantes.
                # Toda vez que você inicia uma thread (uma sessão de conversa) usando o Assistente, é importante vincular os documentos.
                # Isso é feito informando o vector_store_id na criação da thread, garantindo que as respostas do Assistente nesta sessão considerem a base de conhecimento definida.
            }
        }
    )

# Função para criar o assistente com as instruções carregadas
def criar_assistente(armazenamento_vetorial):
    """Cria um novo assistente com base nas instruções carregadas."""

    # Define as instruções que serão usadas pelo assistente (carregadas do arquivo de instruções)
    instrucoes = carregar_instrucoes()

    # Verifica se as instruções foram carregadas corretamente
    if instrucoes is None:
        print("Erro: Não foi possível carregar as instruções do assistente.")
        return None

    # Cria uma instância do assistente no OpenAI usando as instruções carregadas
    assistente = cliente.beta.assistants.create(
        name='assistente_bpo', # Define o nome do assistente
        instructions=instrucoes, # Instruções carregadas do arquivo para o assistente
        model=modelo, # Especifica o modelo de linguagem a ser utilizado pelo assistente
        tools=minhas_ferramentas,
        tool_resources={
            'file_search': {
                'vector_store_ids': [armazenamento_vetorial.id]
            }
        }
        # O parâmetro tool_resources é um dicionário onde você define as ferramentas e recursos adicionais
        # que o assistente terá acesso para usar durante a interação com o usuário.
        # Neste caso, a chave 'file_search' indica que o assistente terá acesso à ferramenta de pesquisa de arquivos.
    )

    # Retorna o objeto do assistente criado para uso
    return assistente

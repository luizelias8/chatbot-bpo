minhas_ferramentas = [
    {"type": "file_search"} # Ferramenta de busca de arquivos
    # A ferramenta file_search permite que o assistente pesquise por informações em arquivos que você fez upload para o ambiente de execução do assistente.
    # A ferramenta de busca de arquivos (file_search) é usada para permitir que o assistente faça consultas inteligentes em arquivos armazenados, com base em conteúdo semântico e não apenas palavras-chave exatas.
    # Quando um assistente está configurado para usar essa ferramenta, ele pode procurar e recuperar documentos ou partes de documentos que são semanticamente relevantes para uma consulta, usando a representação vetorial desses arquivos.
    # Quando um usuário faz uma pergunta ou pede informações, o assistente usa a ferramenta file_search para realizar uma busca dentro do armazenamento vetorial.
    # A entrada do usuário é transformada em um vetor (usando um modelo da OpenAI ou outro modelo de embeddings).
    # Esse vetor é comparado com os vetores armazenados para identificar os documentos ou trechos mais relevantes.
    # O modelo recupera informações relevantes de um conjunto de dados e gera uma resposta personalizada com base nesses dados, em vez de depender apenas de informações pré-treinadas ou de uma base fixa de conhecimento.
]
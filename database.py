import sqlite3
import json
import re
import os
from datetime import datetime, timezone

DB_FILE = 'zoho_cache.db'

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados."""
    conn = sqlite3.connect(DB_FILE)
    _ensure_sqlite_path(conn)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa o banco de dados e cria todas as tabelas do schema."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Executa migrações necessárias
    _migrate_database(cursor)
    
    # Tabela de Projetos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            cliente TEXT,
            gp TEXT,
            produtos_contratados TEXT,
            tem_importacao INTEGER,
            tem_integracao INTEGER,
            importacao_escopo TEXT,
            integracao_escopo TEXT,
            data_inicio TEXT,
            data_criacao TEXT,
            data_liberacao_servidor TEXT,
            data_inicio_implantacao TEXT,
            data_homologacao TEXT,
            data_virada TEXT,
            data_inicio_oa TEXT,
            data_de_onboarding TEXT,
            status_atual TEXT,
            dias_na_fase TEXT,
            dias_total TEXT,
            data_ultima_mudanca TEXT,
            link_google TEXT,
            tags TEXT,
            full_data_json TEXT
        )
    ''')

    # Tabela de Fases (Milestones)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fases (
            id TEXT PRIMARY KEY, -- ID da milestone no Zoho
            projeto_id TEXT NOT NULL,
            nome TEXT NOT NULL,
            status TEXT,
            percentual_conclusao INTEGER,
            FOREIGN KEY (projeto_id) REFERENCES projects (id)
        )
    ''')

    # Tabela de Listas de Tarefas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS listas_de_tarefas (
            id TEXT PRIMARY KEY, -- ID da tasklist no Zoho
            fase_id TEXT NOT NULL,
            projeto_id TEXT NOT NULL, -- Denormalizado para facilitar consultas
            nome TEXT NOT NULL,
            percentual_conclusao INTEGER,
            FOREIGN KEY (fase_id) REFERENCES fases (id),
            FOREIGN KEY (projeto_id) REFERENCES projects (id)
        )
    ''')

    # Tabela de Tarefas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tarefas (
            id TEXT PRIMARY KEY, -- ID da tarefa no Zoho
            lista_de_tarefas_id TEXT NOT NULL,
            fase_id TEXT NOT NULL, -- Denormalizado
            projeto_id TEXT NOT NULL, -- Denormalizado
            nome TEXT NOT NULL,
            concluida INTEGER, -- 0 para False, 1 para True
            FOREIGN KEY (lista_de_tarefas_id) REFERENCES listas_de_tarefas (id),
            FOREIGN KEY (fase_id) REFERENCES fases (id),
            FOREIGN KEY (projeto_id) REFERENCES projects (id)
        )
    ''')

    # Tabela de Comentários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comentarios (
            id TEXT PRIMARY KEY, -- ID do comentário no Zoho
            projeto_id TEXT NOT NULL,
            conteudo TEXT NOT NULL,
            autor_zpuid TEXT,
            autor_nome TEXT,
            autor_email TEXT,
            data_criacao TEXT NOT NULL, -- ISO 8601 format
            data_modificacao TEXT, -- ISO 8601 format
            adicionado_via TEXT, -- WEB, MOBILE, API, etc.
            full_data_json TEXT, -- JSON completo do comentário
            FOREIGN KEY (projeto_id) REFERENCES projects (id)
        )
    ''')
    
    # Índice para buscar comentários por projeto ordenados por data
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_comentarios_projeto_data 
        ON comentarios (projeto_id, data_criacao DESC)
    ''')

    # Tabela de Usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            ativo INTEGER NOT NULL DEFAULT 0
        )
    ''')

    conn.commit()
    conn.close()
    print("Banco de dados 'zoho_cache.db' verificado/inicializado com o schema completo.")

def insert_initial_users():
    """Insere os usuários iniciais no banco de dados se eles não existirem."""
    users = [
        ('Giovani de Sousa', 'giovani.sousa@animati.com.br', 1),
        ('Willian dos Anjos', 'willian.anjos@animati.com.br', 1)
    ]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for nome, email, ativo in users:
        cursor.execute("SELECT id FROM usuarios WHERE email = ?", (email,))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO usuarios (nome, email, ativo) VALUES (?, ?, ?)", (nome, email, ativo))
            print(f"Usuário '{nome}' inserido.")
    
    conn.commit()
    conn.close()

def get_user_by_email(email):
    """Busca um usuário pelo email."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE email = ? AND ativo = 1", (email,))
    user = cursor.fetchone()
    conn.close()
    return user

def _get_custom_field(project_data, field_name):
    """
    Função auxiliar para buscar valores em campos customizados que não são o foco principal.
    """
    # Prioriza campos de primeiro nível se existirem
    if field_name in project_data:
        return project_data[field_name]
    
    # Fallback para a lista de custom_fields
    if 'custom_fields' in project_data and isinstance(project_data['custom_fields'], list):
        for field in project_data['custom_fields']:
            # Busca por label_name
            if field.get('label_name') == field_name:
                return field.get('value')
            
            # Busca também pela chave direta (para campos como "Implantador RIS")
            if isinstance(field, dict):
                for key, value in field.items():
                    if key == field_name:
                        return value
    return None


def _formatar_implantadores(implantadores_data):
    """
    Formata dados de implantadores do Zoho.
    
    O Zoho retorna implantadores em diferentes formatos:
    1. Objeto de usuário: { "zpuid": "123", "name": "João", "full_name": "João Silva", ... }
    2. User Pick List: { "zpuid_123": "Nome do Usuario" }
    3. Lista de objetos de usuários
    
    Args:
        implantadores_data: Dados brutos do campo de implantadores
    
    Returns:
        String com nomes dos implantadores separados por vírgula, ou None
    """
    if not implantadores_data:
        return None
    
    try:
        nomes = []
        
        # Se for string JSON, tenta parsear
        if isinstance(implantadores_data, str):
            implantadores_data = json.loads(implantadores_data)
        
        # Se for dicionário
        if isinstance(implantadores_data, dict):
            # Caso 1: Objeto de usuário do Zoho (com zpuid, name, full_name, etc)
            if 'zpuid' in implantadores_data or 'name' in implantadores_data:
                # Prioriza: full_name > name > first_name + last_name > email
                nome = (
                    implantadores_data.get('full_name') or 
                    implantadores_data.get('name') or
                    f"{implantadores_data.get('first_name', '')} {implantadores_data.get('last_name', '')}".strip() or
                    implantadores_data.get('email', '').split('@')[0]
                )
                if nome:
                    nomes.append(nome)
            else:
                # Caso 2: User Pick List { "zpuid_123": "Nome" }
                for key, value in implantadores_data.items():
                    if isinstance(value, str) and value.strip():
                        nomes.append(value.strip())
        
        # Se for lista de dicionários
        elif isinstance(implantadores_data, list):
            for item in implantadores_data:
                if isinstance(item, dict):
                    # Objeto de usuário
                    if 'zpuid' in item or 'name' in item:
                        nome = (
                            item.get('full_name') or 
                            item.get('name') or
                            f"{item.get('first_name', '')} {item.get('last_name', '')}".strip() or
                            item.get('email', '').split('@')[0]
                        )
                        if nome:
                            nomes.append(nome)
                    else:
                        # Tenta extrair nome de várias chaves possíveis
                        nome = item.get('name') or item.get('display_name') or item.get('email', '').split('@')[0]
                        if nome:
                            nomes.append(nome)
                elif isinstance(item, str) and item.strip():
                    nomes.append(item.strip())
        
        return ', '.join(nomes) if nomes else None
    
    except Exception as e:
        print(f"Erro ao formatar implantadores: {e}")
        return None

def parse_description(description):
    """
    Analisa a descrição HTML de um projeto para extrair informações estruturadas (fallback para dados legados).
    """
    if not description:
        return {
            "produtos_contratados": None,
            "tem_importacao": 0,
            "importacao_escopo": None,
            "tem_integracao": 0,
            "integracao_escopo": None,
            "link_google": None,
        }

    # 1. Produtos Contratados
    produtos = []
    ferramentas_match = re.search(r"Ferramentas Contratadas:.*?<ul>(.*?)</ul>", description, re.DOTALL | re.IGNORECASE)
    if ferramentas_match:
        produtos_raw = re.findall(r"<li>\[\s*X\s*\](.*?)</li>", ferramentas_match.group(1))
        produtos = [re.sub(r"<.*?>", "", p).strip() for p in produtos_raw]

    # 2. Importação
    tem_importacao = 1 if re.search(r"Haverá importação\?.*?\(\s*X\s*\)\s*Sim", description, re.DOTALL | re.IGNORECASE) else 0
    importacao_escopo = None
    if tem_importacao:
        escopo_match = re.search(r"Se Sim, selecione os itens para importação:.*?<ul>(.*?)</ul>", description, re.DOTALL | re.IGNORECASE)
        if escopo_match:
            escopo_raw = re.findall(r"<li>\[\s*X\s*\](.*?)</li>", escopo_match.group(1))
            importacao_escopo = [re.sub(r"<.*?>", "", item).strip() for item in escopo_raw]

    # 3. Integração
    tem_integracao = 1 if re.search(r"Haverá integração\?.*?\(\s*X\s*\)\s*Sim", description, re.DOTALL | re.IGNORECASE) else 0
    integracao_escopo = None
    if tem_integracao:
        escopo_match = re.search(r"Se Sim, selecione as integrações:.*?<ul>(.*?)</ul>", description, re.DOTALL | re.IGNORECASE)
        if escopo_match:
            escopo_raw = re.findall(r"<li>\[\s*X\s*\](.*?)</li>", escopo_match.group(1))
            integracao_escopo = [re.sub(r"<.*?>", "", item).strip() for item in escopo_raw]

    # 4. Link do Google
    link_google = None
    link_match = re.search(r"https://drive\.google\.com/[^\s<]+", description, re.IGNORECASE)
    if link_match:
        link_google = link_match.group(0).strip()

    return {
        "produtos_contratados": json.dumps(produtos) if produtos else None,
        "tem_importacao": tem_importacao,
        "importacao_escopo": json.dumps(importacao_escopo) if importacao_escopo else None,
        "tem_integracao": tem_integracao,
        "integracao_escopo": json.dumps(integracao_escopo) if integracao_escopo else None,
        "link_google": link_google,
    }

def _ensure_sqlite_path(conn):
    """Normaliza o caminho do DB para executáveis locais que esperam arquivo absoluto."""
    try:
        if not os.path.isabs(DB_FILE):
            conn.execute(f"ATTACH DATABASE '{os.path.abspath(DB_FILE)}' AS main")
    except Exception:
        pass


def upsert_project(project_data):
    """
    Insere ou atualiza um projeto, tratando dados estruturados e legados (via descrição).
    Também calcula e persiste dias_total e dias_na_fase (derivados), sem alterar o schema.
    """
    import utils  # import local para evitar ciclos em importação de app

    conn = get_db_connection()
    cursor = conn.cursor()

    project_id = project_data.get('id')
    if not project_id:
        return

    # 1. Extrai dados da descrição como fallback
    desc_data = parse_description(project_data.get("description", ""))

    # 2. Define os parâmetros com lógica de fallback
    
    # Produtos: Prioriza campo estruturado, normaliza e usa fallback da descrição
    produtos_str = project_data.get('solucoes_contratadas')
    if produtos_str and isinstance(produtos_str, str):
        produtos_contratados = json.dumps(produtos_str.split('/'))
    else:
        produtos_contratados = desc_data['produtos_contratados']

    # Importação: Prioriza campo estruturado e usa fallback da descrição
    tem_importacao_raw = project_data.get('havera_importacao')
    if tem_importacao_raw is not None:
        tem_importacao = 1 if str(tem_importacao_raw).lower() == 'sim' else 0
    else:
        tem_importacao = desc_data['tem_importacao']

    # Escopo da Importação: Prioriza, normaliza e usa fallback
    importacoes_list = project_data.get('importacoes')
    if importacoes_list and isinstance(importacoes_list, list):
        valores = [item['value'] for item in importacoes_list]
        # Correção específica: "Prontuários" -> "Prontuário"
        valores_corrigidos = [v.replace('Prontuários', 'Prontuário') for v in valores]
        importacao_escopo = json.dumps(valores_corrigidos)
    else:
        importacao_escopo = desc_data['importacao_escopo']

    # Integração: Prioriza e usa fallback
    tem_integracao_raw = project_data.get('havera_integracao')
    if tem_integracao_raw is not None:
        tem_integracao = 1 if tem_integracao_raw else 0 # API retorna booleano
    else:
        tem_integracao = desc_data['tem_integracao']

    # Escopo da Integração: Apenas fallback, pois não há campo estruturado conhecido
    integracao_escopo = desc_data['integracao_escopo']

    # Link Google: Prioriza e usa fallback
    link_google = project_data.get('link_do_google') or desc_data['link_google']

    # Extrai e formata as tags
    tags_list = project_data.get('tags', [])
    tags_str = ', '.join(tag.get('name', '') for tag in tags_list if tag.get('name')) if tags_list else None

    # 2.1. Datas básicas do projeto para cálculos
    start_date = project_data.get('start_date') or project_data.get('start_date_string')
    created_time = project_data.get('created_time') or project_data.get('created_time_string')
    data_inicio_implantacao = _get_custom_field(project_data, 'Data Início Implantação')
    data_homologacao = _get_custom_field(project_data, 'Data Homologação')
    data_homologacao_prevista = project_data.get('data_de_termino_original')  # Campo customizado do Zoho
    data_virada = project_data.get('data_de_virada')
    data_inicio_oa = _get_custom_field(project_data, 'Data Início OA')

    # 2.2. Cálculo dos derivados
    coluna_hint = utils.determinar_coluna_projeto(project_data)
    dias_total_calc = utils.calcular_dias_total_projeto(start_date, created_time)
    info_min = {
        'data_inicio': start_date,
        'data_criacao': created_time,
        'data_inicio_implantacao': data_inicio_implantacao,
        'data_homologacao': data_homologacao,
        'data_virada': data_virada,
        'data_inicio_oa': data_inicio_oa,
    }
    dias_na_fase_calc = utils.calcular_dias_na_fase(info_min, coluna_hint)

    # 3. Monta o dicionário final de parâmetros
    # Cliente: codigo contrato - nome
    name = project_data.get('name', '')
    parts = name.split(' - ')
    if len(parts) >= 2:
        cliente_formatado = f"{parts[0].strip()} - {parts[1].strip()}"
    else:
        cliente_formatado = name or "Cliente não informado"

    # GP: nome e sobrenome do owner
    owner = project_data.get('owner', {})
    gp_nome = owner.get('first_name', '')
    gp_sobrenome = owner.get('last_name', '')
    gp_valor = f"{gp_nome} {gp_sobrenome}".strip() if gp_nome or gp_sobrenome else owner.get('name', '') or _get_custom_field(project_data, 'GP')

    # Implantadores: Campos de primeiro nível na resposta da API
    # Aparecem diretamente no JSON, não em custom_fields
    implantador_ris_raw = project_data.get('implantador_ris')
    implantador_pacs_raw = project_data.get('implantador_pacs')
    
    # Se os campos são de texto simples, use diretamente; senão, formata do formato User Pick List
    implantador_ris = implantador_ris_raw if isinstance(implantador_ris_raw, str) else (_formatar_implantadores(implantador_ris_raw) if implantador_ris_raw else None)
    implantador_pacs = implantador_pacs_raw if isinstance(implantador_pacs_raw, str) else (_formatar_implantadores(implantador_pacs_raw) if implantador_pacs_raw else None)

    params = {
        'id': project_id,
        'nome': project_data.get('name', 'N/A'),
        'cliente': cliente_formatado,
        'gp': gp_valor,
        'produtos_contratados': produtos_contratados,
        'tem_importacao': tem_importacao,
        'tem_integracao': tem_integracao,
        'importacao_escopo': importacao_escopo,
        'integracao_escopo': integracao_escopo,
        'data_inicio': start_date,
        'data_criacao': created_time,
        'data_liberacao_servidor': _get_custom_field(project_data, 'Data Liberação Servidor'),
        'data_inicio_implantacao': data_inicio_implantacao,
        'data_homologacao': data_homologacao,
        'data_homologacao_prevista': data_homologacao_prevista,  # Data de término original do Zoho
        'data_virada': data_virada, # Campo estruturado
        'data_inicio_oa': data_inicio_oa,
        'data_de_onboarding': _get_custom_field(project_data, 'Data de Onboarding'),
        'status_atual': project_data.get('status', {}).get('name'),
        'dias_na_fase': dias_na_fase_calc,
        'dias_total': dias_total_calc,
        'data_ultima_mudanca': project_data.get('last_modified_time'),
        'data_mudanca_status': None,  # Será preenchido apenas na movimentação manual
        'link_google': link_google,
        'tags': tags_str,
        'implantador_ris': implantador_ris,
        'implantador_pacs': implantador_pacs,
        'full_data_json': json.dumps(project_data)
    }

    # 4. Executa o SQL
    columns = ', '.join(params.keys())
    placeholders = ', '.join('?' for _ in params)
    # IMPORTANTE: Não sobrescrever data_mudanca_status se já existe (foi definida manualmente)
    update_setters = ', '.join(
        f'{key} = excluded.{key}' if key != 'data_mudanca_status' 
        else f'{key} = COALESCE(projects.{key}, excluded.{key})'
        for key in params.keys()
    )

    sql = f'''
        INSERT INTO projects ({columns})
        VALUES ({placeholders})
        ON CONFLICT(id) DO UPDATE SET {update_setters}
    '''

    cursor.execute(sql, tuple(params.values()))
    conn.commit()
    conn.close()

def get_project_by_id(project_id):
    """Busca um projeto pelo seu ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def get_last_sync_time():
    """Retorna o 'last_modified_time' mais recente do banco de dados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT MAX(data_ultima_mudanca) FROM projects')
    row = cursor.fetchone()
    conn.close()
    return row[0] if row and row[0] else '2000-01-01T00:00:00Z'

def upsert_fase(fase_data, projeto_id):
    """Insere ou atualiza uma fase (milestone) no banco de dados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    params = {
        'id': fase_data.get('id'),
        'projeto_id': projeto_id,
        'nome': fase_data.get('name'),
        'status': fase_data.get('status', {}).get('name'),
        'percentual_conclusao': fase_data.get('completion_percent')
    }
    sql = '''INSERT INTO fases (id, projeto_id, nome, status, percentual_conclusao)
             VALUES (:id, :projeto_id, :nome, :status, :percentual_conclusao)
             ON CONFLICT(id) DO UPDATE SET
                projeto_id = excluded.projeto_id,
                nome = excluded.nome,
                status = excluded.status,
                percentual_conclusao = excluded.percentual_conclusao'''
    cursor.execute(sql, params)
    conn.commit()
    conn.close()

def upsert_lista_de_tarefas(lista_data, projeto_id):
    """Insere ou atualiza uma lista de tarefas no banco de dados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    params = {
        'id': lista_data.get('id'),
        'fase_id': lista_data.get('milestone', {}).get('id'),
        'projeto_id': projeto_id,
        'nome': lista_data.get('name'),
        'percentual_conclusao': lista_data.get('completion_percent')
    }
    sql = '''INSERT INTO listas_de_tarefas (id, fase_id, projeto_id, nome, percentual_conclusao)
             VALUES (:id, :fase_id, :projeto_id, :nome, :percentual_conclusao)
             ON CONFLICT(id) DO UPDATE SET
                fase_id = excluded.fase_id,
                projeto_id = excluded.projeto_id,
                nome = excluded.nome,
                percentual_conclusao = excluded.percentual_conclusao'''
    cursor.execute(sql, params)
    conn.commit()
    conn.close()

def upsert_tarefa(tarefa_data, lista_de_tarefas_id, fase_id, projeto_id):
    """Insere ou atualiza uma tarefa no banco de dados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    params = {
        'id': tarefa_data.get('id'),
        'lista_de_tarefas_id': lista_de_tarefas_id,
        'fase_id': fase_id,
        'projeto_id': projeto_id,
        'nome': tarefa_data.get('name'),
        'concluida': 1 if tarefa_data.get('completed') else 0
    }
    sql = '''INSERT INTO tarefas (id, lista_de_tarefas_id, fase_id, projeto_id, nome, concluida)
             VALUES (:id, :lista_de_tarefas_id, :fase_id, :projeto_id, :nome, :concluida)
             ON CONFLICT(id) DO UPDATE SET
                lista_de_tarefas_id = excluded.lista_de_tarefas_id,
                fase_id = excluded.fase_id,
                projeto_id = excluded.projeto_id,
                nome = excluded.nome,
                concluida = excluded.concluida'''
    cursor.execute(sql, params)
    conn.commit()
    conn.close()


def upsert_comentario(comentario_data, projeto_id):
    """
    Insere ou atualiza um comentário no banco de dados.
    
    Args:
        comentario_data: Dicionário com os dados do comentário da API do Zoho
        projeto_id: ID do projeto ao qual o comentário pertence
    
    Returns:
        str: ID do comentário inserido/atualizado
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Extrai informações do autor
    posted_by = comentario_data.get('posted_by', {})
    autor_zpuid = posted_by.get('zpuid')
    autor_nome = posted_by.get('full_name') or posted_by.get('name', 'Desconhecido')
    autor_email = posted_by.get('email')
    
    params = {
        'id': comentario_data.get('id'),
        'projeto_id': projeto_id,
        'conteudo': comentario_data.get('content', ''),
        'autor_zpuid': autor_zpuid,
        'autor_nome': autor_nome,
        'autor_email': autor_email,
        'data_criacao': comentario_data.get('created_time'),
        'data_modificacao': comentario_data.get('last_modified_time'),
        'adicionado_via': comentario_data.get('added_via', 'UNKNOWN'),
        'full_data_json': json.dumps(comentario_data)
    }
    
    sql = '''
        INSERT INTO comentarios (
            id, projeto_id, conteudo, autor_zpuid, autor_nome, autor_email,
            data_criacao, data_modificacao, adicionado_via, full_data_json
        )
        VALUES (
            :id, :projeto_id, :conteudo, :autor_zpuid, :autor_nome, :autor_email,
            :data_criacao, :data_modificacao, :adicionado_via, :full_data_json
        )
        ON CONFLICT(id) DO UPDATE SET
            conteudo = excluded.conteudo,
            data_modificacao = excluded.data_modificacao,
            full_data_json = excluded.full_data_json
    '''
    
    cursor.execute(sql, params)
    conn.commit()
    conn.close()
    
    # Atualiza a data do último comentário no projeto
    atualizar_data_ultimo_comentario(projeto_id)
    
    return params['id']


def get_comentarios_projeto(projeto_id, limit=None, offset=0):
    """
    Busca comentários de um projeto ordenados por data (mais recentes primeiro).
    
    Args:
        projeto_id: ID do projeto
        limit: Número máximo de comentários a retornar (None = todos)
        offset: Número de comentários a pular (para paginação)
    
    Returns:
        list: Lista de comentários (sqlite3.Row objects)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    sql = '''
        SELECT * FROM comentarios 
        WHERE projeto_id = ? 
        ORDER BY data_criacao DESC
    '''
    
    if limit:
        sql += f' LIMIT {limit} OFFSET {offset}'
    
    cursor.execute(sql, (projeto_id,))
    comentarios = cursor.fetchall()
    conn.close()
    
    return comentarios


def get_ultimo_comentario_projeto(projeto_id):
    """
    Busca o comentário mais recente de um projeto.
    
    Args:
        projeto_id: ID do projeto
    
    Returns:
        sqlite3.Row: Comentário mais recente ou None
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM comentarios 
        WHERE projeto_id = ? 
        ORDER BY data_criacao DESC 
        LIMIT 1
    ''', (projeto_id,))
    
    comentario = cursor.fetchone()
    conn.close()
    
    return comentario


def atualizar_data_ultimo_comentario(projeto_id, data_comentario=None):
    """
    Atualiza a coluna data_ultimo_comentario na tabela projects
    com a data do comentário mais recente.
    
    Args:
        projeto_id: ID do projeto
        data_comentario: Data específica para atualizar. Se None, busca a mais recente.
                        Use string vazia '' para forçar NULL.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Se data_comentario não foi fornecida, busca a mais recente
    if data_comentario is None:
        cursor.execute('''
            SELECT MAX(data_criacao) 
            FROM comentarios 
            WHERE projeto_id = ?
        ''', (projeto_id,))
        
        row = cursor.fetchone()
        data_ultimo = row[0] if row and row[0] else None
    elif data_comentario == '':
        # String vazia significa forçar NULL
        data_ultimo = None
    else:
        # Usa a data fornecida
        data_ultimo = data_comentario
    
    # Atualiza o projeto
    cursor.execute('''
        UPDATE projects 
        SET data_ultimo_comentario = ? 
        WHERE id = ?
    ''', (data_ultimo, projeto_id))
    
    conn.commit()
    conn.close()


def contar_comentarios_projeto(projeto_id):
    """
    Conta o número total de comentários de um projeto.
    
    Args:
        projeto_id: ID do projeto
    
    Returns:
        int: Número de comentários
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT COUNT(*) FROM comentarios 
        WHERE projeto_id = ?
    ''', (projeto_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    return row[0] if row else 0


def limpar_comentarios_projeto(projeto_id):
    """
    Remove todos os comentários de um projeto específico.
    
    Args:
        projeto_id: ID do projeto
    
    Returns:
        int: Número de comentários removidos
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM comentarios WHERE projeto_id = ?', (projeto_id,))
    linhas_afetadas = cursor.rowcount
    
    # Atualiza data_ultimo_comentario para NULL
    cursor.execute('UPDATE projects SET data_ultimo_comentario = NULL WHERE id = ?', (projeto_id,))
    
    conn.commit()
    conn.close()
    
    return linhas_afetadas


def count_open_impediments(projeto_id: str) -> int:
    """Conta tarefas abertas (não concluídas) do projeto na fase de impeditivos.
    Observação: como sincronizamos apenas tarefas da fase de impeditivos,
    basta contar tarefas não concluídas por projeto.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT COUNT(1) FROM tarefas WHERE projeto_id = ? AND concluida = 0',
        (projeto_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return int(row[0] if row and row[0] is not None else 0)


essential_web_tasklist_query = (
    "SELECT lt.id FROM listas_de_tarefas lt "
    "JOIN tarefas t ON t.lista_de_tarefas_id = lt.id "
    "WHERE lt.projeto_id = ? LIMIT 1"
)

def get_any_impediments_tasklist_id(projeto_id: str) -> str | None:
    """Retorna uma tasklist do projeto que possua tarefas (as sincronizadas de impeditivos)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(essential_web_tasklist_query, (projeto_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row and row[0] else None


def _migrate_database(cursor):
    """Executa migrações necessárias no banco de dados."""
    try:
        # Migração 1: Adicionar coluna data_de_onboarding se não existir
        cursor.execute("PRAGMA table_info(projects)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'data_de_onboarding' not in columns:
            cursor.execute("ALTER TABLE projects ADD COLUMN data_de_onboarding TEXT")
            print("Migração: Coluna 'data_de_onboarding' adicionada à tabela projects")
        
        # Migração 2: Adicionar coluna data_mudanca_status se não existir
        if 'data_mudanca_status' not in columns:
            cursor.execute("ALTER TABLE projects ADD COLUMN data_mudanca_status TEXT")
            print("Migração: Coluna 'data_mudanca_status' adicionada à tabela projects")
            # Inicializar com data_criacao para projetos existentes
            cursor.execute("UPDATE projects SET data_mudanca_status = COALESCE(data_inicio, data_criacao) WHERE data_mudanca_status IS NULL")
            print("Migração: Coluna 'data_mudanca_status' inicializada para projetos existentes")
        
        # Migração 3: Adicionar coluna data_homologacao_prevista se não existir
        if 'data_homologacao_prevista' not in columns:
            cursor.execute("ALTER TABLE projects ADD COLUMN data_homologacao_prevista TEXT")
            print("Migração: Coluna 'data_homologacao_prevista' adicionada à tabela projects")
        
        # Migração 4: Adicionar colunas de implantadores se não existirem
        if 'implantador_ris' not in columns:
            cursor.execute("ALTER TABLE projects ADD COLUMN implantador_ris TEXT")
            print("Migração: Coluna 'implantador_ris' adicionada à tabela projects")
        
        if 'implantador_pacs' not in columns:
            cursor.execute("ALTER TABLE projects ADD COLUMN implantador_pacs TEXT")
            print("Migração: Coluna 'implantador_pacs' adicionada à tabela projects")
        
        # Migração 5: Adicionar coluna data_ultimo_comentario se não existir
        if 'data_ultimo_comentario' not in columns:
            cursor.execute("ALTER TABLE projects ADD COLUMN data_ultimo_comentario TEXT")
            print("Migração: Coluna 'data_ultimo_comentario' adicionada à tabela projects")
            
    except Exception as e:
        print(f"Erro durante migração do banco de dados: {e}")


# Inicializa o DB na importação do módulo
init_db()
insert_initial_users()
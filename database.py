import sqlite3
import json
import re
from datetime import datetime, timezone

DB_FILE = 'zoho_cache.db'

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa o banco de dados e cria todas as tabelas do schema."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
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
            if field.get('label_name') == field_name:
                return field.get('value')
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
        importacao_escopo = json.dumps([item['value'] for item in importacoes_list])
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
    params = {
        'id': project_id,
        'nome': project_data.get('name', 'N/A'),
        'cliente': project_data.get('owner_name'),
        'gp': _get_custom_field(project_data, 'GP'),
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
        'data_virada': data_virada, # Campo estruturado
        'data_inicio_oa': data_inicio_oa,
        'status_atual': project_data.get('status', {}).get('name'),
        'dias_na_fase': dias_na_fase_calc,
        'dias_total': dias_total_calc,
        'data_ultima_mudanca': project_data.get('last_modified_time'),
        'link_google': link_google,
        'tags': tags_str,
        'full_data_json': json.dumps(project_data)
    }

    # 4. Executa o SQL
    columns = ', '.join(params.keys())
    placeholders = ', '.join('?' for _ in params)
    update_setters = ', '.join(f'{key} = excluded.{key}' for key in params.keys())

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


# Inicializa o DB na importação do módulo
init_db()
insert_initial_users()
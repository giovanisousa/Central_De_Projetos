# Função utilitária para contar projetos
def count_projects():
    session = Session()
    count = session.query(Project).count()
    session.close()
    return count
import os
import json
import re
from datetime import datetime, timezone
import logging # Import logging
from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.postgresql import insert
from config import SQLALCHEMY_DATABASE_URI, BASE_DIR
import utils # Import local para evitar ciclos em importação de app

logger = logging.getLogger(__name__) # Logger para database.py

# Configuração do SQLAlchemy
Base = declarative_base()
engine = create_engine(SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)

# Função para obter conexão direta ao banco (para queries SQL raw)
def get_db_connection():
    """Retorna uma conexão SQLAlchemy para executar queries SQL diretas."""
    return engine.connect()

# --- Definição dos Modelos SQLAlchemy ---

class Project(Base):
    __tablename__ = 'projects'
    id = Column(String, primary_key=True)
    nome = Column(String, nullable=False)
    cliente = Column(String)
    gp = Column(String)
    produtos_contratados = Column(Text) # JSON string
    tem_importacao = Column(Boolean)
    tem_integracao = Column(Boolean)
    importacao_escopo = Column(Text) # JSON string
    integracao_escopo = Column(Text) # JSON string
    data_inicio = Column(String)
    data_criacao = Column(String)
    data_liberacao_servidor = Column(String)
    data_inicio_implantacao = Column(String)
    data_homologacao = Column(String)
    data_homologacao_prevista = Column(String)
    data_virada = Column(String)
    data_de_virada = Column(String)
    data_inicio_oa = Column(String)
    data_de_inicio_da_oa = Column(String)
    data_de_onboarding = Column(String)
    status_atual = Column(String)
    status_id = Column(String)  # ✅ NOVO: ID do status do Zoho (ex: "2376502000000020119")
    dias_na_fase = Column(String)
    dias_total = Column(String)
    data_ultima_mudanca = Column(String)
    data_mudanca_status = Column(String)
    link_google = Column(String)
    tags = Column(Text) # JSON array string com IDs das tags
    precisa_comentario = Column(Boolean, default=True)
    full_data_json = Column(Text) # JSON string - DEPRECATED, usar colunas normalizadas
    data_ultimo_comentario = Column(String)
    implantador_ris = Column(String)
    implantador_pacs = Column(String)
    implantador_homologacao_ris = Column(String)
    implantador_homologacao_pacs = Column(String)
    implantador_virada_ris = Column(String)
    implantador_virada_pacs = Column(String)

class Fase(Base):
    __tablename__ = 'fases'
    id = Column(String, primary_key=True)
    projeto_id = Column(String, ForeignKey('projects.id'), nullable=False)
    nome = Column(String, nullable=False)
    status = Column(String)
    percentual_conclusao = Column(Integer)

class ListaDeTarefas(Base):
    __tablename__ = 'listas_de_tarefas'
    id = Column(String, primary_key=True)
    fase_id = Column(String, ForeignKey('fases.id'), nullable=False)
    projeto_id = Column(String, ForeignKey('projects.id'), nullable=False)
    nome = Column(String, nullable=False)
    percentual_conclusao = Column(Integer)

class Tarefa(Base):
    __tablename__ = 'tarefas'
    id = Column(String, primary_key=True)
    lista_de_tarefas_id = Column(String, ForeignKey('listas_de_tarefas.id'), nullable=False)
    fase_id = Column(String, ForeignKey('fases.id'), nullable=False)
    projeto_id = Column(String, ForeignKey('projects.id'), nullable=False)
    nome = Column(String, nullable=False)
    concluida = Column(Boolean)

class Comentario(Base):
    __tablename__ = 'comentarios'
    id = Column(String, primary_key=True)
    projeto_id = Column(String, ForeignKey('projects.id'), nullable=False)
    conteudo = Column(Text, nullable=False)
    autor_zpuid = Column(String)
    autor_nome = Column(String)
    autor_email = Column(String)
    data_criacao = Column(String, nullable=False)
    data_modificacao = Column(String)
    adicionado_via = Column(String)
    full_data_json = Column(Text) # JSON string

class Usuario(Base):
    __tablename__ = 'usuarios'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    ativo = Column(Boolean, nullable=False, default=False)

# --- Funções de Interação com o Banco de Dados ---

def init_db():
    """Inicializa o banco de dados e cria todas as tabelas do schema."""
    Base.metadata.create_all(engine)
    logger.info("Banco de dados verificado/inicializado com o schema completo.")

def insert_initial_users():
    """Insere os usuários iniciais no banco de dados se eles não existirem."""
    users_to_insert = [
        {'nome': 'Giovani de Sousa', 'email': 'giovani.sousa@animati.com.br', 'ativo': True},
        {'nome': 'Willian dos Anjos', 'email': 'willian.anjos@animati.com.br', 'ativo': True}
    ]
    
    session = Session()
    try:
        for user_data in users_to_insert:
            existing_user = session.query(Usuario).filter_by(email=user_data['email']).first()
            if not existing_user:
                new_user = Usuario(
                    nome=user_data['nome'],
                    email=user_data['email'],
                    ativo=user_data['ativo']
                )
                session.add(new_user)
                logger.info(f"Usuário '{user_data['nome']}' inserido.")
        session.commit()
    except IntegrityError:
        session.rollback()
        logger.warning("Erro de integridade ao inserir usuários iniciais (talvez já existam).")
    except Exception as e:
        session.rollback()
        logger.error(f"Erro ao inserir usuários iniciais: {e}")
    finally:
        session.close()

def get_user_by_email(email):
    """Busca um usuário pelo email."""
    session = Session()
    try:
        user = session.query(Usuario).filter_by(email=email, ativo=True).first()
        return user
    finally:
        session.close()

def _get_custom_field(project_data, field_name):
    """
    Função auxiliar para buscar valores em campos customizados que não são o foco principal.
    """
    if field_name in project_data:
        return project_data[field_name]
    
    if 'custom_fields' in project_data and isinstance(project_data['custom_fields'], list):
        for field in project_data['custom_fields']:
            if field.get('label_name') == field_name:
                return field.get('value')
            if isinstance(field, dict):
                for key, value in field.items():
                    if key == field_name:
                        return value
    return None

def _formatar_implantadores(implantadores_data):
    """
    Formata dados de implantadores do Zoho.
    """
    if not implantadores_data:
        return None
    
    try:
        nomes = []
        if isinstance(implantadores_data, str):
            implantadores_data = json.loads(implantadores_data)
        
        if isinstance(implantadores_data, dict):
            if 'zpuid' in implantadores_data or 'name' in implantadores_data:
                nome = (
                    implantadores_data.get('full_name') or 
                    implantadores_data.get('name') or
                    f"{implantadores_data.get('first_name', '')} {implantadores_data.get('last_name', '')}".strip() or
                    implantadores_data.get('email', '').split('@')[0]
                )
                if nome:
                    nomes.append(nome)
            else:
                for key, value in implantadores_data.items():
                    if isinstance(value, str) and value.strip():
                        nomes.append(value.strip())
        
        elif isinstance(implantadores_data, list):
            for item in implantadores_data:
                if isinstance(item, dict):
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
                        nome = item.get('name') or item.get('display_name') or item.get('email', '').split('@')[0]
                        if nome:
                            nomes.append(nome)
                elif isinstance(item, str) and item.strip():
                    nomes.append(item.strip())
        
        return ', '.join(nomes) if nomes else None
    
    except Exception as e:
        logger.error(f"Erro ao formatar implantadores: {e}")
        return None

def parse_description(description):
    """
    Analisa a descrição HTML de um projeto para extrair informações estruturadas (fallback para dados legados).
    """
    if not description:
        return {
            "produtos_contratados": None,
            "tem_importacao": False,
            "importacao_escopo": None,
            "tem_integracao": False,
            "integracao_escopo": None,
            "link_google": None,
        }

    produtos = []
    ferramentas_match = re.search(r"Ferramentas Contratadas:.*?<ul>(.*?)</ul>", description, re.DOTALL | re.IGNORECASE)
    if ferramentas_match:
        produtos_raw = re.findall(r"<li>\[\s*X\s*\](.*?)</li>", ferramentas_match.group(1))
        produtos = [re.sub(r"<.*?>", "", p).strip() for p in produtos_raw]

    tem_importacao = True if re.search(r"Haverá importação\?.*?\(X\)\s*Sim", description, re.DOTALL | re.IGNORECASE) else False
    importacao_escopo = None
    if tem_importacao:
        escopo_match = re.search(r"Se Sim, selecione os itens para importação:.*?<ul>(.*?)</ul>", description, re.DOTALL | re.IGNORECASE)
        if escopo_match:
            escopo_raw = re.findall(r"<li>\[\s*X\s*\](.*?)</li>", escopo_match.group(1))
            importacao_escopo = [re.sub(r"<.*?>", "", item).strip() for item in escopo_raw]

    tem_integracao = True if re.search(r"Haverá integração\?.*?\(X\)\s*Sim", description, re.DOTALL | re.IGNORECASE) else False
    integracao_escopo = None
    if tem_integracao:
        escopo_match = re.search(r"Se Sim, selecione as integrações:.*?<ul>(.*?)</ul>", description, re.DOTALL | re.IGNORECASE)
        if escopo_match:
            escopo_raw = re.findall(r"<li>\[\s*X\s*\](.*?)</li>", escopo_match.group(1))
            integracao_escopo = [re.sub(r"<.*?>", "", item).strip() for item in escopo_raw]

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
    """
    session = Session()
    try:
        project_id = project_data.get('id')
        if not project_id:
            return

        desc_data = parse_description(project_data.get("description", ""))

        produtos_str = project_data.get('solucoes_contratadas')
        if produtos_str and isinstance(produtos_str, str):
            produtos_contratados = json.dumps(produtos_str.split('/'))
        else:
            produtos_contratados = desc_data['produtos_contratados']

        tem_importacao_raw = project_data.get('havera_importacao')
        if tem_importacao_raw is not None:
            tem_importacao = True if str(tem_importacao_raw).lower() == 'sim' else False
        else:
            tem_importacao = desc_data['tem_importacao']

        importacoes_list = project_data.get('importacoes')
        if importacoes_list and isinstance(importacoes_list, list):
            valores = [item['value'] for item in importacoes_list]
            valores_corrigidos = [v.replace('Prontuários', 'Prontuário') for v in valores]
            importacao_escopo = json.dumps(valores_corrigidos)
        else:
            importacao_escopo = desc_data['importacao_escopo']

        tem_integracao_raw = project_data.get('havera_integracao')
        if tem_integracao_raw is not None:
            tem_integracao = True if tem_integracao_raw else False
        else:
            tem_integracao = desc_data['tem_integracao']

        integracao_escopo = desc_data['integracao_escopo']
        link_google = project_data.get('link_do_google') or desc_data['link_google']

        # ✅ CORRIGIDO: Salvar tags como JSON array com IDs, não apenas nomes
        tags_list = project_data.get('tags', [])
        if tags_list:
            tags_str = json.dumps(tags_list)  # Salva o JSON completo com IDs
        else:
            tags_str = None

        start_date = project_data.get('start_date') or project_data.get('start_date_string')
        created_time = project_data.get('created_time') or project_data.get('created_time_string')
        data_inicio_implantacao = _get_custom_field(project_data, 'Data Início Implantação')
        data_homologacao = _get_custom_field(project_data, 'Data Homologação')
        data_homologacao_prevista = project_data.get('data_de_termino_original')
        data_virada = project_data.get('data_de_virada')
        data_inicio_oa = _get_custom_field(project_data, 'Data Início OA')

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

        name = project_data.get('name', '')
        parts = name.split(' - ')
        if len(parts) >= 2:
            cliente_formatado = f"{parts[0].strip()} - {parts[1].strip()}"
        else:
            cliente_formatado = name or "Cliente não informado"

        owner = project_data.get('owner', {})
        gp_nome = owner.get('first_name', '')
        gp_sobrenome = owner.get('last_name', '')
        gp_valor = f"{gp_nome} {gp_sobrenome}".strip() if gp_nome or gp_sobrenome else owner.get('name', '') or _get_custom_field(project_data, 'GP')

        implantador_ris_raw = project_data.get('implantador_ris')
        implantador_pacs_raw = project_data.get('implantador_pacs')
        implantador_ris = implantador_ris_raw if isinstance(implantador_ris_raw, str) else (_formatar_implantadores(implantador_ris_raw) if implantador_ris_raw else None)
        implantador_pacs = implantador_pacs_raw if isinstance(implantador_pacs_raw, str) else (_formatar_implantadores(implantador_pacs_raw) if implantador_pacs_raw else None)

        implantador_homologacao_ris_raw = project_data.get('homologacao_ris')
        implantador_homologacao_pacs_raw = project_data.get('homologacao_pacs')
        implantador_homologacao_ris = implantador_homologacao_ris_raw if isinstance(implantador_homologacao_ris_raw, str) else (_formatar_implantadores(implantador_homologacao_ris_raw) if implantador_homologacao_ris_raw else None)
        implantador_homologacao_pacs = implantador_homologacao_pacs_raw if isinstance(implantador_homologacao_pacs_raw, str) else (_formatar_implantadores(implantador_homologacao_pacs_raw) if implantador_homologacao_pacs_raw else None)

        implantador_virada_ris_raw = project_data.get('virada_ris')
        implantador_virada_pacs_raw = project_data.get('virada_pacs')
        implantador_virada_ris = implantador_virada_ris_raw if isinstance(implantador_virada_ris_raw, str) else (_formatar_implantadores(implantador_virada_ris_raw) if implantador_virada_ris_raw else None)
        implantador_virada_pacs = implantador_virada_pacs_raw if isinstance(implantador_virada_pacs_raw, str) else (_formatar_implantadores(implantador_virada_pacs_raw) if implantador_virada_pacs_raw else None)
        
        data_de_virada = _get_custom_field(project_data, 'Data de Virada')
        data_de_inicio_da_oa = _get_custom_field(project_data, 'Data de Início da OA')

        project_obj = {
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
            'data_homologacao_prevista': data_homologacao_prevista,
            'data_virada': data_virada,
            'data_de_virada': data_de_virada,
            'data_de_inicio_da_oa': data_de_inicio_da_oa,
            'data_inicio_oa': data_inicio_oa,
            'data_de_onboarding': _get_custom_field(project_data, 'Data de Onboarding'),
            'status_atual': project_data.get('status', {}).get('name'),
            'status_id': project_data.get('status', {}).get('id'),  # ✅ NOVO: ID do status
            'dias_na_fase': dias_na_fase_calc,
            'dias_total': dias_total_calc,
            'data_ultima_mudanca': project_data.get('last_modified_time'),
            'data_mudanca_status': None, # Será preenchido apenas na movimentação manual
            'link_google': link_google,
            'tags': tags_str,
            'implantador_ris': implantador_ris,
            'implantador_pacs': implantador_pacs,
            'implantador_homologacao_ris': implantador_homologacao_ris,
            'implantador_homologacao_pacs': implantador_homologacao_pacs,
            'implantador_virada_ris': implantador_virada_ris,
            'implantador_virada_pacs': implantador_virada_pacs,
            'precisa_comentario': True,
            'full_data_json': json.dumps(project_data)
        }

        # Usar insert.on_conflict_do_update para UPSERT
        stmt = insert(Project).values(**project_obj)
        on_conflict_stmt = stmt.on_conflict_do_update(
            index_elements=[Project.id],
            set_={
                k: v for k, v in project_obj.items() if k != 'id' and k != 'data_mudanca_status'
            }
        )
        # Lógica para data_mudanca_status: COALESCE(projects.data_mudanca_status, excluded.data_mudanca_status)
        # Isso é um pouco mais complexo com on_conflict_do_update diretamente no set,
        # então faremos uma atualização separada se necessário ou garantiremos que o valor inicial seja None
        # e só seja setado manualmente. Por enquanto, o comportamento é que ele será atualizado se o valor
        # no project_obj não for None. Se for None, ele não será alterado pelo update.
        # Para replicar COALESCE, precisaríamos de uma expressão mais complexa no set,
        # mas para a maioria dos casos, o comportamento atual é aceitável se data_mudanca_status
        # só for setado explicitamente.

        session.execute(on_conflict_stmt)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Erro ao inserir/atualizar projeto: {e}")
    finally:
        session.close()

def get_project_by_id(project_id):
    """Busca um projeto pelo seu ID."""
    session = Session()
    try:
        project = session.query(Project).filter_by(id=project_id).first()
        return project
    finally:
        session.close()

def get_last_sync_time():
    """Retorna o 'last_modified_time' mais recente do banco de dados."""
    session = Session()
    try:
        last_sync = session.query(Project.data_ultima_mudanca).order_by(Project.data_ultima_mudanca.desc()).first()
        return last_sync[0] if last_sync and last_sync[0] else '2000-01-01T00:00:00Z'
    finally:
        session.close()

def upsert_fase(fase_data, projeto_id):
    """Insere ou atualiza uma fase (milestone) no banco de dados."""
    session = Session()
    try:
        fase_id = fase_data.get('id')
        stmt = insert(Fase).values(
            id=fase_id,
            projeto_id=projeto_id,
            nome=fase_data.get('name'),
            status=fase_data.get('status', {}).get('name'),
            percentual_conclusao=fase_data.get('completion_percent')
        )
        on_conflict_stmt = stmt.on_conflict_do_update(
            index_elements=[Fase.id],
            set_=dict(
                projeto_id=projeto_id,
                nome=fase_data.get('name'),
                status=fase_data.get('status', {}).get('name'),
                percentual_conclusao=fase_data.get('completion_percent')
            )
        )
        session.execute(on_conflict_stmt)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Erro ao inserir/atualizar fase: {e}")
    finally:
        session.close()

def upsert_lista_de_tarefas(lista_data, projeto_id):
    """Insere ou atualiza uma lista de tarefas no banco de dados."""
    session = Session()
    try:
        lista_id = lista_data.get('id')
        stmt = insert(ListaDeTarefas).values(
            id=lista_id,
            fase_id=lista_data.get('milestone', {}).get('id'),
            projeto_id=projeto_id,
            nome=lista_data.get('name'),
            percentual_conclusao=lista_data.get('completion_percent')
        )
        on_conflict_stmt = stmt.on_conflict_do_update(
            index_elements=[ListaDeTarefas.id],
            set_=dict(
                fase_id=lista_data.get('milestone', {}).get('id'),
                projeto_id=projeto_id,
                nome=lista_data.get('name'),
                percentual_conclusao=lista_data.get('completion_percent')
            )
        )
        session.execute(on_conflict_stmt)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Erro ao inserir/atualizar lista de tarefas: {e}")
    finally:
        session.close()

def upsert_tarefa(tarefa_data, lista_de_tarefas_id, fase_id, projeto_id):
    """Insere ou atualiza uma tarefa no banco de dados."""
    session = Session()
    try:
        tarefa_id = tarefa_data.get('id')
        stmt = insert(Tarefa).values(
            id=tarefa_id,
            lista_de_tarefas_id=lista_de_tarefas_id,
            fase_id=fase_id,
            projeto_id=projeto_id,
            nome=tarefa_data.get('name'),
            concluida=True if tarefa_data.get('completed') else False
        )
        on_conflict_stmt = stmt.on_conflict_do_update(
            index_elements=[Tarefa.id],
            set_=dict(
                lista_de_tarefas_id=lista_de_tarefas_id,
                fase_id=fase_id,
                projeto_id=projeto_id,
                nome=tarefa_data.get('name'),
                concluida=True if tarefa_data.get('completed') else False
            )
        )
        session.execute(on_conflict_stmt)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Erro ao inserir/atualizar tarefa: {e}")
    finally:
        session.close()

def upsert_comentario(comentario_data, projeto_id):
    """
    Insere ou atualiza um comentário no banco de dados.
    """
    session = Session()
    try:
        comentario_id = comentario_data.get('id')
        posted_by = comentario_data.get('posted_by', {})
        autor_zpuid = posted_by.get('zpuid')
        autor_nome = posted_by.get('full_name') or posted_by.get('name', 'Desconhecido')
        autor_email = posted_by.get('email')
        
        stmt = insert(Comentario).values(
            id=comentario_id,
            projeto_id=projeto_id,
            conteudo=comentario_data.get('content', ''),
            autor_zpuid=autor_zpuid,
            autor_nome=autor_nome,
            autor_email=autor_email,
            data_criacao=comentario_data.get('created_time'),
            data_modificacao=comentario_data.get('last_modified_time'),
            adicionado_via=comentario_data.get('added_via', 'UNKNOWN'),
            full_data_json=json.dumps(comentario_data)
        )
        on_conflict_stmt = stmt.on_conflict_do_update(
            index_elements=[Comentario.id],
            set_=dict(
                conteudo=comentario_data.get('content', ''),
                data_modificacao=comentario_data.get('last_modified_time'),
                full_data_json=json.dumps(comentario_data)
            )
        )
        session.execute(on_conflict_stmt)
        session.commit()
        
        atualizar_data_ultimo_comentario(projeto_id)
        
        return comentario_id
    except Exception as e:
        session.rollback()
        logger.error(f"Erro ao inserir/atualizar comentário: {e}")
    finally:
        session.close()

def get_comentarios_projeto(projeto_id, limit=None, offset=0):
    """
    Busca comentários de um projeto ordenados por data (mais recentes primeiro).
    """
    session = Session()
    try:
        query = session.query(Comentario).filter_by(projeto_id=projeto_id).order_by(Comentario.data_criacao.desc())
        if limit:
            query = query.limit(limit).offset(offset)
        return query.all()
    finally:
        session.close()

def get_ultimo_comentario_projeto(projeto_id):
    """
    Busca o comentário mais recente de um projeto.
    """
    session = Session()
    try:
        comentario = session.query(Comentario).filter_by(projeto_id=projeto_id).order_by(Comentario.data_criacao.desc()).first()
        return comentario
    finally:
        session.close()

def atualizar_data_ultimo_comentario(projeto_id, data_comentario=None):
    """
    Atualiza a coluna data_ultimo_comentario na tabela projects
    com a data do comentário mais recente.
    """
    session = Session()
    try:
        if data_comentario is None:
            latest_comment_date = session.query(Comentario.data_criacao).filter_by(projeto_id=projeto_id).order_by(Comentario.data_criacao.desc()).first()
            data_ultimo = latest_comment_date[0] if latest_comment_date else None
        elif data_comentario == '':
            data_ultimo = None
        else:
            data_ultimo = data_comentario
        
        session.query(Project).filter_by(id=projeto_id).update(
            {Project.data_ultimo_comentario: data_ultimo}
        )
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Erro ao atualizar data do último comentário: {e}")
    finally:
        session.close()

def contar_comentarios_projeto(projeto_id):
    """
    Conta o número total de comentários de um projeto.
    """
    session = Session()
    try:
        count = session.query(Comentario).filter_by(projeto_id=projeto_id).count()
        return count
    finally:
        session.close()

def limpar_comentarios_projeto(projeto_id):
    """
    Remove todos os comentários de um projeto específico.
    """
    session = Session()
    try:
        deleted_count = session.query(Comentario).filter_by(projeto_id=projeto_id).delete()
        session.query(Project).filter_by(id=projeto_id).update(
            {Project.data_ultimo_comentario: None}
        )
        session.commit()
        return deleted_count
    except Exception as e:
        session.rollback()
        logger.error(f"Erro ao limpar comentários do projeto: {e}")
    finally:
        session.close()

def count_open_impediments(projeto_id: str) -> int:
    """Conta tarefas abertas (não concluídas) do projeto na fase de impeditivos."""
    session = Session()
    try:
        count = session.query(Tarefa).filter_by(projeto_id=projeto_id, concluida=False).count()
        return count
    finally:
        session.close()

def get_any_impediments_tasklist_id(projeto_id: str) -> str | None:
    """Retorna uma tasklist do projeto que possua tarefas (as sincronizadas de impeditivos)."""
    session = Session()
    try:
        tasklist = session.query(ListaDeTarefas.id).join(Tarefa).filter(
            ListaDeTarefas.projeto_id == projeto_id
        ).first()
        return tasklist[0] if tasklist else None
    finally:
        session.close()

# Inicializa o DB na importação do módulo
init_db()
insert_initial_users()
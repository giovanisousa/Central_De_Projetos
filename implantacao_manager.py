"""
Módulo para gerenciar implantação: adicionar usuários ao projeto e atribuir tarefas
"""

import json
import logging
import requests
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class ImplantacaoManager:
    """Gerencia adição de implantadores e atribuição de tarefas"""
    
    def __init__(self, portal_id: str, access_token: str):
        """
        Inicializa o gerenciador de implantação
        
        Args:
            portal_id: ID do portal Zoho
            access_token: Token de acesso OAuth
        """
        self.portal_id = portal_id
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Zoho-oauthtoken {access_token}"
        }
        self.base_url = "https://projectsapi.zoho.com/restapi"
    
    def carregar_equipe_implantacao(self) -> Dict[str, List[Dict]]:
        """
        Carrega a equipe de implantação do arquivo JSON
        
        Returns:
            Dict com as equipes de RIS e PACS
        """
        try:
            with open('equipe_implantacao_classificada.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar equipe de implantação: {e}")
            return {"Implantação RIS": [], "Implantação PACS": []}
    
    def carregar_tarefas(self, tipo: str, arquivo_customizado: str = None) -> List[str]:
        """
        Carrega as tarefas do arquivo JSON
        
        Args:
            tipo: 'RIS' ou 'PACS'
            arquivo_customizado: Caminho para arquivo JSON customizado (opcional)
        
        Returns:
            Lista de nomes de tarefas
        """
        if arquivo_customizado:
            arquivo = arquivo_customizado
        else:
            arquivo = f'tarefas_{tipo.lower()}.json'
        
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar tarefas de {arquivo}: {e}")
            return []
    
    def adicionar_usuario_ao_projeto(
        self, 
        project_id: str, 
        email: str, 
        role: str = "employee"
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Adiciona um usuário ao projeto no Zoho
        
        Args:
            project_id: ID do projeto
            email: Email do usuário
            role: Role do usuário (employee, manager, etc)
        
        Returns:
            Tupla (sucesso, dados_usuario, mensagem_erro)
        """
        url = f"{self.base_url}/portal/{self.portal_id}/projects/{project_id}/users/"
        
        payload = {
            "email": email,
            "role": role
        }
        
        try:
            response = requests.post(url, headers=self.headers, data=payload, timeout=30)
            
            if response.status_code in [200, 201]:
                data = response.json()
                logger.info(f"✅ Usuário {email} adicionado ao projeto {project_id}")
                return True, data, None
            
            elif response.status_code == 400:
                # Usuário pode já estar no projeto
                error_msg = response.text
                if "already" in error_msg.lower() or "exist" in error_msg.lower():
                    logger.info(f"ℹ️  Usuário {email} já está no projeto {project_id}")
                    return True, None, "Usuário já está no projeto"
                else:
                    logger.warning(f"⚠️  Erro 400 ao adicionar {email}: {error_msg}")
                    return False, None, error_msg
            
            else:
                error_msg = f"Status {response.status_code}: {response.text}"
                logger.error(f"❌ Erro ao adicionar usuário {email}: {error_msg}")
                return False, None, error_msg
                
        except Exception as e:
            error_msg = f"Exceção: {str(e)}"
            logger.error(f"❌ Erro ao adicionar usuário {email}: {error_msg}")
            return False, None, error_msg
    
    def listar_tarefas_projeto(self, project_id: str) -> List[Dict]:
        """
        Lista TODAS as tarefas do projeto com paginação otimizada
        Usa apenas page/per_page que é a estratégia mais eficiente
        
        Args:
            project_id: ID do projeto
        
        Returns:
            Lista de tarefas (todas as páginas)
        """
        tasks_by_id = {}  # Deduplicação por ID
        base_url = f"https://projectsapi.zoho.com/api/v3/portal/{self.portal_id}/projects/{project_id}/tasks"
        
        # Headers v3
        headers_v3 = {
            "Authorization": f"Zoho-oauthtoken {self.access_token}",
            "Accept": "application/json"
        }
        
        try:
            print(f"[DEBUG][LISTAR_TAREFAS] Buscando tarefas do projeto {project_id}...")
            
            # Estratégia otimizada: page/per_page (mais eficiente - retorna 200 tarefas por página)
            page = 1
            while page <= 10:  # Máximo 10 páginas (2000 tarefas)
                url = f"{base_url}?page={page}&per_page=200&status=all"
                
                try:
                    response = requests.get(url, headers=headers_v3, timeout=15)
                    
                    if response.status_code in (200, 201):
                        data = response.json() or {}
                        tasks = data.get('tasks', []) if isinstance(data, dict) else []
                        
                        if not tasks:
                            print(f"[DEBUG][LISTAR_TAREFAS] Sem mais tarefas na página {page}")
                            break  # Não há mais tarefas
                        
                        print(f"[DEBUG][LISTAR_TAREFAS] Página {page}: {len(tasks)} tarefas")
                        
                        # Adicionar tarefas com deduplicação
                        for t in tasks:
                            tid = t.get('id')
                            if tid and tid not in tasks_by_id:
                                tasks_by_id[tid] = t
                        
                        # Se retornou menos que 200, é a última página
                        if len(tasks) < 200:
                            break
                        
                        page += 1
                    else:
                        print(f"[DEBUG][LISTAR_TAREFAS] Status {response.status_code} na página {page}")
                        break
                        
                except Exception as e:
                    print(f"[DEBUG][LISTAR_TAREFAS] Erro na página {page}: {e}")
                    break
            
            total_tasks = len(tasks_by_id)
            print(f"[DEBUG][LISTAR_TAREFAS] ✅ Total de {total_tasks} tarefas únicas encontradas")
            logger.info(f"📋 {total_tasks} tarefas encontradas no projeto {project_id}")
            
            return list(tasks_by_id.values())
            
        except Exception as e:
            logger.error(f"❌ Erro ao listar tarefas: {e}")
            return []
    
    def atribuir_tarefa(
        self, 
        project_id: str, 
        task_id: str, 
        user_ids: List[str]
    ) -> Tuple[bool, Optional[str]]:
        """
        Atribui uma tarefa para um ou mais usuários usando REST API do Zoho
        
        Args:
            project_id: ID do projeto
            task_id: ID da tarefa
            user_ids: Lista de IDs de usuários (zpuid)
        
        Returns:
            Tupla (sucesso, mensagem_erro)
        """
        # URL da REST API (base_url já contém /restapi)
        url = f"{self.base_url}/portal/{self.portal_id}/projects/{project_id}/tasks/{task_id}/"
        
        # Para múltiplos usuários, usar o formato JSON da API v3 com owners_and_work
        if len(user_ids) > 1:
            # Formato documentado: owners_and_work com estrutura add
            owners_and_work = {
                "owners": {
                    "add": [{"zpuid": zpuid} for zpuid in user_ids]
                }
            }
            payload = {"owners_and_work": json.dumps(owners_and_work)}
        else:
            # Para um único usuário, usar person_responsible (mais simples e confiável)
            payload = {"person_responsible": user_ids[0]}
        
        try:
            # Usar headers REST (Bearer token, não Zoho-oauthtoken)
            headers_rest = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.post(url, headers=headers_rest, data=payload, timeout=30)
            
            if response.status_code == 200:
                return True, None
            
            elif response.status_code == 403:
                # Erro 403: Restrição de time (TEAM_ASSOCIATE_RESTRICTION)
                logger.warning(f"⚠️  Tarefa {task_id}: Restrição de time")
                return False, "TEAM_RESTRICTION"
            
            else:
                error_msg = f"Status {response.status_code}"
                logger.error(f"❌ Erro ao atribuir tarefa {task_id}: {error_msg}")
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Exceção: {str(e)}"
            logger.error(f"❌ Erro ao atribuir tarefa {task_id}: {error_msg}")
            import traceback
            traceback.print_exc()
            return False, error_msg
    
    def normalizar_nome_tarefa(self, nome: str) -> str:
        """
        Normaliza nome de tarefa para comparação
        Remove prefixos numéricos (ex: "01.05 - "), acentos, pontuação e converte para minúsculas
        
        Args:
            nome: Nome da tarefa
        
        Returns:
            Nome normalizado
        """
        import unicodedata
        import re
        
        # Remove prefixos numéricos do tipo "01.05 - ", "309 - ", etc
        nome = re.sub(r'^\s*\d+(?:\.\d+)*\s*-\s*', '', nome)
        
        # Remove acentos
        nome = unicodedata.normalize('NFD', nome)
        nome = ''.join(char for char in nome if unicodedata.category(char) != 'Mn')
        
        # Remove pontuação e espaços extras
        nome = ''.join(char if char.isalnum() or char.isspace() else ' ' for char in nome)
        
        # Converte para minúsculas e remove espaços duplicados
        nome = ' '.join(nome.lower().split())
        
        return nome
    
    def encontrar_tarefa_por_nome(
        self, 
        tarefas_projeto: List[Dict], 
        nome_tarefa: str
    ) -> Optional[Dict]:
        """
        Encontra uma tarefa no projeto pelo nome (fuzzy match)
        
        Args:
            tarefas_projeto: Lista de tarefas do projeto
            nome_tarefa: Nome da tarefa a procurar
        
        Returns:
            Dicionário da tarefa ou None se não encontrada
        """
        nome_normalizado = self.normalizar_nome_tarefa(nome_tarefa)
        
        for tarefa in tarefas_projeto:
            nome_tarefa_projeto = self.normalizar_nome_tarefa(tarefa.get('name', ''))
            
            # Match exato
            if nome_normalizado == nome_tarefa_projeto:
                return tarefa
            
            # Match parcial (contém)
            if nome_normalizado in nome_tarefa_projeto or nome_tarefa_projeto in nome_normalizado:
                return tarefa
        
        return None
    
    def _preparar_payload_implantadores(self, usuarios_adicionados: List[Dict]) -> Dict:
        """
        Prepara o payload para atualizar os custom fields de implantadores no Zoho.
        
        Formato correto conforme documentação do Zoho:
        { "zpuid": "123454321" }
        
        Args:
            usuarios_adicionados: Lista de usuários com zpuid e nome
        
        Returns:
            Dicionário com zpuid no formato esperado pelo Zoho
        """
        if not usuarios_adicionados:
            return None
        
        # Pega o primeiro implantador
        primeiro_usuario = usuarios_adicionados[0]
        zpuid = primeiro_usuario.get('zpuid')
        
        if not zpuid:
            return None
        
        # Formato: { "zpuid": "123454321" }
        return {"zpuid": zpuid}
    
    def atualizar_custom_fields_implantadores(
        self, 
        project_id: str,
        implantador_ris: str = None,
        implantador_pacs: str = None
    ) -> bool:
        """
        Atualiza os custom fields de implantadores no Zoho.
        
        Segue o mesmo padrão de api.py (linha 272-283) e dryrun_zoho_payload.py (linha 147):
        - Campos customizados enviados em custom_fields
        - Campos também copiados para o nível raiz do payload
        
        Args:
            project_id: ID do projeto
            implantador_ris: Nome completo do implantador RIS (string)
            implantador_pacs: Nome completo do implantador PACS (string)
        
        Returns:
            True se sucesso, False caso contrário
        """
        if not implantador_ris and not implantador_pacs:
            logger.warning(f"⚠️  Nenhum implantador fornecido para atualizar")
            return False
        
        # API v3
        url = f"https://projectsapi.zoho.com/api/v3/portal/{self.portal_id}/projects/{project_id}"
        headers = {
            "Authorization": f"Zoho-oauthtoken {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        # Monta custom_fields
        custom_fields = {}
        if implantador_ris:
            custom_fields["Implantador RIS"] = implantador_ris
        if implantador_pacs:
            custom_fields["Implantador PACS"] = implantador_pacs
        
        # Payload seguindo o padrão de criação de projeto
        payload = {
            "custom_fields": custom_fields
        }
        
        # Adiciona campos também no nível raiz (igual dryrun_zoho_payload.py linha 147)
        payload.update(custom_fields)
        
        logger.info(f"📤 Enviando payload com implantadores: {payload}")
        
        try:
            response = requests.patch(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Implantadores atualizados com sucesso")
                return True
            else:
                logger.error(f"❌ Falha ao atualizar implantadores: {response.status_code} - {response.text[:500]}")
                return False
        
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar implantadores: {e}")
            return False
    
    def agendar_implantacao(
        self, 
        project_id: str, 
        tipo_projeto: str
    ) -> Dict:
        """
        Executa o agendamento de implantação completo:
        1. Adiciona implantadores ao projeto
        2. Atribui tarefas aos implantadores
        3. Atualiza custom fields no Zoho com os implantadores
        
        Args:
            project_id: ID do projeto
            tipo_projeto: 'RIS' ou 'PACS'
        
        Returns:
            Dicionário com resultado da operação
        """
        resultado = {
            "sucesso": False,
            "usuarios_adicionados": [],
            "usuarios_falharam": [],
            "tarefas_atribuidas": [],
            "tarefas_nao_encontradas": [],
            "tarefas_falharam": [],
            "custom_fields_atualizados": False,
            "mensagem": ""
        }
        
        try:
            # 1. Carregar equipe de implantação
            equipe = self.carregar_equipe_implantacao()
            chave_equipe = f"Implantação {tipo_projeto}"
            
            if chave_equipe not in equipe:
                resultado["mensagem"] = f"Tipo de projeto inválido: {tipo_projeto}"
                return resultado
            
            implantadores = equipe[chave_equipe]
            logger.info(f"🚀 Iniciando agendamento de implantação {tipo_projeto} para projeto {project_id}")
            logger.info(f"👥 {len(implantadores)} implantadores serão adicionados")
            
            # 2. Adicionar implantadores ao projeto
            usuarios_adicionados_ids = []
            
            for implantador in implantadores:
                email = implantador.get('email')
                zpuid = implantador.get('zpuid')
                nome = implantador.get('name')
                
                if not email or not zpuid:
                    logger.warning(f"⚠️  Implantador sem email ou zpuid: {implantador}")
                    continue
                
                sucesso, dados, erro = self.adicionar_usuario_ao_projeto(project_id, email)
                
                if sucesso:
                    resultado["usuarios_adicionados"].append({
                        "nome": nome,
                        "email": email,
                        "zpuid": zpuid
                    })
                    usuarios_adicionados_ids.append(zpuid)
                else:
                    resultado["usuarios_falharam"].append({
                        "nome": nome,
                        "email": email,
                        "erro": erro
                    })
            
            logger.info(f"✅ {len(resultado['usuarios_adicionados'])} usuários adicionados com sucesso")
            
            if resultado["usuarios_falharam"]:
                logger.warning(f"⚠️  {len(resultado['usuarios_falharam'])} usuários falharam")
            
            # 3. Atualizar custom fields no Zoho com os implantadores
            if resultado["usuarios_adicionados"]:
                # Pega o nome completo do primeiro usuário adicionado
                nome_implantador = resultado["usuarios_adicionados"][0]["nome"]
                
                # Determina qual campo atualizar baseado no tipo
                kwargs = {}
                if tipo_projeto.upper() == "RIS":
                    kwargs["implantador_ris"] = nome_implantador
                elif tipo_projeto.upper() == "PACS":
                    kwargs["implantador_pacs"] = nome_implantador
                
                if kwargs:
                    sucesso_cf = self.atualizar_custom_fields_implantadores(
                        project_id,
                        **kwargs
                    )
                    
                    resultado["custom_fields_atualizados"] = sucesso_cf
                    
                    if sucesso_cf:
                        logger.info(f"✅ Implantador '{nome_implantador}' atualizado no Zoho")
                    else:
                        logger.warning(f"⚠️  Falha ao atualizar implantador no Zoho")
                else:
                    logger.warning(f"⚠️  Tipo de projeto '{tipo_projeto}' inválido")
            
            # 4. Carregar tarefas do tipo de projeto
            tarefas_para_atribuir = self.carregar_tarefas(tipo_projeto)
            logger.info(f"📋 {len(tarefas_para_atribuir)} tarefas para atribuir")
            
            # 5. Listar tarefas do projeto
            tarefas_projeto = self.listar_tarefas_projeto(project_id)
            
            if not tarefas_projeto:
                resultado["mensagem"] = "Não foi possível carregar as tarefas do projeto"
                return resultado
            
            # 6. Atribuir tarefas aos implantadores
            for nome_tarefa in tarefas_para_atribuir:
                # Encontrar tarefa no projeto
                tarefa = self.encontrar_tarefa_por_nome(tarefas_projeto, nome_tarefa)
                
                if not tarefa:
                    resultado["tarefas_nao_encontradas"].append(nome_tarefa)
                    logger.warning(f"⚠️  Tarefa não encontrada no projeto: {nome_tarefa}")
                    continue
                
                task_id = tarefa.get('id')
                task_name = tarefa.get('name')
                
                # Atribuir para todos os implantadores adicionados
                if usuarios_adicionados_ids:
                    sucesso, erro = self.atribuir_tarefa(
                        project_id, 
                        task_id, 
                        usuarios_adicionados_ids
                    )
                    
                    if sucesso:
                        resultado["tarefas_atribuidas"].append({
                            "id": task_id,
                            "nome": task_name,
                            "atribuidos": len(usuarios_adicionados_ids)
                        })
                    else:
                        resultado["tarefas_falharam"].append({
                            "nome": task_name,
                            "erro": erro
                        })
            
            # 7. Resumo
            logger.info(f"✅ {len(resultado['tarefas_atribuidas'])} tarefas atribuídas com sucesso")
            
            if resultado["tarefas_nao_encontradas"]:
                logger.warning(f"⚠️  {len(resultado['tarefas_nao_encontradas'])} tarefas não encontradas")
            
            if resultado["tarefas_falharam"]:
                logger.warning(f"⚠️  {len(resultado['tarefas_falharam'])} tarefas falharam na atribuição")
            
            resultado["sucesso"] = True
            resultado["mensagem"] = (
                f"Implantação agendada! "
                f"{len(resultado['usuarios_adicionados'])} usuários adicionados, "
                f"{len(resultado['tarefas_atribuidas'])} tarefas atribuídas"
            )
            
        except Exception as e:
            logger.error(f"❌ Erro ao agendar implantação: {e}")
            resultado["mensagem"] = f"Erro ao agendar implantação: {str(e)}"
        
        return resultado


def agendar_implantacao_simplificado(
    project_id: str, 
    tipo_projeto: str, 
    access_token: str,
    portal_id: str = "868230290"
) -> Dict:
    """
    Função simplificada para agendar implantação
    
    Args:
        project_id: ID do projeto
        tipo_projeto: 'RIS' ou 'PACS'
        access_token: Token de acesso OAuth
        portal_id: ID do portal (padrão: 868230290)
    
    Returns:
        Dicionário com resultado
    """
    manager = ImplantacaoManager(portal_id, access_token)
    return manager.agendar_implantacao(project_id, tipo_projeto)


def adicionar_implantador_e_atribuir_tarefas(
    project_id: str,
    nome_implantador: str,
    tipo_projeto: str,
    access_token: str,
    portal_id: str = "868230290",
    arquivo_tarefas: str = None
) -> Dict:
    """
    Adiciona UM implantador específico ao projeto e atribui tarefas correspondentes
    
    Args:
        project_id: ID do projeto
        nome_implantador: Nome do implantador (ex: "Pablo Pyerri Ferreira da Costa")
        tipo_projeto: 'RIS' ou 'PACS'
        access_token: Token de acesso OAuth
        portal_id: ID do portal (padrão: 868230290)
        arquivo_tarefas: Arquivo JSON customizado com lista de tarefas (opcional)
    
    Returns:
        Dicionário com resultado da operação
    """
    resultado = {
        "sucesso": False,
        "usuario_adicionado": None,
        "tarefas_atribuidas": [],
        "tarefas_nao_encontradas": [],
        "tarefas_falharam": [],
        "mensagem": ""
    }
    
    try:
        manager = ImplantacaoManager(portal_id, access_token)
        
        # LOG: Início do processo
        print(f"[DEBUG][ADICIONAR_IMPLANTADOR] ========== INÍCIO ==========")
        print(f"[DEBUG][ADICIONAR_IMPLANTADOR] Projeto: {project_id}")
        print(f"[DEBUG][ADICIONAR_IMPLANTADOR] Nome: {nome_implantador}")
        print(f"[DEBUG][ADICIONAR_IMPLANTADOR] Tipo: {tipo_projeto}")
        
        # 1. Carregar equipe de implantação
        equipe = manager.carregar_equipe_implantacao()
        chave_equipe = f"Implantação {tipo_projeto}"
        
        # LOG: Equipe carregada
        if chave_equipe in equipe:
            print(f"[DEBUG][ADICIONAR_IMPLANTADOR] Equipe '{chave_equipe}': {len(equipe[chave_equipe])} membros")
        else:
            print(f"[DEBUG][ADICIONAR_IMPLANTADOR] ❌ Equipe '{chave_equipe}' não encontrada!")
        
        if chave_equipe not in equipe:
            resultado["mensagem"] = f"Tipo de projeto inválido: {tipo_projeto}"
            return resultado
        
        implantadores = equipe[chave_equipe]
        
        # 2. Encontrar o implantador pelo nome
        implantador_encontrado = None
        
        # Normalizar nome para busca (remover acentos, case-insensitive)
        nome_normalizado = manager.normalizar_nome_tarefa(nome_implantador)
        
        # LOG: Busca do implantador
        print(f"[DEBUG][ADICIONAR_IMPLANTADOR] Buscando: '{nome_normalizado}'")
        print(f"[DEBUG][ADICIONAR_IMPLANTADOR] Implantadores disponíveis:")
        for idx, imp in enumerate(implantadores, 1):
            print(f"[DEBUG][ADICIONAR_IMPLANTADOR]   {idx}. {imp.get('name')} ({imp.get('email')})")
        
        for implantador in implantadores:
            nome_impl_normalizado = manager.normalizar_nome_tarefa(implantador.get('name', ''))
            
            # Match exato ou parcial
            if nome_normalizado in nome_impl_normalizado or nome_impl_normalizado in nome_normalizado:
                implantador_encontrado = implantador
                print(f"[DEBUG][ADICIONAR_IMPLANTADOR] ✅ Encontrado: {implantador.get('name')}")
                break
        
        if not implantador_encontrado:
            print(f"[DEBUG][ADICIONAR_IMPLANTADOR] ❌ Implantador não encontrado!")
            resultado["mensagem"] = f"Implantador '{nome_implantador}' não encontrado na equipe {tipo_projeto}"
            logger.warning(f"Implantador não encontrado: {nome_implantador}")
            return resultado
        
        email = implantador_encontrado.get('email')
        zpuid = implantador_encontrado.get('zpuid')
        nome = implantador_encontrado.get('name')
        
        # LOG: Dados do implantador
        print(f"[DEBUG][ADICIONAR_IMPLANTADOR] Email: {email}")
        print(f"[DEBUG][ADICIONAR_IMPLANTADOR] ZPUID: {zpuid}")
        print(f"[DEBUG][ADICIONAR_IMPLANTADOR] Nome completo: {nome}")
        
        if not email or not zpuid:
            resultado["mensagem"] = f"Implantador {nome} sem email ou zpuid"
            return resultado
        
        logger.info(f"🚀 Adicionando implantador {nome} ({email}) ao projeto {project_id}")
        
        # 3. Adicionar implantador ao projeto
        sucesso, dados, erro = manager.adicionar_usuario_ao_projeto(project_id, email)
        
        if not sucesso:
            resultado["mensagem"] = f"Falha ao adicionar {nome}: {erro}"
            return resultado
        
        resultado["usuario_adicionado"] = {
            "nome": nome,
            "email": email,
            "zpuid": zpuid
        }
        
        logger.info(f"✅ {nome} adicionado com sucesso")
        
        # 4. Carregar tarefas do tipo de projeto
        tarefas_para_atribuir = manager.carregar_tarefas(tipo_projeto, arquivo_customizado=arquivo_tarefas)
        logger.info(f"📋 {len(tarefas_para_atribuir)} tarefas para atribuir")
        
        # LOG: Lista de tarefas
        print(f"[DEBUG][ADICIONAR_IMPLANTADOR] Tarefas para atribuir:")
        for idx, tarefa in enumerate(tarefas_para_atribuir, 1):
            print(f"[DEBUG][ADICIONAR_IMPLANTADOR]   {idx}. {tarefa}")
        
        # 5. Listar tarefas do projeto
        tarefas_projeto = manager.listar_tarefas_projeto(project_id)
        
        # LOG: Tarefas do projeto
        print(f"[DEBUG][ADICIONAR_IMPLANTADOR] Tarefas encontradas no projeto: {len(tarefas_projeto)}")
        
        if not tarefas_projeto:
            resultado["mensagem"] = f"{nome} adicionado, mas não foi possível carregar tarefas do projeto"
            resultado["sucesso"] = True  # Usuário foi adicionado com sucesso
            return resultado
        
        # 6. Atribuir tarefas ao implantador
        tarefas_atribuidas_count = 0
        for nome_tarefa in tarefas_para_atribuir:
            # Encontrar tarefa no projeto
            tarefa = manager.encontrar_tarefa_por_nome(tarefas_projeto, nome_tarefa)
            
            if not tarefa:
                resultado["tarefas_nao_encontradas"].append(nome_tarefa)
                continue
            
            task_id = tarefa.get('id')
            task_name = tarefa.get('name')
            
            # Atribuir para o implantador
            sucesso_tarefa, erro_tarefa = manager.atribuir_tarefa(
                project_id, 
                task_id, 
                [zpuid]
            )
            
            if sucesso_tarefa:
                resultado["tarefas_atribuidas"].append({
                    "id": task_id,
                    "nome": task_name
                })
                tarefas_atribuidas_count += 1
                # Log a cada 10 tarefas para acompanhamento
                if tarefas_atribuidas_count % 10 == 0:
                    logger.info(f"📊 Progresso: {tarefas_atribuidas_count} tarefas atribuídas...")
            else:
                resultado["tarefas_falharam"].append({
                    "nome": task_name,
                    "erro": erro_tarefa
                })
        
        # 7. Resumo
        logger.info(f"✅ {len(resultado['tarefas_atribuidas'])} tarefas atribuídas para {nome}")
        
        if resultado["tarefas_nao_encontradas"]:
            logger.warning(f"⚠️  {len(resultado['tarefas_nao_encontradas'])} tarefas não encontradas")
        
        if resultado["tarefas_falharam"]:
            logger.warning(f"⚠️  {len(resultado['tarefas_falharam'])} tarefas falharam na atribuição")
        
        resultado["sucesso"] = True
        resultado["mensagem"] = (
            f"{nome} adicionado! "
            f"{len(resultado['tarefas_atribuidas'])} tarefas atribuídas"
        )
        
    except Exception as e:
        logger.error(f"❌ Erro ao adicionar implantador: {e}")
        resultado["mensagem"] = f"Erro ao adicionar implantador: {str(e)}"
    
    return resultado

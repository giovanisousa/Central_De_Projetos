# -*- coding: utf-8 -*-
"""
Módulo para gerenciar tarefas de implantação no Zoho Projects.
Handles both date updates and assignee management for RIS/PACS projects.
Otimizado para lidar com até 200+ tarefas por projeto.
"""

import json
import requests
import time
import re
from typing import Dict, List, Optional, Tuple
from config import ZOHO_PORTAL_ID, TAREFAS_AJUSTE_DATA_IMPLANTACAO
from utils import obter_access_token, _zp_base, _zp_headers
from implantacao_config import (
    TAREFAS_DATA_INICIO, PADROES_TAREFAS_RIS, PADROES_TAREFAS_PACS,
    BATCH_SIZE_TAREFAS, DELAY_ENTRE_LOTES, DELAY_ENTRE_TAREFAS,
    MAX_TENTATIVAS_API, TIMEOUT_API, LOG_PROGRESSO_A_CADA, LOG_DETALHADO,
    MAX_TAREFAS_PROCESSAR, VALIDAR_ZPUID, TAREFAS_EXCLUSAO,
    TAREFAS_ALTA_PRIORIDADE
)

class ImplantacaoTaskManager:
    """Gerenciador de tarefas de implantação."""
    
    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token or obter_access_token()
        self.equipe_data = self._carregar_equipe_implantacao()
        self.tarefas_ris = self._carregar_tarefas_ris()
        self.tarefas_pacs = self._carregar_tarefas_pacs()
    
    def _carregar_equipe_implantacao(self) -> Dict:
        """Carrega dados da equipe de implantação."""
        try:
            with open('equipe_implantacao_classificada.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] Erro ao carregar equipe de implantação: {e}")
            return {}
    
    def _carregar_tarefas_ris(self) -> List[str]:
        """Carrega lista de tarefas específicas do RIS."""
        try:
            with open('tarefas_ris.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                tarefas = data.get('tarefas_ris', [])
                print(f"[INFO] Carregadas {len(tarefas)} tarefas RIS do arquivo JSON")
                return [tarefa.lower() for tarefa in tarefas]  # Converter para lowercase para comparação
        except Exception as e:
            print(f"[ERROR] Erro ao carregar tarefas RIS: {e}")
            print(f"[WARN] Usando padrões genéricos como fallback")
            return PADROES_TAREFAS_RIS
    
    def _carregar_tarefas_pacs(self) -> List[str]:
        """Carrega lista de tarefas específicas do PACS."""
        try:
            with open('tarefas_pacs.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                tarefas = data.get('tarefas_pacs', [])
                print(f"[INFO] Carregadas {len(tarefas)} tarefas PACS do arquivo JSON")
                return [tarefa.lower() for tarefa in tarefas]  # Converter para lowercase para comparação
        except Exception as e:
            print(f"[ERROR] Erro ao carregar tarefas PACS: {e}")
            print(f"[WARN] Usando padrões genéricos como fallback")
            return PADROES_TAREFAS_PACS
    
    def listar_todas_tarefas_projeto(self, project_id: str) -> List[Dict]:
        """
        Lista TODAS as tarefas do projeto usando paginação adequada.
        Usa a mesma abordagem do _listar_tarefas_quick para evitar problemas de paginação.
        """
        from routes.api import _listar_tarefas_quick
        
        headers = {
            "Authorization": f"Zoho-oauthtoken {self.access_token}",
            "Accept": "application/json"
        }
        
        print(f"[INFO] Iniciando listagem COMPLETA de tarefas para projeto {project_id}")
        
        try:
            todas_tarefas = _listar_tarefas_quick(project_id, headers)
            print(f"[INFO] Total de tarefas carregadas: {len(todas_tarefas)}")
            return todas_tarefas
        except Exception as e:
            print(f"[ERROR] Erro ao listar tarefas: {e}")
            return []
    
    def identificar_tipo_tarefa(self, titulo_tarefa: str) -> Optional[str]:
        """
        Identifica se a tarefa é RIS ou PACS baseado na lista específica de títulos.
        Retorna 'RIS', 'PACS' ou None.
        """
        titulo_lower = titulo_tarefa.lower().strip()
        
        # Verificar se a tarefa deve ser excluída
        for exclusao in TAREFAS_EXCLUSAO:
            if exclusao in titulo_lower:
                if LOG_DETALHADO:
                    print(f"[DEBUG] Tarefa excluída: {titulo_tarefa} (padrão: {exclusao})")
                return None
        
        # Método 1: Busca exata na lista de tarefas RIS
        for tarefa_ris in self.tarefas_ris:
            if tarefa_ris == titulo_lower:
                if LOG_DETALHADO:
                    print(f"[DEBUG] Tarefa RIS identificada (exata): {titulo_tarefa}")
                return "RIS"
        
        # Método 2: Busca exata na lista de tarefas PACS
        for tarefa_pacs in self.tarefas_pacs:
            if tarefa_pacs == titulo_lower:
                if LOG_DETALHADO:
                    print(f"[DEBUG] Tarefa PACS identificada (exata): {titulo_tarefa}")
                return "PACS"
        
        # Método 3: Busca parcial (tarefa contém título da lista)
        for tarefa_ris in self.tarefas_ris:
            if tarefa_ris in titulo_lower or titulo_lower in tarefa_ris:
                if LOG_DETALHADO:
                    print(f"[DEBUG] Tarefa RIS identificada (parcial): {titulo_tarefa} ↔ {tarefa_ris}")
                return "RIS"
        
        for tarefa_pacs in self.tarefas_pacs:
            if tarefa_pacs in titulo_lower or titulo_lower in tarefa_pacs:
                if LOG_DETALHADO:
                    print(f"[DEBUG] Tarefa PACS identificada (parcial): {titulo_tarefa} ↔ {tarefa_pacs}")
                return "PACS"
        
        # Método 4: Fallback para padrões genéricos (caso os JSONs não tenham todas as tarefas)
        for padrao in PADROES_TAREFAS_RIS:
            if padrao in titulo_lower:
                if LOG_DETALHADO:
                    print(f"[DEBUG] Tarefa RIS identificada (padrão fallback): {titulo_tarefa} (padrão: {padrao})")
                return "RIS"
        
        for padrao in PADROES_TAREFAS_PACS:
            if padrao in titulo_lower:
                if LOG_DETALHADO:
                    print(f"[DEBUG] Tarefa PACS identificada (padrão fallback): {titulo_tarefa} (padrão: {padrao})")
                return "PACS"
        
        if LOG_DETALHADO:
            print(f"[DEBUG] Tarefa não identificada: {titulo_tarefa}")
        
        return None
    
    def obter_zpuid_implantador(self, tipo_ferramenta: str, nome_implantador: str) -> Optional[str]:
        """Obtém o ZPUID do implantador pelo nome e tipo de ferramenta."""
        categoria = f"Implantação {tipo_ferramenta}"
        
        for implantador in self.equipe_data.get(categoria, []):
            if implantador.get('name') == nome_implantador:
                return implantador.get('zpuid')
        
        return None
    
    def atualizar_data_inicio_tarefa(self, project_id: str, task_id: str, data_inicio: str) -> Tuple[bool, Optional[str]]:
        """
        Atualiza a data de início de uma tarefa específica.
        data_inicio deve estar no formato 'YYYY-MM-DD'.
        
        Usa o endpoint oficial do Zoho Projects API v3:
        PATCH /api/v3/portal/{PORTAL_ID}/projects/{PROJECT_ID}/tasks/{TASK_ID}
        
        Se a tarefa tiver dependências com lag (intervalo de tempo entre predecessoras/sucessoras),
        remove automaticamente essas dependências para permitir a atualização da data.
        
        Returns:
            Tuple[bool, Optional[str]]: (sucesso, codigo_erro)
                - sucesso: True se atualizou, False se falhou
                - codigo_erro: None se sucesso, ou código do erro (ex: 'DEPENDENCY_LAG', 'PERMISSION', etc.)
        """
        for tentativa in range(1, MAX_TENTATIVAS_API + 1):
            try:
                # Endpoint correto conforme documentação do Zoho
                url = f"{_zp_base()}/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks/{task_id}"
                headers = _zp_headers(self.access_token)
                
                # Converter data de 'YYYY-MM-DD' para 'YYYY-MM-DDTHH:MM:SS.000Z' (ISO 8601)
                # Assumindo horário padrão 00:00:00 (meia-noite)
                data_iso = f"{data_inicio}T00:00:00.000Z"
                
                # Payload conforme documentação do Zoho
                # remove_dependency_lag: true permite alterar a data removendo dependências com lag
                payload = {
                    "start_date": data_iso,
                    "remove_dependency_lag": True
                }
                
                if LOG_DETALHADO:
                    print(f"[DEBUG] Atualizando data da tarefa {task_id}")
                    print(f"[DEBUG]   URL: {url}")
                    print(f"[DEBUG]   Payload: {payload}")
                
                response = requests.patch(url, headers=headers, json=payload, timeout=TIMEOUT_API)
                
                if LOG_DETALHADO:
                    print(f"[DEBUG]   Status Code: {response.status_code}")
                    print(f"[DEBUG]   Response: {response.text[:200]}")
                
                response.raise_for_status()
                
                if LOG_DETALHADO:
                    print(f"[SUCCESS] Data de início atualizada para tarefa {task_id}")
                return (True, None)
                
            except requests.exceptions.HTTPError as e:
                error_msg = f"HTTP {e.response.status_code}"
                error_detail = None
                error_code = "UNKNOWN"
                
                try:
                    error_detail = e.response.json()
                    error_msg += f" - {error_detail}"
                    
                    # Verificar se é erro de dependência com lag
                    if e.response.status_code == 403:
                        error_type = error_detail.get('error', {}).get('title', '')
                        if error_type == 'CANNOT_MODIFY_DATE_WITH_DEPENDENCY_LAG':
                            error_code = "DEPENDENCY_LAG"
                            if LOG_DETALHADO:
                                print(f"[INFO] 🔗 Tarefa {task_id} possui dependências com lag (intervalo de tempo)")
                                print(f"[INFO] ⚠️  O parâmetro remove_dependency_lag=True está ativo, mas a API ainda bloqueou")
                                print(f"[INFO] 💡 A tarefa será pulada - não é possível atualizar a data automaticamente")
                        else:
                            error_code = "PERMISSION"
                    elif e.response.status_code == 400:
                        error_code = "BAD_REQUEST"
                    elif e.response.status_code == 500:
                        error_code = "SERVER_ERROR"
                except:
                    error_msg += f" - {e.response.text[:100]}"
                
                if tentativa < MAX_TENTATIVAS_API and error_code not in ["DEPENDENCY_LAG", "PERMISSION"]:
                    # Apenas retry para erros temporários (não para dependências ou permissões)
                    print(f"[WARN] Tentativa {tentativa} falhou para atualizar data da tarefa {task_id}: {error_msg}")
                    # Polling: aguarda até 2s ou até que retry esteja disponível
                    import time
                    polling_timeout = 2
                    polling_interval = 1
                    polling_start = time.time()
                    while time.time() - polling_start < polling_timeout:
                        print(f"[polling] aguardando retry... ({int((time.time()-polling_start)*1000)}ms)")
                        time.sleep(polling_interval)
                else:
                    if error_code != "DEPENDENCY_LAG" or LOG_DETALHADO:
                        # Não logar erro de dependência como ERROR (é esperado em alguns casos)
                        nivel = "[WARN]" if error_code == "DEPENDENCY_LAG" else "[ERROR]"
                        print(f"{nivel} Não foi possível atualizar data da tarefa {task_id}: {error_msg}")
                    return (False, error_code)
                    
            except Exception as e:
                if tentativa < MAX_TENTATIVAS_API:
                    print(f"[WARN] Tentativa {tentativa} falhou para atualizar data da tarefa {task_id}: {e}")
                    # Polling: aguarda até 2s ou até que retry esteja disponível
                    import time
                    polling_timeout = 2
                    polling_interval = 1
                    polling_start = time.time()
                    while time.time() - polling_start < polling_timeout:
                        print(f"[polling] aguardando retry... ({int((time.time()-polling_start)*1000)}ms)")
                        time.sleep(polling_interval)
                else:
                    print(f"[ERROR] Erro definitivo ao atualizar data da tarefa {task_id}: {e}")
                    return (False, "EXCEPTION")
        
        return (False, "MAX_RETRIES")
    
    def atribuir_responsavel_tarefa(self, project_id: str, task_id: str, zpuid: str) -> bool:
        """
        Atribui um responsável a uma tarefa usando o ZPUID.
        Com retry automático para lidar com falhas temporárias.
        """
        for tentativa in range(1, MAX_TENTATIVAS_API + 1):
            try:
                url = f"https://projectsapi.zoho.com/restapi/portal/{ZOHO_PORTAL_ID}/projects/{project_id}/tasks/{task_id}/"
                headers = {"Authorization": f"Bearer {self.access_token}"}
                payload = {"person_responsible": str(zpuid)}
                
                response = requests.post(url, headers=headers, data=payload, timeout=TIMEOUT_API)
                response.raise_for_status()
                
                if LOG_DETALHADO:
                    print(f"[SUCCESS] Responsável atribuído para tarefa {task_id}")
                return True
                
            except Exception as e:
                if tentativa < MAX_TENTATIVAS_API:
                    print(f"[WARN] Tentativa {tentativa} falhou para atribuir responsável da tarefa {task_id}: {e}")
                    # Polling: aguarda até 2s ou até que retry esteja disponível
                    import time
                    polling_timeout = 2
                    polling_interval = 1
                    polling_start = time.time()
                    while time.time() - polling_start < polling_timeout:
                        print(f"[polling] aguardando retry... ({int((time.time()-polling_start)*1000)}ms)")
                        time.sleep(polling_interval)
                else:
                    print(f"[ERROR] Erro definitivo ao atribuir responsável da tarefa {task_id}: {e}")
                    return False
        
        return False
    
    def _remover_prefixos_tarefa(self, titulo: str) -> str:
        """
        Remove prefixos comuns de títulos de tarefas para comparação.
        Exemplos de prefixos: "1. ", "2.1 ", "[RIS] ", "[PACS] ", etc.
        
        Args:
            titulo: Título original da tarefa
        
        Returns:
            Título sem prefixos
        """
        titulo_limpo = titulo.strip()
        
        # Remover padrões de numeração: "1. ", "1.1 ", "1.1.1 ", etc.
        # Aceita múltiplos espaços após os números e pontos
        titulo_limpo = re.sub(r'^\d+(\.\d+)*\.?\s+', '', titulo_limpo)
        
        # Remover tags entre colchetes: "[RIS]", "[PACS]", etc.
        titulo_limpo = re.sub(r'^\[.*?\]\s*', '', titulo_limpo)
        
        # Remover tags entre parênteses no início: "(RIS)", "(PACS)", etc.
        titulo_limpo = re.sub(r'^\(.*?\)\s*', '', titulo_limpo)
        
        return titulo_limpo.strip()
    
    def _verificar_tarefa_ajuste_data(self, titulo: str) -> bool:
        """
        Verifica se uma tarefa precisa ter sua data de início ajustada.
        Compara o título (sem prefixos) com a lista de tarefas configuradas.
        
        Args:
            titulo: Título da tarefa
        
        Returns:
            True se a tarefa deve ter a data ajustada
        """
        # Validar entrada
        if not titulo or not titulo.strip():
            return False
        
        titulo_limpo = self._remover_prefixos_tarefa(titulo).lower()
        
        # Não processar se o título ficou vazio após limpeza
        if not titulo_limpo:
            return False
        
        for tarefa_config in TAREFAS_AJUSTE_DATA_IMPLANTACAO:
            tarefa_config_limpa = tarefa_config.lower().strip()
            
            # Pular configurações vazias
            if not tarefa_config_limpa:
                continue
            
            # Comparação exata
            if titulo_limpo == tarefa_config_limpa:
                if LOG_DETALHADO:
                    print(f"[DEBUG] ✓ Tarefa identificada para ajuste de data (exata): '{titulo}'")
                return True
            
            # Comparação parcial (tarefa contém o padrão ou vice-versa)
            if tarefa_config_limpa in titulo_limpo or titulo_limpo in tarefa_config_limpa:
                if LOG_DETALHADO:
                    print(f"[DEBUG] ✓ Tarefa identificada para ajuste de data (parcial): '{titulo}' ↔ '{tarefa_config}'")
                return True
        
        return False
    
    def processar_tarefas_implantacao(
        self, 
        project_id: str, 
        data_inicio_implantacao: str,
        implantador_ris: Optional[str] = None,
        implantador_pacs: Optional[str] = None,
        tem_ris: bool = False,
        tem_pacs: bool = False
    ) -> Dict[str, int]:
        """
        Processa todas as tarefas de implantação do projeto.
        
        Args:
            project_id: ID do projeto no Zoho
            data_inicio_implantacao: Data de início no formato YYYY-MM-DD
            implantador_ris: Nome do implantador RIS selecionado
            implantador_pacs: Nome do implantador PACS selecionado
            tem_ris: Se o projeto inclui RIS
            tem_pacs: Se o projeto inclui PACS
        
        Returns:
            Estatísticas do processamento
        """
        print(f"[INFO] ===== INICIANDO PROCESSAMENTO DE TAREFAS DE IMPLANTAÇÃO =====")
        print(f"[INFO] Projeto: {project_id}")
        print(f"[INFO] Data início: {data_inicio_implantacao}")
        print(f"[INFO] Tem RIS: {tem_ris} | Tem PACS: {tem_pacs}")
        print(f"[INFO] Implantador RIS: {implantador_ris}")
        print(f"[INFO] Implantador PACS: {implantador_pacs}")
        
        # Estatísticas
        stats = {
            "total_tarefas": 0,
            "datas_atualizadas": 0,
            "datas_especificas_atualizadas": 0,  # Nova estatística
            "datas_bloqueadas_dependencia": 0,  # Tarefas com dependências que bloquearam atualização
            "ris_atribuidas": 0,
            "pacs_atribuidas": 0,
            "erros": 0,
            "usuarios_adicionados": 0
        }
        
        # 1. Obter ZPUIDs e emails dos implantadores
        zpuid_ris = None
        zpuid_pacs = None
        email_ris = None
        email_pacs = None
        
        if tem_ris and implantador_ris:
            # Buscar informações completas do implantador RIS
            for implantador in self.equipe_data.get("Implantação RIS", []):
                if implantador.get('name') == implantador_ris:
                    zpuid_ris = implantador.get('zpuid')
                    email_ris = implantador.get('email')
                    break
            
            if not zpuid_ris:
                print(f"[WARN] ZPUID não encontrado para implantador RIS: {implantador_ris}")
            if not email_ris:
                print(f"[WARN] Email não encontrado para implantador RIS: {implantador_ris}")
        
        if tem_pacs and implantador_pacs:
            # Buscar informações completas do implantador PACS
            for implantador in self.equipe_data.get("Implantação PACS", []):
                if implantador.get('name') == implantador_pacs:
                    zpuid_pacs = implantador.get('zpuid')
                    email_pacs = implantador.get('email')
                    break
            
            if not zpuid_pacs:
                print(f"[WARN] ZPUID não encontrado para implantador PACS: {implantador_pacs}")
            if not email_pacs:
                print(f"[WARN] Email não encontrado para implantador PACS: {implantador_pacs}")
        
        # 2. ADICIONAR USUÁRIOS AO PROJETO ANTES DE ATRIBUIR TAREFAS
        print(f"\n{'='*80}")
        print(f"[INFO] ETAPA 2: ADICIONANDO USUÁRIOS AO PROJETO")
        print(f"{'='*80}")
        
        # Log detalhado dos dados coletados
        print(f"\n[DEBUG] 📋 DADOS DOS IMPLANTADORES:")
        print(f"[DEBUG]   RIS:")
        print(f"[DEBUG]     - Nome: {implantador_ris}")
        print(f"[DEBUG]     - ZPUID: {zpuid_ris}")
        print(f"[DEBUG]     - Email: {email_ris}")
        print(f"[DEBUG]   PACS:")
        print(f"[DEBUG]     - Nome: {implantador_pacs}")
        print(f"[DEBUG]     - ZPUID: {zpuid_pacs}")
        print(f"[DEBUG]     - Email: {email_pacs}")
        print(f"")
        
        from utils import adicionar_usuario_ao_projeto, verificar_usuario_no_projeto
        
        # Log consolidado para análise posterior
        log_adicao_usuarios = {
            "ris": {"tentou_adicionar": False, "ja_estava": False, "adicionado": False, "erro": None},
            "pacs": {"tentou_adicionar": False, "ja_estava": False, "adicionado": False, "erro": None}
        }
        
        # Adicionar implantador RIS ao projeto
        if zpuid_ris and email_ris:
            print(f"[INFO] 🔍 Verificando se implantador RIS está no projeto...")
            try:
                ja_esta = verificar_usuario_no_projeto(project_id, zpuid_ris, self.access_token)
                log_adicao_usuarios["ris"]["ja_estava"] = ja_esta
                
                if not ja_esta:
                    print(f"[INFO] ➕ Adicionando implantador RIS ao projeto: {implantador_ris}")
                    print(f"[DEBUG]    - Project ID: {project_id}")
                    print(f"[DEBUG]    - Email: {email_ris}")
                    print(f"[DEBUG]    - ZPUID: {zpuid_ris}")
                    
                    log_adicao_usuarios["ris"]["tentou_adicionar"] = True
                    resultado = adicionar_usuario_ao_projeto(project_id, email_ris, zpuid_ris, self.access_token)
                    
                    if resultado:
                        stats["usuarios_adicionados"] += 1
                        log_adicao_usuarios["ris"]["adicionado"] = True
                        print(f"[SUCCESS] ✅ Implantador RIS adicionado com sucesso!")
                        # Aguardar um pouco para a API processar
                        print(f"[INFO] ⏳ Aguardando 3 segundos para propagação da API...")
                        # Polling: aguarda até 5s ou até que propagação esteja disponível
                        import time
                        polling_timeout = 5
                        polling_interval = 1
                        polling_start = time.time()
                        while time.time() - polling_start < polling_timeout:
                            print(f"[polling] aguardando propagação... ({int((time.time()-polling_start)*1000)}ms)")
                            time.sleep(polling_interval)
                    else:
                        log_adicao_usuarios["ris"]["erro"] = "Falha na função adicionar_usuario_ao_projeto"
                        print(f"[ERROR] ❌ Falha ao adicionar implantador RIS ao projeto")
                else:
                    print(f"[INFO] ✓ Implantador RIS já está no projeto")
            except Exception as e:
                log_adicao_usuarios["ris"]["erro"] = str(e)
                print(f"[ERROR] ❌ Exceção ao processar implantador RIS: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"[WARN] ⚠️ Dados insuficientes para adicionar implantador RIS")
            if not zpuid_ris:
                print(f"[WARN]    - ZPUID RIS não encontrado")
            if not email_ris:
                print(f"[WARN]    - Email RIS não encontrado")
        
        print(f"")  # Linha em branco para separação
        
        # Adicionar implantador PACS ao projeto
        if zpuid_pacs and email_pacs:
            print(f"[INFO] 🔍 Verificando se implantador PACS está no projeto...")
            try:
                ja_esta = verificar_usuario_no_projeto(project_id, zpuid_pacs, self.access_token)
                log_adicao_usuarios["pacs"]["ja_estava"] = ja_esta
                
                if not ja_esta:
                    print(f"[INFO] ➕ Adicionando implantador PACS ao projeto: {implantador_pacs}")
                    print(f"[DEBUG]    - Project ID: {project_id}")
                    print(f"[DEBUG]    - Email: {email_pacs}")
                    print(f"[DEBUG]    - ZPUID: {zpuid_pacs}")
                    
                    log_adicao_usuarios["pacs"]["tentou_adicionar"] = True
                    resultado = adicionar_usuario_ao_projeto(project_id, email_pacs, zpuid_pacs, self.access_token)
                    
                    if resultado:
                        stats["usuarios_adicionados"] += 1
                        log_adicao_usuarios["pacs"]["adicionado"] = True
                        print(f"[SUCCESS] ✅ Implantador PACS adicionado com sucesso!")
                        # Aguardar um pouco para a API processar
                        print(f"[INFO] ⏳ Aguardando 3 segundos para propagação da API...")
                        time.sleep(3)
                    else:
                        log_adicao_usuarios["pacs"]["erro"] = "Falha na função adicionar_usuario_ao_projeto"
                        print(f"[ERROR] ❌ Falha ao adicionar implantador PACS ao projeto")
                else:
                    print(f"[INFO] ✓ Implantador PACS já está no projeto")
            except Exception as e:
                log_adicao_usuarios["pacs"]["erro"] = str(e)
                print(f"[ERROR] ❌ Exceção ao processar implantador PACS: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"[WARN] ⚠️ Dados insuficientes para adicionar implantador PACS")
            if not zpuid_pacs:
                print(f"[WARN]    - ZPUID PACS não encontrado")
            if not email_pacs:
                print(f"[WARN]    - Email PACS não encontrado")
        
        # Armazenar log para exibição final
        stats["log_adicao_usuarios"] = log_adicao_usuarios
        
        print(f"\n[INFO] 📊 RESUMO DA ADIÇÃO DE USUÁRIOS:")
        print(f"[INFO]   RIS  - Tentou: {log_adicao_usuarios['ris']['tentou_adicionar']}, "
              f"Já estava: {log_adicao_usuarios['ris']['ja_estava']}, "
              f"Adicionado: {log_adicao_usuarios['ris']['adicionado']}")
        print(f"[INFO]   PACS - Tentou: {log_adicao_usuarios['pacs']['tentou_adicionar']}, "
              f"Já estava: {log_adicao_usuarios['pacs']['ja_estava']}, "
              f"Adicionado: {log_adicao_usuarios['pacs']['adicionado']}")
        print(f"{'='*80}\n")
        
        # 3. Listar todas as tarefas do projeto
        print(f"[INFO] ===== LISTANDO TAREFAS DO PROJETO =====")
        todas_tarefas = self.listar_todas_tarefas_projeto(project_id)
        stats["total_tarefas"] = len(todas_tarefas)
        
        if not todas_tarefas:
            print(f"[WARN] Nenhuma tarefa encontrada no projeto {project_id}")
            return stats
        
        # Limitar número máximo de tarefas por segurança
        if len(todas_tarefas) > MAX_TAREFAS_PROCESSAR:
            print(f"[WARN] Limitando processamento a {MAX_TAREFAS_PROCESSAR} tarefas (total: {len(todas_tarefas)})")
            todas_tarefas = todas_tarefas[:MAX_TAREFAS_PROCESSAR]
            stats["total_tarefas"] = len(todas_tarefas)
        
        # 4. Organizar tarefas por prioridade
        tarefas_prioritarias = []
        tarefas_normais = []
        
        for tarefa in todas_tarefas:
            titulo = tarefa.get('name', '').lower()
            is_prioritaria = any(prioridade in titulo for prioridade in TAREFAS_ALTA_PRIORIDADE)
            
            if is_prioritaria:
                tarefas_prioritarias.append(tarefa)
            else:
                tarefas_normais.append(tarefa)
        
        # Processar prioritárias primeiro, depois as normais
        tarefas_ordenadas = tarefas_prioritarias + tarefas_normais
        
        print(f"[INFO] Processando {len(tarefas_prioritarias)} tarefas prioritárias e {len(tarefas_normais)} normais")
        
        # 5. Processar tarefas em lotes para otimizar performance
        total_lotes = (len(tarefas_ordenadas) + BATCH_SIZE_TAREFAS - 1) // BATCH_SIZE_TAREFAS
        
        for lote_num in range(total_lotes):
            inicio_lote = lote_num * BATCH_SIZE_TAREFAS
            fim_lote = min(inicio_lote + BATCH_SIZE_TAREFAS, len(tarefas_ordenadas))
            lote_tarefas = tarefas_ordenadas[inicio_lote:fim_lote]
            
            print(f"[INFO] Processando lote {lote_num + 1}/{total_lotes} ({len(lote_tarefas)} tarefas)")
            
            # Processar cada tarefa no lote
            for i, tarefa in enumerate(lote_tarefas):
                task_id = tarefa.get('id')
                titulo = tarefa.get('name', '')
                posicao_global = inicio_lote + i + 1
                
                if not task_id:
                    continue
                
                # Log de progresso
                if posicao_global % LOG_PROGRESSO_A_CADA == 0 or LOG_DETALHADO:
                    print(f"[INFO] ({posicao_global}/{len(tarefas_ordenadas)}) Processando: {titulo[:50]}...")
                
                try:
                    # 5.1. NOVA FUNCIONALIDADE: Verificar se é uma tarefa específica que precisa de ajuste de data
                    if self._verificar_tarefa_ajuste_data(titulo):
                        if LOG_DETALHADO:
                            print(f"[INFO] 📅 Ajustando data para tarefa específica: {titulo[:60]}...")
                        
                        sucesso, codigo_erro = self.atualizar_data_inicio_tarefa(project_id, task_id, data_inicio_implantacao)
                        if sucesso:
                            stats["datas_especificas_atualizadas"] += 1
                            if LOG_DETALHADO:
                                print(f"[SUCCESS] ✓ Data ajustada com sucesso!")
                        elif codigo_erro == "DEPENDENCY_LAG":
                            stats["datas_bloqueadas_dependencia"] += 1
                            if LOG_DETALHADO:
                                print(f"[INFO] ⚠️  Tarefa possui dependências - data não atualizada")
                    
                    # 5.2. Verificar se precisa atualizar data de início (sistema antigo - TAREFAS_DATA_INICIO)
                    for padrao_data in TAREFAS_DATA_INICIO:
                        if padrao_data.lower() in titulo.lower():
                            sucesso, codigo_erro = self.atualizar_data_inicio_tarefa(project_id, task_id, data_inicio_implantacao)
                            if sucesso:
                                stats["datas_atualizadas"] += 1
                            elif codigo_erro == "DEPENDENCY_LAG":
                                stats["datas_bloqueadas_dependencia"] += 1
                            break
                    
                    # 5.3. Identificar tipo da tarefa e atribuir responsável
                    tipo_tarefa = self.identificar_tipo_tarefa(titulo)
                    
                    if tipo_tarefa == "RIS" and tem_ris and zpuid_ris:
                        if self.atribuir_responsavel_tarefa(project_id, task_id, zpuid_ris):
                            stats["ris_atribuidas"] += 1
                    
                    elif tipo_tarefa == "PACS" and tem_pacs and zpuid_pacs:
                        if self.atribuir_responsavel_tarefa(project_id, task_id, zpuid_pacs):
                            stats["pacs_atribuidas"] += 1
                    
                    # Delay entre tarefas para não sobrecarregar a API
                    time.sleep(DELAY_ENTRE_TAREFAS)
                    
                except Exception as e:
                    print(f"[ERROR] Erro ao processar tarefa {titulo}: {e}")
                    stats["erros"] += 1
            
            # Delay entre lotes
            if lote_num < total_lotes - 1:  # Não fazer delay após o último lote
                print(f"[INFO] Aguardando {DELAY_ENTRE_LOTES}s antes do próximo lote...")
                time.sleep(DELAY_ENTRE_LOTES)
        
        # 6. Relatório final
        print(f"\n{'='*80}")
        print(f"[INFO] RELATÓRIO FINAL DE PROCESSAMENTO")
        print(f"{'='*80}")
        print(f"[INFO] 📊 ESTATÍSTICAS GERAIS:")
        print(f"[INFO]   - Total de tarefas processadas: {stats['total_tarefas']}")
        print(f"[INFO]   - Usuários adicionados ao projeto: {stats['usuarios_adicionados']}")
        print(f"[INFO]   - Datas de início atualizadas (sistema antigo): {stats['datas_atualizadas']}")
        print(f"[INFO]   - Datas ajustadas (tarefas específicas): {stats['datas_especificas_atualizadas']} 📅")
        print(f"[INFO]   - Datas bloqueadas por dependências: {stats['datas_bloqueadas_dependencia']} 🔗")
        print(f"[INFO]   - Tarefas RIS atribuídas: {stats['ris_atribuidas']}")
        print(f"[INFO]   - Tarefas PACS atribuídas: {stats['pacs_atribuidas']}")
        print(f"[INFO]   - Erros encontrados: {stats['erros']}")
        
        # Exibir detalhes da adição de usuários
        print(f"\n[INFO] 👥 DETALHAMENTO DA ADIÇÃO DE USUÁRIOS:")
        log_adicao = stats.get("log_adicao_usuarios", {})
        
        print(f"[INFO] 🔹 IMPLANTADOR RIS ({implantador_ris or 'Não selecionado'}):")
        if log_adicao.get("ris"):
            ris_log = log_adicao["ris"]
            print(f"[INFO]   - ZPUID encontrado: {'✓' if zpuid_ris else '✗'} ({zpuid_ris or 'N/A'})")
            print(f"[INFO]   - Email encontrado: {'✓' if email_ris else '✗'} ({email_ris or 'N/A'})")
            print(f"[INFO]   - Já estava no projeto: {'✓' if ris_log.get('ja_estava') else '✗'}")
            print(f"[INFO]   - Tentou adicionar: {'✓' if ris_log.get('tentou_adicionar') else '✗'}")
            print(f"[INFO]   - Adicionado com sucesso: {'✓' if ris_log.get('adicionado') else '✗'}")
            if ris_log.get('erro'):
                print(f"[ERROR]  - Erro: {ris_log['erro']}")
        else:
            print(f"[INFO]   - Sem dados de processamento")
        
        print(f"\n[INFO] 🔹 IMPLANTADOR PACS ({implantador_pacs or 'Não selecionado'}):")
        if log_adicao.get("pacs"):
            pacs_log = log_adicao["pacs"]
            print(f"[INFO]   - ZPUID encontrado: {'✓' if zpuid_pacs else '✗'} ({zpuid_pacs or 'N/A'})")
            print(f"[INFO]   - Email encontrado: {'✓' if email_pacs else '✗'} ({email_pacs or 'N/A'})")
            print(f"[INFO]   - Já estava no projeto: {'✓' if pacs_log.get('ja_estava') else '✗'}")
            print(f"[INFO]   - Tentou adicionar: {'✓' if pacs_log.get('tentou_adicionar') else '✗'}")
            print(f"[INFO]   - Adicionado com sucesso: {'✓' if pacs_log.get('adicionado') else '✗'}")
            if pacs_log.get('erro'):
                print(f"[ERROR]  - Erro: {pacs_log['erro']}")
        else:
            print(f"[INFO]   - Sem dados de processamento")
        
        print(f"{'='*80}\n")
        
        return stats


def processar_implantacao_completa(
    project_id: str,
    data_inicio_implantacao: str,
    implantador_ris: Optional[str] = None,
    implantador_pacs: Optional[str] = None,
    tem_ris: bool = False,
    tem_pacs: bool = False
) -> Dict[str, int]:
    """
    Função de conveniência para processar todas as tarefas de implantação.
    
    Esta função deve ser chamada pela rota /iniciar_implantacao após 
    o cálculo das datas e atualização dos campos do projeto.
    """
    manager = ImplantacaoTaskManager()
    
    return manager.processar_tarefas_implantacao(
        project_id=project_id,
        data_inicio_implantacao=data_inicio_implantacao,
        implantador_ris=implantador_ris,
        implantador_pacs=implantador_pacs,
        tem_ris=tem_ris,
        tem_pacs=tem_pacs
    )


if __name__ == "__main__":
    # Exemplo de uso para testes
    # processar_implantacao_completa(
    #     project_id="2376502000005544019",
    #     data_inicio_implantacao="2025-10-15",
    #     implantador_ris="Pablo Pyerri Ferreira da Costa",
    #     implantador_pacs="Aneidia Sa",
    #     tem_ris=True,
    #     tem_pacs=True
    # )
    pass
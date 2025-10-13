# -*- coding: utf-8 -*-
"""
Configurações específicas para o processamento de tarefas de implantação.
Este arquivo define os padrões e títulos usados para identificar e processar tarefas.
"""

# ===== TAREFAS QUE PRECISAM TER A DATA DE INÍCIO ATUALIZADA =====
# Estas são as 2 tarefas específicas mencionadas pelo usuário
TAREFAS_DATA_INICIO = [
    # Adicione aqui os títulos EXATOS das tarefas que precisam ter a data atualizada
    # Exemplo:
    "Definição do cronograma de homologação",
    "Início da implantação",
    "Homologação inicial",
    "Kickoff da implantação"
    # IMPORTANTE: Substituir pelos títulos reais das tarefas do template
]

# ===== PADRÕES PARA IDENTIFICAÇÃO DE TAREFAS POR FERRAMENTA =====
PADROES_TAREFAS_RIS = [
    # Padrões que identificam tarefas relacionadas ao RIS
    "ris",
    "netris", 
    "net ris",
    "radiology information",
    "sistema de informação radiológica",
    "configuração ris",
    "instalação ris",
    "implantação ris",
    "treinamento ris",
    "setup ris",
    "ris server",
    "servidor ris"
]

PADROES_TAREFAS_PACS = [
    # Padrões que identificam tarefas relacionadas ao PACS
    "pacs",
    "animatipacs",
    "animati pacs", 
    "picture archiving",
    "sistema de arquivamento",
    "configuração pacs",
    "instalação pacs",
    "implantação pacs",
    "treinamento pacs",
    "setup pacs",
    "pacs server",
    "servidor pacs"
]

# ===== CONFIGURAÇÕES DE PERFORMANCE =====
# Configurações para lidar com o alto volume de tarefas (200+ para RIS)
BATCH_SIZE_TAREFAS = 50  # Processar tarefas em lotes
DELAY_ENTRE_LOTES = 2    # Segundos entre lotes (rate limiting)
DELAY_ENTRE_TAREFAS = 0.3  # Segundos entre tarefas individuais
MAX_TENTATIVAS_API = 3   # Máximo de tentativas para chamadas de API
TIMEOUT_API = 30         # Timeout para chamadas de API

# ===== CONFIGURAÇÕES DE LOG =====
LOG_PROGRESSO_A_CADA = 10  # Mostrar log a cada X tarefas processadas
LOG_DETALHADO = True       # Se deve mostrar logs detalhados

# ===== CONFIGURAÇÕES DE SEGURANÇA =====
MAX_TAREFAS_PROCESSAR = 500  # Limite máximo para evitar loops infinitos
VALIDAR_ZPUID = True         # Se deve validar se o ZPUID existe antes de atribuir

# ===== TÍTULOS DE TAREFAS A EXCLUIR =====
# Tarefas que nunca devem ser processadas automaticamente
TAREFAS_EXCLUSAO = [
    "conclusão do projeto",
    "fechamento",
    "finalização", 
    "arquivamento",
    "encerramento"
]

# ===== MAPEAMENTO DE PRIORIDADES =====
# Algumas tarefas são mais importantes que outras
TAREFAS_ALTA_PRIORIDADE = [
    # Tarefas críticas que devem ser processadas primeiro
    "configuração inicial",
    "instalação principal",
    "setup básico"
]

# ===== CONFIGURAÇÕES ESPECÍFICAS POR AMBIENTE =====
AMBIENTE_PRODUCAO = True  # Set False para testes

if not AMBIENTE_PRODUCAO:
    # Configurações para ambiente de teste
    MAX_TAREFAS_PROCESSAR = 10
    BATCH_SIZE_TAREFAS = 5
    LOG_DETALHADO = True
    print("[CONFIG] Modo de TESTE ativado - processamento limitado")
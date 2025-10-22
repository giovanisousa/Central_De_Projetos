"""
Script de Limpeza - Central de Projetos
Remove arquivos de teste, debug e não utilizados
"""

import os
from pathlib import Path
import shutil

# Diretório raiz do projeto
ROOT_DIR = Path(__file__).parent

# Criar pasta para scripts utilitários
SCRIPTS_DIR = ROOT_DIR / "scripts_utilitarios"
SCRIPTS_DIR.mkdir(exist_ok=True)

# Arquivos para REMOVER completamente
arquivos_para_remover = [
    # teste_*.py
    "teste_api_v3.py",
    "teste_atualizacao_final_implantadores.py",
    "teste_atualizar_implantadores_completo.py",
    "teste_campos_texto.py",
    "teste_envio_formato_correto.py",
    "teste_final_campos_texto.py",
    "teste_formato_correto_zoho.py",
    "teste_nome_completo.py",
    "teste_restapi_v1.py",
    "teste_restapi_v1_maiusculo.py",
    "teste_restapi_v1_post_formdata.py",
    "teste_usuarios_equipes_corretas.py",
    "teste_zpuid_formatos.py",
    "teste_zpuids_corretos.py",
    
    # testar_*.py
    "testar_custom_fields_structure.py",
    "testar_filtros_implementados.py",
    "testar_leitura_implantadores.py",
    "testar_novo_formato_implantadores.py",
    "testar_ordenacao.py",
    "testar_todos_formatos_nomes.py",
    
    # test_*.py
    "test_add_user_detailed.py",
    "test_add_user_final.py",
    "test_add_user_to_project.py",
    "test_ajuste_datas_tarefas.py",
    "test_alternative_endpoint.py",
    "test_completo_ferramentas.py",
    "test_custom_field.py",
    "test_date_format.py",
    "test_descobrir_ids.py",
    "test_endpoint_progresso.py",
    "test_endpoint_progresso_completo.py",
    "test_extrair_nome_cliente.py",
    "test_google_calendar.py",
    "test_implantacao_tarefas.py",
    "test_implantadores.py",
    "test_novo_projeto_produto.py",
    "test_pasta_drive.py",
    "test_payload.py",
    "test_progresso_fix.py",
    "test_quick_extraction.py",
    "test_simple.py",
    "test_status_change.py",
    "test_task_assignment.py",
    "test_task_finding.py",
    "test_with_access_token.py",
    
    # debug_*.py
    "debug_busca_cliente.py",
    "debug_implantadores_zoho.py",
    "debug_projeto.py",
    
    # diagnostico_*.py
    "diagnostico_completo_custom_fields.py",
    "diagnostico_payload_implantadores.py",
    
    # verificar_*.py / validar_*.py
    "verificar_atualizacao.py",
    "verificar_campos_no_projeto.py",
    "verificar_fases_ris.py",
    "verificar_formato_manual.py",
    "verificar_projeto_zoho.py",
    "verificar_resposta_post.py",
    "verify_token_scopes.py",
    "validate_status_ids.py",
    "validar_filtro_projetos.py",
    
    # descobrir_*.py / investigar_*.py
    "descobrir_nomes_exatos_campos.py",
    "descobrir_picklist_values.py",
    "descobrir_usuarios_validos.py",
    "discover_all_status.py",
    "investigar_custom_fields_completo.py",
    
    # buscar_*.py (não essenciais)
    "buscar_todos_custom_fields.py",
    "buscar_zpuids_v1.py",
    
    # check_*.py
    "check_custom_fields.py",
    
    # Arquivos antigos/não utilizados
    "app_antigo.py",
    "analisar_pacs.py",
    "customizados.py",
    "ipv6.py",
    "projeto.py",
    "usuario.py",
    "zoho_fields.py",
]

# Arquivos para MOVER para scripts_utilitarios/
arquivos_para_mover = [
    "gerar_zoho_token.py",
    "gerar_json_equipe.py",
    "get_custom_fields.py",
    "get_custom_fields_v3.py",
    "get_layout_fields.py",
    "get_project_details.py",
    "get_project_layout.py",
    "list_custom_fields.py",
    "listar_usuarios_projeto.py",
    "find_completed_status.py",
    "teste_campos_implantadores_direto.py",  # Teste que funcionou - referência
]

def main():
    print("=" * 80)
    print("LIMPEZA DE ARQUIVOS - CENTRAL DE PROJETOS")
    print("=" * 80)
    
    removidos = 0
    nao_encontrados = 0
    movidos = 0
    
    # 1. REMOVER arquivos
    print(f"\n[1/2] Removendo {len(arquivos_para_remover)} arquivos de teste/debug...")
    
    for arquivo in arquivos_para_remover:
        caminho = ROOT_DIR / arquivo
        if caminho.exists():
            try:
                caminho.unlink()
                print(f"  ✅ Removido: {arquivo}")
                removidos += 1
            except Exception as e:
                print(f"  ❌ Erro ao remover {arquivo}: {e}")
        else:
            nao_encontrados += 1
    
    # 2. MOVER arquivos utilitários
    print(f"\n[2/2] Movendo {len(arquivos_para_mover)} arquivos utilitários para scripts_utilitarios/...")
    
    for arquivo in arquivos_para_mover:
        caminho_origem = ROOT_DIR / arquivo
        caminho_destino = SCRIPTS_DIR / arquivo
        
        if caminho_origem.exists():
            try:
                shutil.move(str(caminho_origem), str(caminho_destino))
                print(f"  ✅ Movido: {arquivo} → scripts_utilitarios/")
                movidos += 1
            except Exception as e:
                print(f"  ❌ Erro ao mover {arquivo}: {e}")
        else:
            nao_encontrados += 1
    
    # 3. RESUMO
    print("\n" + "=" * 80)
    print("RESUMO DA LIMPEZA:")
    print("=" * 80)
    print(f"✅ Arquivos removidos: {removidos}")
    print(f"✅ Arquivos movidos: {movidos}")
    print(f"⚠️  Arquivos não encontrados: {nao_encontrados}")
    
    print(f"\n📁 Pasta de scripts utilitários criada: {SCRIPTS_DIR}")
    
    print("\n" + "=" * 80)
    print("ESTRUTURA FINAL DO PROJETO:")
    print("=" * 80)
    print("""
    Central_De_Projetos/
    ├── app.py                          (Principal)
    ├── config.py                       (Configurações)
    ├── database.py                     (Banco de dados)
    ├── sync_zoho.py                    (Sincronização Zoho)
    ├── utils.py                        (Utilitários)
    ├── google_calendar.py              (Google Calendar)
    ├── implantacao_manager.py          (Gerenciador de implantação)
    ├── implantacao_tarefas.py          (Tarefas de implantação)
    ├── implantacao_config.py           (Config de implantação)
    ├── phases.py                       (Fases do projeto)
    ├── buscar_tarefas.py               (Buscar tarefas)
    ├── create_real_zoho_project.py     (Criar projeto Zoho)
    ├── dryrun_zoho_payload.py          (Payload Zoho)
    ├── routes/
    │   ├── api.py                      (Endpoints API)
    │   └── main.py                     (Rotas principais)
    ├── templates/                      (Templates HTML)
    ├── static/                         (CSS, JS, imagens)
    └── scripts_utilitarios/            (Scripts auxiliares)
        ├── gerar_zoho_token.py
        ├── gerar_json_equipe.py
        ├── get_custom_fields.py
        └── ...
    """)
    
    print("✅ LIMPEZA CONCLUÍDA COM SUCESSO!")
    print("=" * 80)

if __name__ == "__main__":
    main()

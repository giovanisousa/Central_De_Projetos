# -*- coding: utf-8 -*-
import json
from datetime import date, datetime

from config import GRUPOS_ZOHO, DONOS_PROJETO, MODELOS_ZOHO, BASE_DIR

# IDs e valores para campos de múltipla seleção
INTEGRACOES_OPTIONS = {
    "Worklist": {"id": "2376502000005584852", "value": "Worklist"},
    "Retorno de Laudo": {"id": "2376502000005584854", "value": "Retorno de Laudo"},
    "Laboratório": {"id": "2376502000005584856", "value": "Laboratório"},
    "Teleradiologia": {"id": "2376502000005584858", "value": "Teleradiologia"},
    "Outros": {"id": "2376502000005584860", "value": "Outros"}
}

IMPORTACOES_OPTIONS = {
    "Cadastros": {"id": "2376502000005584868", "value": "Cadastros"},
    "Prontuários": {"id": "2376502000005584866", "value": "Prontuários"},
    "Laudos": {"id": "2376502000005584870", "value": "Laudos"},
    "Imagens": {"id": "2376502000005584872", "value": "Imagens"}
}


def montar_payload_com_ids_descobertos(dados, integracoes_options=None, importacoes_options=None):
    """
    Versão do montar_payload que monta objetos corretos para campos de múltipla seleção
    """
    # Usar opções fornecidas ou fallback para as padrões
    if integracoes_options is None:
        integracoes_options = INTEGRACOES_OPTIONS
    if importacoes_options is None:
        importacoes_options = IMPORTACOES_OPTIONS
    
    # Resto da lógica igual ao montar_payload original...
    try:
        start_date_obj = datetime.strptime(dados['start_date'], '%d-%m-%Y')
        start_date_api_format = start_date_obj.strftime('%Y-%m-%d')
    except Exception:
        start_date_api_format = date.today().strftime('%Y-%m-%d')

    produto = dados.get('produto', '')
    if produto in ('netRIS e AnimatiPACS', 'AnimatiPACS/netRIS'):
        solucoes_contratadas = 'AnimatiPACS/netRIS'
    elif produto == 'netRIS':
        solucoes_contratadas = 'netRIS'
    elif produto == 'AnimatiPACS':
        solucoes_contratadas = 'AnimatiPACS'
    else:
        solucoes_contratadas = str(produto or '')

    # Importações com formato de objeto correto
    importacoes_list = []
    if dados.get('import_imagens') and "Imagens" in importacoes_options:
        importacoes_list.append(importacoes_options["Imagens"])
    if dados.get('import_prontuarios') and "Prontuários" in importacoes_options:
        importacoes_list.append(importacoes_options["Prontuários"])
    if dados.get('import_cadastros') and "Cadastros" in importacoes_options:
        importacoes_list.append(importacoes_options["Cadastros"])
    if dados.get('import_laudos') and "Laudos" in importacoes_options:
        importacoes_list.append(importacoes_options["Laudos"])

    # Data de virada
    data_virada_fmt = None
    raw_virada = dados.get('data_de_virada') or dados.get('data_virada')
    if raw_virada:
        for fmt in ('%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y'):
            try:
                data_vir = datetime.strptime(raw_virada, fmt)
                data_virada_fmt = data_vir.strftime('%Y-%m-%d')
                break
            except Exception:
                continue

    custom_fields = {
        "solucoes_contratadas": solucoes_contratadas,
        "havera_integracao": "Sim" if dados.get('integracao_status') == 's' else "Não",  # String, não boolean
        "havera_importacao": "Sim" if dados.get('importacao') == 's' else "Não",
        "projects_cf_0001": "Sim" if dados.get('integracao_status') == 's' else "Não",
        "link_do_google": dados.get('link_google') or dados.get('link_google_drive') or dados.get('link'),
        "GP": dados.get('gp_selecionado', ''),
        "Código Cliente": dados.get('codigo_contrato_numero', ''),
    }
    
    if importacoes_list:
        custom_fields["importacoes"] = importacoes_list

    if data_virada_fmt:
        custom_fields["data_de_virada"] = data_virada_fmt

    # Integrações com formato de objeto correto
    if dados.get('integracao_status') == 's':
        integracoes_list = []
        if dados.get('integ_worklist') and "Worklist" in integracoes_options:
            integracoes_list.append(integracoes_options["Worklist"])
        if dados.get('integ_laudos') and "Retorno de Laudo" in integracoes_options:
            integracoes_list.append(integracoes_options["Retorno de Laudo"])
        if dados.get('integ_lab') and "Laboratório" in integracoes_options:
            integracoes_list.append(integracoes_options["Laboratório"])
        if dados.get('integ_teleradiologia') and "Teleradiologia" in integracoes_options:
            integracoes_list.append(integracoes_options["Teleradiologia"])
        if dados.get('integ_outros') and "Outros" in integracoes_options:
            integracoes_list.append(integracoes_options["Outros"])
        
        if integracoes_list:
            custom_fields["integracoes"] = integracoes_list

    # UDF fields - manter apenas IDs para UDF
    custom_fields_udf = {
        "UDF_CHAR2": custom_fields.get("solucoes_contratadas"),
        "UDF_CHAR4": custom_fields.get("havera_integracao"),
        "UDF_CHAR5": custom_fields.get("havera_importacao"),
        "UDF_CHAR3": custom_fields.get("link_do_google"),
    }
    
    # Para UDF, usar apenas os IDs
    if importacoes_list:
        ids_importacoes = [item["id"] for item in importacoes_list]
        custom_fields_udf["UDF_MULTI2"] = ids_importacoes
    
    if custom_fields.get("integracoes"):
        ids_integracoes = [item["id"] for item in custom_fields["integracoes"]]
        custom_fields_udf["UDF_MULTI1"] = ids_integracoes

    template_id = escolher_template_zoho(dados)

    payload = {
        "name": construir_titulo_projeto(dados),
        "description": construir_descricao(dados),
        "start_date": start_date_api_format,
        "copy_from": str(template_id or ''),
        "project_type": "active",
        "project_group": {
            "id": GRUPOS_ZOHO.get(
                "Hibrido" if ("e" in dados.get('produto', '') or dados.get('produto') == 'AnimatiPACS/netRIS') else ("RIS" if "RIS" in dados.get('produto', '') else "PACS")
            )
        },
        "layout": {"id": "2376502000005584766"},
        "owner": {"zpuid": DONOS_PROJETO[dados['gp_selecionado']]},
        "is_rollup_project": True,
        "tags": [{"id": 2376502000001291513}],
        "custom_fields": custom_fields,
        "custom_fields_udf": custom_fields_udf,
    }
    
    # Adicionar campos customizados também no nível raiz
    payload.update(custom_fields)
    
    return payload


def construir_titulo_projeto(dados):
    sufixo_map = {
        "netRIS": "NR",
        "AnimatiPACS": "AP",
        "netRIS e AnimatiPACS": "NR/AP",
        "AnimatiPACS/netRIS": "NR/AP",
    }
    sufixo = sufixo_map.get(dados['produto'], "")
    return f"{dados['codigo_contrato_numero']} - {dados['nome_cliente']} - {sufixo}"


def construir_descricao(dados):
    # Espelha a lógica atual do utils, mas sem dependências extras
    pacs_check = "[X]" if 'PACS' in dados['produto'] else "[ ]"
    ris_check = "[X]" if 'RIS' in dados['produto'] else "[ ]"
    servidor_local = "(X)" if dados['servidor'] == 'Local' else "( )"
    servidor_cloud_animati = "(X)" if dados['servidor'] == 'Cloud Animati' else "( )"
    servidor_cloud_terceiros = "(X)" if dados['servidor'] == 'Cloud Terceiros' else "( )"
    integracao_sim = "(X)" if dados['integracao_status'] == 's' else "( )"
    importacao_sim = "(X)" if dados['importacao'] == 's' else "( )"
    integracao_nao = "( )" if dados['integracao_status'] == 's' else "(X)"
    importacao_nao = "( )" if dados['importacao'] == 's' else "(X)"

    detalhes_integracao = ""
    if dados['integracao_status'] == 's':
        worklist_check = "[X]" if dados.get('integ_worklist') else "[ ]"
        laudos_check = "[X]" if dados.get('integ_laudos') else "[ ]"
        lab_check = "[X]" if dados.get('integ_lab') else "[ ]"
        telerad_check = "[X]" if dados.get('integ_teleradiologia') else "[ ]"
        outros_check = "[X]" if dados.get('integ_outros') else "[ ]"
        detalhes_integracao = (f"<p><b>Se Sim, selecione as integrações:</b></p><ul>"
                               f"<li>{worklist_check} Worklist</li>"
                               f"<li>{laudos_check} Retorno de Laudo</li>"
                               f"<li>{lab_check} Laboratório</li>"
                               f"<li>{telerad_check} Teleradiologia</li>"
                               f"<li>{outros_check} Outros</li></ul>")

    detalhes_importacao = ""
    if dados['importacao'] == 's':
        cadastros_check = "[X]" if dados.get('import_cadastros') else "[ ]"
        prontuarios_check = "[X]" if dados.get('import_prontuarios') else "[ ]"
        laudos_check = "[X]" if dados.get('import_laudos') else "[ ]"
        imagens_check = "[X]" if dados.get('import_imagens') else "[ ]"
        detalhes_importacao = (f"<p><b>Se Sim, selecione os itens para importação:</b></p><ul>"
                               f"<li>{cadastros_check} Cadastros</li>"
                               f"<li>{prontuarios_check} Prontuários</li>"
                               f"<li>{laudos_check} Laudos</li>"
                               f"<li>{imagens_check} Imagens</li></ul>")

    obs_texto = ""
    if dados.get('observacoes') and dados['observacoes'].strip():
        obs_formatado = dados['observacoes'].strip().replace('\\n', '<br>')
        obs_texto = f"<p><b>Observações Adicionais:</b></p><p>{obs_formatado}</p>"

    descricao_html = (f"<h2>Descrição do Projeto</h2>"
                      f"<p><b>Ferramentas Contratadas:</b></p>"
                      f"<ul><li>{pacs_check} AnimatiPACS</li><li>{ris_check} netRIS</li><li>[ ] netPACS</li></ul>"
                      f"<p><b>Servidor:</b></p>"
                      f"<ul><li>{servidor_local} Local</li><li>{servidor_cloud_animati} Cloud Animati</li><li>{servidor_cloud_terceiros} Cloud Terceiros</li></ul>"
                      f"<p><b>Haverá integração?</b></p><ul><li>{integracao_sim} Sim</li><li>{integracao_nao} Não</li></ul>"
                      f"{detalhes_integracao}"
                      f"<p><b>Haverá importação?</b></p><ul><li>{importacao_sim} Sim</li><li>{importacao_nao} Não</li></ul>"
                      f"{detalhes_importacao}"
                      f"<p><b>Link da pasta do Google:</b></p><p>{dados.get('link_google', 'Link não gerado')}</p>"
                      f"{obs_texto}")
    return " ".join(descricao_html.split())


def escolher_template_zoho(dados):
    produto = dados['produto']
    importacao = dados['importacao'] == 's'
    integracao = dados['integracao_status'] == 's'
    if produto == 'netRIS':
        if importacao and integracao: return MODELOS_ZOHO.get("Implantação RIS (COM importação e COM integração)")
        if importacao and not integracao: return MODELOS_ZOHO.get("Implantação RIS (COM importação e SEM integração)")
        return MODELOS_ZOHO.get("Implantação RIS (SEM importação e SEM integração)")
    if produto == 'AnimatiPACS':
        if importacao and integracao: return MODELOS_ZOHO.get("Implantação PACS ( IMPORTAÇÃO + INTEGRAÇÃO) - UNIFICADO FINAL")
        if importacao and not integracao: return MODELOS_ZOHO.get("Implantação PACS (COM importação e SEM integração) - UNIFICADO FINAL")
        if not importacao and integracao: return MODELOS_ZOHO.get("Implantação PACS (COM integração e SEM importação) - Unificado FINAL")
        return MODELOS_ZOHO.get("Implantação PACS (SEM importação e SEM integração) - UNIFICADO FINAL")
    if produto in ('netRIS e AnimatiPACS', 'AnimatiPACS/netRIS'):
        if importacao: return MODELOS_ZOHO.get("Implantação RIS + PACS (COM importação) - UNIFICADO Final")
        return MODELOS_ZOHO.get("Implantação RIS + PACS (SEM importação ) - UNIFICADO FINAL")
    return None


def montar_payload(dados):
    """Versão original mantida para compatibilidade - usa IDs padrão"""
    return montar_payload_com_ids_descobertos(dados)


if __name__ == '__main__':
    # Dados de exemplo para dry-run
    dados = {
        'produto': 'AnimatiPACS/netRIS',
        'integracao_status': 's',
        'importacao': 's',
        'integ_worklist': True,
        'integ_laudos': True,
        'integ_lab': False,
        'integ_teleradiologia': True,
        'integ_outros': False,
        'import_cadastros': True,
        'import_prontuarios': True,
        'import_laudos': False,
        'import_imagens': True,
        'gp_selecionado': 'Giovani de Sousa',
        'codigo_contrato_numero': '1234',
        'nome_cliente': 'Cliente Dry-Run',
        'start_date': '19-09-2025',
        'servidor': 'Cloud Animati',
        'link_google': 'https://drive.google.com/fake-folder',
        'observacoes': 'Projeto de teste dry-run',
        'data_de_virada': '25/09/2025',
    }

    payload = montar_payload(dados)
    print("=== PAYLOAD GERADO (DRY-RUN) ===")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    print("\n=== CUSTOM FIELDS DETALHADO ===")
    print("Campos customizados:")
    for k, v in payload.get("custom_fields", {}).items():
        print(f"  {k}: {v}")
    
    print("\nCampos UDF:")
    for k, v in payload.get("custom_fields_udf", {}).items():
        print(f"  {k}: {v}")
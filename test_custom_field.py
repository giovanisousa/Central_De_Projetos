#!/usr/bin/env python3
"""
Script para testar a atualização de custom fields no Zoho Projects.
Usado para debug do campo 'Data Liberação Servidor' no projeto 2376502000005544019.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import utils
import requests
from datetime import date
from config import ZOHO_PORTAL_ID

def main():
    project_id = "2376502000005544019"  # Projeto de teste
    data_atual = date.today().strftime('%Y-%m-%d')

    print(f"Testando atualização do custom field no projeto {project_id}")
    print(f"Data atual: {data_atual}")

    try:
        # Obter access token
        access_token = utils.obter_access_token()
        if not access_token:
            print("Erro: Não foi possível obter o access token")
            return

        # Como a API de custom fields não funcionou, tentar diretamente com labels conhecidos
        target_labels = ["UDF_DATE4", "data_liberacao_servidor", "Data Liberação Servidor"]

        for target_label in target_labels:
            try:
                print(f"Tentando atualizar com label: '{target_label}'")
                # Atualizar o campo
                result = utils.atualizar_custom_field_projeto(access_token, project_id, target_label, data_atual)
                print(f"Sucesso com '{target_label}'!")
                break  # Se sucesso, parar
            except Exception as e:
                print(f"Falhou com '{target_label}': {e}")
                continue
        else:
            print("Nenhum label funcionou")
            return

        # Atualizar o campo
        print(f"Atualizando campo '{target_label}' para '{data_atual}'...")
        result = utils.atualizar_custom_field_projeto(access_token, project_id, target_label, data_atual)
        print("Atualização realizada com sucesso!")
        print(f"Resposta: {result}")

        # Tentar encontrar campos customizados disponíveis
        print("Tentando descobrir campos customizados disponíveis...")
        headers = {
            "Authorization": f"Zoho-oauthtoken {access_token}",
            "Content-Type": "application/json"
        }

        # Tentar API de custom fields geral
        try:
            url_fields = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/customfields"
            resp_fields = requests.get(url_fields, headers=headers, timeout=30)
            if resp_fields.status_code == 200:
                fields_data = resp_fields.json()
                fields = fields_data.get('custom_fields', [])
                print(f"Campos customizados encontrados: {len(fields)}")
                for field in fields:
                    field_id = field.get('id')
                    field_name = field.get('name', '')
                    field_type = field.get('type', '')
                    if 'date' in field_type.lower() or 'UDF_DATE' in field_name:
                        print(f"  Campo de data: {field_name} (ID: {field_id}, Tipo: {field_type})")
            else:
                print(f"Erro na API de custom fields: {resp_fields.status_code}")
        except Exception as e:
            print(f"Erro ao buscar campos customizados: {e}")

        # Verificar se o campo existe tentando uma atualização simples
        print("Testando se o campo existe com uma atualização simples...")
        test_payload = {"custom_fields": {target_label: data_atual}}
        url_patch = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
        resp_test = requests.patch(url_patch, headers=headers, json=test_payload, timeout=30)
        if resp_test.status_code in (200, 201):
            print("Campo existe e foi atualizado com sucesso!")
        else:
            print(f"Campo pode não existir ou erro na atualização: {resp_test.status_code} - {resp_test.text}")
            # Tentar com UDF_DATE1 até UDF_DATE10
            print("Tentando outros campos UDF_DATE...")
            for i in range(1, 11):
                test_label = f"UDF_DATE{i}"
                test_payload = {"custom_fields": {test_label: data_atual}}
                resp_test = requests.patch(url_patch, headers=headers, json=test_payload, timeout=30)
                if resp_test.status_code in (200, 201):
                    print(f"Campo {test_label} existe e foi atualizado!")
                    break
                elif resp_test.status_code == 400:
                    error_data = resp_test.json() if resp_test.text else {}
                    if "invalid" in str(error_data).lower():
                        print(f"Campo {test_label} não é válido")
                    else:
                        print(f"Campo {test_label} pode existir mas houve erro: {error_data}")

    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()

    # Testar atualização de um campo que sabemos que existe
    print("Testando atualização do campo 'data_de_virada' que aparece no GET...")
    try:
        result = utils.atualizar_custom_field_projeto(access_token, project_id, "data_de_virada", "2025-12-01")
        print("Campo 'data_de_virada' atualizado com sucesso!")
    except Exception as e:
        print(f"Falhou ao atualizar 'data_de_virada': {e}")

    # Testar atualização do campo data_liberacao_servidor
    print("Testando atualização do campo 'data_liberacao_servidor'...")
    try:
        result = utils.atualizar_custom_field_projeto(access_token, project_id, "data_liberacao_servidor", data_atual)
        print("Campo 'data_liberacao_servidor' atualizado com sucesso!")
    except Exception as e:
        print(f"Falhou ao atualizar 'data_liberacao_servidor': {e}")

    # Testar atualização de um campo padrão para ver se PATCH funciona
    print("Testando atualização de um campo padrão 'description'...")
    try:
        headers = {
            "Authorization": f"Zoho-oauthtoken {access_token}",
            "Content-Type": "application/json"
        }
        url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
        payload = {"description": "TESTE - Descrição alterada para debug"}
        resp = requests.patch(url, headers=headers, json=payload, timeout=30)
        if resp.status_code in (200, 201):
            print("Campo 'description' atualizado com sucesso!")
        else:
            print(f"Falhou ao atualizar 'description': {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"Erro ao atualizar 'description': {e}")

    # Verificar se apareceu no GET
    print("Verificando se o campo apareceu no GET do projeto...")
    try:
        project_url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
        resp_get = requests.get(project_url, headers=headers, timeout=30)
        if resp_get.status_code == 200:
            project_data = resp_get.json()
            if 'project' in project_data:
                project_data = project_data['project']
            print("Campos no GET após atualização:")
            print(f"  description: {project_data.get('description', '')[:100]}...")
            for key, value in project_data.items():
                if key.startswith('UDF_') or 'data' in key.lower():
                    print(f"  {key}: {value}")
        else:
            print(f"Erro ao obter projeto: {resp_get.status_code}")
    except Exception as e:
        print(f"Erro ao verificar projeto: {e}")

    # Aguardar um pouco e tentar GET novamente
    print("Aguardando 5 segundos e fazendo GET novamente...")
    import time
    time.sleep(5)
    try:
        resp_get2 = requests.get(project_url, headers=headers, timeout=30)
        if resp_get2.status_code == 200:
            project_data2 = resp_get2.json()
            if 'project' in project_data2:
                project_data2 = project_data2['project']
            print("Campos no segundo GET:")
            print(f"  description: {project_data2.get('description', '')[:100]}...")
            for key, value in project_data2.items():
                if key.startswith('UDF_') or 'data' in key.lower():
                    print(f"  {key}: {value}")
        else:
            print(f"Erro no segundo GET: {resp_get2.status_code}")
    except Exception as e:
        print(f"Erro no segundo GET: {e}")

    # Verificar custom fields disponíveis para o projeto
    print("Verificando custom fields disponíveis para o projeto...")
    try:
        custom_fields = utils.obter_custom_fields_projeto(access_token, project_id)
        print(f"Encontrados {len(custom_fields)} custom fields:")
        for cf in custom_fields:
            field_name = cf.get('field_name', '')
            label_name = cf.get('label_name', '')
            field_type = cf.get('field_type', '')
            print(f"  - {field_name} ({label_name}) - Tipo: {field_type}")
    except Exception as e:
        print(f"Erro ao obter custom fields: {e}")

    # Verificar se o campo foi realmente atualizado (GET do projeto)
    print("Verificando valores atuais do projeto...")
    try:
        project_url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
        resp_get = requests.get(project_url, headers=headers, timeout=30)
        if resp_get.status_code == 200:
            project_data = resp_get.json()
            if 'project' in project_data:
                project_data = project_data['project']
            print("Campos customizados no GET (se disponíveis):")
            for key, value in project_data.items():
                if key.startswith('UDF_') or 'data' in key.lower():
                    print(f"  {key}: {value}")
        else:
            print(f"Erro ao obter projeto: {resp_get.status_code}")
    except Exception as e:
        print(f"Erro ao verificar projeto: {e}")

if __name__ == "__main__":
    main()
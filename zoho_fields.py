"""
Módulo para atualização de campos personalizados no Zoho Projects.
"""
from typing import Any
import requests
from config import ZOHO_PORTAL_ID
from utils import obter_access_token

def atualizar_campo_projeto(project_id: str, field_label: str, value: str, access_token: str | None = None) -> dict:
    """
    Atualiza um campo do projeto usando a API do Zoho Projects.

    Args:
        project_id: ID do projeto
        field_label: Nome do campo como exibido no Zoho
        value: Novo valor para o campo (formato yyyy-mm-dd)
        access_token: Token de acesso opcional
    """
    if not access_token:
        access_token = obter_access_token()

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json",
    }

    # URL para API de campos customizados usando PATCH
    url = f"https://projectsapi.zoho.com/api/v3/portal/{ZOHO_PORTAL_ID}/projects/{project_id}"
    
    # Converte a data para o formato do Zoho se necessário
    if value and "-" in value and len(value.split("-")) == 3:
        year, month, day = value.split("-")
        if len(year) == 4:  # Confirma que é mesmo yyyy-mm-dd
            value = f"{day}-{month}-{year}"

    # Payload usando o formato que funciona com PATCH
    payload = {
        "custom_fields": {
            field_label: value
        }
    }

    print(f"[DEBUG] Atualizando campo customizado:")
    print(f"[DEBUG] URL: {url}")
    print(f"[DEBUG] Field Label: {field_label}")
    print(f"[DEBUG] Value: {value}")
    print(f"[DEBUG] Payload: {payload}")

    # Faz a requisição PATCH para atualizar o campo
    response = requests.patch(url, headers=headers, json=payload)
    
    if not response.ok:
        raise RuntimeError(
            f"Falha ao atualizar campo: {response.status_code} {response.text[:300]}"
        )

    return response.json()


if __name__ == "__main__":
    # Teste de atualização
    project_id = "2376502000005544019"
    result = atualizar_campo_projeto(
        project_id=project_id,
        field_label="Data Liberação Servidor",
        value="2025-10-08"  # Usando formato yyyy-mm-dd
    )
    print("\nResposta da API:")
    print(result)
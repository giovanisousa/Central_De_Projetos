# Variáveis de Ambiente para Deploy no Railway

Este documento lista todas as informações sensíveis e configurações do projeto que devem ser transformadas em variáveis de ambiente para um deploy seguro e flexível na Railway.

## 1. Flask e Sessão
- `FLASK_SECRET_KEY`: <sua-chave-secreta>  # Exemplo: 8f3c2e1a4b5d6e7f8a9b0c1d2e3f4a5b
- `SESSION_TYPE`: filesystem
- `SESSION_FILE_DIR`: c:/Users/Giovani Souza/Documents/Central_De_Projetos/.flask_session

## 2. Diretórios e Caminhos
- `BASE_DIR`: ./
- `UPLOAD_FOLDER`: ./uploads
- `TEMPLATE_DOCS_PATH`: ./templates_doc
- `CREDENTIALS_PATH`: ./credentials.json
- `ZOHO_TOKEN_PATH`: ./zoho_refresh_token.txt

## 3. Google API
- `ID_PASTA_PAI_NETRIS`: 1I2dSlvfxmphkBdYIjsovCSxizE3Iu-pc
- `ID_PASTA_PAI_ANIMATIPACS`: 1hBBRW5wYQ1_aw1PWiJ5oEbDURLYcfCbL
- `ID_PLANILHA_PROJETOS`: 11GzE9NQXKNBgOWArcvX8ErmfzALIApbmh7m8PANUVLc
- `ID_PLANILHA_PROJETOS_SECUNDARIA`: 12_eu6174i93OUK3CnN_u9CVeH0ZtOaUANC34JHXgBjM
- `GOOGLE_CALENDAR_ID`: animati.com.br_g82f2343cocg9tgr5soplsl210@group.calendar.google.com
- `SCOPES_GOOGLE`: openid, https://www.googleapis.com/auth/userinfo.email, https://www.googleapis.com/auth/userinfo.profile, https://www.googleapis.com/auth/drive, https://www.googleapis.com/auth/spreadsheets, https://www.googleapis.com/auth/documents, https://www.googleapis.com/auth/calendar

## 4. Zoho API
- `ZOHO_CLIENT_ID`: 1000.FHMB9OAB6ARPGZN1IS5ORTIKNTT1DR
- `ZOHO_CLIENT_SECRET`: 70226965d09b04444346222d9b4846c86a5d31d2fe
- `ZOHO_PORTAL_ID`: 868230290
- `ZOHO_PROJECTS_CUSTOM_WEB_HOST`: https://projects.animati.com.br
- `ZOHO_TOKEN_PATH`: <CAMINHO_DO_TOKEN>

## 5. IDs de Status e Tags do Zoho
- `STATUS_ABERTO_ID`: 2376502000000020089
- `STATUS_EM_ANDAMENTO_ID`: 2376502000000020092
- `STATUS_CANCELADO_ID`: 2376502000000020110
- `STATUS_FINALIZADO_ID`: 2376502000000020116
- `STATUS_OPERACAO_ASSISTIDA_ID`: 2376502000000020119
- `STATUS_AGUARDANDO_CLIENTE_ID`: 2376502000000020107
- `STATUS_PENDENCIA_ID`: 2376502000000020104
- `STATUS_CONCLUIDO_ID`: 2376502000000674703
- `TAG_AGUARDANDO_ONBOARDING_ID`: 2376502000001291513
- `TAG_AGUARDANDO_INFRA_ID`: 2376502000000958355
- `TAG_EM_HOMOLOGACAO_ID`: 2376502000000983053
- `TAG_EM_VIRADA_ID`: 2376502000001228741
- `TAG_PARADO_ID`: 2376502000000983125
- `TAG_AGUARDANDO_ENCERRAMENTO_ID`: 2376502000005304184
- `TAG_IMPLANTACAO`: 2376502000000188201
- `TAG_AGUARDANDO_CRONOGRAMA`: 2376502000006124423

## 6. Outros
- `DEFAULT_TASKS_CUSTOM_VIEW_ID`: 2376502000000046003
- `DONOS_PROJETO`: {"Giovani de Sousa": "2376502000000057291", "Willian dos Anjos": "2376502000000057285"}
- `GRUPOS_ZOHO`: {"PACS": "2376502000000057307", "Hibrido": "2376502000000111007", "RIS": "2376502000000117069"}
- `MODELOS_ZOHO`: {"Implantação RIS (COM importação e SEM integração)": "2376502000004197548", "Implantação RIS (SEM importação e COM integração)": "2376502000004197548", "Implantação RIS (SEM importação e SEM integração)": "2376502000004197548", "Implantação RIS (COM importação e COM integração)": "2376502000004181530", "Implantação RIS + PACS (SEM importação ) - UNIFICADO FINAL": "2376502000004157044", "Implantação PACS (COM importação e SEM integração) - UNIFICADO FINAL": "2376502000004131436", "Implantação PACS (SEM importação e SEM integração) - UNIFICADO FINAL": "2376502000004114904", "Implantação PACS (COM integração e SEM importação) - Unificado FINAL": "2376502000004114562", "Implantação PACS ( IMPORTAÇÃO + INTEGRAÇÃO) - UNIFICADO FINAL": "2376502000004050339", "Implantação RIS + PACS (COM importação) - UNIFICADO Final": "2376502000001362286"}
- `ZOHO_MENTION_USERS`: {"William Floriano": {"usernum": "870213453", "name": "William Floriano"}, "Giovani Sousa": {"usernum": "868816641", "name": "Giovani Sousa"}, "Roger Machado": {"usernum": "870218464", "name": "Roger Machado"}, "Carlo Tristão": {"usernum": "870217691", "name": "Carlo Tristão"}}

## 7. Banco de Dados
- Se houver uso de banco de dados externo, adicionar:
  - `DATABASE_URL` ou `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`

## 8. Outras APIs
- Se houver integração com outros serviços, adicionar:
  - `API_KEY`, `API_SECRET`, `API_URL`, etc.

## 9. Configuração Railway
- Variáveis de ambiente devem ser configuradas no painel do Railway.
- Nunca versionar dados sensíveis (tokens, secrets, senhas) no código.

---

**Recomendações:**
- Utilize `os.environ.get('NOME_VARIAVEL')` para consumir variáveis de ambiente no código.
- Adapte o código para buscar todas as configurações sensíveis via ambiente.
- Documente no README como configurar as variáveis no Railway.

---

*Este documento deve ser revisado e atualizado conforme novas integrações ou alterações de infraestrutura.*

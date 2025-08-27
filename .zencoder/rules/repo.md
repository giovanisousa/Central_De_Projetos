# Repository Information

## Project
- Name: Central_De_Projetos
- Purpose: Automação de onboarding e gestão de projetos (Google Drive + Google Sheets + Zoho Projects) com Flask.

## Main app
- Entry point: app.py
- Server: Flask (porta 5000)
- Templates: templates/index.html (principal)
- Static: static/
- Uploads: uploads/

## Key environment/config
- Google OAuth credentials: credentials.json (na raiz)
- Zoho refresh token file: zoho_refresh_token.txt (na raiz)
- OAUTHLIB_INSECURE_TRANSPORT: definido no app.py para facilitar o callback local

## Google IDs
- ID_PASTA_PAI_NETRIS: 1I2dSlvfxmphkBdYIjsovCSxizE3Iu-pc
- ID_PASTA_PAI_ANIMATIPACS: 1hBBRW5wYQ1_aw1PWiJ5oEbDURLYcfCbL
- ID_PLANILHA_PROJETOS: 11GzE9NQXKNBgOWArcvX8ErmfzALIApbmh7m8PANUVLc
- NOME_ABA_PLANILHA: PAINEL
- LINHA_CABECALHO: 12
- COLUNA_REFERENCIA_PARA_CONTAR_LINHAS: Cliente
- ID_PLANILHA_PROJETOS_SECUNDARIA: 12_eu6174i93OUK3CnN_u9CVeH0ZtOaUANC34JHXgBjM
- NOME_ABA_PLANILHA_SECUNDARIA: Em andamento

## Zoho
- ZOHO_CLIENT_ID: 1000.RCJUGJ7L8JAKEFYN0S21ISWEVMB87W
- ZOHO_CLIENT_SECRET: 206ea2f3276dae6e7b653305b5e4467379c17dbb66
- ZOHO_PORTAL_ID: 868230290

- Status IDs:
  - ABERTO: 2376502000000020089
  - EM_ANDAMENTO: 2376502000000020092
  - CANCELADO: 2376502000000020110
  - FINALIZADO: 2376502000000020116
  - OPERACAO_ASSISTIDA: 2376502000000020119
  - AGUARDANDO_CLIENTE: 2376502000000020107
  - PENDENCIA: 2376502000000020104

- Tag IDs:
  - AGUARDANDO_ONBOARDING: 2376502000001291513
  - AGUARDANDO_INFRA: 2376502000000958355
  - EM_HOMOLOGACAO: 2376502000000983053
  - EM_VIRADA: 2376502000001228741
  - PARADO: 2376502000000983125

- STATUS_CONCLUIDO_ID: 2376502000000674703

- DONOS_PROJETO:
  - Giovani de Sousa: 2376502000000057291
  - Willian dos Anjos: 2376502000000057285

- GRUPOS_ZOHO:
  - PACS: 2376502000000057307
  - Hibrido: 2376502000000111007
  - RIS: 2376502000000117069

- MODELOS_ZOHO:
  - Implantação RIS (COM importação e SEM integração): 2376502000004197548
  - Implantação RIS (SEM importação e COM integração): 2376502000004197548
  - Implantação RIS (SEM importação e SEM integração): 2376502000004197548
  - Implantação RIS (COM importação e COM integração): 2376502000004181530
  - Implantação RIS + PACS (SEM importação ) - UNIFICADO FINAL: 2376502000004157044
  - Implantação PACS (COM importação e SEM integração) - UNIFICADO FINAL: 2376502000004131436
  - Implantação PACS (SEM importação e SEM integração) - UNIFICADO FINAL: 2376502000004114904
  - Implantação PACS (COM integração e SEM importação) - Unificado FINAL: 2376502000004114562
  - Implantação PACS ( IMPORTAÇÃO + INTEGRAÇÃO) - UNIFICADO FINAL: 2376502000004050339
  - Implantação RIS + PACS (COM importação) - UNIFICADO Final: 2376502000001362286

## API routes
- GET /
  - Renderiza index.html com gps e cores_colunas.
- GET /login, /oauth2callback, /logout
- POST /api/criar-projeto
  - Requer login Google; cria estrutura em Drive, atualiza planilhas, cria projeto no Zoho e atribui/conclui tarefas iniciais conforme listas.
- POST /api/carregar_projetos
  - Retorna os projetos do Zoho Projects do GP selecionado organizados por colunas do Kanban.
- POST /api/mover_projeto
  - Placeholder para futura atualização de status no Zoho.

## Frontend
- Template principal: templates/index.html
- CSS: static/css/style.css
- JS: static/js/script_registro.js (ou script.js, conforme template)

## Observações
- O arquivo app_geral.py foi removido após a unificação.
- Ajustes no template podem ser necessários para usar gps e cores_colunas.
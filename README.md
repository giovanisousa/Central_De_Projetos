# Central_De_Projetos

Automação de onboarding e gestão de projetos (Google Drive + Google Sheets + Zoho Projects) com interface web Flask.

## Requisitos
- Python 3.10+
- pip

## Instalação
1. Instale as dependências:
   ```powershell
   pip install -r requirements.txt
   ```
2. Coloque o arquivo de credenciais do Google (`credentials.json`) na raiz do projeto.
3. Garanta que o arquivo de refresh token do Zoho esteja presente: `zoho_refresh_token.txt` (já incluído no repositório).

## Execução
1. Execute o servidor Flask:
   ```powershell
   python "c:\Users\Giovani Souza\Documents\Central_De_Projetos\app.py"
   ```
   - Obs.: o próprio app define `OAUTHLIB_INSECURE_TRANSPORT=1` em modo local.

2. Acesse no navegador:
   - http://localhost:5000

## Uso
- Faça login com Google quando solicitado.
- Selecione o GP e clique em "Carregar Projetos" para preencher o Kanban (dados do Zoho Projects).
- Para criar um novo projeto:
  - Preencha o formulário, selecione o arquivo DEIP (PDF) e envie.
  - A automação criará a pasta no Google Drive, atualizará as planilhas e criará o projeto no Zoho Projects.

## Observações
- Este repositório agora usa apenas `app.py` (o arquivo `app_geral.py` foi removido).
- Caso precise CORS para outro domínio, podemos habilitar no `app.py`.
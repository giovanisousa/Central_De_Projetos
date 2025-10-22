# 🎯 Central de Projetos

Sistema web completo para automação de onboarding e gestão de projetos com integração Google Drive, Google Sheets e Zoho Projects.

---

## 📊 Status do Projeto

**Versão:** 1.0.0  
**Status:** 🟢 **PRONTO PARA PRODUÇÃO**  
**Última Atualização:** Outubro 2025

### Funcionalidades Principais
- ✅ Dashboard Kanban interativo
- ✅ Criação automatizada de projetos
- ✅ Agendamento de implantação com atribuição automática
- ✅ Sincronização com Zoho Projects e Google Services
- ✅ Métricas e indicadores de SLA
- ✅ Sistema de busca e navegação

---

## 📚 Documentação

### 🎯 **COMEÇAR AQUI**
Se você é **gestor** ou precisa **decidir sobre colocar em produção**:
- 📊 **[RESUMO_EXECUTIVO_DEPLOY.md](RESUMO_EXECUTIVO_DEPLOY.md)** - Análise para deploy em produção

Se você quer **entender todas as funcionalidades**:
- 📋 **[LEVANTAMENTO_FUNCIONALIDADES.md](LEVANTAMENTO_FUNCIONALIDADES.md)** - Documentação completa

Se você precisa de **suporte ou troubleshooting**:
- 🐛 **[ISSUES_CONHECIDOS.md](ISSUES_CONHECIDOS.md)** - Bugs conhecidos e workarounds

### 📖 Índice Completo
- 📚 **[INDICE_DOCUMENTACAO.md](INDICE_DOCUMENTACAO.md)** - Índice de toda a documentação disponível

---

## 🚀 Quick Start

### Requisitos
- Python 3.10+
- pip
- Credenciais Google OAuth (`credentials.json`)
- Token Zoho (`zoho_refresh_token.txt`)

### Instalação
```powershell
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Configurar credenciais
# - Colocar credentials.json na raiz
# - Verificar zoho_refresh_token.txt

# 3. Executar aplicação
python app.py
```

### Acesso
```
http://localhost:5000
```

---

## 💡 Funcionalidades Destacadas

### 🎯 Criação de Projetos
- Upload de DEIP (PDF)
- Extração automática de dados
- Criação de estrutura no Google Drive
- Atualização de planilhas Google Sheets
- Criação de projeto no Zoho Projects
- Atribuição automática de tarefas ao GP

### 📊 Dashboard Kanban
- 12 colunas de status
- Drag & Drop para mover projetos
- Indicadores visuais de SLA
- Busca rápida de projetos
- Contadores por coluna
- Barras de progresso por fase

### 🎉 Agendamento de Implantação (NOVO)
- Cálculo automático de datas previstas
- Adição automática de implantadores
- Atribuição automática de tarefas RIS/PACS
- Ajuste de datas de tarefas
- Sincronização completa

### 🔄 Sincronização
- Cache local com SQLite
- Carregamento rápido (< 2 segundos)
- Sincronização automática após movimentações
- Sistema de retry inteligente

---

## 🏗️ Arquitetura

### Backend
- **Framework:** Flask (Python)
- **Database:** SQLite (cache local)
- **APIs:** Google (Drive, Sheets, Calendar, OAuth) + Zoho Projects

### Frontend
- **UI:** HTML5 + CSS3
- **JavaScript:** Vanilla JS (sem frameworks)
- **Design:** Kanban responsivo com drag & drop

### Integrações
- **Google Drive:** Estrutura de pastas automática
- **Google Sheets:** Atualização de planilhas
- **Google Calendar:** Eventos de implantação
- **Zoho Projects:** Gestão completa de projetos

---

## 📋 Próximos Passos

### Para Deploy em Produção
1. Revisar [RESUMO_EXECUTIVO_DEPLOY.md](RESUMO_EXECUTIVO_DEPLOY.md)
2. Seguir checklist de produção
3. Configurar variáveis de ambiente
4. Treinar usuários (2h)
5. Deploy e monitoramento

### Melhorias Futuras (Backlog)
- Dashboard de métricas gerenciais
- Sistema de notificações
- Gestão de equipe via UI
- Relatórios avançados
- Histórico de movimentações

Ver lista completa em [ISSUES_CONHECIDOS.md](ISSUES_CONHECIDOS.md)

---

## 🐛 Suporte

### Issues Conhecidos
2 bugs não-críticos com workarounds funcionais. Ver detalhes em:
- [ISSUES_CONHECIDOS.md](ISSUES_CONHECIDOS.md)

### Contato
- Issues no GitHub
- Documentação completa no repositório

---

## 📄 Licença

[Especificar licença do projeto]

---

**Central de Projetos** - Automação de Onboarding e Gestão de Projetos  
Desenvolvido com ❤️ pela equipe Animati
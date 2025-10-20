# 🚀 GUIA RÁPIDO - Agendar Implantação

## ✅ O Que a Funcionalidade Faz

Automaticamente:
1. ✅ Adiciona **todos os implantadores** (RIS/PACS) ao projeto
2. ✅ Atribui **todas as tarefas** (RIS/PACS) aos implantadores
3. ✅ Move o projeto para "Em Andamento - Implantação"
4. ✅ Atualiza a planilha Google Sheets

## 🎯 Como Usar

### Passo 1: Encontre o Projeto
- Vá para a coluna **"Em Andamento"**
- Localize o projeto que deseja agendar

### Passo 2: Abra o Modal
- Clique no ícone **▶️** (Play) do projeto

### Passo 3: Preencha os Dados
- **Data de início**: Selecione a data
- **Implantador RIS**: Selecione (se projeto tiver RIS)
- **Implantador PACS**: Selecione (se projeto tiver PACS)

### Passo 4: Confirme
- Clique em **"Agendar Implantação"**
- Aguarde ~15-30 segundos
- Veja a mensagem de sucesso! ✅

## 📊 O Que Acontece

### No Zoho Projects:
- **Team**: 7 novos membros adicionados (RIS ou PACS)
- **Tasks**: ~150 tarefas (RIS) ou ~30 tarefas (PACS) atribuídas

### Na Planilha:
- **Dt Inicio Implantação**: Data preenchida
- **Implant Responsável**: Nome registrado

## 🔍 Como Verificar

### No Zoho:
1. Abra o projeto no Zoho Projects
2. Vá em **Team** → Veja os implantadores
3. Vá em **Tasks** → Veja as atribuições

### Na Planilha:
1. Abra a planilha "Central de Projetos"
2. Procure o cliente
3. Confira as colunas atualizadas

## ⚡ Equipes Adicionadas

### RIS (7 pessoas):
- Pablo Pyerri
- Lukas Correa
- Rodrigo Brasil
- Jessika Rodrigues
- Rodrigo Viera Chagas
- Celio Santos
- Fernando Carvalho

### PACS (7 pessoas):
- Aneidia Sa
- Camilo Osaida
- Fernando Carvalho
- Jorge Trindade
bastos Junior
- Luis Noronha
- Nery Paolo
- Walter Ferreira

## 📋 Tarefas Atribuídas

### RIS - 158 tarefas, incluindo:
- Cadastrar Convênios
- Cadastrar Médicos
- Configurar Permissões
- Validação de Empresa
- + 154 outras tarefas

### PACS - 31 tarefas, incluindo:
- Configurar Viewer AnimatiPACS
- Validar Worklist
- Configurar Layouts de Impressão
- Treinamento de Cadastro
- + 27 outras tarefas

## ⚠️ Observações Importantes

1. **Usuários já existentes**: Não causa erro, continua normalmente
2. **Tarefas não encontradas**: Registrado em log, não interrompe
3. **Tipo de projeto**: Detectado automaticamente pelo nome
4. **Tempo de execução**: 15-30 segundos (não feche a janela!)

## 🆘 Problemas Comuns

### "Falha ao agendar implantação"
- Verifique sua conexão com internet
- Verifique se está autenticado
- Tente novamente em alguns segundos

### Usuários não aparecem no Zoho
- Aguarde 1-2 minutos (propagação)
- Atualize a página do Zoho
- Verifique os logs do servidor

### Tarefas não atribuídas
- Verifique se as tarefas existem no projeto
- Verifique os logs para ver quais não foram encontradas
- Algumas podem ter nomes diferentes

## 📞 Suporte

Em caso de dúvidas:
1. Verifique o console do servidor (logs detalhados)
2. Consulte `RESUMO_AGENDAR_IMPLANTACAO.md`
3. Consulte `IMPLEMENTACAO_AGENDAR_IMPLANTACAO.md`

---

**Desenvolvido para facilitar sua vida!** 🎉

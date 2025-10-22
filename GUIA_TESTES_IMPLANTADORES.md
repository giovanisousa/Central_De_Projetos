# 🧪 Guia de Testes: Implantadores nos Cards

## ✅ Testes Automatizados - CONCLUÍDOS

Todos os testes automatizados passaram com sucesso:
- ✅ Colunas do banco de dados criadas
- ✅ Função de formatação de implantadores
- ✅ Preparação de payload para Zoho
- ✅ Arquivos CSS criados e validados

---

## 🔍 Testes Manuais - PRÓXIMOS PASSOS

### 1. Teste de Agendamento de Implantação

#### Passos:
1. Inicie a aplicação: `python app.py`
2. Acesse o dashboard
3. Localize um projeto na coluna "Servidor Liberado"
4. Clique no botão "Agendar Implantação"
5. Selecione o tipo: **RIS** ou **PACS**
6. Confirme o agendamento

#### Validações:
- [ ] Modal abre corretamente
- [ ] Botão de agendamento funciona
- [ ] Mensagem de sucesso é exibida
- [ ] Logs mostram: "✅ Custom field 'implantador_ris' atualizado no Zoho"

#### Logs Esperados:
```
🚀 Iniciando agendamento de implantação RIS para projeto 2376502000005544019
👥 2 implantadores serão adicionados
✅ 2 usuários adicionados com sucesso
✅ Custom field 'implantador_ris' atualizado no Zoho
📋 10 tarefas para atribuir
✅ 10 tarefas atribuídas com sucesso
```

---

### 2. Verificação no Zoho Projects

#### Passos:
1. Acesse o Zoho Projects
2. Navegue até o projeto que foi agendado
3. Abra a aba de "Custom Fields" ou "Detalhes"
4. Procure pelos campos:
   - `implantador_ris`
   - `implantador_pacs`

#### Validações:
- [ ] Campos aparecem no projeto
- [ ] Implantadores estão listados nos campos
- [ ] Formato está correto (User Pick List)

---

### 3. Sincronização de Projetos

#### Passos:
1. Execute a sincronização de projetos
2. Aguarde a conclusão
3. Verifique os logs

#### Comando:
```bash
# Se houver endpoint de sincronização:
curl http://localhost:5000/sincronizar

# Ou através do agendamento automático
```

#### Validações:
- [ ] Sincronização executa sem erros
- [ ] Banco de dados é atualizado
- [ ] Campos `implantador_ris` e `implantador_pacs` são preenchidos

#### SQL para Verificar:
```sql
SELECT 
    nome, 
    status_atual,
    implantador_ris,
    implantador_pacs
FROM projects 
WHERE implantador_ris IS NOT NULL 
   OR implantador_pacs IS NOT NULL;
```

---

### 4. Validação Visual nos Cards

#### Passos:
1. Acesse o dashboard
2. Navegue até a coluna **"Em Andamento - Implantação"**
3. Localize os cards de projetos com implantadores

#### Validações Visuais:

##### ✅ Card COM implantadores:
```
┌─────────────────────────────────┐
│ 📦 Cliente ABC - Projeto X      │
│ 📦 netRIS, netPACS             │
│ 👤 João Silva (GP)             │
│ 📅 15/10/2025                  │
│                                 │
│ ⏳ 5 dias   📅 45 dias         │
│                                 │
│ 👥 📱 João Silva  💻 Maria      │ ← NOVO!
│    [Badge roxo]   [Badge rosa] │
│                                 │
│ 🏁 20/10/2025                  │
└─────────────────────────────────┘
```

- [ ] Seção de implantadores aparece
- [ ] Ícone de usuários (👥) está presente
- [ ] Badges RIS têm cor roxa/gradiente
- [ ] Badges PACS têm cor rosa/gradiente
- [ ] Nomes dos implantadores estão visíveis
- [ ] Layout não quebra com nomes longos

##### ✅ Card SEM implantadores:
- [ ] Seção de implantadores NÃO aparece
- [ ] Layout normal do card é mantido

---

### 5. Teste de Mudança de Implantador

#### Passos:
1. Acesse o Zoho Projects
2. Abra um projeto com implantadores
3. Altere o valor do campo `implantador_ris` ou `implantador_pacs`
4. Salve as alterações
5. Execute sincronização no sistema
6. Verifique o card no dashboard

#### Validações:
- [ ] Mudança é refletida no banco de dados
- [ ] Card exibe o novo implantador
- [ ] Histórico de alterações está disponível no Zoho

---

### 6. Teste de Múltiplos Implantadores

#### Cenário: Projeto com RIS e PACS

#### Validações:
- [ ] Ambos os badges aparecem no card
- [ ] Cores são diferenciadas (roxo RIS, rosa PACS)
- [ ] Ícones são diferenciados (📱 RIS, 💻 PACS)
- [ ] Layout acomoda ambos sem quebrar

---

### 7. Teste de Responsividade

#### Passos:
1. Redimensione a janela do navegador
2. Teste em diferentes resoluções
3. Verifique o comportamento mobile

#### Validações:
- [ ] Badges se ajustam ao espaço disponível
- [ ] Texto não transborda
- [ ] Layout permanece legível
- [ ] Em telas pequenas, fonte diminui adequadamente

---

### 8. Teste de Performance

#### Validações:
- [ ] Cards carregam rapidamente (sem API calls extras)
- [ ] Não há travamentos ao renderizar múltiplos cards
- [ ] Sincronização não impacta performance

---

## 🐛 Troubleshooting

### Problema: Implantadores não aparecem no card

**Possíveis causas:**
1. Sincronização ainda não executou após agendamento
2. Campos custom no Zoho não foram atualizados
3. Projeto não está na coluna "Em Andamento - Implantação"

**Solução:**
```bash
# 1. Verificar banco de dados
sqlite3 zoho_cache.db "SELECT id, nome, implantador_ris, implantador_pacs FROM projects WHERE id = 'PROJECT_ID';"

# 2. Forçar sincronização
# (executar endpoint ou aguardar sincronização automática)

# 3. Verificar logs
tail -f app.log | grep implantador
```

---

### Problema: Erro ao atualizar custom fields no Zoho

**Possíveis causas:**
1. Access token expirado
2. Campos custom não existem no Zoho
3. Formato de payload incorreto

**Solução:**
```bash
# 1. Verificar access token
python -c "import utils; print(utils.obter_access_token())"

# 2. Verificar campos no Zoho via API
python -c "
import utils
token = utils.obter_access_token()
fields = utils.obter_custom_fields_projeto(token, 'PROJECT_ID')
print(fields)
"
```

---

### Problema: CSS não está aplicado

**Possíveis causas:**
1. Arquivo CSS não foi importado no HTML
2. Cache do navegador

**Solução:**
```bash
# 1. Verificar importação no HTML
grep "implantadores.css" templates/index.html

# 2. Limpar cache do navegador
# Ctrl + Shift + R (hard refresh)
# Ou abrir em modo anônimo
```

---

## 📊 Checklist Final de Validação

### Backend:
- [ ] ✅ Migrações do banco executadas
- [ ] ✅ Função de formatação testada
- [ ] ✅ Payload preparado corretamente
- [ ] 🔄 Agendamento envia ao Zoho
- [ ] 🔄 Sincronização atualiza banco

### Frontend:
- [ ] ✅ CSS criado e importado
- [ ] 🔄 Cards exibem implantadores
- [ ] 🔄 Badges diferenciados por tipo
- [ ] 🔄 Layout responsivo

### Integração:
- [ ] 🔄 Dados do Zoho → Banco → Frontend
- [ ] 🔄 Mudanças refletidas corretamente
- [ ] 🔄 Performance adequada

**Legenda:**
- ✅ Validado automaticamente
- 🔄 Aguardando teste manual

---

## 🚀 Comandos Úteis

```bash
# Iniciar aplicação
python app.py

# Executar testes automatizados
python test_implantadores.py

# Verificar banco de dados
sqlite3 zoho_cache.db "SELECT * FROM projects LIMIT 5;"

# Logs em tempo real
tail -f app.log

# Limpar cache (se necessário)
rm -rf __pycache__
rm zoho_cache.db  # CUIDADO: Apaga todo o banco!
```

---

**Data de Criação**: 21 de Outubro de 2025
**Status**: Pronto para testes manuais

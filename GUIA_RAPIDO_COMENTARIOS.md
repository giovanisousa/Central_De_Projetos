# ⚡ GUIA RÁPIDO - Começar a Usar Comentários

## 🎯 3 Passos Para Começar

### ✅ PASSO 1: Atualizar Token OAuth (5 minutos)

1. **Cole esta URL no navegador:**
   ```
   https://accounts.zoho.com/oauth/v2/auth?scope=ZohoProjects.portals.READ,ZohoProjects.projects.ALL,ZohoProjects.tasks.ALL,ZohoProjects.tags.ALL,ZohoProjects.tasklists.ALL,ZohoProjects.users.ALL,ZohoProjects.teams.ALL,ZohoProjects.timesheets.ALL,ZohoProjects.milestones.ALL,ZohoProjects.comments.ALL,ZohoSearch.securesearch.READ&client_id=1000.FHMB9OAB6ARPGZN1IS5ORTIKNTT1DR&response_type=code&access_type=offline&redirect_uri=https://localhost
   ```

2. **Autorize a aplicação** e copie o `code` da URL de redirecionamento
   ```
   Exemplo: https://localhost/?code=1000.abc123...xyz789
   ```

3. **Execute no PowerShell:**
   ```powershell
   .\gerar_token_zoho.ps1
   ```
   *(Edite o arquivo e cole o code)*

4. **Salve o novo refresh token** quando solicitado

---

### ✅ PASSO 2: Testar Sincronização (2 minutos)

Execute o script de testes:
```bash
python test_comentarios.py
```

Escolha a opção **2** (Executar TODOS os testes) e selecione um projeto.

**Resultados esperados:**
```
✅ Sincronização: PASSOU
✅ Busca no Banco: PASSOU
✅ Adicionar Comentário: PASSOU
✅ Verificar Data: PASSOU

🎉 TODOS OS TESTES PASSARAM!
```

---

### ✅ PASSO 3: Sincronizar Todos os Projetos (10-30 minutos)

Execute a sincronização completa:
```bash
python sync_comentarios.py
```

Escolha a opção **2** (Sincronizar TODOS os projetos)

**Aguarde a conclusão:**
```
📊 RESUMO DA SINCRONIZAÇÃO
✅ Projetos processados: 150
📝 Total de comentários sincronizados: 3842
❌ Projetos com erros: 0
```

---

## 🚀 Uso Rápido (Snippets)

### Buscar Comentários de um Projeto

```python
from database import get_comentarios_projeto

comentarios = get_comentarios_projeto("SEU_PROJETO_ID")
for c in comentarios:
    print(f"{c['autor_nome']}: {c['conteudo']}")
```

### Adicionar Comentário

```python
from sync_comentarios import adicionar_comentario_projeto_zoho

adicionar_comentario_projeto_zoho(
    projeto_id="SEU_PROJETO_ID",
    conteudo="Seu comentário aqui"
)
```

### Sincronizar Comentários de um Projeto

```python
from sync_comentarios import sincronizar_comentarios_projeto

sincronizar_comentarios_projeto("SEU_PROJETO_ID")
```

---

## 📚 Documentação Completa

- **`README_COMENTARIOS.md`** - Documentação técnica completa
- **`ATUALIZACAO_ESCOPOS_COMENTARIOS.md`** - Guia detalhado de OAuth
- **`RESUMO_IMPLEMENTACAO_COMENTARIOS.md`** - Resumo executivo

---

## ⚠️ Troubleshooting Rápido

### Erro: "Invalid OAuth Scope"

**Solução:** Você pulou o Passo 1. Atualize o token OAuth.

### Erro: "Project not found"

**Solução:** Verifique se o ID do projeto está correto.

### Comentários não aparecem

**Solução:** Execute a sincronização (Passo 3).

---

## ✅ Pronto!

Agora você pode:
- ✅ Buscar comentários de qualquer projeto
- ✅ Adicionar novos comentários via código
- ✅ Sincronizar automaticamente com o Zoho

**Próximo passo:** Criar interface web (Parte 2)

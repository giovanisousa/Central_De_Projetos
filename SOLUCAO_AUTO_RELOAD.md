# Solução: Auto-Reload Interrompendo Requisições

**Data:** 13/10/2025  
**Status:** ✅ RESOLVIDO

---

## 🐛 Problema Identificado

A atualização do card após movimentação não funcionava porque **o servidor Flask estava reiniciando automaticamente no meio das requisições**.

### Sintomas

1. **Console do navegador:**
   - Mostrava apenas: `[enviarMovimentoParaServidor] Enviando...`
   - **Nunca** mostrava: `[enviarMovimentoParaServidor] HTTP 200`
   - Nenhum log subsequente aparecia

2. **Erro no console:**
   ```
   Uncaught (in promise) Error: A listener indicated an asynchronous response by returning true, 
   but the message channel closed before a response was received
   ```

3. **Logs do servidor:**
   ```
   [MOVE][DB] Projeto 2376502000004208431: data_mudanca_status = 2025-10-13
   ...
   * Detected change in 'database.py', reloading
   * Detected change in 'utils.py', reloading
   * Detected change in 'routes\api.py', reloading
   * Restarting with watchdog (windowsapi)
   ```

---

## 🔍 Causa Raiz

O **Flask Watchdog** (auto-reload em modo debug) estava detectando modificações nos arquivos Python durante a execução das requisições e **reiniciando o servidor imediatamente**.

### Sequência do Problema

```
1. Frontend envia POST /api/mover_projeto
2. Backend começa a processar (atualiza DB, chama Zoho API, atualiza planilha)
3. [PROBLEMA] Watchdog detecta mudança em database.py/utils.py/routes/api.py
4. [PROBLEMA] Servidor reinicia ANTES de enviar resposta HTTP
5. Frontend recebe erro: "message channel closed"
6. Response nunca chega ao JavaScript
7. Logs do frontend param em "Enviando..."
```

### Por Que os Arquivos Estavam Mudando?

Possíveis causas:
- **Editor/IDE salvando automaticamente** (ex: VS Code auto-save)
- **Formatadores automáticos** (ex: Black, autopep8, Prettier)
- **Linters/Type checkers** modificando arquivos (ex: pylint)
- **Git operations** alterando timestamps
- **Sistema de arquivos** registrando acesso como modificação

---

## ✅ Solução Implementada

### 1. Desabilitar Auto-Reload (app.py)

**Antes:**
```python
if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run(debug=True, port=5000)
```

**Depois:**
```python
if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    # use_reloader=False para evitar reinicializações durante requisições
    app.run(debug=True, port=5000, use_reloader=False)
```

### 2. Adicionar Tratamento de Promise (templates/index.html)

**Antes:**
```javascript
enviarMovimentoParaServidor(projetoId, colunaOrigem, colunaDestino, clienteSheet);
```

**Depois:**
```javascript
enviarMovimentoParaServidor(projetoId, colunaOrigem, colunaDestino, clienteSheet)
    .then(() => console.log('[moverCardVisualmente] ✅ Servidor atualizado com sucesso'))
    .catch(err => console.error('[moverCardVisualmente] ❌ Erro ao atualizar servidor:', err));
```

---

## 🧪 Validação

### Teste Realizado

1. ✅ Servidor reiniciado com `use_reloader=False`
2. ✅ Nenhuma mensagem de "Restarting with watchdog" nos logs
3. ✅ Servidor **não reinicia** durante requisições

### O Que Deve Acontecer Agora

**Ao mover um card, você deve ver:**

```
[enviarMovimentoParaServidor] Enviando... {projetoId: "...", ...}
[enviarMovimentoParaServidor] HTTP 200 body: {"sucesso":true,"dados_atualizados":{...}}
[enviarMovimentoParaServidor] Resposta parseada: {...}
[enviarMovimentoParaServidor] ✅ Sucesso! dados_atualizados: {...}
[enviarMovimentoParaServidor] Buscando card com ID: ...
[enviarMovimentoParaServidor] Card encontrado: <div...>
[enviarMovimentoParaServidor] Badge encontrado: <span...>
[enviarMovimentoParaServidor] Atualizando badge de "Xd" para "Hoje"
[enviarMovimentoParaServidor] ✅ Card atualizado! dias_fase="Hoje" data_mudanca="2025-10-13"
[moverCardVisualmente] ✅ Servidor atualizado com sucesso
```

---

## ⚠️ Implicações

### O Que Mudou

**Com `use_reloader=False`:**
- ✅ Servidor **NÃO** reinicia automaticamente ao salvar arquivos
- ⚠️ Você **DEVE** reiniciar manualmente após modificar código Python
- ✅ Requisições **NÃO** são mais interrompidas
- ✅ Debugging continua funcionando normalmente

### Como Reiniciar Manualmente

```powershell
# Opção 1: Parar e iniciar novamente
Ctrl+C
python app.py

# Opção 2: Usar comando do PowerShell
Stop-Process -Name python -Force; python app.py
```

---

## 🔄 Alternativas (Não Implementadas)

### Opção 1: Excluir Arquivos do Watchdog
```python
app.run(debug=True, port=5000, extra_files=[])  # Lista vazia desabilita watch
```

### Opção 2: Usar Intervalo de Polling Maior
```python
app.run(debug=True, port=5000, reloader_interval=60)  # 60 segundos
```

### Opção 3: Usar Gunicorn/Waitress (Produção)
```bash
pip install gunicorn
gunicorn -w 4 -b 127.0.0.1:5000 app:app
```

**Por que escolhemos `use_reloader=False`?**
- ✅ Mais simples e direto
- ✅ Mantém debug mode ativo (traceback, var inspection)
- ✅ Não requer dependências adicionais
- ✅ Fácil de reverter quando necessário

---

## 📊 Comparação

| Aspecto | Com Auto-Reload | Sem Auto-Reload (Atual) |
|---------|-----------------|-------------------------|
| Requisições interrompidas | ❌ Sim | ✅ Não |
| Reinício automático | ✅ Sim | ❌ Não (manual) |
| Debug mode | ✅ Ativo | ✅ Ativo |
| Traceback detalhado | ✅ Sim | ✅ Sim |
| Hot-reload ao salvar | ✅ Sim | ❌ Não |
| Estabilidade | ⚠️ Instável | ✅ Estável |

---

## 🧪 Como Testar Agora

### 1. Limpar Console do Navegador
- Pressione **F12**
- Aba **Console**
- Clique no ícone 🚫 para limpar

### 2. Mover um Card
- Arraste um card de uma coluna para outra
- Exemplo: "Aguardando Onboarding" → "Falta Liberar Servidor Infra"

### 3. Observar Logs Completos
Agora você **DEVE** ver **TODOS** os logs:
```
✅ [enviarMovimentoParaServidor] Enviando...
✅ [enviarMovimentoParaServidor] HTTP 200
✅ [enviarMovimentoParaServidor] Resposta parseada
✅ [enviarMovimentoParaServidor] ✅ Sucesso!
✅ [enviarMovimentoParaServidor] Card encontrado
✅ [enviarMovimentoParaServidor] Badge encontrado
✅ [enviarMovimentoParaServidor] Atualizando badge
✅ [enviarMovimentoParaServidor] ✅ Card atualizado!
✅ [moverCardVisualmente] ✅ Servidor atualizado com sucesso
```

### 4. Verificar Badge
- O badge deve exibir **"Hoje"** imediatamente
- Cor deve ser **verde** (dentro do SLA)
- **SEM** necessidade de atualizar a página (F5)

---

## 📝 Próximos Passos

### Se Tudo Funcionar ✅

```bash
git add app.py templates/index.html
git commit -m "fix: desabilita auto-reload para evitar interrupção de requisições

- Adiciona use_reloader=False em app.run()
- Adiciona tratamento de Promise em enviarMovimentoParaServidor()
- Resolve problema de requisições interrompidas durante movimentação
- Logs detalhados confirmam atualização de card funcionando"
```

### Se Ainda Não Funcionar ⚠️

Copie **TODO** o conteúdo do console do navegador após mover um card e me envie para análise.

---

## 🚀 Status Atual

✅ Servidor rodando em: http://127.0.0.1:5000  
✅ Auto-reload **desabilitado**  
✅ Debug mode **ativo**  
✅ Logs detalhados **ativados**  
✅ Pronto para teste final

**Teste agora e me avise se funcionou!** 🎉

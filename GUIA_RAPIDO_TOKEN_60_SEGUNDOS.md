# ⚡ GUIA ULTRA-RÁPIDO: Gerar Token SEM Expirar

**Problema:** Grant code expira em 60 segundos!  
**Solução:** Prepare tudo ANTES de gerar o code.

---

## 🎯 Método Rápido (Recomendado)

### PASSO 1: Prepare o Comando PowerShell

Cole isto no PowerShell, mas **NÃO execute ainda**:

```powershell
try {
    $params = @{
        grant_type = "authorization_code"
        client_id = "1000.FHMB9OAB6ARPGZN1IS5ORTIKNTT1DR"
        client_secret = "70226965d09b04444346222d9b4846c86a5d31d2fe"
        redirect_uri = "https://localhost"
        code = "3f2c6749ef8190381ac0e7f1ae6d3359.5aded841402c989876949563ad169833"
    }
    $response = Invoke-RestMethod -Uri "https://accounts.zoho.com/oauth/v2/token" -Method Post -Body $params -ErrorAction Stop
    Write-Output "=== SUCESSO ==="
    Write-Output "REFRESH TOKEN:"
    Write-Output $response.refresh_token
    Write-Output ""
    Write-Output "Agora execute:"
    Write-Output "Set-Content -Path 'zoho_refresh_token.txt' -Value '$($response.refresh_token)'"
} catch {
    $errorResponse = $_.ErrorDetails.Message | ConvertFrom-Json -ErrorAction SilentlyContinue
    Write-Output "ERRO: $($errorResponse.error)"
    if ($errorResponse.error -eq "invalid_code") {
        Write-Output "Grant code EXPIROU! Gere um novo (volte ao passo 2)"
    }
}
```

### PASSO 2: Gere o Grant Code

Abra esta URL no navegador:
```
https://accounts.zoho.com/oauth/v2/auth?scope=ZohoProjects.portals.READ,ZohoProjects.projects.ALL,ZohoProjects.tasks.ALL,ZohoProjects.tags.ALL,ZohoProjects.tasklists.ALL,ZohoProjects.users.ALL,ZohoProjects.teams.ALL,ZohoProjects.timesheets.ALL,ZohoProjects.milestones.ALL,ZohoSearch.securesearch.READ&client_id=1000.FHMB9OAB6ARPGZN1IS5ORTIKNTT1DR&response_type=code&access_type=offline&redirect_uri=https://localhost
```

### PASSO 3: Copie o Code RAPIDAMENTE

Você será redirecionado para:
```
https://localhost/?code=1000.abc123def456.xyz789&location=...
```

⚠️ **ATENÇÃO:** Copie APENAS a parte DEPOIS do `code=`

**CORRETO:** `1000.abc123def456.xyz789` (código completo com 1000.)  
**ERRADO:** `abc123def456` (sem o 1000. - isso NÃO funciona!)

O Zoho espera o code completo incluindo o prefixo `1000.`

### PASSO 4: Execute IMEDIATAMENTE

No PowerShell preparado no PASSO 1:
1. Substitua `SEU_CODE_AQUI` pelo code copiado (INCLUINDO o `1000.`)
2. Exemplo: `code = "1000.abc123def456.xyz789"`
3. Pressione ENTER imediatamente

**Tempo: < 60 segundos do passo 2 ao 4!** ⏱️

⚠️ **IMPORTANTE:** 
- Use o code COMPLETO (com `1000.` no início)
- Cada code só funciona UMA vez
- Se errar, precisa gerar novo code (voltar ao PASSO 2)

### PASSO 5: Salve o Refresh Token

O comando mostrará:
```
=== SUCESSO ===
REFRESH TOKEN:
1000.xxxxx.yyyyy

Agora execute:
Set-Content -Path 'zoho_refresh_token.txt' -Value '1000.xxxxx.yyyyy'
```

**Copie e execute** o comando `Set-Content` mostrado.

### PASSO 6: Valide

```powershell
python test_add_user_detailed.py
```

✅ Se der certo: Status 200/201  
❌ Se erro 401: O refresh token não foi salvo corretamente

---

## 🚨 Se Deu "invalid_code"

**Causa:** Code expirou (passou de 60s) OU já foi usado antes.

**Solução:** Volte ao PASSO 2 e gere um NOVO code. Cada code só funciona UMA vez!

---

## ⏱️ Timeline de Expiração

```
0s   - Você autoriza a aplicação
0s   - Zoho gera o grant code
60s  - Grant code EXPIRA ❌
```

**Você tem 60 segundos para:**
1. Copiar o code da URL
2. Colar no PowerShell
3. Executar o comando
4. Obter o refresh token

---

## 💡 Dica Pro

Tenha dois monitores ou use Alt+Tab rápido:
- **Tela 1:** Navegador (para gerar code)
- **Tela 2:** PowerShell (comando já preparado)

Fluxo:
1. Autoriza no navegador
2. Alt+Tab para PowerShell
3. Ctrl+C (copia code)
4. Volta PowerShell
5. Cola code e executa
6. **Total: ~10 segundos** ✅

---

## ✅ Checklist Final

- [ ] Comando PowerShell preparado (PASSO 1)
- [ ] URL aberta no navegador (PASSO 2)
- [ ] Aplicação autorizada
- [ ] Code copiado da URL (**COM** o prefixo `1000.`)
- [ ] Code colado no PowerShell (substituindo `SEU_CODE_AQUI`)
- [ ] Comando executado em < 60s
- [ ] Viu "=== SUCESSO ==="
- [ ] Refresh token exibido (começa com `1000.`)
- [ ] Refresh token salvo em `zoho_refresh_token.txt`
- [ ] Teste executado: `python test_add_user_detailed.py`
- [ ] Resultado: Status 200/201 ✅

## ❌ Erros Comuns

1. **Code sem o `1000.`** → Resultado: `invalid_code`
2. **Code usado 2x** → Resultado: `invalid_code` (gere novo)
3. **Code expirado (>60s)** → Resultado: `invalid_code` (gere novo)
4. **Refresh token vazio** → Provavelmente deu erro mas não apareceu (veja logs)

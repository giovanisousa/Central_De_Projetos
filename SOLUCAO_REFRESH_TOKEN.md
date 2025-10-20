# 🔧 SOLUÇÃO: Refresh Token Não Retorna

## 🔍 Diagnóstico

Se você não está recebendo o `refresh_token` na resposta, pode ser:

1. ✅ **Grant code já foi usado** (mais comum)
2. ✅ **Grant code expirou** (60 segundos)
3. ✅ **Grant code incorreto** (sem o prefixo 1000.)

---

## ✅ SOLUÇÃO PASSO A PASSO - Método Garantido

### 📌 PASSO 1: Gerar Grant Code

**Copie e cole esta URL no navegador:**

```
https://accounts.zoho.com/oauth/v2/auth?scope=ZohoProjects.portals.READ,ZohoProjects.projects.ALL,ZohoProjects.tasks.ALL,ZohoProjects.tags.ALL,ZohoProjects.tasklists.ALL,ZohoProjects.users.ALL,ZohoProjects.teams.ALL,ZohoProjects.timesheets.ALL,ZohoProjects.milestones.ALL,ZohoSearch.securesearch.READ&client_id=1000.FHMB9OAB6ARPGZN1IS5ORTIKNTT1DR&response_type=code&access_type=offline&redirect_uri=https://localhost
```

**Você verá:**
- Tela de autorização do Zoho
- Clique em **"Aceitar"** ou **"Allow"**

**Depois será redirecionado para:**
```
https://localhost/?code=1000.abc123xyz789def456...&location=us&...
```

**COPIE TODO o código** (a parte depois de `code=` até o próximo `&`)

Exemplo: `1000.abc123xyz789def456ghi...`

---

### 📌 PASSO 2: Preparar o Comando (NÃO EXECUTE AINDA!)

**Copie este comando COMPLETO no PowerShell** (mas não pressione Enter ainda):

```powershell
# COMANDO COMPLETO - LEIA ANTES DE EXECUTAR!
$grantCode = "1000.aedc88c6440308ed3108bdf6397e6eb5.f94b2bab2ddaeb78d32f38e3c213546d"  # ← TROQUE ESTA LINHA!

$params = @{
    grant_type = "authorization_code"
    client_id = "1000.FHMB9OAB6ARPGZN1IS5ORTIKNTT1DR"
    client_secret = "70226965d09b04444346222d9b4846c86a5d31d2fe"
    redirect_uri = "https://localhost"
    code = $grantCode
}

Write-Host "🔄 Trocando grant code por refresh token..." -ForegroundColor Cyan

$response = Invoke-RestMethod -Uri "https://accounts.zoho.com/oauth/v2/token" -Method Post -Body $params

Write-Host ""
Write-Host "📋 RESPOSTA COMPLETA:" -ForegroundColor Yellow
Write-Host ($response | ConvertTo-Json -Depth 5)
Write-Host ""

if ($response.refresh_token) {
    Write-Host "✅ ✅ ✅ SUCESSO! ✅ ✅ ✅" -ForegroundColor Green
    Write-Host ""
    Write-Host "REFRESH TOKEN:" -ForegroundColor Yellow
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Host $response.refresh_token -ForegroundColor White
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Host ""
    
    # Salvar automaticamente
    Set-Content -Path "zoho_refresh_token.txt" -Value $response.refresh_token
    Write-Host "✅ Salvo em zoho_refresh_token.txt!" -ForegroundColor Green
    
} elseif ($response.error) {
    Write-Host "❌ ERRO DO ZOHO:" -ForegroundColor Red
    Write-Host "   Tipo: $($response.error)" -ForegroundColor Yellow
    Write-Host ""
    
    switch ($response.error) {
        "invalid_code" {
            Write-Host "⚠️  O grant code JÁ FOI USADO ou EXPIROU!" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "SOLUÇÃO:" -ForegroundColor Cyan
            Write-Host "  1. Volte ao navegador"
            Write-Host "  2. Cole a URL novamente (gerará NOVO code)"
            Write-Host "  3. Copie o NOVO code"
            Write-Host "  4. Substitua na linha: `$grantCode = ""..."
            Write-Host "  5. Execute IMEDIATAMENTE (< 60 segundos)"
        }
        "invalid_client" {
            Write-Host "⚠️  Client ID ou Secret incorretos" -ForegroundColor Yellow
        }
        default {
            Write-Host "⚠️  Erro desconhecido" -ForegroundColor Yellow
        }
    }
    
} elseif ($response.access_token -and -not $response.refresh_token) {
    Write-Host "⚠️ ⚠️ ⚠️ ATENÇÃO! ⚠️ ⚠️ ⚠️" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Recebemos ACCESS TOKEN mas NÃO refresh token!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "CAUSA: Grant code já foi usado anteriormente" -ForegroundColor Red
    Write-Host ""
    Write-Host "SOLUÇÃO:" -ForegroundColor Cyan
    Write-Host "  Você precisa de um NOVO grant code (não pode reutilizar!)"
    Write-Host "  Volte ao PASSO 1 e gere um código NOVO"
    
} else {
    Write-Host "❌ Resposta inesperada!" -ForegroundColor Red
}
```

---

### 📌 PASSO 3: Substituir o Grant Code

**Na linha:**
```powershell
$grantCode = "COLE_SEU_CODE_AQUI"  # ← TROQUE ESTA LINHA!
```

**Substitua** `COLE_SEU_CODE_AQUI` pelo code que você copiou no PASSO 1.

**Exemplo:**
```powershell
$grantCode = "1000.abc123xyz789def456ghi..."
```

⚠️ **IMPORTANTE:** Não remova as aspas `""`!

---

### 📌 PASSO 4: Executar IMEDIATAMENTE

Depois de substituir o code, **pressione Enter IMEDIATAMENTE** (dentro de 60 segundos)!

---

## ✅ O Que Você Deve Ver

### Se der CERTO:
```
✅ ✅ ✅ SUCESSO! ✅ ✅ ✅

REFRESH TOKEN:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1000.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Salvo em zoho_refresh_token.txt!
```

### Se der ERRO:
```
❌ ERRO DO ZOHO:
   Tipo: invalid_code

⚠️  O grant code JÁ FOI USADO ou EXPIROU!
```

**Neste caso:** Volte ao PASSO 1 e gere um NOVO code!

---

## 🐛 Troubleshooting

### Problema: "Só recebo access_token, não refresh_token"

**Causa:** Grant code já foi usado antes.

**Solução:**
1. Abra uma aba ANÔNIMA/PRIVADA no navegador
2. Cole a URL de autorização
3. Autorize novamente
4. Copie o NOVO code
5. Use IMEDIATAMENTE

---

### Problema: "Grant code expira muito rápido"

**Dica:** Prepare o comando PowerShell ANTES de gerar o code:

```
1. Cole o comando no PowerShell (com "COLE_SEU_CODE_AQUI")
2. DEIXE preparado
3. Vá no navegador
4. Gere o code
5. Volte no PowerShell (Alt+Tab)
6. Cole o code
7. Execute IMEDIATAMENTE
```

**Tempo total:** ~15 segundos ✅

---

### Problema: "Erro 'invalid_client'"

**Causa:** Client ID ou Secret incorretos.

**Verificação:**
- Client ID: `1000.FHMB9OAB6ARPGZN1IS5ORTIKNTT1DR`
- Client Secret: `70226965d09b04444346222d9b4846c86a5d31d2fe`

Se estiverem corretos, pode ser problema de configuração no console do Zoho.

---

## 🎯 Checklist de Validação

Antes de executar, verifique:

- [ ] Cole a URL no navegador
- [ ] Clicou em "Aceitar/Allow"
- [ ] Foi redirecionado para `https://localhost/?code=...`
- [ ] Copiou TODO o code (com `1000.` no início)
- [ ] Comando PowerShell preparado
- [ ] Substituiu `COLE_SEU_CODE_AQUI` pelo code real
- [ ] Executou em < 60 segundos após gerar o code
- [ ] NÃO reutilizou um code antigo

---

## 💡 Dica Final

**Se continuar sem funcionar:**

Execute este comando para ver a resposta completa e me mostre:

```powershell
$code = "SEU_CODE_AQUI"
$params = @{
    grant_type = "authorization_code"
    client_id = "1000.FHMB9OAB6ARPGZN1IS5ORTIKNTT1DR"
    client_secret = "70226965d09b04444346222d9b4846c86a5d31d2fe"
    redirect_uri = "https://localhost"
    code = $code
}
$response = Invoke-RestMethod -Uri "https://accounts.zoho.com/oauth/v2/token" -Method Post -Body $params
$response | ConvertTo-Json -Depth 10
```

Me mostre a saída completa e eu te ajudo a identificar o problema!

# ⚡ COMANDO FINAL - COPIE ISTO!

## 📋 Comando PowerShell Melhorado

Cole isto no PowerShell e substitua o code quando gerar:

```powershell
# ========================================
# GERAR REFRESH TOKEN DO ZOHO
# ========================================

try {
    # ⚠️ SUBSTITUA o valor de 'code' pelo código que você recebeu
    # O code DEVE incluir o prefixo "1000."
    # Exemplo: "1000.abc123def456.xyz789"
    
    $params = @{
        grant_type = "authorization_code"
        client_id = "1000.FHMB9OAB6ARPGZN1IS5ORTIKNTT1DR"
        client_secret = "70226965d09b04444346222d9b4846c86a5d31d2fe"
        redirect_uri = "https://localhost"
        code = "1000.2c25bea6d8e11f355fd58fedb70f854b.242de3d8f48e420a1a1115082875266d"  # ← TROQUE AQUI!
    }
    
    Write-Output "Trocando grant code por refresh token..."
    Write-Output ""
    
    $response = Invoke-RestMethod -Uri "https://accounts.zoho.com/oauth/v2/token" -Method Post -Body $params -ErrorAction Stop
    
    # Verificar se tem refresh_token
    if (-not $response.refresh_token) {
        Write-Output "❌ ERRO: Resposta não contém refresh_token!"
        Write-Output "Resposta recebida:"
        Write-Output ($response | ConvertTo-Json -Depth 5)
        exit
    }
    
    Write-Output "✅ ✅ ✅ SUCESSO! ✅ ✅ ✅"
    Write-Output ""
    Write-Output "REFRESH TOKEN (copie isto):"
    Write-Output "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    Write-Output $response.refresh_token
    Write-Output "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    Write-Output ""
    Write-Output "ACCESS TOKEN (válido por 1 hora):"
    Write-Output $response.access_token
    Write-Output ""
    Write-Output "Expira em: $($response.expires_in) segundos"
    Write-Output ""
    Write-Output "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    Write-Output "PRÓXIMO PASSO - Execute este comando:"
    Write-Output "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    Write-Output ""
    Write-Output "Set-Content -Path 'zoho_refresh_token.txt' -Value '$($response.refresh_token)'"
    Write-Output ""
    
} catch {
    Write-Output "❌ ❌ ❌ ERRO! ❌ ❌ ❌"
    Write-Output ""
    Write-Output "Mensagem: $($_.Exception.Message)"
    Write-Output ""
    
    # Tentar extrair erro do Zoho
    $errorResponse = $_.ErrorDetails.Message | ConvertFrom-Json -ErrorAction SilentlyContinue
    
    if ($errorResponse.error) {
        Write-Output "Erro do Zoho: $($errorResponse.error)"
        Write-Output ""
        
        switch ($errorResponse.error) {
            "invalid_code" {
                Write-Output "⚠️  CAUSA: Grant code inválido, expirado ou já usado"
                Write-Output ""
                Write-Output "SOLUÇÕES:"
                Write-Output "1. Verifique se copiou o code COMPLETO (com '1000.' no início)"
                Write-Output "2. O code expira em 60 segundos - gere um novo"
                Write-Output "3. Cada code só funciona UMA vez - não reutilize"
                Write-Output ""
                Write-Output "Volte ao navegador e gere um NOVO code!"
            }
            "invalid_client" {
                Write-Output "⚠️  CAUSA: Client ID ou Secret incorretos"
                Write-Output "Verifique as credenciais no código"
            }
            "redirect_uri_mismatch" {
                Write-Output "⚠️  CAUSA: redirect_uri não está configurado no Zoho"
                Write-Output "Deve ser: https://localhost"
            }
            default {
                Write-Output "Erro desconhecido. Resposta completa:"
                Write-Output ($errorResponse | ConvertTo-Json -Depth 5)
            }
        }
    } else {
        Write-Output "Detalhes completos:"
        Write-Output $_.Exception
    }
}
```

---

## 🚀 PASSO A PASSO RÁPIDO

### 1. Copie o comando acima no PowerShell (NÃO execute ainda)

### 2. Gere o grant code - Cole esta URL no navegador:

```
https://accounts.zoho.com/oauth/v2/auth?scope=ZohoProjects.portals.READ,ZohoProjects.projects.ALL,ZohoProjects.tasks.ALL,ZohoProjects.tags.ALL,ZohoProjects.tasklists.ALL,ZohoProjects.users.ALL,ZohoProjects.teams.ALL,ZohoProjects.timesheets.ALL,ZohoProjects.milestones.ALL,ZohoSearch.securesearch.READ&client_id=1000.FHMB9OAB6ARPGZN1IS5ORTIKNTT1DR&response_type=code&access_type=offline&redirect_uri=https://localhost
```

### 3. Copie o code da URL de redirecionamento

Exemplo de URL após autorizar:
```
https://localhost/?code=1000.abc123def456.xyz789&location=us&...
```

Copie: `1000.abc123def456.xyz789` (código completo!)

### 4. No PowerShell, substitua `COLE_SEU_CODE_COMPLETO_AQUI` e execute

### 5. Se der sucesso, execute o comando mostrado para salvar:

```powershell
Set-Content -Path 'zoho_refresh_token.txt' -Value 'SEU_REFRESH_TOKEN'
```

### 6. Valide:

```powershell
python test_add_user_detailed.py
```

---

## ✅ O Que Você Deve Ver

```
✅ ✅ ✅ SUCESSO! ✅ ✅ ✅

REFRESH TOKEN (copie isto):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1000.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PRÓXIMO PASSO - Execute este comando:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Set-Content -Path 'zoho_refresh_token.txt' -Value '1000.xxxx...'
```

---

## ❌ Se Ver Erro

```
❌ ❌ ❌ ERRO! ❌ ❌ ❌

Erro do Zoho: invalid_code

⚠️  CAUSA: Grant code inválido, expirado ou já usado
```

**Solução:** Gere um NOVO code (volte ao passo 2)

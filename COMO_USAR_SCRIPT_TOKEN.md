# 🚀 SOLUÇÃO: Terminal Não Fecha + Cores + Salvamento Automático

## 📁 Arquivo Criado: `gerar_token_zoho.ps1`

Este script PowerShell:
- ✅ Não fecha o terminal automaticamente
- ✅ Usa cores para destacar informações
- ✅ Oferece salvamento automático do token
- ✅ Espera você pressionar uma tecla para fechar

---

## 🎯 Como Usar (MÉTODO RECOMENDADO)

### Passo 1: Gere o Grant Code

Cole esta URL no navegador:
```
https://accounts.zoho.com/oauth/v2/auth?scope=ZohoProjects.portals.READ,ZohoProjects.projects.ALL,ZohoProjects.tasks.ALL,ZohoProjects.tags.ALL,ZohoProjects.tasklists.ALL,ZohoProjects.users.ALL,ZohoProjects.teams.ALL,ZohoProjects.timesheets.ALL,ZohoProjects.milestones.ALL,ZohoSearch.securesearch.READ&client_id=1000.FHMB9OAB6ARPGZN1IS5ORTIKNTT1DR&response_type=code&access_type=offline&redirect_uri=https://localhost
```

### Passo 2: Copie o Code

Após autorizar, você será redirecionado para:
```
https://localhost/?code=1000.abc123def456.xyz789&...
```

Copie: `1000.abc123def456.xyz789`

### Passo 3: Edite o Script

Abra `gerar_token_zoho.ps1` e substitua:
```powershell
code = "COLE_SEU_CODE_AQUI"  # ← TROQUE AQUI!
```

Por:
```powershell
code = "1000.abc123def456.xyz789"  # ← SEU CODE AQUI!
```

### Passo 4: Execute o Script

**Opção A - Clique Duplo:**
1. Botão direito em `gerar_token_zoho.ps1`
2. Selecione "Executar com PowerShell"

**Opção B - Linha de Comando:**
```powershell
cd "C:\Users\Giovani Souza\Documents\Central_De_Projetos"
.\gerar_token_zoho.ps1
```

### Passo 5: Resultado

Se der **SUCESSO**, você verá (em cores):

```
✅ ✅ ✅ SUCESSO! ✅ ✅ ✅

REFRESH TOKEN (copie isto):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1000.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Deseja salvar o refresh token AGORA? (S/N)
```

Digite `S` e pressione Enter para salvar automaticamente!

### Passo 6: Valide

```powershell
python test_add_user_detailed.py
```

---

## 🔧 Alternativa: Comando Direto (Sem Fechar Terminal)

Se preferir não usar o script, execute isto no PowerShell:

```powershell
$code = "COLE_SEU_CODE_AQUI"

$params = @{
    grant_type = "authorization_code"
    client_id = "1000.FHMB9OAB6ARPGZN1IS5ORTIKNTT1DR"
    client_secret = "70226965d09b04444346222d9b4846c86a5d31d2fe"
    redirect_uri = "https://localhost"
    code = $code
}

$response = Invoke-RestMethod -Uri "https://accounts.zoho.com/oauth/v2/token" -Method Post -Body $params

if ($response.refresh_token) {
    Write-Host "✅ SUCESSO!" -ForegroundColor Green
    Write-Host ""
    Write-Host "REFRESH TOKEN:" -ForegroundColor Yellow
    Write-Host $response.refresh_token -ForegroundColor White
    Write-Host ""
    
    # Perguntar se quer salvar
    $salvar = Read-Host "Salvar em zoho_refresh_token.txt? (S/N)"
    if ($salvar -eq "S") {
        Set-Content -Path "zoho_refresh_token.txt" -Value $response.refresh_token
        Write-Host "✅ Salvo!" -ForegroundColor Green
    }
} else {
    Write-Host "❌ ERRO:" -ForegroundColor Red
    Write-Host ($response | ConvertTo-Json) -ForegroundColor Yellow
}
```

**Vantagem:** 
- Terminal não fecha
- Você pode copiar o token com calma
- Pergunta se quer salvar

---

## 💡 Dicas

### 1. Se o Terminal Fechar Muito Rápido

Execute assim:
```powershell
powershell -NoExit -File "gerar_token_zoho.ps1"
```

O `-NoExit` mantém o PowerShell aberto mesmo após o script terminar.

### 2. Se Precisar Ver o Token Depois

O refresh token fica salvo em:
```
C:\Users\Giovani Souza\Documents\Central_De_Projetos\zoho_refresh_token.txt
```

Para ver:
```powershell
Get-Content zoho_refresh_token.txt
```

### 3. Se Der Erro "Execution Policy"

Execute primeiro:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Depois execute o script normalmente.

---

## ✅ Checklist

- [ ] Gerou grant code no navegador
- [ ] Copiou code completo (com `1000.`)
- [ ] Editou `gerar_token_zoho.ps1` com o code
- [ ] Executou o script
- [ ] Viu mensagem de SUCESSO em verde
- [ ] Respondeu "S" para salvar o token
- [ ] Token salvo em `zoho_refresh_token.txt`
- [ ] Executou `python test_add_user_detailed.py`
- [ ] Teste retornou Status 200/201

---

## 🎨 Vantagens do Script .ps1

| Recurso | Script .ps1 | Comando direto |
|---------|-------------|----------------|
| Não fecha terminal | ✅ | ❌ |
| Cores | ✅ | ⚠️ Parcial |
| Salvamento automático | ✅ | ❌ |
| Reutilizável | ✅ | ❌ |
| Tratamento de erros | ✅ | ⚠️ Básico |

---

**Arquivo:** `gerar_token_zoho.ps1` (já criado!)  
**Próximo:** Edite o arquivo, execute, e copie seu refresh token! 🚀

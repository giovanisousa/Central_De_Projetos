# 🔍 Como Saber se o Grant Code é NOVO ou REPETIDO

## ⚠️ O Problema

Quando você acessa a URL de autorização, o Zoho pode:
1. ✅ Gerar um NOVO grant code
2. ❌ Redirecionar com o MESMO code antigo (se você já autorizou antes)

---

## 🎯 SOLUÇÃO GARANTIDA - Forçar Grant Code NOVO

### Método 1: Usar Aba Anônima/Privada ⭐ RECOMENDADO

1. **Abra uma aba ANÔNIMA** no navegador:
   - Chrome/Edge: `Ctrl + Shift + N`
   - Firefox: `Ctrl + Shift + P`

2. **Cole a URL de autorização** na aba anônima

3. **Faça login no Zoho** (na aba anônima)

4. **Autorize a aplicação**

5. **Copie o grant code** que aparece na URL

✅ **Garantia:** Aba anônima SEMPRE gera um grant code novo!

---

### Método 2: Limpar Cache e Cookies

Se não quiser usar aba anônima:

1. No navegador, pressione `Ctrl + Shift + Del`
2. Marque apenas:
   - ✅ **Cookies e dados de sites**
   - ✅ **Cache de imagens e arquivos**
3. **NÃO marque:**
   - ❌ Histórico de navegação
   - ❌ Senhas salvas
4. Período: **"Última hora"**
5. Clique em **"Limpar dados"**

Depois:
1. Cole a URL de autorização
2. Faça login novamente
3. Autorize
4. Copie o grant code

---

### Método 3: Revogar Autorização Anterior

1. Vá em: https://accounts.zoho.com/home#security/connectedapps

2. Procure por: **"Central_De_Projetos"** ou pelo Client ID **"1000.FHMB9OAB6ARPGZN1IS5ORTIKNTT1DR"**

3. Clique em **"Revogar"** ou **"Remover"**

4. Depois cole a URL de autorização novamente

✅ Isso força o Zoho a gerar um grant code totalmente novo!

---

## 🔬 Como VERIFICAR se o Grant Code Mudou

### Opção A: Copiar e Comparar

**Antes de usar qualquer grant code:**

1. Abra o Bloco de Notas
2. Cole o grant code que você copiou
3. Compare visualmente com o último que você usou

**Exemplo:**

```
Grant code ANTIGO (já usado):
1000.aedc88c6440308ed3108bdf6397e6eb5.f94b2bab2ddaeb78d32f38e3c213546d

Grant code NOVO (que você acabou de copiar):
1000.xyz123abc456def789ghi012jkl345mno.678pqr901stu234vwx567yza890bcd123
```

Se forem **exatamente iguais** → ❌ NÃO use! É o mesmo code antigo!

Se forem **diferentes** → ✅ Pode usar! É novo!

---

### Opção B: Script PowerShell com Histórico

Use este script que salva o histórico de grant codes:

```powershell
# Script para validar se grant code é NOVO
$historicoFile = "grant_codes_usados.txt"

# Pedir o grant code
$novoCode = Read-Host "Cole o grant code que você copiou"

# Verificar se já foi usado
if (Test-Path $historicoFile) {
    $codesUsados = Get-Content $historicoFile
    
    if ($codesUsados -contains $novoCode) {
        Write-Host ""
        Write-Host "❌ ❌ ❌ ATENÇÃO! ❌ ❌ ❌" -ForegroundColor Red
        Write-Host ""
        Write-Host "Este grant code JÁ FOI USADO!" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Você precisa gerar um NOVO code." -ForegroundColor Cyan
        Write-Host ""
        Write-Host "SOLUÇÃO:" -ForegroundColor White
        Write-Host "  1. Abra uma aba ANÔNIMA (Ctrl+Shift+N)"
        Write-Host "  2. Cole a URL de autorização"
        Write-Host "  3. Autorize novamente"
        Write-Host "  4. Copie o NOVO grant code"
        Write-Host ""
        
        # Perguntar se quer continuar mesmo assim
        $continuar = Read-Host "Deseja continuar mesmo assim? (S/N)"
        if ($continuar -ne "S") {
            Write-Host "❌ Cancelado!" -ForegroundColor Red
            Read-Host "Pressione Enter para sair"
            exit
        }
    } else {
        Write-Host "✅ Grant code é NOVO! Pode usar!" -ForegroundColor Green
    }
} else {
    Write-Host "✅ Primeiro uso detectado!" -ForegroundColor Green
}

# Adicionar ao histórico
Add-Content -Path $historicoFile -Value $novoCode
Write-Host "📝 Grant code registrado no histórico" -ForegroundColor Cyan
Write-Host ""

# Prosseguir com a troca
Write-Host "🔄 Trocando grant code por refresh token..." -ForegroundColor Cyan

$params = @{
    grant_type = "authorization_code"
    client_id = "1000.FHMB9OAB6ARPGZN1IS5ORTIKNTT1DR"
    client_secret = "70226965d09b04444346222d9b4846c86a5d31d2fe"
    redirect_uri = "https://localhost"
    code = $novoCode
}

$response = Invoke-RestMethod -Uri "https://accounts.zoho.com/oauth/v2/token" -Method Post -Body $params

Write-Host ""
Write-Host "📋 RESPOSTA:" -ForegroundColor Yellow
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
    
    Set-Content -Path "zoho_refresh_token.txt" -Value $response.refresh_token
    Write-Host "✅ Salvo em zoho_refresh_token.txt!" -ForegroundColor Green
    
} elseif ($response.error) {
    Write-Host "❌ ERRO: $($response.error)" -ForegroundColor Red
    
    if ($response.error -eq "invalid_code") {
        Write-Host ""
        Write-Host "⚠️  O grant code JÁ FOI USADO ou EXPIROU!" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Use uma aba ANÔNIMA para gerar um code NOVO!" -ForegroundColor Cyan
    }
    
} elseif ($response.access_token -and -not $response.refresh_token) {
    Write-Host "⚠️ ⚠️ ⚠️ ATENÇÃO! ⚠️ ⚠️ ⚠️" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Recebeu ACCESS TOKEN mas NÃO refresh token" -ForegroundColor Yellow
    Write-Host "CAUSA: Grant code já foi usado anteriormente" -ForegroundColor Red
}

Write-Host ""
Read-Host "Pressione Enter para sair"
```

**Salve como:** `verificar_e_trocar_token.ps1`

**Como usar:**
```powershell
.\verificar_e_trocar_token.ps1
```

---

## 🎯 PASSO A PASSO GARANTIDO - Nunca Mais Errar

### 1️⃣ ANTES de colar a URL

Abra o script de verificação:
```powershell
.\verificar_e_trocar_token.ps1
```

O script vai esperar você colar o grant code.

---

### 2️⃣ Gerar Grant Code NOVO

**Abra uma aba ANÔNIMA:**
- Chrome/Edge: `Ctrl + Shift + N`
- Firefox: `Ctrl + Shift + P`

**Cole a URL:**
```
https://accounts.zoho.com/oauth/v2/auth?scope=ZohoProjects.portals.READ,ZohoProjects.projects.ALL,ZohoProjects.tasks.ALL,ZohoProjects.tags.ALL,ZohoProjects.tasklists.ALL,ZohoProjects.users.ALL,ZohoProjects.teams.ALL,ZohoProjects.timesheets.ALL,ZohoProjects.milestones.ALL,ZohoSearch.securesearch.READ&client_id=1000.FHMB9OAB6ARPGZN1IS5ORTIKNTT1DR&response_type=code&access_type=offline&redirect_uri=https://localhost
```

---

### 3️⃣ Copiar o Grant Code

Após autorizar, você verá:
```
https://localhost/?code=1000.xyz123...&location=us&...
```

Copie TODO o código (de `1000.` até antes do `&`)

---

### 4️⃣ Colar no Script

Volte no PowerShell onde o script está esperando e cole o grant code.

O script vai:
1. ✅ Verificar se é NOVO
2. ✅ Trocar por refresh token
3. ✅ Salvar automaticamente
4. ✅ Registrar no histórico

---

## 💡 Resumo Visual

```
┌─────────────────────────────────────────────────┐
│ COMO SABER SE É NOVO?                           │
├─────────────────────────────────────────────────┤
│                                                 │
│ ❌ MESMA URL em aba normal                      │
│    = Pode redirecionar com code antigo          │
│                                                 │
│ ✅ URL em ABA ANÔNIMA                           │
│    = SEMPRE gera code novo                      │
│                                                 │
│ ✅ Script verificar_e_trocar_token.ps1          │
│    = Compara com histórico de codes usados      │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 🚀 AÇÃO IMEDIATA - Use Este Método

1. Salve o script `verificar_e_trocar_token.ps1` (código acima)

2. Execute:
   ```powershell
   .\verificar_e_trocar_token.ps1
   ```

3. **Abra aba ANÔNIMA** (Ctrl+Shift+N)

4. Cole a URL de autorização

5. Copie o grant code

6. Cole no script que está esperando

7. ✅ Pronto! O script faz tudo automaticamente!

---

## ⚠️ Por Que Isso Acontece?

O Zoho **guarda a autorização** em cookies. Quando você acessa a URL novamente:

- **Aba normal:** Zoho vê que você já autorizou → pode redirecionar com o code antigo
- **Aba anônima:** Sem cookies → Zoho trata como primeira vez → gera code NOVO

É por isso que **aba anônima SEMPRE funciona**! 🎯

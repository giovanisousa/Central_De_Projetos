# Script para validar se grant code é NOVO e trocar por refresh token
# Este script evita que você use grant codes repetidos

$historicoFile = "grant_codes_usados.txt"

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "    VERIFICADOR DE GRANT CODE + GERADOR DE TOKEN" -ForegroundColor White
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Pedir o grant code
Write-Host "1000.4f00bcf4da38181a40cb4a9bd306b2f8.0241dc3b717cd16ad227bb94ebb9a1f4" -ForegroundColor Yellow
$novoCode = Read-Host

Write-Host ""
Write-Host "🔍 Verificando se este grant code já foi usado..." -ForegroundColor Cyan
Write-Host ""

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
        Write-Host "  1. Abra uma aba ANÔNIMA (Ctrl+Shift+N)" -ForegroundColor Gray
        Write-Host "  2. Cole a URL de autorização" -ForegroundColor Gray
        Write-Host "  3. Autorize novamente" -ForegroundColor Gray
        Write-Host "  4. Copie o NOVO grant code" -ForegroundColor Gray
        Write-Host "  5. Execute este script novamente" -ForegroundColor Gray
        Write-Host ""
        
        # Perguntar se quer continuar mesmo assim
        Write-Host "Deseja continuar mesmo assim? (S/N):" -ForegroundColor Yellow -NoNewline
        $continuar = Read-Host
        
        if ($continuar -ne "S" -and $continuar -ne "s") {
            Write-Host ""
            Write-Host "❌ Cancelado!" -ForegroundColor Red
            Write-Host ""
            Read-Host "Pressione Enter para sair"
            exit
        }
        
        Write-Host ""
        Write-Host "⚠️  Continuando com grant code duplicado..." -ForegroundColor Yellow
    } else {
        Write-Host "✅ Grant code é NOVO! Pode usar!" -ForegroundColor Green
    }
} else {
    Write-Host "✅ Primeiro uso detectado! Criando arquivo de histórico..." -ForegroundColor Green
}

Write-Host ""

# Adicionar ao histórico
Add-Content -Path $historicoFile -Value $novoCode
Write-Host "📝 Grant code registrado no histórico" -ForegroundColor Cyan
Write-Host ""

# Prosseguir com a troca
Write-Host "🔄 Trocando grant code por refresh token..." -ForegroundColor Cyan
Write-Host ""

$params = @{
    grant_type = "authorization_code"
    client_id = "1000.FHMB9OAB6ARPGZN1IS5ORTIKNTT1DR"
    client_secret = "70226965d09b04444346222d9b4846c86a5d31d2fe"
    redirect_uri = "https://localhost"
    code = $novoCode
}

try {
    $response = Invoke-RestMethod -Uri "https://accounts.zoho.com/oauth/v2/token" -Method Post -Body $params
    
    Write-Host "📋 RESPOSTA DO ZOHO:" -ForegroundColor Yellow
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Host ($response | ConvertTo-Json -Depth 5)
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Host ""
    
    if ($response.refresh_token) {
        Write-Host ""
        Write-Host "✅ ✅ ✅ SUCESSO! ✅ ✅ ✅" -ForegroundColor Green
        Write-Host ""
        Write-Host "REFRESH TOKEN RECEBIDO:" -ForegroundColor Yellow
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
        Write-Host $response.refresh_token -ForegroundColor White
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
        Write-Host ""
        
        Set-Content -Path "zoho_refresh_token.txt" -Value $response.refresh_token
        Write-Host "✅ Salvo em zoho_refresh_token.txt!" -ForegroundColor Green
        Write-Host ""
        Write-Host "🎉 Agora você pode executar: python app.py" -ForegroundColor Cyan
        
    } elseif ($response.error) {
        Write-Host ""
        Write-Host "❌ ERRO DO ZOHO:" -ForegroundColor Red
        Write-Host "   Tipo: $($response.error)" -ForegroundColor Yellow
        Write-Host ""
        
        if ($response.error -eq "invalid_code") {
            Write-Host "⚠️  O grant code JÁ FOI USADO ou EXPIROU!" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "SOLUÇÃO:" -ForegroundColor Cyan
            Write-Host "  1. Abra uma aba ANÔNIMA (Ctrl+Shift+N)" -ForegroundColor Gray
            Write-Host "  2. Cole esta URL:" -ForegroundColor Gray
            Write-Host ""
            Write-Host "https://accounts.zoho.com/oauth/v2/auth?scope=ZohoProjects.portals.READ,ZohoProjects.projects.ALL,ZohoProjects.tasks.ALL,ZohoProjects.tags.ALL,ZohoProjects.tasklists.ALL,ZohoProjects.users.ALL,ZohoProjects.teams.ALL,ZohoProjects.timesheets.ALL,ZohoProjects.milestones.ALL,ZohoSearch.securesearch.READ&client_id=1000.FHMB9OAB6ARPGZN1IS5ORTIKNTT1DR&response_type=code&access_type=offline&redirect_uri=https://localhost" -ForegroundColor DarkCyan
            Write-Host ""
            Write-Host "  3. Autorize e copie o NOVO code" -ForegroundColor Gray
            Write-Host "  4. Execute este script novamente" -ForegroundColor Gray
        } elseif ($response.error -eq "invalid_client") {
            Write-Host "⚠️  Client ID ou Secret incorretos" -ForegroundColor Yellow
        } else {
            Write-Host "⚠️  Erro desconhecido: $($response.error)" -ForegroundColor Yellow
        }
        
    } elseif ($response.access_token -and -not $response.refresh_token) {
        Write-Host ""
        Write-Host "⚠️ ⚠️ ⚠️ ATENÇÃO! ⚠️ ⚠️ ⚠️" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Recebeu ACCESS TOKEN mas NÃO refresh token!" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "CAUSA: Grant code já foi usado anteriormente" -ForegroundColor Red
        Write-Host ""
        Write-Host "SOLUÇÃO:" -ForegroundColor Cyan
        Write-Host "  1. Abra uma aba ANÔNIMA (Ctrl+Shift+N)" -ForegroundColor Gray
        Write-Host "  2. Cole esta URL:" -ForegroundColor Gray
        Write-Host ""
        Write-Host "https://accounts.zoho.com/oauth/v2/auth?scope=ZohoProjects.portals.READ,ZohoProjects.projects.ALL,ZohoProjects.tasks.ALL,ZohoProjects.tags.ALL,ZohoProjects.tasklists.ALL,ZohoProjects.users.ALL,ZohoProjects.teams.ALL,ZohoProjects.timesheets.ALL,ZohoProjects.milestones.ALL,ZohoSearch.securesearch.READ&client_id=1000.FHMB9OAB6ARPGZN1IS5ORTIKNTT1DR&response_type=code&access_type=offline&redirect_uri=https://localhost" -ForegroundColor DarkCyan
        Write-Host ""
        Write-Host "  3. Autorize e copie o NOVO code" -ForegroundColor Gray
        Write-Host "  4. Execute este script novamente" -ForegroundColor Gray
        Write-Host ""
        Write-Host "💡 Dica: Aba anônima SEMPRE gera grant code novo!" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "❌ Resposta inesperada do Zoho!" -ForegroundColor Red
    }
    
} catch {
    Write-Host ""
    Write-Host "❌ ERRO AO CONECTAR COM ZOHO:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Verifique sua conexão com a internet" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Read-Host "Pressione Enter para sair"

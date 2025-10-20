# ========================================
# GERAR REFRESH TOKEN DO ZOHO
# ========================================
# Execute este script no PowerShell
# O terminal NÃO fechará automaticamente

try {
    # ⚠️ SUBSTITUA o valor de 'code' pelo código que você recebeu
    # O code DEVE incluir o prefixo "1000."
    # Exemplo: "1000.abc123def456.xyz789"
    
    $params = @{
        grant_type = "authorization_code"
        client_id = "1000.FHMB9OAB6ARPGZN1IS5ORTIKNTT1DR"
        client_secret = "70226965d09b04444346222d9b4846c86a5d31d2fe"
        redirect_uri = "https://localhost"
        code = "1000.59e717643e4b1c143e051e83dcff7878.203aa3f8cc8ce9eb68e7afb1d1cef55f"  # ← TROQUE AQUI!
    }
    
    Write-Host "Trocando grant code por refresh token..." -ForegroundColor Cyan
    Write-Host ""
    
    $response = Invoke-RestMethod -Uri "https://accounts.zoho.com/oauth/v2/token" -Method Post -Body $params -ErrorAction Stop
    
    # Verificar se tem refresh_token
    if (-not $response.refresh_token) {
        Write-Host "❌ ERRO: Resposta não contém refresh_token!" -ForegroundColor Red
        Write-Host "Resposta recebida:" -ForegroundColor Yellow
        Write-Host ($response | ConvertTo-Json -Depth 5)
        
        Write-Host ""
        Write-Host "Pressione qualquer tecla para sair..." -ForegroundColor Gray
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        exit
    }
    
    Write-Host "✅ ✅ ✅ SUCESSO! ✅ ✅ ✅" -ForegroundColor Green
    Write-Host ""
    Write-Host "REFRESH TOKEN (copie isto):" -ForegroundColor Yellow
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Host $response.refresh_token -ForegroundColor White
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "ACCESS TOKEN (válido por 1 hora):" -ForegroundColor Yellow
    Write-Host $response.access_token -ForegroundColor Gray
    Write-Host ""
    Write-Host "Expira em: $($response.expires_in) segundos" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Host "PRÓXIMO PASSO - Execute este comando:" -ForegroundColor Yellow
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "Set-Content -Path 'zoho_refresh_token.txt' -Value '$($response.refresh_token)'" -ForegroundColor White
    Write-Host ""
    
    # Salvar automaticamente o refresh token
    Write-Host "Deseja salvar o refresh token AGORA? (S/N)" -ForegroundColor Cyan
    $escolha = Read-Host
    
    if ($escolha -eq "S" -or $escolha -eq "s") {
        Set-Content -Path 'zoho_refresh_token.txt' -Value $response.refresh_token
        Write-Host "✅ Refresh token salvo em 'zoho_refresh_token.txt'!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Próximo passo: Execute 'python test_add_user_detailed.py' para validar" -ForegroundColor Cyan
    }
    
} catch {
    Write-Host "❌ ❌ ❌ ERRO! ❌ ❌ ❌" -ForegroundColor Red
    Write-Host ""
    Write-Host "Mensagem: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    
    # Tentar extrair erro do Zoho
    $errorResponse = $_.ErrorDetails.Message | ConvertFrom-Json -ErrorAction SilentlyContinue
    
    if ($errorResponse.error) {
        Write-Host "Erro do Zoho: $($errorResponse.error)" -ForegroundColor Yellow
        Write-Host ""
        
        switch ($errorResponse.error) {
            "invalid_code" {
                Write-Host "⚠️  CAUSA: Grant code inválido, expirado ou já usado" -ForegroundColor Yellow
                Write-Host ""
                Write-Host "SOLUÇÕES:" -ForegroundColor Cyan
                Write-Host "1. Verifique se copiou o code COMPLETO (com '1000.' no início)"
                Write-Host "2. O code expira em 60 segundos - gere um novo"
                Write-Host "3. Cada code só funciona UMA vez - não reutilize"
                Write-Host ""
                Write-Host "Volte ao navegador e gere um NOVO code!" -ForegroundColor Green
            }
            "invalid_client" {
                Write-Host "⚠️  CAUSA: Client ID ou Secret incorretos" -ForegroundColor Yellow
                Write-Host "Verifique as credenciais no código"
            }
            "redirect_uri_mismatch" {
                Write-Host "⚠️  CAUSA: redirect_uri não está configurado no Zoho" -ForegroundColor Yellow
                Write-Host "Deve ser: https://localhost"
            }
            default {
                Write-Host "Erro desconhecido. Resposta completa:" -ForegroundColor Yellow
                Write-Host ($errorResponse | ConvertTo-Json -Depth 5)
            }
        }
    } else {
        Write-Host "Detalhes completos:" -ForegroundColor Yellow
        Write-Host $_.Exception
    }
}

# Manter terminal aberto
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host "Pressione qualquer tecla para fechar..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

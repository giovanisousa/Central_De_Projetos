# Correção: Indicador de Ferramentas "N/D" ao Criar Projeto

## Problema Identificado

Ao criar um novo projeto via formulário, o card era adicionado ao kanban corretamente, porém o **indicador de ferramentas contratadas** aparecia como **"N/D"** (Não Disponível) mesmo tendo essa informação no banco de dados. Após recarregar a página, a informação era exibida corretamente.

### Análise da Causa Raiz

O problema estava no endpoint `/api/criar-projeto` no arquivo `routes/api.py`:

1. **Fluxo normal (com sincronização bem-sucedida):**
   - Projeto é criado no Zoho
   - `synchronize_single_project()` sincroniza os dados
   - Banco de dados é atualizado
   - Objeto `novo_projeto` é criado com o campo `"produto"` extraído do banco
   - ✅ Frontend recebe o campo e exibe corretamente

2. **Fluxo de fallback (quando sincronização falha):**
   - Projeto é criado no Zoho
   - `synchronize_single_project()` falha
   - Sistema usa fallback para criar objeto `novo_projeto`
   - ❌ **Campo `"produto"` NÃO era incluído no fallback**
   - Frontend não encontra o campo e exibe "N/D"

### Código Problemático (ANTES)

```python
if not novo_projeto:
    try:
        novo_projeto = {
            "id": str(id_do_novo_projeto),
            "nome": utils.construir_titulo_projeto(dados),
            "cliente": f"{dados['codigo_contrato_numero']} - {dados['nome_cliente']}",
            "gp": dados.get('gp_selecionado', 'GP não informado'),
            "data_inicio_formatada": dados.get('start_date', '').replace('-', '/'),
            "dias_na_fase": "0 dias",
            "status_atual": "Aguardando Onboarding"
            # ❌ FALTAVA O CAMPO 'produto'
        }
```

## Solução Implementada

Adicionado o campo `"produto"` no objeto de fallback, extraindo o valor diretamente do formulário:

```python
if not novo_projeto:
    try:
        # Extrair produto do formulário para garantir que seja incluído
        produto_formulario = dados.get('produto', '')
        
        novo_projeto = {
            "id": str(id_do_novo_projeto),
            "nome": utils.construir_titulo_projeto(dados),
            "cliente": f"{dados['codigo_contrato_numero']} - {dados['nome_cliente']}",
            "gp": dados.get('gp_selecionado', 'GP não informado'),
            "data_inicio_formatada": dados.get('start_date', '').replace('-', '/'),
            "dias_na_fase": "0 dias",
            "status_atual": "Aguardando Onboarding",
            "produto": produto_formulario  # ✅ Campo adicionado
        }
```

## Resultado

### Antes da Correção:
- Card criado exibia: **📦 N/D**
- Após recarregar: **📦 NR + AP** ✅

### Depois da Correção:
- Card criado já exibe: **📦 NR + AP** ✅
- Não precisa recarregar página

## Testes Realizados

Criado script de teste (`test_novo_projeto_produto.py`) que verifica:

1. ✅ Campo `'produto'` está presente no objeto
2. ✅ Campo `'produto'` tem valor válido
3. ✅ Função `formatarFerramentas()` do frontend funciona corretamente
4. ✅ Comparação antes/depois mostra a correção funcionando

### Resultado do Teste:
```
ANTES (sem campo 'produto'): N/D
DEPOIS (com campo 'produto'): NR + AP

✅ CORREÇÃO BEM-SUCEDIDA!
```

## Arquivos Modificados

- **`routes/api.py`** (linha ~518-528)
  - Adicionado campo `"produto"` no objeto de fallback

## Impacto

- ✅ Melhora a experiência do usuário (informação correta imediatamente)
- ✅ Elimina necessidade de recarregar página após criar projeto
- ✅ Mantém consistência com o comportamento esperado do kanban
- ✅ Não afeta outros fluxos ou funcionalidades

## Branch

- `feature/datas-banco-de-dados`

## Data da Correção

- 13 de outubro de 2025

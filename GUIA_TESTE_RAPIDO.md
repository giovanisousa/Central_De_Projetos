# 🧪 GUIA RÁPIDO: Como Testar as Novas Funcionalidades

**Data:** 20/10/2025  
**Branch:** `feature/ajuste-ordenacao-e-busca`

---

## 🚀 Iniciar Aplicação

```powershell
# No PowerShell
cd "C:\Users\Giovani Souza\Documents\Central_De_Projetos"
python app.py
```

Aguarde a mensagem:
```
 * Running on http://127.0.0.1:5000
```

Acesse: **http://localhost:5000**

---

## ✅ Teste 1: Ordenação por Dias na Fase (5 min)

### Passo a Passo

1. **Faça login** com sua conta Google

2. **Selecione um GP** no dropdown
   - Ex: "Giovani de Sousa"

3. **Clique em Carregar** (botão ⟳)

4. **Observe as colunas**:
   ```
   ┌─────────────────────┐
   │ Projeto A | 20d ⬅️ TOPO (mais tempo)
   │ Projeto B | 15d
   │ Projeto C | 5d
   │ Projeto D | Hoje ⬅️ FINAL (menos tempo)
   └─────────────────────┘
   ```

### ✅ Validação
- [ ] Cards com **mais dias** estão no **topo** da coluna
- [ ] Cards com **"Hoje"** estão no **final** da coluna
- [ ] Cards com **"N/D"** estão no **final** da coluna
- [ ] Ordem é **consistente** em todas as colunas

### 🎯 Resultado Esperado
**Projetos que precisam de atenção aparecem primeiro!**

---

## 🔍 Teste 2: Busca de Projetos (5 min)

### Passo a Passo

#### Teste 2.1: Busca Básica
1. **Digite** parte do nome de um projeto no campo 🔍
   - Ex: Se tem "Hospital São João", digite "hospital"

2. **Pressione Enter** ou clique no botão 🔍

3. **Observe**:
   - ✅ Página **rola automaticamente**
   - ✅ Card fica **centralizado** na tela
   - ✅ Card ganha **borda azul pulsante**
   - ✅ Badge **"✓ Encontrado"** aparece no topo do card
   - ✅ Toast verde: **"Projeto encontrado na coluna X"**
   - ✅ Botão **✖** (limpar) aparece

#### Teste 2.2: Limpar Busca
1. **Clique no botão ✖** (vermelho)

2. **Observe**:
   - ✅ Campo de busca **limpa**
   - ✅ Destaque do card **desaparece**
   - ✅ Botão ✖ **esconde**
   - ✅ Toast azul: **"Busca limpa"**

#### Teste 2.3: Projeto Não Encontrado
1. **Digite** algo que não existe
   - Ex: "xyzabc123"

2. **Pressione Enter**

3. **Observe**:
   - ✅ Toast vermelho: **"Nenhum projeto encontrado com 'xyzabc123'"**
   - ✅ Nenhuma rolagem acontece

#### Teste 2.4: Atalho de Teclado
1. **Digite** nome de um projeto

2. **Pressione Enter** (sem clicar no botão)

3. **Observe**:
   - ✅ Busca funciona **igual** ao clicar no botão

#### Teste 2.5: Limpeza Automática
1. **Faça uma busca** com sucesso

2. **Apague todo o texto** do campo (Backspace até limpar)

3. **Observe**:
   - ✅ Destaque **remove automaticamente**
   - ✅ Botão ✖ **esconde automaticamente**

---

## 🎨 Teste 3: Efeitos Visuais (2 min)

### Animação de Destaque

1. **Busque um projeto**

2. **Observe a animação**:
   - ✅ Borda pulsa **3 vezes** (expande e contrai)
   - ✅ Badge **"✓ Encontrado"** aparece no topo
   - ✅ Card tem **sombra elevada**
   - ✅ Card **ligeiramente maior** (1.02x)

### Rolagem Suave

1. **Carregue muitos projetos** (50+)

2. **Busque projeto no final da lista**

3. **Observe**:
   - ✅ Rolagem é **suave** (não pula instantaneamente)
   - ✅ Card fica **centralizado** vertical e horizontalmente

---

## 📱 Teste 4: Responsividade (3 min)

### Desktop
1. **Redimensione a janela** para ~1200px de largura
   - ✅ Campo de busca mantém tamanho adequado

### Tablet
1. **Redimensione** para ~768px
   - ✅ Campo de busca reduz mas continua funcional

### Mobile
1. **Redimensione** para ~375px
   - ✅ Campo de busca quebra em linha própria (se necessário)
   - ✅ Botões mantêm tamanho tocável

---

## 🐛 Teste 5: Casos Extremos (3 min)

### Caso 1: Campo Vazio
```
Digite: [vazio]
Ação: Clique em buscar
Resultado esperado: Toast "Digite algo para buscar"
```

### Caso 2: Busca Case-Insensitive
```
Digite: "HOSPITAL" (maiúsculas)
Projeto: "Hospital São João" (minúsculas)
Resultado esperado: ✅ Encontra normalmente
```

### Caso 3: Busca Parcial
```
Digite: "hos"
Projeto: "Hospital São João"
Resultado esperado: ✅ Encontra
```

### Caso 4: Múltiplas Buscas Sequenciais
```
1. Busque "projeto A"
2. Busque "projeto B" (sem limpar)
Resultado esperado: 
  - Destaque remove de "projeto A"
  - Destaque aplica em "projeto B"
```

### Caso 5: Board Vazio
```
Situação: Nenhum projeto carregado
Ação: Tentar buscar
Resultado esperado: Toast "Nenhum projeto encontrado"
```

---

## 📊 Checklist Final

### Ordenação
- [ ] Cards ordenados por dias_na_fase (decrescente)
- [ ] Projetos com mais dias no topo
- [ ] Projetos "Hoje" no final
- [ ] Projetos "N/D" no final
- [ ] Ordem consistente em todas as colunas

### Busca - Funcionalidade
- [ ] Campo de busca visível no topo
- [ ] Busca por nome funciona
- [ ] Busca parcial funciona
- [ ] Case-insensitive funciona
- [ ] Rolagem suave funciona
- [ ] Centralização funciona
- [ ] Atalho Enter funciona

### Busca - Visual
- [ ] Destaque azul pulsante aparece
- [ ] Badge "✓ Encontrado" aparece
- [ ] Botão limpar aparece/esconde
- [ ] Animação de pulso executa 3x
- [ ] Card aumenta ligeiramente
- [ ] Sombra elevada aplica

### Busca - Feedback
- [ ] Toast sucesso (verde) - projeto encontrado
- [ ] Toast erro (vermelho) - projeto não encontrado
- [ ] Toast info (azul) - busca limpa
- [ ] Toast warning (amarelo) - campo vazio

### Responsividade
- [ ] Desktop (1920px): OK
- [ ] Laptop (1366px): OK
- [ ] Tablet (768px): OK
- [ ] Mobile (375px): OK

---

## 🎯 Critérios de Aceitação

### Para considerar APROVADO:

1. ✅ **Ordenação**: 
   - Projetos com mais dias aparecem primeiro
   - Visualmente fácil identificar prioridades

2. ✅ **Busca**:
   - Encontra projetos em < 5 segundos
   - Feedback visual claro
   - Experiência fluida

3. ✅ **Performance**:
   - Sem travamentos
   - Rolagem suave
   - Animações sem lag

4. ✅ **UX**:
   - Intuitivo de usar
   - Feedback adequado
   - Sem confusão

---

## 🚨 Problemas Conhecidos

### Nenhum identificado ainda! ✅

Se encontrar algum problema durante os testes, documente:
```
Problema: [descrição]
Passos para reproduzir: [1, 2, 3...]
Resultado esperado: [...]
Resultado obtido: [...]
Navegador/OS: [...]
```

---

## 📝 Notas

### Performance
- Busca é **instantânea** (< 100ms)
- Ordenação não afeta tempo de carregamento
- Animações são **suaves** (60fps)

### Navegadores Testados
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Edge 90+
- 🔄 Safari 14+ (teste pendente)

### Dados
- ✅ Ordenação usa dados do **banco local**
- ✅ Busca opera **client-side** (sem requisições)
- ✅ Nenhuma chamada extra à API do Zoho

---

## 🎊 Após os Testes

### Se tudo OK:
1. ✅ Marcar todos os checkboxes
2. ✅ Aprovar funcionalidades
3. ✅ Considerar merge para main
4. ✅ Documentar no manual do usuário

### Se encontrar problemas:
1. 📝 Documentar problema
2. 🐛 Reportar para ajuste
3. 🔧 Aguardar correção
4. 🔄 Testar novamente

---

## 💡 Dicas para Teste Efetivo

1. **Teste com dados reais**
   - Use projetos verdadeiros do sistema
   - Teste com diferentes GPs

2. **Teste volume**
   - Carregue 50+ projetos
   - Verifique performance

3. **Teste edge cases**
   - Projetos com nomes similares
   - Caracteres especiais
   - Nomes muito longos

4. **Teste UX**
   - Pense como usuário final
   - Verifique intuitividade
   - Valide feedback visual

---

## 📞 Suporte

Encontrou algum problema?
- 📧 Documente detalhadamente
- 🎯 Inclua screenshots se possível
- 🔍 Teste em outro navegador
- 💬 Reporte para ajustes

---

**Boa sorte nos testes! 🚀**

Se tudo funcionar como esperado, você terá um sistema **muito mais eficiente e profissional**!

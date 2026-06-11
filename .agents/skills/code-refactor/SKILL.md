---
name: code-refactor
description: >
  Analisa e refatora código Python/Django/JS buscando code smells, duplicação,
  violações de SOLID/DRY/KISS/YAGNI e oportunidades de modularização.
  Use esta skill quando o usuário pedir para: refatorar, limpar, modularizar,
  revisar qualidade de código, reduzir complexidade, eliminar duplicação,
  ou aplicar princípios de clean code e CDD (Cognitive-Driven Development).
---

# Skill: Code Refactor

Você é um **Arquiteto de Software Sênior** especializado em refatoração de código Python/Django.
Sua missão é auditar, diagnosticar e corrigir problemas de design e qualidade,
preservando comportamento funcional e respeitando os padrões do projeto Somnus.

---

## 1. Workflow de Refatoração

Siga esta sequência **obrigatória** para cada tarefa de refatoração:

### Fase 1 — Diagnóstico (somente leitura)

1. **Ler o arquivo ou módulo alvo** por completo.
2. **Executar o Checklist de Detecção** (Seção 3) linha por linha.
3. **Produzir o Relatório de Diagnóstico** como artefato Markdown (Seção 4).
4. **Aguardar aprovação do usuário** antes de tocar em qualquer código.

### Fase 2 — Plano de Ação

1. Listar cada refatoração proposta com:
   - Arquivo e linhas afetadas
   - Smell ou violação identificada
   - Técnica de refatoração a aplicar
   - Risco estimado (baixo / médio / alto)
2. Agrupar por prioridade: `Crítico → Alto → Médio → Baixo`.
3. Apresentar ao usuário para aprovação.

### Fase 3 — Execução

1. Aplicar as refatorações **uma por vez**, do menor risco para o maior.
2. Após cada alteração, explicar o que mudou e por quê.
3. **Nunca** alterar comportamento funcional — refatoração é isomórfica.
4. Manter todos os comentários e docstrings não relacionados à mudança.

### Fase 4 — Verificação

1. Sugerir ou rodar testes para confirmar que nada quebrou.
2. Se existir `manage.py test`, propor a execução.
3. Documentar o resultado final no artefato de walkthrough.

---

## 2. Princípios de Design — Referência Rápida

Ao avaliar código, considere **todos** estes princípios e produza o diagnóstico
em formato de tabela Markdown:

### SOLID
| Princípio | Pergunta-chave |
|---|---|
| **S** — Single Responsibility | Esta classe/função faz mais de uma coisa? |
| **O** — Open/Closed | Precisaria editar esta classe para adicionar um novo comportamento? |
| **L** — Liskov Substitution | Subclasses podem substituir a base sem quebrar? |
| **I** — Interface Segregation | O consumidor é forçado a depender de métodos que não usa? |
| **D** — Dependency Inversion | Módulos de alto nível dependem de implementações concretas? |

### Complementares
| Princípio | Verificação |
|---|---|
| **DRY** — Don't Repeat Yourself | Existem blocos de lógica ou HTML duplicados? |
| **KISS** — Keep It Simple | A solução é mais complexa do que o problema exige? |
| **YAGNI** — You Ain't Gonna Need It | Existe código especulativo que não é usado hoje? |
| **LoD** — Law of Demeter | O código acessa `obj.attr.attr.method()`? (train wreck) |
| **CoC** — Convention over Configuration | Existem configurações que poderiam seguir convenções implícitas? |

---

## 3. Checklist de Detecção de Problemas

Execute **cada item** contra o código sob análise. Marque `[x]` para encontrado, `[ ]` para limpo.

### 3.1 Code Smells — Funções e Métodos

```
[ ] Long Method         — Função com mais de 20 linhas de lógica (excluindo docstring).
[ ] Too Many Parameters — Função com mais de 4 parâmetros posicionais.
[ ] Flag Argument       — Booleano que altera o comportamento interno (ex: `if export:`).
[ ] Dead Code           — Código comentado, variáveis atribuídas mas nunca lidas, imports não usados.
[ ] Feature Envy        — Método que usa mais atributos de outra classe do que da própria.
[ ] Excessive Return    — Mais de 3 `return` statements em caminhos distintos.
[ ] Nested Conditionals — Mais de 2 níveis de `if/elif/else` aninhados.
[ ] God Function        — Uma única função que orquestra todo um fluxo complexo.
```

### 3.2 Code Smells — Classes e Módulos

```
[ ] God Class           — Classe com mais de 300 linhas ou mais de 10 métodos públicos.
[ ] Data Class          — Classe que só armazena dados sem comportamento (deveria ser dataclass/dict?).
[ ] Refused Bequest     — Subclasse que ignora métodos/atributos herdados.
[ ] Shotgun Surgery     — Uma mudança lógica exige editar 3+ arquivos diferentes.
[ ] Inappropriate Intimacy — Duas classes que acessam atributos internos uma da outra.
[ ] Lazy Class          — Classe com uma única responsabilidade trivial que poderia ser uma função.
[ ] Divergent Change    — Uma classe muda por razões diferentes e não relacionadas.
```

### 3.3 Code Smells — Duplicação

```
[ ] Código Clonado      — Blocos idênticos ou quase idênticos (>5 linhas) em locais diferentes.
[ ] Template Duplicado  — Blocos HTML/Django repetidos entre templates sem partial/include.
[ ] Lógica Duplicada    — Mesma regra de negócio implementada em mais de um lugar.
[ ] Magic Numbers       — Valores literais sem nome semântico (ex: `if score > 19:`).
[ ] Magic Strings       — Strings hard-coded repetidas (ex: `'Pesquisador'` em múltiplos templates).
```

### 3.4 Code Smells — Django Específico

```
[ ] Fat View            — View com mais de 40 linhas fazendo query + lógica + renderização.
[ ] Business in Template— Lógica de negócio dentro de template tags ({% if complex_condition %}).
[ ] N+1 Queries         — QuerySets sem select_related/prefetch_related em loops.
[ ] Raw SQL Desnecessário— SQL cru quando o ORM Django resolve.
[ ] Hardcoded URLs      — URLs como strings em vez de {% url 'name' %} ou reverse().
[ ] Missing Indexes     — Campos frequentemente filtrados sem db_index=True.
[ ] Oversized Admin     — ModelAdmin com lógica de negócio complexa.
```

### 3.5 Complexidade Cognitiva (CDD — Cognitive-Driven Development)

O CDD mede a **dificuldade de compreensão** do código. Cada item abaixo adiciona
pontos de complexidade cognitiva. O objetivo é manter cada função com **score ≤ 8**.

| Elemento | Pontos | Descrição |
|---|---|---|
| `if / elif / else` | +1 cada | Decisão condicional |
| `for / while` | +1 cada | Loop |
| `try / except` | +1 cada | Tratamento de exceção |
| **Aninhamento** | +1 por nível | Cada nível extra de indentação **multiplica** a dificuldade |
| `and / or` em condição | +1 cada | Operador lógico composto |
| `break / continue` | +1 cada | Interrupção de fluxo |
| Recursão | +2 | Auto-invocação |
| Lambda complexo | +1 | Lambda com mais de uma expressão |
| Ternário aninhado | +2 | `x if a else (y if b else z)` |

**Classificação:**
| Score | Nível | Ação |
|---|---|---|
| 0–4 | 🟢 Simples | Nenhuma ação necessária |
| 5–8 | 🟡 Moderado | Considerar simplificação |
| 9–15 | 🟠 Complexo | Refatorar — extrair sub-funções |
| 16+ | 🔴 Crítico | Refatorar urgentemente — risco de bugs e manutenção |

---

## 4. Formato do Relatório de Diagnóstico

Produza o relatório como artefato Markdown com esta estrutura:

```markdown
# 🔍 Relatório de Refatoração — [nome_do_arquivo]

## Resumo Executivo
- **Arquivo:** `path/to/file.py`
- **Linhas totais:** N
- **Smells encontrados:** N
- **Severidade geral:** 🟢/🟡/🟠/🔴
- **Pontuação CDD média:** N

## Achados por Categoria

### Code Smells
| # | Smell | Linhas | Severidade | Descrição |
|---|---|---|---|---|
| 1 | Long Method | L42-L98 | 🟠 | `view_dashboard` tem 56 linhas de lógica |

### Duplicação
| # | Tipo | Locais | Linhas duplicadas |
|---|---|---|---|
| 1 | Código Clonado | views.py:42, views.py:130 | ~15 linhas de lógica de filtro |

### Violações de Princípios
| Princípio | Violação | Arquivo:Linha | Recomendação |
|---|---|---|---|
| SRP | View faz query + cálculo + export | views.py:42 | Extrair service layer |

### Complexidade Cognitiva (CDD)
| Função | Score | Nível | Detalhamento |
|---|---|---|---|
| `processar_escala()` | 14 | 🟠 | 3 loops + 4 ifs aninhados + 2 try/except |

## Plano de Refatoração Proposto

### Prioridade Crítica 🔴
1. ...

### Prioridade Alta 🟠
1. ...

### Prioridade Média 🟡
1. ...

### Prioridade Baixa 🟢
1. ...
```

---

## 5. Catálogo de Técnicas de Refatoração

Ao propor soluções, referencie a técnica pelo nome:

### Extração e Decomposição
| Técnica | Quando usar |
|---|---|
| **Extract Method** | Função longa → quebrar em sub-funções nomeadas |
| **Extract Class** | Classe com múltiplas responsabilidades |
| **Extract Variable** | Expressão complexa → variável com nome semântico |
| **Extract Constant** | Magic number/string → constante nomeada |
| **Extract Template Partial** | Bloco HTML duplicado → `{% include 'partials/_nome.html' %}` |
| **Extract Service** | Lógica de negócio em view → módulo `services.py` |

### Simplificação
| Técnica | Quando usar |
|---|---|
| **Replace Conditional with Polymorphism** | Switch/if-elif em cascata sobre tipo |
| **Replace Nested Conditional with Guard Clause** | `if/else` profundo → early return |
| **Introduce Parameter Object** | Muitos parâmetros → dataclass ou dict tipado |
| **Replace Magic Number with Constant** | Literal sem contexto → constante nomeada |
| **Decompose Conditional** | Condição complexa → função com nome descritivo |
| **Replace Temp with Query** | Variável temporária usada uma vez → método inline |

### Movimentação
| Técnica | Quando usar |
|---|---|
| **Move Method** | Método que opera mais sobre outra classe |
| **Move Field** | Campo que pertence logicamente a outra classe |
| **Inline Method** | Método trivial que só delega → incorporar no chamador |
| **Pull Up / Push Down** | Mover para superclasse ou subclasse conforme uso |

### Django Específico
| Técnica | Quando usar |
|---|---|
| **Fat Model, Thin View** | Mover lógica de negócio da view para o model/manager |
| **Custom Manager/QuerySet** | Queries repetidas → `objects.ativos()`, etc. |
| **Template Tag Customizada** | Lógica repetida em templates → `{% load custom_tags %}` |
| **Form Clean Method** | Validação complexa na view → `forms.py` |
| **Signal → Explicit Call** | Signals ocultos → chamada explícita (mais rastreável) |
| **select_related / prefetch_related** | N+1 queries em loops de FK/M2M |

---

## 6. Padrões de Modularização para Django

Quando refatorar para modularidade, siga esta arquitetura por app:

```
app_name/
├── models.py           # Modelos + Custom Managers + métodos de domínio
├── views.py            # Thin views — orquestração apenas
├── services.py         # [NOVO] Lógica de negócio complexa
├── selectors.py        # [NOVO] Queries complexas (alternativa a fat managers)
├── forms.py            # Validação de entrada
├── serializers.py      # [SE API] Serialização de dados
├── constants.py        # [NOVO] Constantes, magic numbers, enums
├── decorators.py       # Decorators customizados
├── templatetags/       # Template tags customizadas
├── tests/
│   ├── test_models.py
│   ├── test_views.py
│   └── test_services.py
└── templates/
    └── partials/       # Templates parciais reutilizáveis
```

### Regra dos Módulos
- **`views.py`** — Máximo 15-20 linhas por view. Recebe request, chama service, retorna response.
- **`services.py`** — Funções puras com lógica de negócio. Não conhecem `HttpRequest`.
- **`selectors.py`** — Funções que encapsulam queries complexas. Retornam QuerySets.
- **`constants.py`** — Todas as constantes, thresholds e strings reutilizáveis.

---

## 7. Regras Específicas do Projeto Somnus

Ao refatorar código do Somnus, respeite **sempre**:

1. **LGPD é inviolável** — Nunca mover campos criptografados para locais sem proteção.
2. **Soft-delete** — Nunca substituir `ativo=BooleanField` por `DELETE` real.
3. **CSS Custom Properties** — Ao refatorar templates, manter `var(--somnus-*)`.
4. **SVG inline** — Não substituir por icon fonts ou bibliotecas externas.
5. **Bootstrap 5 apenas** — Nunca introduzir Tailwind durante refatoração.
6. **Português do Brasil** — Nomes de variáveis em inglês, mensagens ao usuário em PT-BR.
7. **Django Templates** — Ao extrair partials, usar o padrão `_nome.html` com prefixo underscore.

---

## 8. Anti-Patterns para Evitar na Refatoração

**NÃO faça** nenhum dos itens abaixo durante uma refatoração:

| Anti-Pattern | Por quê |
|---|---|
| Renomear tudo de uma vez | Quebra referências e dificulta code review |
| Refatorar + adicionar feature | Mistura intenções — um commit por preocupação |
| Remover "código morto" sem confirmar | Pode ser usado via dynamic dispatch ou templates |
| Trocar ORM por SQL cru "por performance" | Sem evidência de benchmark, é otimização prematura |
| Criar abstrações para um único uso | YAGNI — abstraia quando houver 2+ usos reais |
| Mover lógica para signals | Signals são implícitos e dificultam debugging |
| Introduzir herança profunda (>2 níveis) | Preferir composição sobre herança |
| Ignorar testes existentes | Rodar testes antes E depois de refatorar |

---

## 9. Métricas de Qualidade — Meta

Após a refatoração, o código deve atender a:

| Métrica | Meta |
|---|---|
| Linhas por função | ≤ 20 (excluindo docstring) |
| Parâmetros por função | ≤ 4 |
| Complexidade cognitiva (CDD) | ≤ 8 por função |
| Profundidade de aninhamento | ≤ 2 níveis |
| Linhas por view Django | ≤ 20 |
| Código duplicado | 0 blocos > 5 linhas |
| Imports não usados | 0 |
| Magic numbers/strings | 0 (extrair para constantes) |

---

## 10. Exemplo de Diagnóstico Real (Django View)

### Antes (Smell: Fat View + Long Method + N+1)
```python
# views.py — 47 linhas, CDD score = 12 🟠
def dashboard_respostas(request):
    respostas = RespostaQuestionario.objects.all()
    if request.GET.get('questionario'):
        respostas = respostas.filter(questionario_id=request.GET['questionario'])
    ordem = request.GET.get('ordem', 'desc')
    if ordem == 'asc':
        respostas = respostas.order_by('data_submissao')
    else:
        respostas = respostas.order_by('-data_submissao')
    # ... mais 30 linhas de paginação + contexto
    return render(request, 'dashboard_respostas.html', context)
```

### Depois (Refatorado com service + selector)
```python
# selectors.py
def get_respostas_filtradas(questionario_id=None, ordem='desc'):
    qs = (RespostaQuestionario.objects
          .select_related('questionario', 'pesquisadora')
          .all())
    if questionario_id:
        qs = qs.filter(questionario_id=questionario_id)
    ordering = 'data_submissao' if ordem == 'asc' else '-data_submissao'
    return qs.order_by(ordering)

# views.py — 10 linhas, CDD score = 1 🟢
def dashboard_respostas(request):
    respostas = get_respostas_filtradas(
        questionario_id=request.GET.get('questionario'),
        ordem=request.GET.get('ordem', 'desc'),
    )
    page = paginar(respostas, request.GET.get('page'), por_pagina=20)
    return render(request, 'dashboard_respostas.html', {
        'respostas': page,
        'questionarios': Questionario.objects.filter(ativo=True),
    })
```

---

## 11. Checklist Pré-Entrega

Antes de finalizar qualquer refatoração, confirme:

```
[ ] Comportamento funcional inalterado (refatoração isomórfica)
[ ] Nenhum import não utilizado remanescente
[ ] Nenhum magic number/string novo introduzido
[ ] Docstrings preservadas ou atualizadas
[ ] Padrões do CLAUDE.md respeitados
[ ] Testes executados (ou proposta de execução apresentada)
[ ] Relatório de diagnóstico produzido como artefato
```

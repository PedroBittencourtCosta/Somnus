# Auditoria de Cobertura de Testes e Criação de Novos Testes

## Diagnóstico Atual

O projeto Somnus possui **cobertura de testes ZERO**. Os três arquivos `tests.py` (core, accounts, ethics) contêm apenas o import padrão do Django sem nenhum teste implementado:

```python
from django.test import TestCase
# Create your tests here.
```

Isso significa que **nenhum** modelo, view, formulário, serviço, calculadora ou URL possui testes automatizados.

---

## Inventário de Módulos a Testar

### Mapa de Complexidade e Risco

| Módulo | Arquivo | Linhas | Complexidade | Risco | Prioridade |
|--------|---------|--------|--------------|-------|------------|
| **Calculadoras de Escalas** | [`Scaleprocessor.py`](file:///c:/Users/pedro/Documents/Somnus/core/Scaleprocessor.py) | 392 | 🔴 Alta | 🔴 Crítico — cálculos clínicos | **P0** |
| **Serviços de Negócio** | [`core/services.py`](file:///c:/Users/pedro/Documents/Somnus/core/services.py) | 125 | 🟡 Média | 🔴 Crítico — persistência de resultados | **P0** |
| **Modelos Core** | [`core/models.py`](file:///c:/Users/pedro/Documents/Somnus/core/models.py) | 257 | 🟡 Média | 🟡 Alto — regras de negócio em `save()` | **P1** |
| **Views Core** | [`core/views.py`](file:///c:/Users/pedro/Documents/Somnus/core/views.py) | 891 | 🔴 Alta | 🔴 Crítico — fluxo de questionário + TCLE | **P1** |
| **Formulários Accounts** | [`accounts/forms.py`](file:///c:/Users/pedro/Documents/Somnus/accounts/forms.py) | 81 | 🟢 Baixa | 🟡 Alto — validação de dados de entrada | **P1** |
| **Views Accounts** | [`accounts/views.py`](file:///c:/Users/pedro/Documents/Somnus/accounts/views.py) | 155 | 🟡 Média | 🟡 Alto — auth e permissões | **P1** |
| **Modelos Accounts** | [`accounts/models.py`](file:///c:/Users/pedro/Documents/Somnus/accounts/models.py) | 18 | 🟢 Baixa | 🟡 Alto — lógica custom no `save()` | **P2** |
| **Views Ethics** | [`ethics/views.py`](file:///c:/Users/pedro/Documents/Somnus/ethics/views.py) | 81 | 🟡 Média | 🟡 Alto — controle de acesso e validação | **P2** |
| **Modelos Ethics** | [`ethics/models.py`](file:///c:/Users/pedro/Documents/Somnus/ethics/models.py) | 29 | 🟢 Baixa | 🟢 Médio | **P3** |
| **Template Tags** | [`custom_filters.py`](file:///c:/Users/pedro/Documents/Somnus/core/templatetags/custom_filters.py) | 15 | 🟢 Baixa | 🟢 Baixo | **P3** |
| **Decorators** | [`core/decorators.py`](file:///c:/Users/pedro/Documents/Somnus/core/decorators.py) | 11 | 🟢 Baixa | 🟡 Alto — segurança de acesso | **P3** |
| **Management Command** | [`backfill_resultados.py`](file:///c:/Users/pedro/Documents/Somnus/core/management/commands/backfill_resultados.py) | 73 | 🟡 Média | 🟢 Médio | **P3** |
| **URLs** | `core/urls.py`, `accounts/urls.py`, `ethics/urls.py` | ~58 | 🟢 Baixa | 🟢 Médio — garantir que rotas resolvem | **P3** |

---

## Proposta de Estrutura dos Testes

Vou reorganizar os testes de arquivos monolíticos (`tests.py`) para pacotes de teste bem organizados:

```
core/
├── tests/
│   ├── __init__.py
│   ├── test_models.py            # Modelos do core
│   ├── test_scaleprocessor.py    # Calculadoras de escalas (PSQI, DASS-21, K10, etc.)
│   ├── test_services.py          # calcular_e_salvar_resultados, _extrair_score_e_classif
│   ├── test_views.py             # Views do core (responder, dashboard, exportar, etc.)
│   ├── test_views_api.py         # Views API (salvar questionário, configurar escala, etc.)
│   ├── test_urls.py              # Resolução de URLs
│   ├── test_templatetags.py      # Template filters customizados
│   └── test_decorators.py        # Decorators de permissão

accounts/
├── tests/
│   ├── __init__.py
│   ├── test_models.py            # Modelo Usuario
│   ├── test_forms.py             # Formulários de cadastro, perfil, senha
│   ├── test_views.py             # Login, logout, cadastro, gestão de assistentes
│   └── test_urls.py              # Resolução de URLs

ethics/
├── tests/
│   ├── __init__.py
│   ├── test_models.py            # TCLE e AceiteTCLE
│   ├── test_views.py             # TCLE views
│   └── test_urls.py              # Resolução de URLs
```

---

## Mudanças Propostas

### Fase 0 — Infraestrutura (pré-requisito)

#### [DELETE] `core/tests.py`, `accounts/tests.py`, `ethics/tests.py`
Remover os arquivos vazios e substituí-los por pacotes de teste.

#### [NEW] `conftest.py` (raiz do projeto)
Fixtures compartilhadas para pytest/Django:
- `usuario_pesquisador` — Usuário no grupo Pesquisador
- `usuario_assistente` — Usuário no grupo Assistente de Pesquisa
- `usuario_comum` — Usuário sem grupo
- `questionario_completo` — Questionário com seções, perguntas e alternativas
- `resposta_completa` — RespostaQuestionario com RespostaPergunta populadas
- `escala_psqi`, `escala_dass21`, etc. — EscalaConfig para cada tipo
- `tcle_ativo` — TCLE para fluxo de aceite

> [!IMPORTANT]
> **Decisão de framework**: O projeto atualmente não usa `pytest`. Precisamos decidir entre usar o `TestCase` nativo do Django ou instalar `pytest-django`. O pytest oferece fixtures reutilizáveis e output mais limpo, mas o Django `TestCase` funciona sem dependências extras.

---

### Fase 1 — Testes de Calculadoras de Escalas (P0 — Crítico)

#### [NEW] `core/tests/test_scaleprocessor.py`

Este é o módulo **mais crítico** — erros aqui significam resultados clínicos incorretos.

**Testes planejados (~60 testes):**

| Classe | Casos de teste |
|--------|----------------|
| `SafeParser` | `to_float` (inteiro, float, string com vírgula, string com unidade "75kg", None, string vazia, valores negativos) |
| | `to_int` (mesmos cenários do to_float) |
| | `parse_time` ("01:30", "1h30", "0130", None, string vazia, formato inválido) |
| `DASS21Calculator` | Score completo com dados corretos, dados parciais (missing keys), todos zeros, valores máximos |
| `K10Calculator` | Score baixo (<20 = "Baixo risco"), score alto (≥20 = "Provável transtorno"), boundary (19→20), zeros |
| `SRQ20Calculator` | Soma correta de respostas "Sim", boundary (6→7 = "Suspeita de TMC"), zeros, todos "Sim" |
| `ESECalculator` | Score normal (≤10), sonolência excessiva (>10), boundary (10→11), zeros, score máximo (24) |
| `AUDITCalculator` | "Baixo Risco" (≤7), "Uso de Risco" (8-15), "Uso Nocivo" (16-19), "Provável Dependência" (≥20), boundaries exatas |
| `EMSSPCalculator` | Scores por categoria (família, amigos, outros), total correto, zeros |
| `PSQICalculator` | Score global com dados completos, qualidade boa (≤5), qualidade ruim (>5), eficiência do sono, tempos de dormir/levantar |
| `IMCCalculator` | Abaixo do peso (<18.5), normal, sobrepeso, obesidade, altura zero ("Dados incompletos"), vírgula vs ponto |
| `DynamicResolver` | Operação SUM, SUM_BY_SUBSCALE, AVERAGE, operação desconhecida ("erro"), limiares, config vazia |
| `EscalaEngine` | Roteamento correto para cada strategy_class, strategy desconhecida ("erro"), DYNAMIC sem config ("erro") |

---

### Fase 2 — Testes de Serviços e Modelos (P0/P1)

#### [NEW] `core/tests/test_services.py`
**Testes planejados (~15 testes):**
- `_extrair_score_e_classif`: Cada strategy_class (PSQI, DASS21, K10, SRQ20, ESE, AUDIT, EMSSP, IMC, DYNAMIC)
- `_montar_answers_map`: Mapeamento correto por identificador, com alternativa vs texto
- `calcular_e_salvar_resultados`: Criação de ResultadoEscala, update_or_create idempotente, skip de erros

#### [NEW] `core/tests/test_models.py`
**Testes planejados (~20 testes):**
- `Questionario`: `__str__`, `titulo_curto` (≤7 palavras OK, >7 palavras trunca)
- `Secao`: `__str__`, ordering por `ordem`
- `Pergunta`: `__str__` com e sem identificador, ordering
- `RespostaQuestionario`: Geração automática de `codigo_paciente` (UUID, 10 chars, uppercase), unicidade garantida no `save()`, `__str__`
- `EscalaConfig`: `__str__`, choices de `strategy_class`
- `ResultadoEscala`: `unique_together`, `__str__`

#### [NEW] `accounts/tests/test_models.py`
**Testes planejados (~5 testes):**
- `Usuario.save()`: Username sincroniza com email automaticamente
- `__str__`: Retorna full_name se disponível, senão email
- `USERNAME_FIELD` é `email`

#### [NEW] `accounts/tests/test_forms.py`
**Testes planejados (~12 testes):**
- `CadastroAssistenteForm`: Validação de senhas iguais, senhas diferentes (erro), campos obrigatórios
- `PerfilForm`: Edição de dados válidos
- `AlterarSenhaForm`: Troca válida, senha atual incorreta
- `UsuarioCreationForm`: Criação com email válido, email duplicado

#### [NEW] `ethics/tests/test_models.py`
**Testes planejados (~5 testes):**
- `TCLE`: `__str__`, criação com versão
- `AceiteTCLE`: `__str__`, relacionamento OneToOne com RespostaQuestionario

---

### Fase 3 — Testes de Views (P1)

#### [NEW] `core/tests/test_views.py`
**Testes planejados (~35 testes):**
- `index_view`: Status 200, template correto
- `lista_questionarios`: Exibe apenas questionários ativos
- `gerenciar_questionarios`: Requer login, exibe todos (ativos e inativos)
- `responder_questionario`: Fluxo completo (GET → paginação → POST próximo → POST finalizar), proteção de página, TCLE obrigatório, salvamento na sessão
- `desativar_questionario`: Toggle ativo/inativo, requer login e POST
- `dashboard_respostas`: Requer login, filtro por questionário, KPIs corretos
- `exportar_respostas_excel`: Retorna `.xlsx`, conteúdo correto
- `exportar_resultados_massa_excel`: Exportação em massa
- `recalcular_escalas`: Requer login e POST, retorno JSON

#### [NEW] `core/tests/test_views_api.py`
**Testes planejados (~15 testes):**
- `salvar_questionario_api`: Criar novo questionário, editar existente, dependências entre perguntas, cleanup de registros removidos
- `configurar_escala_view`: Vincular/desvincular escala, desativar, criar DYNAMIC, criar nativa

#### [NEW] `accounts/tests/test_views.py`
**Testes planejados (~18 testes):**
- `login_view`: Login com credenciais corretas, incorretas, conta desativada, usuário já logado
- `logout_view`: Redireciona para home
- `cadastro_view`: GET exibe formulário, POST válido cria usuário, POST inválido mostra erros
- `perfil_view`: Requer login, GET mostra dados, POST atualiza
- `alterar_senha_view`: Troca válida, senha atual incorreta
- `cadastrar_assistente`: Só pesquisador/staff, criação com grupo correto
- `gestao_assistentes`: Só pesquisador/staff, lista correta (exclui próprio user e superusers)
- `alternar_status_assistente`: Toggle is_active, resposta JSON para AJAX, não pode desativar a si mesmo

#### [NEW] `ethics/tests/test_views.py`
**Testes planejados (~12 testes):**
- `aceitar_tcle`: Marca sessão, requer login e POST
- `lista_tcle`: Só pesquisador/staff, ordenação por data
- `nova_versao_tcle`: Validação (conteúdo vazio, versão inválida, versão duplicada), sugestão de próxima versão, criação com sucesso

---

### Fase 4 — Testes Complementares (P3)

#### [NEW] `core/tests/test_urls.py`
- Resolução de todas as URLs do `core/urls.py` para as views corretas

#### [NEW] `accounts/tests/test_urls.py`
- Resolução de todas as URLs do `accounts/urls.py`

#### [NEW] `ethics/tests/test_urls.py`
- Resolução de todas as URLs do `ethics/urls.py`

#### [NEW] `core/tests/test_templatetags.py`
- `get_item`, `get_item_key`, `get_val`: Com chaves existentes e inexistentes

#### [NEW] `core/tests/test_decorators.py`
- `medico_ou_admin_required`: Acesso staff, grupo Medicos, usuário comum, anônimo

---

## Resumo Quantitativo

| Fase | Arquivos | Testes estimados | Prioridade |
|------|----------|------------------|------------|
| Fase 0 — Infraestrutura | 4 (conftest + __init__.py) | — | Pré-requisito |
| Fase 1 — Calculadoras | 1 | ~60 | P0 |
| Fase 2 — Serviços/Modelos | 5 | ~57 | P0/P1 |
| Fase 3 — Views | 5 | ~80 | P1 |
| Fase 4 — Complementares | 6 | ~30 | P3 |
| **Total** | **~21 arquivos** | **~227 testes** | — |

---

## Verificação

### Testes Automatizados
```bash
python manage.py test --verbosity=2
```
Todos os testes devem passar sem erros.

### Relatório de Cobertura (opcional)
Se quiser instalar `coverage`:
```bash
pip install coverage
coverage run manage.py test
coverage report --show-missing
```

---

## Open Questions

> [!IMPORTANT]
> **Framework de testes**: Prefere usar `pytest-django` (com fixtures, parametrize, output mais moderno) ou o `TestCase` nativo do Django (zero dependências extras)?

> [!IMPORTANT]
> **Banco de dados para testes**: O projeto usa PostgreSQL + campos criptografados (`django-encrypted-model-fields`). Os testes precisam de um banco PostgreSQL local rodando, ou podemos usar SQLite em memória para testes? Os campos `EncryptedCharField`/`EncryptedTextField` funcionam com SQLite desde que a `FIELD_ENCRYPTION_KEY` esteja configurada.

> [!IMPORTANT]
> **Escopo desta execução**: Deseja que eu implemente todas as 4 fases de uma vez, ou prefere que eu execute fase por fase para revisar incrementalmente?

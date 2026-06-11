# CLAUDE.md — Guia de Contexto do Projeto Somnus

> Este arquivo documenta os padrões técnicos, visuais e arquiteturais do projeto Somnus.
> Deve ser lido por qualquer agente de IA antes de propor ou executar alterações.

---

## 1. O que é o Somnus?

O **Somnus** é um sistema web de pesquisa clínica desenvolvido em **Django** para a **UniRV (Universidade de Rio Verde)**, pelo escritório de design **EMGRAFI**.

Seu objetivo é **coletar, processar e exportar respostas de questionários clínicos** validados sobre qualidade de sono, saúde mental e bem-estar. O sistema é voltado para pesquisadores e assistentes de pesquisa, com suporte a múltiplos questionários e escalas clínicas padronizadas.

### Escalas suportadas
| Sigla | Nome completo |
|---|---|
| PSQI | Índice de Qualidade de Sono de Pittsburgh |
| DASS-21 | Depression, Anxiety and Stress Scale |
| K10 | Escala de Sofrimento Psicológico de Kessler |
| SRQ-20 | Self-Reporting Questionnaire |
| ESE | Escala de Sonolência de Epworth |
| AUDIT | Alcohol Use Disorder Identification Test |
| EMSSP | Escala Multidimensional de Suporte Social Percebido |
| IMC | Índice de Massa Corporal |
| DYNAMIC | Construtor visual de escalas customizadas |

---

## 2. Stack Tecnológica

| Camada | Tecnologia |
|---|---|
| Backend | Python / Django |
| Frontend | Bootstrap 5 + Vanilla CSS + SVG Icons inline |
| Banco de dados | PostgreSQL (via Docker) |
| Template engine | Django Templates (Jinja-like) |
| Criptografia | `django-encrypted-model-fields` (AES-256) |
| Autenticação | Django Auth nativo + grupos de permissão |
| Containerização | Docker Compose (`compose.yml`) |

---

## 3. Estrutura do Projeto

```
somnus_project/
├── accounts/          # App de autenticação e gestão de usuários
│   └── templates/     # login, cadastro, perfil, modal_login, gestao_assistentes
├── core/              # App principal: questionários, respostas, escalas
│   ├── templates/     # dashboard, lista, responder, gerenciar, configurar_escala
│   ├── static/        # CSS e assets do app core
│   ├── Scaleprocessor.py  # Motor de processamento de escalas clínicas
│   ├── models.py      # Modelos principais
│   └── views.py       # Views principais
├── ethics/            # App de TCLE (Termo de Consentimento Livre e Esclarecido)
│   └── templates/     # lista_tcle, nova_versao_tcle, modal_tcle
├── somnus/            # Configurações Django (settings, urls, wsgi)
├── templates/         # Templates globais (base.html, home, partials)
│   └── partials/      # _navbar.html, _footer.html
├── static/            # Assets globais
│   └── css/style.css  # Design system global (variáveis CSS)
└── CLAUDE.md          # Este arquivo
```

---

## 4. Design System — Cores

Todas as cores estão definidas como **CSS Custom Properties** em [`static/css/style.css`](static/css/style.css).

```css
:root {
    --somnus-blue-deep:  #253786;   /* Azul institucional escuro — títulos, footer, botão Entrar */
    --somnus-blue-inst:  #0067b1;   /* Azul institucional médio — links ativos, botões secundários, focus */
    --somnus-green-light: #76b82a;  /* Verde claro — hover de botão CTA, rodapé links hover */
    --somnus-green-dark:  #009640;  /* Verde escuro — botão CTA principal ("Avaliar agora") */
}
```

### Mapeamento de uso

| Token | Uso principal |
|---|---|
| `--somnus-blue-deep` | Títulos `<h2>`, footer background, botão "Entrar" navbar, labels de filtro |
| `--somnus-blue-inst` | Links ativos, botão "Novo Colaborador", bordas no focus de inputs, botão ativo de ordenação |
| `--somnus-green-dark` | Botão primário CTA ("Avaliar agora"), badge de status ativo |
| `--somnus-green-light` | Hover de links no footer, hover do botão CTA |

### Cores semânticas hard-coded (usadas com moderação)

| Hex | Uso |
|---|---|
| `#d1fae5` / `#065f46` | Badge "Ativo" (fundo verde suave / texto verde escuro) |
| `#fee2e2` / `#991b1b` | Badge "Inativo" (fundo vermelho suave / texto vermelho escuro) |
| `#e0e7ff` / `#3730a3` | Badge de função/grupo (fundo índigo suave / texto índigo) |
| `#dc2626` | Botão de desativar / ícone de perigo |
| `#059669` | Botão de reativar |
| `#6b7280` | Textos secundários, bordas neutras, botão "Limpar filtros" |
| `#dee2e6` | Bordas padrão de inputs e separadores |

---

## 5. Design System — Tipografia

| Propriedade | Valor |
|---|---|
| Família principal | `Poppins` (Google Fonts) |
| Pesos carregados | 300, 400, 600, 700 |
| Fallback | `sans-serif` |
| Aplicação | Sobrescreve `--bs-body-font-family` do Bootstrap globalmente |

### Tamanhos de texto recorrentes

| Contexto | Tamanho |
|---|---|
| Labels de filtro | `0.82rem` |
| Textos de tabela secundários | `0.9rem` |
| Badges | `0.75rem` |
| Textos de rodapé / créditos | `0.65rem` |
| Botões de ação pequenos | `0.82rem` |
| Corpo padrão | `1rem` (Bootstrap default) |

---

## 6. Design System — Ícones

O projeto usa **dois sistemas de ícones simultâneos**:

### 6.1 SVG Inline (padrão nos templates de navegação e ações)
Todos os ícones da navbar, botões de ação e estados vazios são SVGs inline do estilo **Heroicons** (outline, `stroke-width="2"`, `fill="none"`).

Padrão de escrita:
```html
<svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="..."/>
</svg>
```

**Catálogo de ícones SVG usados no projeto:**

| Ícone | Contexto | Path `d=` |
|---|---|---|
| Clipboard / Avaliações | Nav → Avaliações | `M9 5H7a2 2 0 00-2 2v12...` (clipboard com check) |
| Bar chart | Nav → Dashboard | `M9 19v-6a2 2 0 00-2-2H5...` (gráfico de barras) |
| Users / Colaboradores | Nav → Colaboradores | `M17 20h5v-2a3 3 0 00-5.356...` |
| Document text | Nav → TCLE | `M9 12h6m-6 4h6m2 5H7...` (documento com linhas) |
| Document add | Nav → Questionários | `M9 13h6m-3-3v6m5 5H7...` (documento com +) |
| User | Nav → Perfil | `M16 7a4 4 0 11-8 0 4 4...` (pessoa) |
| Logout | Nav → Sair | `M17 16l4-4m0 0l-4-4m4 4H7...` (seta saindo) |
| Trash / Delete | Ação → Desativar | `M19 7l-.867 12.142A2 2 0...` (lixeira) |
| Refresh | Ação → Reativar | `M4 4v5h.582m15.356 2A8.001...` (seta circular) |
| Chevron down | Ordenar decrescente | `M19 9l-7 7-7-7` |
| Chevron up | Ordenar crescente | `M5 15l7-7 7 7` |
| X / Close | Limpar filtros | `M6 18L18 6M6 6l12 12` |
| Phone | Rodapé → Contato | SVG fill com path do telefone |
| Double chevron down | Home → scroll | `M19 14l-7 7-7-7m14-8l-7 7-7-7` (bounce) |

### 6.2 Bootstrap Icons (`bi bi-*`)
Usados nos filtros de texto e alguns estados de componentes. Requerem que a biblioteca Bootstrap Icons esteja carregada.

| Classe | Contexto |
|---|---|
| `bi bi-search` | Input de busca por nome/e-mail |
| `bi bi-people` | Select de função/grupo |
| `bi bi-toggle-on` | Select de status |
| `bi bi-x-circle` | Botão "Limpar filtros" |
| `bi bi-funnel` | Estado vazio após filtro |
| `bi bi-shield-lock-fill` | Código do paciente (privacidade) |
| `bi bi-download` | Botão exportar Excel |
| `bi bi-exclamation-circle` | Mensagem de erro no login |

---

## 7. Padrões de Componentes UI

### 7.1 Cards
```html
<!-- Card padrão de container -->
<div class="card border-0 shadow-sm rounded-4">
    <div class="card-body px-4 py-3">
        <!-- conteúdo -->
    </div>
</div>
```
- Sempre `border-0 shadow-sm rounded-4`
- Padding interno: `px-4 py-3` (filtros) ou `p-4` (cards informativos)

### 7.2 Tabelas
```html
<div class="card border-0 shadow-sm rounded-4 overflow-hidden">
    <div class="table-responsive">
        <table class="table table-hover align-middle mb-0">
            <thead class="table-light">...</thead>
        </table>
    </div>
</div>
```
- Sempre envoltas em `card border-0 shadow-sm rounded-4 overflow-hidden`
- Hover personalizado: `rgba(0, 103, 177, 0.04)` (azul institucional com 4% opacidade)
- Bordas entre células: `rgba(0, 0, 0, 0.05)`

### 7.3 Badges de Status
```html
<!-- Ativo -->
<span class="badge rounded-pill px-3 py-2"
    style="background-color: #d1fae5; color: #065f46; font-size: 0.75rem;">
    ● Ativo
</span>

<!-- Inativo -->
<span class="badge rounded-pill px-3 py-2"
    style="background-color: #fee2e2; color: #991b1b; font-size: 0.75rem;">
    ○ Inativo
</span>
```

### 7.4 Badges de Função/Grupo
```html
<span class="badge rounded-pill px-3 py-2"
    style="background-color: #e0e7ff; color: #3730a3; font-size: 0.75rem; font-weight: 600;">
    Pesquisador
</span>
```

### 7.5 Botões Principais
```html
<!-- CTA primário (ação verde) -->
<a class="btn btn-lg px-5 py-3 rounded-pill fw-bold text-white shadow-lg"
   style="background-color: var(--somnus-green-dark);">
    Avaliar agora
</a>

<!-- Botão institucional azul -->
<a class="btn text-white fw-bold shadow-sm rounded-pill px-4"
   style="background-color: var(--somnus-blue-inst);">
    + Novo Colaborador
</a>

<!-- Botão "Entrar" navbar -->
<button class="btn btn-primary rounded-pill px-4 py-2 fw-semibold shadow-sm"
    style="background-color: var(--somnus-blue-deep); border: none; font-size: 0.85rem;">
    Entrar
</button>
```

### 7.6 Inputs de Filtro
```css
.filter-label {
    font-weight: 600;
    font-size: 0.82rem;
    color: var(--somnus-blue-deep);
    margin-bottom: 0.4rem;
}

.filter-input {
    border-radius: 0.75rem;
    border: 1px solid #e5e7eb;
    background-color: #f8f9fa;
    font-size: 0.875rem;
}

.filter-input:focus {
    border-color: var(--somnus-blue-inst);
    box-shadow: 0 0 0 0.2rem rgba(0, 103, 177, 0.1);
}
```

### 7.7 Títulos de Página
```html
<h2 class="fw-bold" style="color: var(--somnus-blue-deep);">Título da Página</h2>
<p class="text-muted mb-0">Subtítulo descritivo curto.</p>
```

---

## 8. Modelos de Dados Principais

| Model | App | Descrição |
|---|---|---|
| `Questionario` | core | Questionário clínico (soft-delete via `ativo`) |
| `Secao` | core | Seções de um questionário (layout LISTA ou TABELA) |
| `Pergunta` | core | Pergunta com tipo (MC, TX, MX), máscara e dependências |
| `Alternativa` | core | Opções de resposta com valor numérico |
| `RespostaQuestionario` | core | Submissão de um paciente (criptografada via LGPD) |
| `RespostaPergunta` | core | Resposta individual por pergunta |
| `EscalaConfig` | core | Configuração de escala clínica vinculada a questionários |
| `User` | accounts | Usuário Django padrão com grupos de permissão |

### Grupos de permissão
| Grupo | Acesso |
|---|---|
| `Pesquisador` | Acesso total: dashboard, TCLE, questionários, colaboradores |
| `Assistente de Pesquisa` | Acesso ao dashboard de respostas |
| `is_staff` | Equivalente ao Pesquisador (acesso total) |
| Não autenticado | Apenas páginas públicas + formulários de resposta |

---

## 9. Convenções de Código

### Templates Django
- Sempre estender `base.html`: `{% extends 'base.html' %}`
- CSS específico de página vai dentro do próprio template em `<style>` no final do bloco `content`
- **Nunca** usar Tailwind — somente Bootstrap 5 + classes utilitárias do projeto
- IDs de elementos: `kebab-case` (ex: `filtro-questionario`, `btn-ordem-desc`)
- Para SVG inline, sempre usar `fill="none" stroke="currentColor"` para herdar a cor do contexto

### CSS
- Variáveis de cor sempre via `var(--somnus-*)` — nunca hex direto para as cores do design system
- Transições padrão: `transition: all 0.18s ease` ou `transition: color 0.2s ease`
- Hover em botões de ação: `filter: brightness(1.1)` para variações sutis

### JavaScript
- Padrão: Vanilla JS com `document.addEventListener('DOMContentLoaded', ...)`
- AJAX/fetch para ações sem reload (ex: toggle ativo/inativo)
- CSRF Token via `{{ csrf_token }}` no header `X-CSRFToken`

### Privacidade e LGPD
- Nome real do paciente: **sempre** via `EncryptedCharField` (AES-256)
- Identificador público: `codigo_paciente` (UUID truncado, 10 chars, uppercase)
- Dados sensíveis de texto livre: `EncryptedTextField`

---

## 10. Imagens e Assets

| Arquivo | Uso |
|---|---|
| `images/Marca - Sonmus.png` | Logo principal (navbar, modal de login) |
| `images/marca em branco.png` | Logo branca para o rodapé escuro |
| `images/icone - Somnus.png` | Favicon do site |

---

## 11. URLs e Rotas Conhecidas

| URL name | Descrição |
|---|---|
| `lista_questionarios` | Página pública de avaliações |
| `dashboard_respostas` | Dashboard de respostas (restrito) |
| `gestao_assistentes` | Gestão de colaboradores (Pesquisador/Staff) |
| `lista_tcle` | Lista de TCLEs (Pesquisador/Staff) |
| `gerenciar_questionarios` | Gerenciamento de questionários (Pesquisador/Staff) |
| `configurar_escala` | Configurador de escalas clínicas |
| `perfil` | Perfil do usuário logado |
| `login` / `logout` | Autenticação |
| `cadastro` | Cadastro público (atualmente oculto) |
| `exportar_respostas_excel` | Exportação de respostas em `.xlsx` |
| `alternar_status_assistente` | Toggle ativo/inativo via POST (fetch) |
| `dicas` | Dicas de segurança |
| `sobre` | Sobre nós |
| `bem_estar` | Página de bem-estar |
| `sono` | Página sobre sono |

---

## 12. Regras para o Agente de IA

1. **Sempre usar as variáveis CSS do design system** (`--somnus-blue-deep`, etc.) — nunca substituir por hex equivalente.
2. **Manter o padrão de SVG inline** para novos ícones — estilo Heroicons outline, `stroke-width="2"`.
3. **Não usar Tailwind CSS** — somente Bootstrap 5 + Vanilla CSS.
4. **CSS de página** vai dentro do `<style>` no final do bloco `{% block content %}` do próprio template.
5. **Respeitar os grupos de permissão** ao criar novas rotas ou views.
6. **Dados de pacientes são sensíveis** — qualquer campo de identificação pessoal deve usar `EncryptedCharField` ou `EncryptedTextField`.
7. **Soft-delete** é o padrão: usar campo `ativo = BooleanField` em vez de deletar registros.
8. **Badges de status** sempre seguem o padrão verde (`#d1fae5` / `#065f46`) para ativo e vermelho (`#fee2e2` / `#991b1b`) para inativo.
9. **Paginação** em listagens longas usando `django.core.paginator.Paginator`.
10. **Respostas de idioma**: todo o sistema está em **Português do Brasil**.

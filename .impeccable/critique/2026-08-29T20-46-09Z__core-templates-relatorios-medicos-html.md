---
target: core/templates/relatorios_medicos.html
total_score: 20
max_score: 28
na_heuristics: 5,9,10
p0_count: 0
p1_count: 1
timestamp: 2026-08-29T20-46-09Z
slug: core-templates-relatorios-medicos-html
---
⚠️ DEGRADED: single-context (no general sub-agent spawn tool exposed in this session)

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 3 | Sort arrows and pagination are clear |
| 2 | Match System / Real World | 4 | "Relatórios" and "Exportar excel" are clear |
| 3 | User Control and Freedom | 3 | "Voltar ao Dashboard" is a clear exit |
| 4 | Consistency and Standards | 1 | "Exportar" buttons violate "The One CTA Rule" and use undocumented colors |
| 5 | Error Prevention | n/a | Read-only list |
| 6 | Recognition Rather Than Recall | 4 | Filters and headers are visible |
| 7 | Flexibility and Efficiency | 3 | Sorting and filtering are functional |
| 8 | Aesthetic and Minimalist Design | 2 | Solid green buttons clutter the list |
| 9 | Error Recovery | n/a | Read-only list |
| 10 | Help and Documentation | n/a | Read-only list |
| **Total** | | **20/28** | **Good** |

### Design Specificity Verdict

O design tem uma base sólida, mas perde a especificidade do produto nas ações da tabela. A avaliação nota que a interface se baseia bem no Bootstrap, mas desrespeita diretamente o `DESIGN.md` ao aplicar uma cor primária em ações repetitivas de listagem, criando ruído visual.

A análise do detector confirma isso: encontrou múltiplos tamanhos de fonte (`0.95rem`, `0.9rem`, `0.75rem`) que fogem da escala tipográfica do projeto, e uma cor hardcoded (`#3f8753`) usada nos botões que não pertence à paleta oficial, além de fundo branco hardcoded (`#fff`). Não foi possível injetar overlay visual no navegador.

### Overall Impression
O layout geral é limpo e a estruturação em cards funciona bem, mas a lista de botões verdes pesados desvia o foco dos dados e quebra as regras da marca. A maior oportunidade é suavizar as ações da tabela para que a interface de gestão não pareça uma página de check-in de paciente.

### What's Working
1. **Estrutura de Card Limpa**: O uso de fundo claro, sombras leves e bordas arredondadas nos containers segue muito bem o "The Tactual Rule".
2. **Identificação de Questionários**: O uso de badges em formato pill para os questionários facilita muito a leitura e o escaneamento visual.

### Priority Issues
- **[P1] Violação da Regra "The One CTA Rule"**:
  - **Why it matters**: Botões de "Exportar excel" usam um verde não documentado (`#3f8753`) e um estilo sólido chamativo. O `DESIGN.md` dita que apenas a ação principal absoluta do paciente recebe o verde primário, e interfaces do pesquisador devem usar o azul institucional. Isso satura a tela e rouba atenção.
  - **Fix**: Substituir a classe/estilo dos botões da tabela para usar `btn-outline-secondary` ou o azul institucional do Somnus, ou ainda trocar o texto por apenas um ícone de download sutil.
  - **Suggested command**: `$impeccable quieter`
- **[P2] Tamanhos de Fonte Fora do Padrão (Drift)**:
  - **Why it matters**: Existem vários `font-size` hardcoded (`0.95rem`, `0.9rem`, `0.85rem`, `0.75rem`) poluindo o HTML e criando pequenas inconsistências visuais em relação ao "Poppins" e à hierarquia do sistema.
  - **Fix**: Remover os tamanhos em linha e usar as classes de tipografia do Bootstrap ou as definidas no CSS (`small`, labels, etc.).
  - **Suggested command**: `$impeccable typeset`
- **[P3] Inconsistência de Formas na Paginação**:
  - **Why it matters**: Os botões e badges seguem a regra "rounded-pill" amigável, mas os botões de paginação utilizam cantos semi-quadrados (`0.5rem`). Isso faz o rodapé parecer de outro template.
  - **Fix**: Aplicar cantos totalmente arredondados (`rounded-pill`) na estrutura da paginação para unificar as formas.
  - **Suggested command**: `$impeccable polish`

### Persona Red Flags
- **Alex (Power User)**: Precisa exportar dados de múltiplos pacientes, mas é obrigado a clicar em "Exportar excel" linha por linha. A falta de uma ação "Exportar Todos" (Bulk) é ineficiente.
- **Jordan (First-Timer)**: Ao olhar para a tela, a enorme quantidade de verde nos botões da direita chama mais atenção do que os nomes dos pacientes ou as datas. A hierarquia visual está invertida.

### Minor Observations
- O filtro superior e os textos auxiliares têm cores hardcoded text-muted que poderiam ser substituídas diretamente por opacidade ou pelas cores neutras do Somnus.
- O ícone de tabela vazia tem boa intenção, mas usa traços que poderiam estar num arquivo SVG centralizado.

### Questions to Consider
- E se a exportação ocorresse no nível do questionário/filtro (um único botão "Exportar Resultados") em vez de linha por linha?
- Se os botões de exportar da tabela fossem apenas ícones, a interface não ficaria mais "acadêmica" e limpa?

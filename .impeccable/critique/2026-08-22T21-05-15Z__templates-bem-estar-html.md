---
target: templatesem_estar.html
total_score: 17
max_score: 20
na_heuristics: 1,3,5,7,9
p0_count: 0
p1_count: 1
timestamp: 2026-08-22T21-05-15Z
slug: templates-bem-estar-html
---
⚠️ DEGRADED: single-context (sub-agents indisponíveis no ambiente atual)

### Design Health Score

| # | Heurística | Score | Problema Principal |
|---|---|---|---|
| 1 | Visibilidade do Status do Sistema | n/a | Página informacional estática |
| 2 | Compatibilidade com o Mundo Real | 4 | Linguagem clínica acessível e sem jargões confusos |
| 3 | Controle e Liberdade do Usuário | n/a | Fluxo linear de leitura |
| 4 | Consistência e Padrões | 2 | Desvio massivo dos tokens do Design System (uso de HEX e RGBA soltos) |
| 5 | Prevenção de Erros | n/a | Página sem formulários de entrada |
| 6 | Reconhecimento em Vez de Lembrança | 4 | Informações divididas em blocos claros |
| 7 | Flexibilidade e Eficiência | n/a | Superfície de Persuasão (Leitura) |
| 8 | Estética e Design Minimalista | 3 | Sombra pesada no botão principal e contraste sobre imagem hero |
| 9 | Recuperação de Erros | n/a | Não aplicável |
| 10 | Ajuda e Documentação | 4 | "Nota Importante" traz ótimo disclaimer clínico |
| **Total** | | **17/20** | **Good** |

### Veredito de Especificidade do Design
A estrutura visual está **bem elaborada e responsiva**, mas sofre de forte *drift* (desvio técnico) do Design System oficial. A página funciona perfeitamente em dispositivos móveis graças ao uso intensivo de `@media queries` e funções `clamp()`, mas tecnicamente ela atua como um "corpo estranho" no sistema, ignorando as variáveis globais. O detector encontrou **24 instâncias** onde cores e tamanhos de fonte foram *hard-coded* (`rgba`, `#fff`, fonte `Inter`, `1.25rem`, etc.) em vez de usar os tokens documentados no `DESIGN.md`.

### Impressão Geral
Visulamente, a página cumpre muito bem o papel de persuadir e informar de maneira clínica e segura, se adaptando de forma elegante para o tablet e celular. No entanto, a manutenção do código será difícil se as cores da marca mudarem, devido ao uso excessivo de CSS isolado e valores engessados.

### O Que Está Funcionando
- **Responsividade Elegante:** O uso de tipografia fluida (`clamp`) e a adaptação do layout do Hero Image nos breakpoints de 900px e 600px garantem uma excelente experiência de leitura, perfeitamente de acordo com os princípios do produto para foco em mobile/tablet.
- **Card de Segurança:** O bloco "Nota Importante" com gradiente traz o peso e a seriedade necessários para um projeto clínico, quebrando a monotonia da leitura.

### Problemas Prioritários

- **[P1] Cores e Fontes Hard-coded (Quebra de Padrão Técnico)**
  - **Por que importa:** O arquivo cria seu próprio universo de variáveis (`--be-blue-inst`) e usa valores fixos ignorando o sistema. Se a cor global atualizar, essa tela ficará desatualizada. Além disso, o detector acusou o uso da fonte `Inter`, que não pertence ao padrão (Poppins).
  - **Fix:** Substituir todas as cores literais e variáveis locais pelas globais do projeto, removendo declarações de tamanho de fonte isoladas.
  - **Comando Sugerido:** `$impeccable polish` (para unificar o código com o Design System).

- **[P2] Contraste e Legibilidade do Texto no Hero Image**
  - **Por que importa:** O texto (`.bem-hero-title`) está posicionado de forma absoluta sobre a imagem. Dependendo da foto escolhida, o texto azul pode se perder no fundo, falhando em requisitos de acessibilidade (WCAG).
  - **Fix:** Adicionar um véu de gradiente ou uma caixa de cor translúcida atrás do texto, ou separar o texto da imagem.
  - **Comando Sugerido:** `$impeccable layout` (focando em acessibilidade e legibilidade).

### Alertas de Personas (Red Flags)
**Jordan (Iniciante Confuso):** O botão "Iniciar avaliação" está flutuando sobre a imagem fotográfica. Se a foto for visualmente ruidosa, Jordan pode demorar a entender qual é a ação principal, pois a interface mistura a fotografia com a interação.
**Casey (Usuário Mobile Distraído):** No celular (<600px), a imagem encolhe e o layout reage bem, mas o botão flutuante compete com o texto do hero na mesma área restrita.

### Observações Menores
- O `box-shadow` do botão verde (`0 16px 48px rgba(0, 0, 0, 0.18)`) é muito dramático para o estilo clínico da plataforma. O Design System recém-criado define sombras mais contidas (The Tactual Rule).

### Perguntas para Considerar
- Precisamos mesmo que a imagem Hero atue como papel de parede do texto? Se o texto ficasse em um bloco sólido e a imagem ao lado (ou abaixo), não ganharíamos 100% de clareza na leitura?
- A sombra dramática do botão flutuante é intencional para dar aspecto de app, ou um desvio que devemos normalizar?

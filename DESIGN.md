---
name: Somnus
description: Sistema web de pesquisa clínica e coleta de dados sobre o sono
colors:
  primary: "#009640"
  primary-hover: "#76b82a"
  secondary: "#0067b1"
  neutral-deep: "#253786"
  neutral-bg: "#f8f9fa"
  neutral-border: "#e5e7eb"
  status-active-bg: "#d1fae5"
  status-active-text: "#065f46"
  status-inactive-bg: "#fee2e2"
  status-inactive-text: "#991b1b"
typography:
  display:
    fontFamily: "'Poppins', sans-serif"
    fontWeight: 700
  headline:
    fontFamily: "'Poppins', sans-serif"
    fontWeight: 600
  body:
    fontFamily: "'Poppins', sans-serif"
    fontWeight: 400
  label:
    fontFamily: "'Poppins', sans-serif"
    fontWeight: 600
    fontSize: "0.82rem"
rounded:
  sm: "0.5rem"
  md: "0.75rem"
  lg: "1rem"
  pill: "50rem"
spacing:
  sm: "1rem"
  md: "1.5rem"
  lg: "3rem"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "#ffffff"
    rounded: "{rounded.pill}"
    padding: "0.75rem 1.5rem"
  button-secondary:
    backgroundColor: "{colors.secondary}"
    textColor: "#ffffff"
    rounded: "{rounded.pill}"
    padding: "0.375rem 1.5rem"
---

# Design System: Somnus

## Overview

**Creative North Star: "O Assistente de Pesquisa Fluido"**

O Somnus foca na ergonomia e na redução extrema de atrito durante a coleta de dados de pesquisas clínicas. Projetado para tablets e ambientes acadêmicos, a interface oferece ações óbvias, componentes altamente táteis e uma experiência fluida que guia o paciente pelo questionário sem confusão. Não há excesso decorativo: cada elemento visual existe para apoiar a clareza, a tomada de ação e a autoridade da plataforma.

**Key Characteristics:**
- Tipografia limpa, amigável e acadêmica (Poppins)
- Botões em formato "pill" (pílula) para incentivar o toque
- Layouts limpos organizados em "Cards" elevados
- Altíssimo contraste na ação principal para eliminar dúvidas

## Colors

O esquema de cores é institucional e confiável, utilizando azuis profundos de autoridade e verdes afirmativos para progressão.

### Primary
- **Green CTA** (#009640): Ação primária do paciente ("Avaliar agora"). Representa progresso e positividade.
- **Green Light** (#76b82a): Feedback interativo (hover).

### Secondary
- **Institutional Blue** (#0067b1): Interações do sistema de gestão, botões secundários ("Novo Colaborador"), links ativos e foco em formulários.

### Neutral
- **Deep Blue** (#253786): Cor institucional de peso. Usada em títulos principais (`<h2>`), rodapés e navegação.
- **Cool Background** (#f8f9fa): Fundo suave para inputs e formulários.

### Named Rules
**The One CTA Rule.** Apenas a ação principal absoluta da tela deve receber a cor verde (`#009640`). Todas as demais ações devem usar o azul institucional.

## Typography

**Display Font:** Poppins
**Body Font:** Poppins
**Fallback:** sans-serif

**Character:** Arredondada, legível e convidativa. Confere acessibilidade amigável sem perder o peso de um software clínico.

### Hierarchy
- **Display** (700, 2rem a 2.75rem): Títulos hero e painéis principais de pesquisa.
- **Headline** (700): Títulos estruturais de página (`<h2>`), utilizando a cor Deep Blue.
- **Body** (400, 1rem): Corpo base de textos e instruções.
- **Label** (600, 0.82rem): Títulos de filtro e badges de status — tamanho reduzido, alto contraste.

## Layout

O layout segue um grid fluido adaptado para não saturar a área de leitura em tablets. Elementos estruturais pesados sempre vivem contidos para não gerar distração na coleta de questionários. No mobile, os paddings horizontais diminuem, mas as áreas úteis (containers) se expandem para ocupar a tela.

## Elevation & Depth

As superfícies principais repousam sobre sombras que comunicam "físico" e interatividade, reforçando a natureza tátil da interface em tablets.

### Shadow Vocabulary
- **Card Base** (`box-shadow: 0 .125rem .25rem rgba(0,0,0,.075)`): O nível de fundo de cards informativos.
- **Hover Lift** (`box-shadow: 0 1rem 3rem rgba(0, 0, 0, 0.12)`): Sombreamento forte acionado quando o mouse interage com a superfície.

### Named Rules
**The Tactual Rule.** Se o agrupamento ou card é altamente interativo, ele deve "flutuar" (`translateY(-6px)`) perante o olhar do paciente ao ser focado ou pairado.

## Shapes

As formas geométricas priorizam o conforto visual. Curvas acentuadas ajudam na amigabilidade e criam targets de clique mais naturais.

- **Cards e Tabelas**: `1rem` de raio (`rounded-4`).
- **Botões e Badges**: Formato esférico prolongado (`rounded-pill`).
- **Inputs**: Borda suave de `0.75rem`.

## Components

### Botões Primários
- **Shape:** Pílula (`50rem` de radius)
- **Cores:** Fundo Green CTA (#009640), fonte Branca.
- **Hover / Focus:** Transição de 0.4s, alterando levemente o brilho/elevação para gerar feedback.

### Botões Institucionais (Secundários)
- **Foco:** Tarefas do pesquisador. Fundo Institutional Blue (#0067b1).
- **Tratamento:** Usados de forma contida para não competirem com o verde.

### Cards (Containers de Leitura)
- **Raio:** 16px (`1rem`)
- **Background:** Branco puro
- **Sombra:** Base plana e muito leve, saltando sob hover.

### Campos de Input / Filtro
- **Forma:** Fundo muito leve (`#f8f9fa`), bordas neutras macias.
- **Foco:** Anel de foco azul de baixa opacidade para guiar a atenção visual.

## Do's and Don'ts

### Do:
- **Do** manter a distinção rígida entre interface do paciente (verde para CTA de preenchimento) e interface do pesquisador (azul para sistema/listagem).
- **Do** garantir que todos os elementos clicáveis sejam táteis, com transições óbvias.
- **Do** adotar os SVGs inline simples (ex: `stroke-width="2"`) da biblioteca estilo Heroicons.

### Don't:
- **Don't** utilizar estilos hard-coded nas telas que fujam da estrutura limpa baseada em Bootstrap 5 e `style.css`.
- **Don't** achatar alvos de clique em dispositivos móveis, comprometendo o preenchimento de pacientes desatentos ou apressados.
- **Don't** sobrecarregar visualmente com uso desnecessário de sombras ou gradientes artificiais.

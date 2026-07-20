O objetivo central deste painel será correlacionar os Transtornos Mentais Comuns (TMC) com a qualidade do sono
, além de preparar a base de dados estruturada para análises preditivas futuras usando Inteligência Artificial
.
Aqui está o plano detalhado para o seu dashboard:
1. O que seria excelente apresentar nesse dashboard? (Visão Geral)
Um bom dashboard para este projeto deve permitir aos pesquisadores visualizar rapidamente o progresso da coleta de campo e os prognósticos clínicos automatizados
. Seria excelente incluir:
KPIs (Indicadores-Chave de Desempenho) Rápidos: Número total de pacientes avaliados, proporção de pacientes com má qualidade do sono, proporção com sonolência diurna excessiva (SED) e a incidência de depressão/ansiedade grave.
Matriz de Correlação: Gráficos que cruzem diretamente a pontuação das escalas de sono (como o PSQI) com as escalas de saúde mental (como o DASS-21 e K10) para evidenciar a relação bidirecional proposta pela pesquisa
.
Visualização de Perfis: Gráficos de barras ou pizza para visualizar os perfis demográficos e de hábitos (como uso de álcool e tabaco) dos pacientes mais afetados
.
2. Quais dados devem compor o dashboard?
Os dados a serem apresentados são as "variáveis exploratórias" mapeadas pela pesquisa
, divididas em quatro categorias principais
:
Dados Sociodemográficos: Sexo, idade, estado civil (acompanhado/não acompanhado), ocupação (ativo/aposentado), escolaridade (alfabetizado/analfabeto) e faixas de renda
.
Dados Comportamentais e Clínicos: Presença de doenças crônicas, uso de medicações para depressão/ansiedade
, níveis de consumo de álcool (avaliado pelo AUDIT-3) e frequência/tipo de consumo de tabaco
.
Dados de Saúde Mental e Suporte: Escores calculados das escalas de Depressão, Ansiedade e Estresse (DASS-21)
, Sofrimento Psicológico de Kessler (K10)
, rastreamento de transtornos não-psicóticos (SRQ-20)
 e Suporte Social Percebido (EMSSP)
.
Dados de Qualidade do Sono: Escores do Índice de Qualidade do Sono de Pittsburgh (PSQI)
 e da Escala de Sonolência de Epworth (ESE)
.
3. Quais porcentagens (prevalências) apresentar?
De acordo com os objetivos específicos da pesquisa
, o dashboard precisará evidenciar em destaque as seguintes frequências relativas (porcentagens):
Prevalência da má qualidade do sono: Qual a porcentagem exata de pacientes com TMC neste CESM que pontuam mal no PSQI
.
Prevalência de Sonolência Diurna Excessiva (SED): Qual a porcentagem de pacientes que relatam SED com base na escala de Epworth (ESE)
.
Prevalência de privação de sono: Porcentagem de pacientes reportando horas de sono inadequadas
.
Perfil da amostra: Porcentagens de distribuição demográfica e socioeconômica, como % de mulheres, % de faixas de renda e % de níveis de escolaridade
.
Comorbidades e Hábitos: Porcentagem da amostra com doenças crônicas associadas e as porcentagens de uso nocivo de álcool e tabaco
.
Resumo do Plano para o Dashboard: O ideal é que o painel possua uma tela de "Overview" com as porcentagens de prevalência (KPIs) e o funil demográfico. Em seguida, deve haver uma seção de "Métricas Clínicas" contendo os dados já processados das 6 escalas (convertidos de respostas brutas para pontuações e diagnósticos). Por fim, uma área de "Relatório/Exportação" que permita aplicar o tratamento estatístico (Regressão de Poisson, valor p) para identificar as razões de prevalência reais e cruzar o impacto do estilo de vida no sono e no Transtorno Mental Comum.
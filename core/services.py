"""
core/services.py — Lógica de negócio desacoplada das views.

Centraliza o cálculo e a persistência dos resultados de escalas clínicas,
reutilizando integralmente a infraestrutura já existente (EscalaEngine,
calculadoras nativas e construtor dinâmico).
"""

from .Scaleprocessor import EscalaEngine
from .models import RespostaPergunta, ResultadoEscala


# Mapeamento de como extrair o score principal e a classificação de cada
# tipo de estratégia. O EscalaEngine já retorna um dict; basta saber qual
# chave usar para desnormalizar no banco.
_SCORE_MAP = {
    'PSQI':  {'score': 'psqi_global',      'classif': 'psqi_status'},
    'DASS21': {'score': 'dass_depressao',  'classif': None},
    'K10':   {'score': 'k10_total',        'classif': 'k10_classificacao'},
    'SRQ20': {'score': 'srq_total',        'classif': 'srq_status'},
    'ESE':   {'score': 'ese_total',        'classif': 'ese_status'},
    'AUDIT': {'score': 'audit_total',      'classif': 'audit_status'},
    'EMSSP': {'score': 'suporte_total',    'classif': None},
    'IMC':   {'score': 'imc_valor',        'classif': 'imc_status'},
    # Escalas DYNAMIC usam chaves genéricas geradas pelo DynamicResolver
    'DYNAMIC': {'score': None,             'classif': None},
}


def _extrair_score_e_classif(resultado: dict, strategy_class: str):
    """
    Extrai o score numérico principal e a classificação textual
    de um resultado retornado pelo EscalaEngine.
    """
    mapa = _SCORE_MAP.get(strategy_class, {})
    score_key = mapa.get('score')
    classif_key = mapa.get('classif')

    # Score numérico principal
    score = None
    if score_key and score_key in resultado:
        try:
            score = float(resultado[score_key])
        except (TypeError, ValueError):
            score = None
    elif strategy_class == 'DYNAMIC':
        # Tenta chaves genéricas do DynamicResolver em ordem de preferência
        for chave in ('total', 'media'):
            if chave in resultado:
                try:
                    score = float(resultado[chave])
                    break
                except (TypeError, ValueError):
                    pass

    # Classificação textual
    classif = ''
    if classif_key and classif_key in resultado:
        classif = str(resultado[classif_key])
    elif strategy_class == 'DYNAMIC' and 'status' in resultado:
        classif = str(resultado['status'])

    return score, classif


def _montar_answers_map(resposta_questionario) -> dict:
    """
    Monta o dicionário de respostas mapeado por identificador de pergunta.
    Reutiliza a mesma lógica já usada em exportar_respostas_excel.
    """
    respostas_qs = RespostaPergunta.objects.filter(
        resposta_questionario=resposta_questionario
    ).select_related('pergunta', 'alternativa')

    answers_map = {}
    for rp in respostas_qs:
        identificador = rp.pergunta.identificador
        if identificador:
            if rp.alternativa:
                answers_map[identificador] = rp.alternativa.valor
            elif rp.resposta_texto:
                answers_map[identificador] = rp.resposta_texto

    return answers_map


def calcular_e_salvar_resultados(resposta_questionario) -> list:
    """
    Calcula todas as escalas vinculadas ao questionário da resposta
    e persiste os resultados em ResultadoEscala (cache materializado).

    Usa integralmente o EscalaEngine existente — não reimplementa
    nenhuma lógica de cálculo. Suporta:
      - Escalas nativas (PSQI, DASS21, K10, SRQ20, ESE, AUDIT, EMSSP, IMC)
      - Escalas dinâmicas (DYNAMIC) configuradas pelo pesquisador

    Retorna a lista de objetos ResultadoEscala criados/atualizados.
    """
    answers_map = _montar_answers_map(resposta_questionario)
    resultados_salvos = []

    escalas = resposta_questionario.questionario.escalas_config.filter(ativo=True)

    for escala in escalas:
        resultado = EscalaEngine.processar(answers_map, escala)

        if 'erro' in resultado:
            # Não persiste resultados com erro; continua para as demais escalas
            continue

        score, classif = _extrair_score_e_classif(resultado, escala.strategy_class)

        obj, _ = ResultadoEscala.objects.update_or_create(
            resposta_questionario=resposta_questionario,
            escala_config=escala,
            defaults={
                'resultado_json': resultado,
                'score_principal': score,
                'classificacao': classif,
            }
        )
        resultados_salvos.append(obj)

    return resultados_salvos

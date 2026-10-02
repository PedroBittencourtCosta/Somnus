import pytest
from types import SimpleNamespace

from core.Scaleprocessor import (
    SafeParser,
    DASS21Calculator,
    K10Calculator,
    SRQ20Calculator,
    ESECalculator,
    AUDITCalculator,
    EMSSPCalculator,
    PSQICalculator,
    IMCCalculator,
    DynamicResolver,
    EscalaEngine,
)


# ── SafeParser.to_float ──────────────────────────────────────────────────────

class TestSafeParserToFloat:
    def test_integer(self):
        assert SafeParser.to_float(5) == 5.0

    def test_float(self):
        assert SafeParser.to_float(3.14) == 3.14

    def test_string_comma_decimal(self):
        assert SafeParser.to_float('1,75') == 1.75

    def test_string_with_unit_kg(self):
        assert SafeParser.to_float('75kg') == 75.0

    def test_string_with_unit_m(self):
        assert SafeParser.to_float('1,80m') == 1.80

    def test_none_returns_zero(self):
        assert SafeParser.to_float(None) == 0.0

    def test_empty_string_returns_zero(self):
        assert SafeParser.to_float('') == 0.0

    def test_negative_value(self):
        assert SafeParser.to_float('-3.5') == -3.5

    def test_zero(self):
        assert SafeParser.to_float(0) == 0.0

    def test_string_integer(self):
        assert SafeParser.to_float('42') == 42.0


# ── SafeParser.to_int ────────────────────────────────────────────────────────

class TestSafeParserToInt:
    def test_integer(self):
        assert SafeParser.to_int(5) == 5

    def test_float_truncates(self):
        assert SafeParser.to_int(3.9) == 3

    def test_string_comma(self):
        assert SafeParser.to_int('2,0') == 2

    def test_none_returns_zero(self):
        assert SafeParser.to_int(None) == 0

    def test_empty_string_returns_zero(self):
        assert SafeParser.to_int('') == 0

    def test_string_with_unit(self):
        assert SafeParser.to_int('75kg') == 75


# ── SafeParser.parse_time ────────────────────────────────────────────────────

class TestSafeParserParseTime:
    def test_hh_mm_colon(self):
        assert SafeParser.parse_time('01:30') == (1, 30)

    def test_h_notation(self):
        assert SafeParser.parse_time('1h30') == (1, 30)

    def test_compact_four_digits(self):
        assert SafeParser.parse_time('0130') == (1, 30)

    def test_none_returns_none(self):
        assert SafeParser.parse_time(None) is None

    def test_empty_string_returns_none(self):
        assert SafeParser.parse_time('') is None

    def test_invalid_format_returns_none(self):
        assert SafeParser.parse_time('abc') is None

    def test_midnight(self):
        assert SafeParser.parse_time('00:00') == (0, 0)

    def test_23_59(self):
        assert SafeParser.parse_time('23:59') == (23, 59)


# ── DASS21Calculator ─────────────────────────────────────────────────────────

class TestDASS21Calculator:
    def test_all_zeros_returns_zeros(self):
        result = DASS21Calculator.calculate({})
        assert result == {'dass_depressao': 0, 'dass_ansiedade': 0, 'dass_estresse': 0}

    def test_all_ones_sums_each_subscale(self):
        all_ids = DASS21Calculator.DEPRESSAO_IDS + DASS21Calculator.ANSIEDADE_IDS + DASS21Calculator.ESTRESSE_IDS
        result = DASS21Calculator.calculate({vid: 1 for vid in all_ids})
        assert result['dass_depressao'] == 7
        assert result['dass_ansiedade'] == 7
        assert result['dass_estresse'] == 7

    def test_partial_data_missing_keys_default_zero(self):
        result = DASS21Calculator.calculate({'dassc': 3, 'dasse': 2})
        assert result['dass_depressao'] == 5
        assert result['dass_ansiedade'] == 0
        assert result['dass_estresse'] == 0

    def test_max_values(self):
        all_ids = DASS21Calculator.DEPRESSAO_IDS + DASS21Calculator.ANSIEDADE_IDS + DASS21Calculator.ESTRESSE_IDS
        result = DASS21Calculator.calculate({vid: 3 for vid in all_ids})
        assert result['dass_depressao'] == 21
        assert result['dass_ansiedade'] == 21
        assert result['dass_estresse'] == 21

    def test_subscales_are_independent(self):
        result = DASS21Calculator.calculate({vid: 2 for vid in DASS21Calculator.ESTRESSE_IDS})
        assert result['dass_depressao'] == 0
        assert result['dass_ansiedade'] == 0
        assert result['dass_estresse'] == 14


# ── K10Calculator ────────────────────────────────────────────────────────────

class TestK10Calculator:
    def test_zeros_baixo_risco(self):
        result = K10Calculator.calculate({})
        assert result['k10_total'] == 0
        assert result['k10_classificacao'] == 'Baixo risco'

    def test_boundary_19_baixo_risco(self):
        # 9 itens × 2 + 1 item × 1 = 19
        answers = {K10Calculator.K10_IDS[i]: 2 for i in range(9)}
        answers[K10Calculator.K10_IDS[9]] = 1
        result = K10Calculator.calculate(answers)
        assert result['k10_total'] == 19
        assert result['k10_classificacao'] == 'Baixo risco'

    def test_boundary_20_provavel_transtorno(self):
        # 10 itens × 2 = 20
        result = K10Calculator.calculate({vid: 2 for vid in K10Calculator.K10_IDS})
        assert result['k10_total'] == 20
        assert result['k10_classificacao'] == 'Provável transtorno'

    def test_max_score(self):
        result = K10Calculator.calculate({vid: 5 for vid in K10Calculator.K10_IDS})
        assert result['k10_total'] == 50
        assert result['k10_classificacao'] == 'Provável transtorno'

    def test_partial_keys_missing_default_zero(self):
        result = K10Calculator.calculate({'k10a': 3, 'k10b': 3})
        assert result['k10_total'] == 6
        assert result['k10_classificacao'] == 'Baixo risco'


# ── SRQ20Calculator ──────────────────────────────────────────────────────────

class TestSRQ20Calculator:
    def test_zeros_sem_indicios(self):
        result = SRQ20Calculator.calculate({})
        assert result['srq_total'] == 0
        assert result['srq_status'] == 'Sem indícios de TMC'

    def test_boundary_6_sem_indicios(self):
        result = SRQ20Calculator.calculate({vid: 1 for vid in SRQ20Calculator.SRQ_IDS[:6]})
        assert result['srq_total'] == 6
        assert result['srq_status'] == 'Sem indícios de TMC'

    def test_boundary_7_suspeita_tmc(self):
        result = SRQ20Calculator.calculate({vid: 1 for vid in SRQ20Calculator.SRQ_IDS[:7]})
        assert result['srq_total'] == 7
        assert result['srq_status'] == 'Suspeita de TMC'

    def test_all_positive(self):
        result = SRQ20Calculator.calculate({vid: 1 for vid in SRQ20Calculator.SRQ_IDS})
        assert result['srq_total'] == 20
        assert result['srq_status'] == 'Suspeita de TMC'

    def test_ignores_zero_values(self):
        result = SRQ20Calculator.calculate({vid: 0 for vid in SRQ20Calculator.SRQ_IDS})
        assert result['srq_total'] == 0


# ── ESECalculator ────────────────────────────────────────────────────────────

class TestESECalculator:
    def test_zeros_normal(self):
        result = ESECalculator.calculate({})
        assert result['ese_total'] == 0
        assert result['ese_status'] == 'Normal'

    def test_boundary_10_normal(self):
        # 7 itens × 1 + 1 item × 3 = 10
        answers = {vid: 1 for vid in ESECalculator.ESE_IDS}
        answers[ESECalculator.ESE_IDS[0]] = 3
        result = ESECalculator.calculate(answers)
        assert result['ese_total'] == 10
        assert result['ese_status'] == 'Normal'

    def test_boundary_11_sonolencia(self):
        # 7 itens × 1 + 1 item × 4 = 11
        answers = {vid: 1 for vid in ESECalculator.ESE_IDS}
        answers[ESECalculator.ESE_IDS[0]] = 4
        result = ESECalculator.calculate(answers)
        assert result['ese_total'] == 11
        assert result['ese_status'] == 'Sonolência Diurna Excessiva'

    def test_max_score(self):
        result = ESECalculator.calculate({vid: 3 for vid in ESECalculator.ESE_IDS})
        assert result['ese_total'] == 24
        assert result['ese_status'] == 'Sonolência Diurna Excessiva'


# ── AUDITCalculator ──────────────────────────────────────────────────────────

class TestAUDITCalculator:
    def _single_item_score(self, total):
        answers = {vid: 0 for vid in AUDITCalculator.AUDIT_IDS}
        answers[AUDITCalculator.AUDIT_IDS[0]] = total
        return answers

    def test_zeros_baixo_risco(self):
        result = AUDITCalculator.calculate({})
        assert result['audit_total'] == 0
        assert result['audit_status'] == 'Baixo Risco'

    def test_boundary_7_baixo_risco(self):
        result = AUDITCalculator.calculate(self._single_item_score(7))
        assert result['audit_total'] == 7
        assert result['audit_status'] == 'Baixo Risco'

    def test_boundary_8_uso_risco(self):
        result = AUDITCalculator.calculate(self._single_item_score(8))
        assert result['audit_total'] == 8
        assert result['audit_status'] == 'Uso de Risco'

    def test_boundary_15_uso_risco(self):
        result = AUDITCalculator.calculate(self._single_item_score(15))
        assert result['audit_total'] == 15
        assert result['audit_status'] == 'Uso de Risco'

    def test_boundary_16_uso_nocivo(self):
        result = AUDITCalculator.calculate(self._single_item_score(16))
        assert result['audit_total'] == 16
        assert result['audit_status'] == 'Uso Nocivo'

    def test_boundary_19_uso_nocivo(self):
        result = AUDITCalculator.calculate(self._single_item_score(19))
        assert result['audit_total'] == 19
        assert result['audit_status'] == 'Uso Nocivo'

    def test_boundary_20_provavel_dependencia(self):
        # 10 itens × 2 = 20
        result = AUDITCalculator.calculate({vid: 2 for vid in AUDITCalculator.AUDIT_IDS})
        assert result['audit_total'] == 20
        assert result['audit_status'] == 'Provável Dependência'

    def test_max_score_40(self):
        result = AUDITCalculator.calculate({vid: 4 for vid in AUDITCalculator.AUDIT_IDS})
        assert result['audit_total'] == 40
        assert result['audit_status'] == 'Provável Dependência'


# ── EMSSPCalculator ──────────────────────────────────────────────────────────

class TestEMSSPCalculator:
    def test_zeros(self):
        result = EMSSPCalculator.calculate({})
        assert result == {
            'suporte_familia': 0,
            'suporte_amigos': 0,
            'suporte_outros': 0,
            'suporte_total': 0,
        }

    def test_familia_only(self):
        result = EMSSPCalculator.calculate({vid: 7 for vid in EMSSPCalculator.FAMILIA_IDS})
        assert result['suporte_familia'] == 28
        assert result['suporte_amigos'] == 0
        assert result['suporte_outros'] == 0
        assert result['suporte_total'] == 28

    def test_amigos_only(self):
        result = EMSSPCalculator.calculate({vid: 5 for vid in EMSSPCalculator.AMIGOS_IDS})
        assert result['suporte_amigos'] == 20
        assert result['suporte_familia'] == 0
        assert result['suporte_total'] == 20

    def test_max_all_categories(self):
        all_ids = EMSSPCalculator.FAMILIA_IDS + EMSSPCalculator.AMIGOS_IDS + EMSSPCalculator.OUTROS_IDS
        result = EMSSPCalculator.calculate({vid: 7 for vid in all_ids})
        assert result['suporte_familia'] == 28
        assert result['suporte_amigos'] == 28
        assert result['suporte_outros'] == 28
        assert result['suporte_total'] == 84

    def test_total_equals_sum_of_categories(self):
        answers = {
            **{vid: 3 for vid in EMSSPCalculator.FAMILIA_IDS},
            **{vid: 5 for vid in EMSSPCalculator.AMIGOS_IDS},
            **{vid: 7 for vid in EMSSPCalculator.OUTROS_IDS},
        }
        result = EMSSPCalculator.calculate(answers)
        assert result['suporte_total'] == (
            result['suporte_familia'] + result['suporte_amigos'] + result['suporte_outros']
        )


# ── PSQICalculator ───────────────────────────────────────────────────────────

class TestPSQICalculator:
    def _good_quality_answers(self):
        return {
            'qualsono': 0,              # c1 = 0 (muito boa)
            'dormin': 10,               # latência < 15 min → ponto_item2 = 0
            'ndorm': 0,                 # c2 = 0
            'sonoh': 8,                 # c3: > 7h → 0
            'deith, deitm': '23:00',    # deitar 23h
            'levanh, levanm': '07:00',  # levantar 7h → 8h na cama
            'acordm': 0, 'levaban': 0, 'nrespir': 0, 'roncof': 0,
            'frio': 0, 'calor': 0, 'sonhor': 0, 'dor': 0, 'frpson': 0,
            'frmson': 0,                # c6 = 0
            'difacor': 0, 'probativ': 0,
        }

    def test_good_quality_score_lte_5(self):
        result = PSQICalculator.calculate(self._good_quality_answers())
        assert result['psqi_global'] <= 5
        assert result['psqi_status'] == 'Qualidade Boa'

    def test_bad_quality_score_gt_5(self):
        answers = {
            'qualsono': 3,              # c1 = 3
            'dormin': 90,               # > 60 min → ponto_item2 = 3
            'ndorm': 3,                 # soma_c2 = 6 → c2 = 3
            'sonoh': 4,                 # c3 = 3 (< 5h)
            'deith, deitm': '01:00',
            'levanh, levanm': '06:00',  # 5h na cama; efic. = 4/5 = 80% → c4 = 1
            'acordm': 3, 'levaban': 3, 'nrespir': 3, 'roncof': 3,
            'frio': 3, 'calor': 3, 'sonhor': 3,  # soma_c5 = 21 → c5 = 3
            'dor': 0, 'frpson': 0,
            'frmson': 3,                # c6 = 3
            'difacor': 3, 'probativ': 3,  # soma_c7 = 6 → c7 = 3
        }
        result = PSQICalculator.calculate(answers)
        assert result['psqi_global'] > 5
        assert result['psqi_status'] == 'Qualidade Ruim'

    def test_result_has_seven_components(self):
        result = PSQICalculator.calculate(self._good_quality_answers())
        assert 'psqi_componentes' in result
        assert len(result['psqi_componentes']) == 7

    def test_zero_sonoh_gives_worst_c3(self):
        # sonoh=0 → c3=3 (pior caso: nenhuma hora de sono reportada)
        # Total mínimo esperado com dict vazio: c3=3, restante=0 → global=3
        result = PSQICalculator.calculate({})
        # global=3 ainda está ≤ 5 → "Qualidade Boa" pelo limiar do PSQI
        assert result['psqi_global'] == 3
        assert result['psqi_status'] == 'Qualidade Boa'

    def test_missing_time_data_skips_efficiency(self):
        # Sem horários de dormir/levantar → horas_na_cama = 0 → c4 = 0 (seguro)
        result = PSQICalculator.calculate({'sonoh': 6})
        assert result['psqi_componentes'][3] == 0


# ── IMCCalculator ────────────────────────────────────────────────────────────

class TestIMCCalculator:
    def test_underweight(self):
        # IMC = 50 / 1.75² ≈ 16.3
        result = IMCCalculator.calculate({'peso': '50', 'altura': '1,75'})
        assert result['imc_status'] == 'Abaixo do peso'
        assert result['imc_valor'] < 18.5

    def test_normal_weight(self):
        # IMC = 70 / 1.75² ≈ 22.9
        result = IMCCalculator.calculate({'peso': '70', 'altura': '1,75'})
        assert result['imc_status'] == 'Peso normal'

    def test_overweight(self):
        # IMC = 85 / 1.70² ≈ 29.4
        result = IMCCalculator.calculate({'peso': '85', 'altura': '1,70'})
        assert result['imc_status'] == 'Sobrepeso'

    def test_obesity(self):
        # IMC = 100 / 1.60² ≈ 39.1
        result = IMCCalculator.calculate({'peso': '100', 'altura': '1,60'})
        assert result['imc_status'] == 'Obesidade'

    def test_zero_height_returns_incomplete(self):
        result = IMCCalculator.calculate({'peso': '70', 'altura': '0'})
        assert result['imc_status'] == 'Dados incompletos'
        assert result['imc_valor'] == 0

    def test_missing_height_returns_incomplete(self):
        result = IMCCalculator.calculate({'peso': '70'})
        assert result['imc_status'] == 'Dados incompletos'

    def test_comma_and_dot_produce_same_result(self):
        r_comma = IMCCalculator.calculate({'peso': '70,0', 'altura': '1,75'})
        r_dot   = IMCCalculator.calculate({'peso': '70.0', 'altura': '1.75'})
        assert r_comma['imc_valor'] == r_dot['imc_valor']


# ── DynamicResolver ──────────────────────────────────────────────────────────

class TestDynamicResolver:
    def test_sum_operation(self):
        config = {'operacao': 'SUM', 'variaveis': ['q1', 'q2', 'q3'], 'limiares': []}
        result = DynamicResolver.resolve({'q1': 2, 'q2': 3, 'q3': 5}, config)
        assert result['total'] == 10.0

    def test_sum_threshold_baixo(self):
        config = {
            'operacao': 'SUM',
            'variaveis': ['q1', 'q2'],
            'limiares': [
                {'max': 5, 'status': 'Baixo'},
                {'max': 10, 'status': 'Alto'},
            ],
        }
        result = DynamicResolver.resolve({'q1': 2, 'q2': 2}, config)
        assert result['status'] == 'Baixo'

    def test_sum_threshold_alto(self):
        config = {
            'operacao': 'SUM',
            'variaveis': ['q1', 'q2'],
            'limiares': [
                {'max': 5, 'status': 'Baixo'},
                {'max': 10, 'status': 'Alto'},
            ],
        }
        result = DynamicResolver.resolve({'q1': 5, 'q2': 2}, config)
        assert result['status'] == 'Alto'

    def test_sum_by_subscale(self):
        config = {
            'operacao': 'SUM_BY_SUBSCALE',
            'subescalas': {'fisica': ['q1', 'q2'], 'mental': ['q3', 'q4']},
            'limiares': {},
        }
        result = DynamicResolver.resolve({'q1': 3, 'q2': 4, 'q3': 1, 'q4': 2}, config)
        assert result['fisica_total'] == 7
        assert result['mental_total'] == 3

    def test_average_operation(self):
        config = {'operacao': 'AVERAGE', 'variaveis': ['q1', 'q2', 'q3'], 'limiares': []}
        result = DynamicResolver.resolve({'q1': 1, 'q2': 2, 'q3': 3}, config)
        assert result['media'] == 2.0

    def test_unknown_operation_returns_error(self):
        config = {'operacao': 'MULTIPLICAR', 'variaveis': ['q1']}
        result = DynamicResolver.resolve({'q1': 5}, config)
        assert 'erro' in result

    def test_missing_variable_defaults_to_zero(self):
        config = {'operacao': 'SUM', 'variaveis': ['q1', 'q2', 'q99'], 'limiares': []}
        result = DynamicResolver.resolve({'q1': 5}, config)
        assert result['total'] == 5.0


# ── EscalaEngine ─────────────────────────────────────────────────────────────

class TestEscalaEngine:
    def _cfg(self, strategy, config_dinamica=None):
        return SimpleNamespace(strategy_class=strategy, config_dinamica=config_dinamica)

    def test_routes_k10(self):
        result = EscalaEngine.processar({vid: 2 for vid in K10Calculator.K10_IDS}, self._cfg('K10'))
        assert 'k10_total' in result

    def test_routes_dass21(self):
        result = EscalaEngine.processar({}, self._cfg('DASS21'))
        assert 'dass_depressao' in result

    def test_routes_srq20(self):
        result = EscalaEngine.processar({}, self._cfg('SRQ20'))
        assert 'srq_total' in result

    def test_routes_ese(self):
        result = EscalaEngine.processar({}, self._cfg('ESE'))
        assert 'ese_total' in result

    def test_routes_audit(self):
        result = EscalaEngine.processar({}, self._cfg('AUDIT'))
        assert 'audit_total' in result

    def test_routes_emssp(self):
        result = EscalaEngine.processar({}, self._cfg('EMSSP'))
        assert 'suporte_total' in result

    def test_routes_imc(self):
        result = EscalaEngine.processar({'peso': '70', 'altura': '1,75'}, self._cfg('IMC'))
        assert 'imc_valor' in result

    def test_routes_psqi(self):
        result = EscalaEngine.processar({}, self._cfg('PSQI'))
        assert 'psqi_global' in result

    def test_unknown_strategy_returns_error(self):
        result = EscalaEngine.processar({}, self._cfg('INEXISTENTE'))
        assert 'erro' in result

    def test_dynamic_with_valid_config(self):
        config_din = {'operacao': 'SUM', 'variaveis': ['q1'], 'limiares': []}
        result = EscalaEngine.processar({'q1': 5}, self._cfg('DYNAMIC', config_din))
        assert result['total'] == 5.0

    def test_dynamic_without_config_returns_error(self):
        result = EscalaEngine.processar({}, self._cfg('DYNAMIC', None))
        assert 'erro' in result

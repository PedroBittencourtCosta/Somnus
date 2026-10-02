from core.templatetags.custom_filters import get_item, get_item_key, get_val


class TestGetItem:
    """get_item coerce a chave para str antes de buscar no dicionário."""

    def test_chave_existente_str(self):
        assert get_item({'a': 1}, 'a') == 1

    def test_chave_existente_int_coercionada(self):
        assert get_item({'42': 'resposta'}, 42) == 'resposta'

    def test_chave_ausente_retorna_none(self):
        assert get_item({'a': 1}, 'z') is None

    def test_dicionario_vazio(self):
        assert get_item({}, 'x') is None

    def test_valor_falsy(self):
        assert get_item({'k': 0}, 'k') == 0

    def test_valor_none(self):
        assert get_item({'k': None}, 'k') is None


class TestGetItemKey:
    """get_item_key retorna {} quando a chave não existe (nunca None)."""

    def test_chave_existente(self):
        assert get_item_key({'a': {'x': 1}}, 'a') == {'x': 1}

    def test_chave_ausente_retorna_dict_vazio(self):
        assert get_item_key({}, 'nao_existe') == {}

    def test_chave_int_coercionada(self):
        assert get_item_key({'1': {'ok': True}}, 1) == {'ok': True}


class TestGetVal:
    """get_val NÃO coerce a chave — usa exatamente o tipo passado."""

    def test_chave_str_existente(self):
        assert get_val({'k': 99}, 'k') == 99

    def test_chave_int_nao_coercionada(self):
        # Chave inteira não bate com chave string — retorna None
        assert get_val({'1': 'um'}, 1) is None

    def test_chave_ausente(self):
        assert get_val({'a': 1}, 'b') is None

    def test_dicionario_vazio(self):
        assert get_val({}, 'qualquer') is None

class Scaleprocessor:
    """Processador de escalas para o projeto Somnus."""

    @staticmethod
    def process_dass21(answers):
        """
        Processa DASS-21 agrupando em subescalas.
        answers: dict {item_id: score} (1 a 21)
        """
        depressao = [3, 5, 10, 13, 16, 17, 21]
        ansiedade = [2, 4, 7, 9, 15, 19, 20]
        estresse = [1, 6, 8, 11, 12, 14, 18]
        
        scores = {
            "depressao": sum(answers.get(i, 0) for i in depressao),
            "ansiedade": sum(answers.get(i, 0) for i in ansiedade),
            "estresse": sum(answers.get(i, 0) for i in estresse)
        }
        return scores

    @staticmethod
    def process_emssp(answers):
        """
        Processa EMSSP por fonte de suporte.
        answers: dict {item_id: score} (1 a 12)
        """
        familia = [3, 4, 8, 11]
        amigos = [6, 7, 9, 12]
        outros = [1, 2, 5, 10]
        
        return {
            "familia": sum(answers.get(i, 0) for i in familia),
            "amigos": sum(answers.get(i, 0) for i in amigos),
            "outros": sum(answers.get(i, 0) for i in outros),
            "total": sum(answers.values())
        }

    @staticmethod
    def process_psqi(answers):
        """
        Processa PSQI simplificado (7 componentes).
        answers: dict com as respostas mapeadas conforme o manual.
        """
        # Exemplo de lógica para Componente 6: Uso de medicação (item 7)
        c6 = answers.get('item_7', 0)
        
        # O resultado global é a soma dos 7 componentes (C1 a C7)
        # Cada componente deve ser normalizado para 0-3
        componentes = [
            answers.get('c1', 0), answers.get('c2', 0), answers.get('c3', 0),
            answers.get('c4', 0), answers.get('c5', 0), c6, answers.get('c7', 0)
        ]
        return {"global_score": sum(componentes)}

    @staticmethod
    def process_srq20(answers):
        """SRQ-20: Soma simples de respostas 'Sim' (1)."""
        return sum(1 for v in answers.values() if v == 1 or v is True)

    @staticmethod
    def process_ese(answers):
        """Escala de Epworth: Soma simples (0-24)."""
        return sum(answers.values())


class DASS21Calculator:
    
    # [cite_start]Mapeamento conforme itens do protocolo [cite: 258, 259, 260] e planilha
    DEPRESSAO_IDS = ['dassc', 'dasse', 'dassj', 'dassm', 'dassp', 'dassq', 'dassu'] # Itens 3,5,10,13,16,17,21
    ANSIEDADE_IDS = ['dassb', 'dassd', 'dassg', 'dassi', 'dasso', 'dasss', 'dasst'] # Itens 2,4,7,9,15,19,20
    ESTRESSE_IDS  = ['dassa', 'dassf', 'dassh', 'dassk', 'dassl', 'dassn', 'dassr'] # Itens 1,6,8,11,12,14,18

    @staticmethod
    def calculate(answers_map):
        """
        Calcula os scores brutos. 
        answers_map: dict {'identificador': valor}
        """
        return {
            "dass_depressao": sum(answers_map.get(vid, 0) for vid in DASS21Calculator.DEPRESSAO_IDS),
            "dass_ansiedade": sum(answers_map.get(vid, 0) for vid in DASS21Calculator.ANSIEDADE_IDS),
            "dass_estresse":  sum(answers_map.get(vid, 0) for vid in DASS21Calculator.ESTRESSE_IDS)
        }
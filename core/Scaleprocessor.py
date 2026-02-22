class Scaleprocessor:

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
    
class K10Calculator:
    """Calcula o score da Escala de Kessler (K10)[cite: 1503]."""
    
    # Identificadores técnicos encontrados no seu CSV
    K10_IDS = [
        'k10a', 'k10b', 'k10c', 'k10d', 'k10e', 
        'k10f', 'k10g', 'k10h', 'k10i', 'k10j'
    ]

    @staticmethod
    def calculate(answers_map):
        """
        Soma os 10 itens. Score máximo: 50[cite: 1505].
        answers_map: dict {'identificador': valor}
        """
        total = sum(answers_map.get(vid, 0) for vid in K10Calculator.K10_IDS)
        
        # Classificação clínica sugerida para o TFC
        nivel = "Provável transtorno" if total >= 20 else "Baixo risco"
        
        return {
            "k10_total": total,
            "k10_classificacao": nivel
        }
    

class SRQ20Calculator:
    """Calcula o score da Escala SRQ-20."""
    
    # Identificadores mapeados do seu CSV (rsqa até rsqt)
    SRQ_IDS = [
        'rsqa', 'rsqb', 'rsqc', 'rsqd', 'rsqe', 'rsqf', 'rsqg', 'rsqh', 'rsqi', 'rsqj',
        'rsqk', 'rsql', 'rsqm', 'rsqn', 'rsqo', 'rsqp', 'rsqq', 'rsqr', 'rsqs', 'rsqt'
    ]

    @staticmethod
    def calculate(answers_map):
        """
        Soma as respostas afirmativas (1 ponto para 'Sim')[cite: 266].
        """
        total = sum(1 for vid in SRQ20Calculator.SRQ_IDS if answers_map.get(vid) == 1)
        
        # O ponto de corte comum na literatura para TMC é 7 ou 8 [cite: 61, 266]
        status = "Suspeita de TMC" if total >= 7 else "Sem indícios de TMC"
        
        return {
            "srq_total": total,
            "srq_status": status
        }
    
class ESECalculator:
    """Calcula a Sonolência Diurna Excessiva (ESE) - Itens sonolea a sonoleh."""
    
    ESE_IDS = [
        'sonolea', 'sonoleb', 'sonolec', 'sonoled', 
        'sonolee', 'sonolef', 'sonoleg', 'sonoleh'
    ]

    @staticmethod
    def calculate(answers_map):
        """Soma os 8 itens. Score de 0 a 24."""
        total = sum(answers_map.get(vid, 0) for vid in ESECalculator.ESE_IDS)
        
        # Conforme o referencial teórico: > 10 indica sonolência excessiva 
        status = "Sonolência Diurna Excessiva" if total > 10 else "Normal"
        
        return {
            "ese_total": total,
            "ese_status": status
        }

class AUDITCalculator:
    """Calcula o Risco de Consumo de Álcool (AUDIT) - Itens audit1 a audit10."""
    
    AUDIT_IDS = [f'audit{i}' for i in range(1, 11)]

    @staticmethod
    def calculate(answers_map):
        """Soma os 10 itens. Score de 0 a 40."""
        total = sum(answers_map.get(vid, 0) for vid in AUDITCalculator.AUDIT_IDS)
        
        # Classificação padrão da OMS
        if total <= 7:
            status = "Baixo Risco"
        elif total <= 15:
            status = "Uso de Risco"
        elif total <= 19:
            status = "Uso Nocivo"
        else:
            status = "Provável Dependência"
            
        return {
            "audit_total": total,
            "audit_status": status
        }
    
class EMSSPCalculator:
    """
    Calcula o suporte social percebido por categoria.
    Baseado nos itens 1 a 12 da escala[cite: 269, 270].
    """
    
    # Mapeamento dos Identificadores Técnicos do seu banco
    FAMILIA_IDS = ['emsspec', 'emssped', 'emsspeh', 'emsspel'] # Itens 3, 4, 8, 11
    AMIGOS_IDS  = ['emsspef', 'emsspeg', 'emsspei', 'emsspm'] # Itens 6, 7, 9, 12
    OUTROS_IDS  = ['emsspea', 'emsspeb', 'emsspee', 'emsspej'] # Itens 1, 2, 5, 10

    @staticmethod
    def calculate(answers_map):
        """
        Retorna as somas por categoria. Score total máx: 84.
        As respostas variam de 1 a 7[cite: 270].
        """
        fam = sum(answers_map.get(vid, 0) for vid in EMSSPCalculator.FAMILIA_IDS)
        ami = sum(answers_map.get(vid, 0) for vid in EMSSPCalculator.AMIGOS_IDS)
        out = sum(answers_map.get(vid, 0) for vid in EMSSPCalculator.OUTROS_IDS)
        
        return {
            "suporte_familia": fam,
            "suporte_amigos": ami,
            "suporte_outros": out,
            "suporte_total": fam + ami + out
        }
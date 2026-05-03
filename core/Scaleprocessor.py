from datetime import datetime, timedelta
import re


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
    
class PSQICalculator:
    @staticmethod
    def calculate(answers_map):
        # C1: Qualidade (Valor da alternativa ou texto convertido)
        c1 = SafeParser.to_int(answers_map.get('qualsono', 0))

        # C2: Latência (AQUI DAVA O ERRO: convertemos '75' para 75)
        dormin = SafeParser.to_int(answers_map.get('dormin', 0))
        ponto_item2 = 0
        if dormin > 60: ponto_item2 = 3
        elif dormin > 30: ponto_item2 = 2
        elif dormin > 15: ponto_item2 = 1
        
        soma_c2 = ponto_item2 + SafeParser.to_int(answers_map.get('ndorm', 0))
        c2 = 3 if soma_c2 >= 5 else 2 if soma_c2 >= 3 else 1 if soma_c2 >= 1 else 0

        # C3: Duração
        sonoh = SafeParser.to_float(answers_map.get('sonoh', 0))
        c3 = 0 if sonoh > 7 else 1 if sonoh >= 6 else 2 if sonoh >= 5 else 3

        # C4: Eficiência (Usa o novo parse de tempo)
        horas_na_cama = PSQICalculator._get_hours_in_bed(answers_map)
        if horas_na_cama > 0:
            eficiencia = (sonoh / horas_na_cama) * 100
            c4 = 0 if eficiencia >= 85 else 1 if eficiencia >= 75 else 2 if eficiencia >= 65 else 3
        else:
            c4 = 0

        # C5: Distúrbios (Soma segura de todos os itens)
        dist_ids = ['acordm', 'levaban', 'nrespir', 'roncof', 'frio', 'calor', 'sonhor', 'dor', 'frpson']
        soma_c5 = sum(SafeParser.to_int(answers_map.get(vid, 0)) for vid in dist_ids)
        c5 = 3 if soma_c5 >= 19 else 2 if soma_c5 >= 10 else 1 if soma_c5 >= 1 else 0

        # C6 e C7
        c6 = SafeParser.to_int(answers_map.get('frmson', 0))
        soma_c7 = SafeParser.to_int(answers_map.get('difacor', 0)) + SafeParser.to_int(answers_map.get('probativ', 0))
        c7 = 3 if soma_c7 >= 5 else 2 if soma_c7 >= 3 else 1 if soma_c7 >= 1 else 0

        total = c1 + c2 + c3 + c4 + c5 + c6 + c7
        return {
            "psqi_global": total,
            "psqi_status": "Qualidade Ruim" if total > 5 else "Qualidade Boa",
            "psqi_componentes": [c1, c2, c3, c4, c5, c6, c7]
        }

    @staticmethod
    def _get_hours_in_bed(answers_map):
        # Trata o identificador combinado que vimos no seu log: 'deith, deitm'
        t_deitar = SafeParser.parse_time(answers_map.get('deith, deitm', ''))
        t_levan = SafeParser.parse_time(answers_map.get('levanh, levanm', ''))
        
        if t_deitar and t_levan:
            d = datetime(2026, 1, 1, t_deitar[0], t_deitar[1])
            l = datetime(2026, 1, 1, t_levan[0], t_levan[1])
            if l <= d: l += timedelta(days=1)
            return (l - d).total_seconds() / 3600
        return 0

class IMCCalculator:
    """Calcula o IMC tratando entradas de texto (Peso e Altura)."""

    @staticmethod
    def parse_value(value):
        """Converte string '1,75' ou '80.5' para float."""
        if not value: return 0.0
        try:
            # Substitui vírgula por ponto e tenta converter
            return float(str(value).replace(',', '.'))
        except ValueError:
            return 0.0

    @staticmethod
    def calculate(answers_map):
        # Buscamos o texto bruto nos identificadores técnicos
        peso = IMCCalculator.parse_value(answers_map.get('peso'))
        altura = IMCCalculator.parse_value(answers_map.get('altura'))

        if altura > 0:
            imc = round(peso / (altura ** 2), 2)
            if imc < 18.5: status = "Abaixo do peso"
            elif imc < 25: status = "Peso normal"
            elif imc < 30: status = "Sobrepeso"
            else: status = "Obesidade"
            return {"imc_valor": imc, "imc_status": status, "peso": peso, "altura": altura}
        
        return {"imc_valor": 0, "imc_status": "Dados incompletos", "peso": peso, "altura": altura}
    

class SafeParser:
    """Helper para converter textos sujos do usuário em números e tempos."""
    
    @staticmethod
    def to_float(value):
        if value is None: return 0.0
        if isinstance(value, (int, float)): return float(value)
        # Remove tudo que não é número, ponto ou vírgula (ex: remove "kg", "m")
        sanitized = re.sub(r'[^\d.,-]', '', str(value))
        if not sanitized: return 0.0
        try:
            return float(sanitized.replace(',', '.'))
        except ValueError:
            return 0.0

    @staticmethod
    def to_int(value):
        return int(SafeParser.to_float(value))

    @staticmethod
    def parse_time(time_str):
        """Extrai hora e minuto de formatos como '01:30', '1h30' ou '0130'."""
        if not time_str or not isinstance(time_str, str): return None
        match = re.search(r'(\d{1,2})[h:]?(\d{2})', time_str.lower())
        if match:
            return int(match.group(1)), int(match.group(2))
        return None

class EscalaEngine:
    """
    Ponto de entrada central para cálculo de resultados de questionários.
    Roteia para as classes especializadas ou para o interpretador dinâmico.
    """
    @staticmethod
    def processar(answers_map: dict, config) -> dict:
        # 1. Padrão Strategy: Roteia para cálculos complexos via código nativo
        if config.strategy_class != "DYNAMIC":
            strategy_factory = {
                "PSQI": PSQICalculator,
                "IMC": IMCCalculator
                # Novas escalas complexas entram aqui
            }
            strategy = strategy_factory.get(config.strategy_class)
            if not strategy:
                return {"erro": f"Strategy '{config.strategy_class}' não mapeada no backend."}
            return strategy.calculate(answers_map)
        
        # 2. Padrão Interpreter: Processa metadados gerados pelo Pesquisador
        if not config.config_dinamica:
            return {"erro": "Configuração da escala está vazia. Salve as regras no Construtor Visual."}
            
        return DynamicResolver.resolve(answers_map, config.config_dinamica)

class DynamicResolver:
    """
    Lê o JSON estruturado do banco de dados e executa matemática simples 
    sem necessidade de criar novas classes Python.
    """
    @staticmethod
    def resolve(answers_map: dict, json_config: dict) -> dict:
        resultados = {}
        op = json_config.get("operacao")
        
        try:
            if op == "SUM":
                vars_keys = json_config.get("variaveis", [])
                total = sum(SafeParser.to_float(answers_map.get(v, 0)) for v in vars_keys)
                resultados["total"] = total
                resultados["status"] = DynamicResolver._aplicar_limiares(total, json_config.get("limiares", []))
                
            elif op == "SUM_BY_SUBSCALE":
                subescalas = json_config.get("subescalas", {})
                for sub_nome, vars_keys in subescalas.items():
                    total = sum(SafeParser.to_float(answers_map.get(v, 0)) for v in vars_keys)
                    resultados[f"{sub_nome}_total"] = total
                    
                    limiares_sub = json_config.get("limiares", {}).get(sub_nome, [])
                    if limiares_sub:
                        resultados[f"{sub_nome}_status"] = DynamicResolver._aplicar_limiares(total, limiares_sub)
                        
            elif op == "AVERAGE":
                vars_keys = json_config.get("variaveis", [])
                if vars_keys:
                    total = sum(SafeParser.to_float(answers_map.get(v, 0)) for v in vars_keys)
                    media = total / len(vars_keys)
                    resultados["media"] = round(media, 2)
                    resultados["status"] = DynamicResolver._aplicar_limiares(media, json_config.get("limiares", []))
            else:
                resultados["erro"] = f"Operação '{op}' não suportada pelo construtor dinâmico."
        except Exception as e:
            resultados["erro"] = f"Falha no processamento dinâmico: {str(e)}"
                
        return resultados

    @staticmethod
    def _aplicar_limiares(valor: float, limiares: list) -> str:
        if not limiares:
            return "Sem classificação"
            
        # Ordena ascendente pelo valor máximo da regra (max)
        for regra in sorted(limiares, key=lambda x: x.get("max", float('inf'))):
            if valor <= regra.get("max", float('inf')):
                return regra.get("status", "Indefinido")
                
        return "Indefinido"
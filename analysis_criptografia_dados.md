# Análise: Proteção de Dados Sensíveis no Somnus

## Contexto

O Somnus armazena dados clínicos de pacientes (respostas a questionários de saúde mental: DASS-21, PSQI, SRQ-20, K10, etc.). O avaliador sugeriu criptografar as respostas no banco. Abaixo, uma análise das opções reais e seus impactos.

---

## 1. Mapeamento dos Dados Sensíveis (PII)

Antes de criptografar, é preciso identificar **o que precisa de proteção**. Nem todo dado no banco é sensível.

| Modelo | Campo | Tipo de Dado | Sensível? |
|---|---|---|---|
| `RespostaQuestionario` | `paciente_nome` | Nome completo do paciente | ✅ **PII direto** |
| `RespostaPergunta` | `resposta_texto` | Texto livre (idade, peso, relatos) | ✅ **PII indireto** |
| `RespostaPergunta` | `alternativa` (FK → valor int) | Score numérico de escalas | ⚠️ Depende do contexto |
| `Usuario` (accounts) | `username`, `email` | Dados da pesquisadora | ⚠️ Moderado |
| `Questionario`, `Pergunta`, etc. | Estrutura do instrumento | Dados públicos | ❌ Não sensível |

> [!IMPORTANT]
> Os campos realmente críticos são apenas **2**: `paciente_nome` e `resposta_texto`. Esses são os que vinculam uma pessoa identificável a dados de saúde mental.

---

## 2. As 3 Opções Viáveis

### Opção A: Criptografia a Nível de Campo (Application-Level Encryption)

**Como funciona:** Substitui os `CharField`/`TextField` por campos criptografados no model Django. Os dados são criptografados antes de ir ao banco e descriptografados ao serem lidos pela aplicação.

**Bibliotecas principais:**
- [`django-fernet-fields`](https://github.com/orcasgit/django-fernet-fields) — usa Fernet (AES-128-CBC + HMAC)
- [`django-encrypted-model-fields`](https://gitlab.com/lansharkconsulting/django-encrypted-model-fields) — mais mantida, usa AES-256

**Exemplo de como ficaria no model:**

```python
# models.py
from encrypted_model_fields.fields import EncryptedCharField, EncryptedTextField

class RespostaQuestionario(models.Model):
    pesquisadora = models.ForeignKey(...)
    questionario = models.ForeignKey(...)
    data_submissao = models.DateTimeField(auto_now_add=True)
    paciente_nome = EncryptedCharField(max_length=255, null=True)  # 🔒

class RespostaPergunta(models.Model):
    resposta_questionario = models.ForeignKey(...)
    pergunta = models.ForeignKey(...)
    alternativa = models.ForeignKey(...)  # FK continua normal (é só um int)
    resposta_texto = EncryptedTextField(null=True, blank=True)  # 🔒
```

#### Impacto no restante do código

| Camada | Impacto | Detalhes |
|---|---|---|
| **Views (leitura/escrita)** | ✅ Nenhum | A descriptografia é transparente. `res_quest.paciente_nome` continua retornando texto limpo. |
| **Scale Processors** | ✅ Nenhum | `answers_map` é montado na view a partir de dados já descriptografados. |
| **Export Excel** | ✅ Nenhum | A view já lê via ORM, que descriptografa automaticamente. |
| **Django Admin** | ✅ Nenhum | O admin lê via ORM normalmente. |
| **Filtros/Buscas (ORM)** | ❌ **QUEBRA** | `RespostaQuestionario.objects.filter(paciente_nome__icontains="João")` **não funciona mais**. Dados criptografados não são pesquisáveis. |
| **Ordering** | ❌ **QUEBRA** | `order_by('paciente_nome')` retorna ordem aleatória (cifrotexto). |

> [!WARNING]
> **Impacto real no seu código:**  
> Há uma busca implícita em `dashboard_respostas.html` via `search_fields = ('paciente_nome',)` no admin. Essa busca deixaria de funcionar. Você precisaria de uma estratégia alternativa (ex: hash determinístico para busca exata, ou buscar no app e filtrar em Python).

#### Prós e Contras

| ✅ Prós | ❌ Contras |
|---|---|
| Dados protegidos mesmo com dump do banco vazado | Impossibilita `filter()`, `search`, `order_by` nos campos criptografados |
| Chave fica na aplicação, fora do banco | Overhead de performance: encrypt/decrypt a cada leitura |
| Fácil de apresentar na banca ("campo X é criptografado com AES-256") | Requer migration para converter dados existentes |
| Compliant com LGPD art. 46 | Gestão de chave: se perder a `FIELD_ENCRYPTION_KEY`, **perde tudo** |

---

### Opção B: Transparent Data Encryption (TDE) — Nível de Banco

**Como funciona:** O PostgreSQL criptografa os dados **no disco** (at-rest). A aplicação não sabe que existe criptografia — tudo é transparente.

**Implementação:** Configuração do PostgreSQL com `pgcrypto` ou criptografia de volume no servidor (ex: LUKS no Linux, BitLocker no Windows, ou a opção nativa do Railway/Render).

#### Impacto no código

| Camada | Impacto |
|---|---|
| **Tudo** | ✅ **Zero mudanças no código** |

#### Prós e Contras

| ✅ Prós | ❌ Contras |
|---|---|
| Zero mudanças no código | ❌ **Não protege contra SQL injection** — quem acessa o banco vê tudo em texto limpo |
| Zero impacto em queries | Não protege contra dump de banco (o atacante vê plaintext se tiver acesso ao DBMS) |
| Performace nativa | Fraco para apresentar na banca: é "só config de infra" |

> [!CAUTION]
> TDE **não protege o cenário que o avaliador mencionou** ("vazarem os dados"). Se alguém faz `pg_dump` ou SQL injection, os dados saem em texto limpo. TDE só protege contra roubo físico do disco.

---

### Opção C: Pseudoanonimização + Criptografia Seletiva (🏆 Recomendada)

**A melhor solução para o seu caso** é uma combinação:

1. **Pseudoanonimizar** o `paciente_nome` → Gerar um código aleatório (ex: `PAC-A3F9B2`) e guardar o nome real criptografado
2. **Criptografar** apenas o `resposta_texto` (que pode conter relatos sensíveis)
3. **Não criptografar** os valores numéricos das alternativas (scores), pois são necessários para cálculos e não identificam ninguém sozinhos

**Isso resolve o problema real:** mesmo com dump completo do banco, não é possível vincular "Score DASS-21 = 28" a "João da Silva".

```python
# models.py — Abordagem recomendada
from encrypted_model_fields.fields import EncryptedCharField, EncryptedTextField
import uuid

class RespostaQuestionario(models.Model):
    pesquisadora = models.ForeignKey(...)
    questionario = models.ForeignKey(...)
    data_submissao = models.DateTimeField(auto_now_add=True)
    
    # Pseudônimo público (pesquisável, ordenável)
    codigo_paciente = models.CharField(
        max_length=12, unique=True, editable=False,
        default=lambda: f"PAC-{uuid.uuid4().hex[:6].upper()}"
    )
    # Nome real criptografado (só visível na aplicação)
    paciente_nome = EncryptedCharField(max_length=255, null=True)

class RespostaPergunta(models.Model):
    resposta_questionario = models.ForeignKey(...)
    pergunta = models.ForeignKey(...)
    alternativa = models.ForeignKey(...)  # NÃO criptografar (int, necessário para cálculos)
    resposta_texto = EncryptedTextField(null=True, blank=True)  # 🔒
```

#### Impacto no código

| Camada | Alteração |
|---|---|
| `views.py` — `dashboard_respostas` | Exibir `codigo_paciente` na listagem em vez de `paciente_nome` |
| `views.py` — `exportar_excel` | Continua funcionando (lê via ORM, descriptografa automaticamente) |
| `admin.py` — `search_fields` | Buscar por `codigo_paciente` em vez de `paciente_nome` |
| `Scaleprocessor.py` | ✅ Nenhuma (usa `answers_map` com valores numéricos) |
| `scale_evaluator.py` | ✅ Nenhuma |
| Templates | Trocar `{{ resposta.paciente_nome }}` por `{{ resposta.codigo_paciente }}` nas listagens |

---

## 3. Comparativo Final

| Critério | Opção A (Campo) | Opção B (TDE) | Opção C (Pseudo + Cripto) |
|---|---|---|---|
| Protege contra dump do banco | ✅ | ❌ | ✅ |
| Protege contra SQL injection | ✅ | ❌ | ✅ |
| Mantém queries funcionando | ❌ | ✅ | ⚠️ Parcial (pseudônimo é pesquisável) |
| Impacto no código | Médio | Zero | Médio |
| Impacto nos cálculos de escala | ❌ Se criptografar tudo | ✅ | ✅ Não criptografa scores |
| Argumentação para banca | ✅ Forte | ❌ Fraco | ✅ **Muito forte** (LGPD + pseudoanonimização) |
| Complexidade | Média | Baixa | Média |

---

## 4. Recomendação

> [!TIP]
> **Opção C (Pseudoanonimização + Criptografia Seletiva)** é a mais adequada para o Somnus porque:
> 1. Protege os dados que **realmente importam** (nome + texto livre)
> 2. **Não quebra** os cálculos de escalas clínicas (PSQI, DASS-21, etc.)
> 3. Gera um **argumento técnico muito forte** para a banca (LGPD art. 46 + pseudoanonimização conforme art. 13§4º)
> 4. É implementável em **~2-3 horas** de trabalho

## 5. Pré-requisitos Técnicos

- Instalar: `pip install django-encrypted-model-fields`
- Adicionar `FIELD_ENCRYPTION_KEY` ao `.env` (gerada com Fernet)
- Criar migration para converter dados existentes
- **Backup do banco ANTES de migrar** (obrigatório)

---

## Perguntas para Decisão

1. **Você já tem dados reais de pacientes no banco de produção?** Se sim, precisamos de um script de migração para criptografar os dados existentes.
2. **O dashboard precisa buscar/filtrar por nome de paciente?** Se sim, a pseudoanonimização resolve isso com o `codigo_paciente`.
3. **Deseja seguir com a Opção C?**

"""
Management command para processar retroativamente (backfill) todas as
RespostaQuestionario que ainda não possuem ResultadoEscala no banco.

Uso:
    python manage.py backfill_resultados
    python manage.py backfill_resultados --questionario 3   # filtra por questionário
    python manage.py backfill_resultados --recalcular       # força recálculo de tudo
"""

from django.core.management.base import BaseCommand
from core.models import RespostaQuestionario, ResultadoEscala
from core.services import calcular_e_salvar_resultados


class Command(BaseCommand):
    help = "Calcula e persiste resultados de escalas para respostas existentes (backfill de cache)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--questionario', type=int, default=None,
            help='ID do questionário para processar apenas suas respostas (opcional).'
        )
        parser.add_argument(
            '--recalcular', action='store_true',
            help='Força o recálculo mesmo para respostas que já possuem cache.'
        )

    def handle(self, *args, **options):
        questionario_id = options.get('questionario')
        recalcular = options.get('recalcular', False)

        qs = RespostaQuestionario.objects.select_related('questionario').all()

        if questionario_id:
            qs = qs.filter(questionario_id=questionario_id)
            self.stdout.write(f"Filtrando pelo questionário ID={questionario_id}.")

        if not recalcular:
            # Pula respostas que já têm ao menos um ResultadoEscala associado
            ids_com_cache = ResultadoEscala.objects.values_list(
                'resposta_questionario_id', flat=True
            ).distinct()
            qs = qs.exclude(id__in=ids_com_cache)

        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS(
                "Nenhuma resposta pendente. Backfill já está completo."
            ))
            return

        self.stdout.write(f"Processando {total} resposta(s)...")
        sucesso = 0
        falhas = 0

        for resposta in qs.iterator():
            try:
                resultados = calcular_e_salvar_resultados(resposta)
                sucesso += 1
                self.stdout.write(
                    f"  [OK] [{resposta.codigo_paciente}] --- {len(resultados)} escala(s) processada(s)."
                )
            except Exception as e:
                falhas += 1
                self.stderr.write(
                    f"  [ERRO] [{resposta.codigo_paciente}] Erro: {e}"
                )

        self.stdout.write(self.style.SUCCESS(
            f"\nBackfill concluído: {sucesso} sucesso(s), {falhas} falha(s)."
        ))

import openpyxl
from django.core.management.base import BaseCommand
from compliance.models import AuditCategoria, AuditDomanda

class Command(BaseCommand):
    help = 'Trasforma l\'Excel in domande chiuse per l\'Audit Tecnico'

    def handle(self, *args, **kwargs):
        file_path = 'Checklist Security Base Rev2.2.xlsx'
        wb = openpyxl.load_workbook(file_path, data_only=True)
        sheet = wb['Tabelle1']

        # Creiamo una categoria contenitore
        categoria, _ = AuditCategoria.objects.get_or_create(
            nome="Security Base Rev 2.2",
            tipo='TECNICO'
        )

        count = 0
        for row in sheet.iter_rows(min_row=3, values_only=True):
            testo_domanda = row[1] # Colonna B
            suggerimento_tecnico = row[2] # Colonna C

            if testo_domanda:
                # Creiamo la domanda nel database
                AuditDomanda.objects.get_or_create(
                    categoria=categoria,
                    testo=str(testo_domanda).strip(),
                    defaults={
                        'suggerimento': str(suggerimento_tecnico).strip() if suggerimento_tecnico else "",
                        'riferimento_normativo': "NIS2 Art. 21",
                        'ordine': count
                    }
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f'Importate {count} domande chiuse!'))
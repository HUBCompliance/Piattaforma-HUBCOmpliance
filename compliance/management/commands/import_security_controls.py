import openpyxl
from django.core.management.base import BaseCommand
from compliance.models import SecurityControl # Percorso corretto per la tua app

class Command(BaseCommand):
    help = 'Importa i controlli di sicurezza dal file Excel della Checklist'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Il percorso del file .xlsx')

    def handle(self, *args, **options):
        path = options['file_path']
        
        try:
            workbook = openpyxl.load_workbook(path)
            sheet = workbook.active

            current_control_id = None
            current_main_text = ""
            support_lines = []
            count = 0

            # Iteriamo dalla riga 3 per saltare titolo e intestazioni vuote
            for row in sheet.iter_rows(min_row=3, values_only=True):
                col_a = row[0] # ID (1, 2, 3...)
                col_b = row[1] # Testo domanda o dettaglio

                if not col_b:
                    continue

                # Se la Colonna A ha un valore, è una nuova domanda principale
                if col_a is not None:
                    # Salviamo il controllo precedente prima di iniziare il nuovo
                    if current_control_id:
                        self.save_to_db(current_control_id, current_main_text, support_lines)
                        count += 1
                    
                    # Reset per il nuovo blocco
                    current_control_id = str(col_a)
                    current_main_text = col_b
                    support_lines = []
                else:
                    # È un dettaglio della domanda corrente
                    support_lines.append(str(col_b))

            # Salviamo l'ultimo blocco dopo la fine del ciclo
            if current_control_id:
                self.save_to_db(current_control_id, current_main_text, support_lines)
                count += 1

            self.stdout.write(self.style.SUCCESS(f'Importazione completata: {count} controlli caricati! ✅'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Errore: {e}'))

    def save_to_db(self, ctrl_id, text, support):
        # Uniamo le righe di supporto in un unico testo leggibile
        support_text = "\n".join(support)
        
        SecurityControl.objects.update_or_create(
            control_id=ctrl_id,
            defaults={
                'area': 'General Security', # Puoi personalizzarlo o estrarlo se presente
                'descrizione': text,
                'supporto_verifica': support_text,
            }
        )
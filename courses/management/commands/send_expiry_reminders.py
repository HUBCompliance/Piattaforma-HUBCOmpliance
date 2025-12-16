import datetime
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from courses.models import IscrizioneCorso, ImpostazioniSito

class Command(BaseCommand):
    help = 'Invia email di avviso per le iscrizioni ai corsi in scadenza tra 7 giorni.'

    def handle(self, *args, **options):
        
        # 1. Carica le impostazioni globali
        try:
            config = ImpostazioniSito.load()
            if not config.email_scadenza_template_id:
                self.stdout.write(self.style.ERROR('ID Template Email di Scadenza non impostato. Uscita.'))
                return
        except ImpostazioniSito.DoesNotExist:
            self.stdout.write(self.style.ERROR('Impostazioni Sito non trovate. Uscita.'))
            return

        # 2. Trova le iscrizioni rilevanti
        today = timezone.now().date()
        target_date = today + datetime.timedelta(days=7)
        
        iscrizioni_in_scadenza = IscrizioneCorso.objects.filter(
            data_scadenza=target_date,
            completato=False # Non inviare se l'hanno già completato
        ).select_related('studente', 'corso')

        if not iscrizioni_in_scadenza.exists():
            self.stdout.write(self.style.SUCCESS('Nessuna iscrizione in scadenza tra 7 giorni. Nessuna email inviata.'))
            return

        self.stdout.write(f'Trovate {iscrizioni_in_scadenza.count()} iscrizioni in scadenza il {target_date.strftime("%d/%m/%Y")}. Invio email...')

        sent_count = 0
        for iscrizione in iscrizioni_in_scadenza:
            studente = iscrizione.studente
            corso = iscrizione.corso
            data_formattata = iscrizione.data_scadenza.strftime('%d/%m/%Y')

            # 3. Prepara l'email
            subject = "Avviso di Scadenza Corso" # Questo triggera il template giusto nel backend
            
            # Questi dati verranno letti dal backend e passati a EmailJS
            message_body = f"""
            Studente: {studente.get_full_name()}
            Corso: {corso.titolo}
            Data: {data_formattata}
            """
            
            try:
                send_mail(
                    subject,
                    message_body,
                    settings.DEFAULT_FROM_EMAIL,
                    [studente.email],
                    fail_silently=False
                )
                self.stdout.write(self.style.SUCCESS(f'Email inviata a {studente.email} per il corso {corso.titolo}'))
                sent_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Errore invio email a {studente.email}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'Operazione completata. Inviate {sent_count} email.'))
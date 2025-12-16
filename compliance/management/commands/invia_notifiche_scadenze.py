from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from compliance.models import Compito
from courses.models import Azienda
from user_auth.models import CustomUser as User

class Command(BaseCommand):
    help = 'Invia email di notifica per i compiti scaduti e aperti.'

    def handle(self, *args, **kwargs):
        oggi = timezone.now().date()
        
        compiti_scaduti = Compito.objects.filter(
            data_scadenza__lt=oggi, 
            stato='APERTO',
            notifica_scadenza_inviata=False
        )
        
        if not compiti_scaduti.exists():
            self.stdout.write(self.style.SUCCESS("Nessun compito scaduto da notificare."))
            return

        self.stdout.write(f"Trovati {compiti_scaduti.count()} compiti scaduti da notificare.")

        for compito in compiti_scaduti:
            destinatari = set() 
            
            if compito.is_global:
                aziende_target = Azienda.objects.all()
            else:
                aziende_target = compito.aziende_assegnate.all()
            
            for azienda in aziende_target:
                # 1. Aggiungi i Referenti dell'azienda
                for ref in User.objects.filter(azienda=azienda, ruolo='REFERENTE'):
                    if ref.email: destinatari.add(ref.email)
                
                # 2. Aggiungi i Consulenti assegnati all'azienda
                for consulente in azienda.consulenti.all():
                    if consulente.email: destinatari.add(consulente.email)
            
            if destinatari:
                subject = f"AVVISO SCADENZA: {compito.titolo}"
                
                # --- MODIFICA: Corpo formattato per EmailJSBackend ---
                message = (
                    f"TITOLO: {compito.titolo}\n"
                    f"SCADUTO IL: {compito.data_scadenza.strftime('%d/%m/%Y')}\n"
                    f"DESCRIZIONE: {compito.descrizione or '-'}\n"
                    f"PRIORITÀ: {compito.get_priorita_display()}\n"
                )
                # --- FINE MODIFICA ---
                
                try:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        list(destinatari),
                        fail_silently=False
                    )
                    self.stdout.write(self.style.SUCCESS(f"Email inviata per '{compito.titolo}' a {len(destinatari)} destinatari."))
                    
                    compito.notifica_scadenza_inviata = True
                    compito.save()
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Errore invio per '{compito.titolo}': {e}"))
            else:
                self.stdout.write(self.style.WARNING(f"Nessun destinatario per '{compito.titolo}'"))

        self.stdout.write(self.style.SUCCESS("Procedura completata."))
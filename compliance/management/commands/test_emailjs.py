from django.core.management.base import BaseCommand
from django.core.mail import send_mail
import time

class Command(BaseCommand):
    help = 'Testa il routing dei template del backend EmailJS'

    def handle(self, *args, **kwargs):
        # Metti qui una tua mail reale per verificare la ricezione
        destinatario = "gianluca@muggittu.it" 
        
        self.stdout.write(self.style.SUCCESS("--- Inizio Test EmailJS Backend ---"))

        # 1. TEST RESET PASSWORD
        self.stdout.write("\n1. Invio mail di Reset Password...")
        try:
            send_mail(
                subject="Reimposta la tua password",
                message="Ecco il link: https://tuosito.it/reset/user123/token456/",
                from_email=None,
                recipient_list=[destinatario],
                fail_silently=False,
            )
            self.stdout.write("   Check: Guarda i log del server per confermare il template reset.")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   Errore: {e}"))

        time.sleep(1) # Piccola pausa per EmailJS

        # 2. TEST SCADENZA COMPITO
        self.stdout.write("\n2. Invio mail di Scadenza Compito...")
        try:
            send_mail(
                subject="Avviso: Scadenza compito NIS2",
                message="Un compito assegnato è prossimo alla scadenza.",
                from_email=None,
                recipient_list=[destinatario],
                fail_silently=False,
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   Errore: {e}"))

        time.sleep(1)

        # 3. TEST EMAIL BLOCCATA (NON WHITELISTED)
        self.stdout.write("\n3. Invio mail generica (Deve essere BLOCCATA dal backend)...")
        try:
            send_mail(
                subject="Saluti generici",
                message="Questa mail non dovrebbe passare il filtro.",
                from_email=None,
                recipient_list=[destinatario],
                fail_silently=False,
            )
            self.stdout.write("   Check: Se vedi 'BLOCCATA' nel log sopra, il filtro funziona!")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   Errore: {e}"))

        self.stdout.write(self.style.SUCCESS("\n--- Test terminati ---"))
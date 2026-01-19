from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import IscrizioneCorso, RegistroFormazione

@receiver(post_save, sender=IscrizioneCorso)
def aggiorna_registro_completamento(sender, instance, **kwargs):
    # Se il corso è segnato come completato, creiamo la riga nel registro
    if instance.completato:
        # Usiamo update_or_create per evitare duplicati se il segnale scatta due volte
        RegistroFormazione.objects.update_or_create(
            azienda=instance.studente.azienda,
            studente=instance.studente,
            titolo_corso=instance.corso.nome,
            fonte='A', # A sta per Automatico
            defaults={
                'data_completamento': instance.data_completamento or timezone.now().date(),
                'durata_ore': instance.corso.durata_ore,
                'note': "Completato sulla piattaforma e-learning."
            }
        )
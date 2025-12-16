import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class ComplexityValidator:
    """
    Valida che la password contenga maiuscole, minuscole, numeri e caratteri speciali.
    """
    def validate(self, password, user=None):
        # 1. Controllo Maiuscola
        if not re.findall(r'[A-Z]', password):
            raise ValidationError(
                _("La password deve contenere almeno una lettera MAIUSCOLA.")
            )
        
        # 2. Controllo Minuscola
        if not re.findall(r'[a-z]', password):
            raise ValidationError(
                _("La password deve contenere almeno una lettera minuscola.")
            )

        # 3. Controllo Numero
        if not re.findall(r'[0-9]', password):
            raise ValidationError(
                _("La password deve contenere almeno un NUMERO.")
            )

        # 4. Controllo Carattere Speciale
        if not re.findall(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(
                _("La password deve contenere almeno un carattere SPECIALE (es. @, #, $, !).")
            )

    def get_help_text(self):
        return _(
            "La password deve contenere almeno una lettera maiuscola, una minuscola, "
            "un numero e un carattere speciale."
        )
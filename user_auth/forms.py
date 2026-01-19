from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, SetPasswordForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import authenticate 
from .models import CustomUser as User, Azienda, Consulente
from django.core.exceptions import ValidationError
from compliance.models import Compito 


# ==============================================================================
# 1. AUTHENTICATION FORMS
# ==============================================================================

class LoginForm(AuthenticationForm):
    """Form di login standard basato su AuthenticationForm di Django."""
    username = forms.CharField(label=_("Nome Utente o Email"), widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(self.request, username=username, password=password)
            
            if self.user_cache is None:
                try:
                    user_match = User.objects.get(email=username)
                    self.user_cache = authenticate(self.request, username=user_match.username, password=password)
                except User.DoesNotExist:
                    pass
            
            if self.user_cache is None:
                raise forms.ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login',
                    params={'username': self.username_field.verbose_name},
                )
        return self.cleaned_data

class RegisterForm(UserCreationForm):
    """Form di registrazione per nuovi studenti/referenti."""
    email = forms.EmailField(label=_("Email"), max_length=254, help_text=_('Richiesta. Inserisci un indirizzo email valido.'), widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(label=_("Nome"), max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label=_("Cognome"), max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "username")
        field_classes = {'username': forms.CharField}

    def clean_username(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError(_("L'email è richiesta."))
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email
        if commit:
            user.save()
        return user


# === FORMS CUSTOM PER IL FLUSSO DI RESET PASSWORD ===

class CustomPasswordResetForm(PasswordResetForm):
    """Form di reset password che usa l'email come campo unico."""
    email = forms.EmailField(
        label=_("Email"),
        max_length=254,
        widget=forms.EmailInput(attrs={'autocomplete': 'email', 'class': 'form-control'})
    )

class CustomSetPasswordForm(SetPasswordForm):
    """Form per impostare la nuova password dopo il reset."""
    new_password1 = forms.CharField(
        label=_("Nuova password"),
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control'}),
        strip=False,
    )
    new_password2 = forms.CharField(
        label=_("Conferma nuova password"),
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control'}),
        strip=False,
    )

class SecurityLoginForm(LoginForm):
    """Placeholder per il login con eventuali controlli di sicurezza aggiuntivi."""
    pass
    
# ==============================================================================
# 2. REFERENTE/STUDENTE FORMS 
# ==============================================================================

class ProfiloStudenteForm(forms.ModelForm): 
    """Form per l'aggiornamento del profilo (usato in views.profilo_studente)."""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if self.instance.pk:
            if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
                raise ValidationError(_("Questa email è già in uso."))
        elif User.objects.filter(email=email).exists():
            raise ValidationError(_("Questa email è già in uso."))
        return email


class ReferenteStudenteForm(forms.ModelForm):
    """Form generico per la creazione/modifica di un utente Studente/Referente."""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class ReferenteUpdateForm(ReferenteStudenteForm):
    """Form per l'aggiornamento del profilo (stessi campi ma nome diverso)."""
    class Meta(ReferenteStudenteForm.Meta):
        fields = ['first_name', 'last_name', 'email']
        
        
class ConsulenteUpdateForm(forms.ModelForm):
    """Form per l'aggiornamento del profilo Consulente."""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class AziendaProfileForm(forms.ModelForm): 
    """Form per l'aggiornamento dei dettagli dell'Azienda (usato dal Referente)."""
    class Meta:
        model = Azienda
        # Campi che ESISTONO nel modello Azienda:
        fields = ['nome', 'p_iva', 'indirizzo'] 
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'p_iva': forms.TextInput(attrs={'class': 'form-control'}), # Nota: usa p_iva, non partita_iva
            'indirizzo': forms.TextInput(attrs={'class': 'form-control'}),
        }


# ==============================================================================
# 3. CONSULENTE ADMIN FORMS
# ==============================================================================

class ConsulenteCreaReferenteForm(forms.ModelForm):
    """Form che il Consulente usa per creare un Referente per una specifica Azienda."""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class ConsulenteCompitoForm(forms.ModelForm):
    """Form per la creazione di un compito da parte del Consulente."""
    
    class Meta:
        model = Compito
        fields = ['titolo', 'descrizione', 'priorita', 'data_scadenza']
        widgets = {
            'data_scadenza': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'titolo': forms.TextInput(attrs={'class': 'form-control'}),
            'descrizione': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'priorita': forms.Select(attrs={'class': 'form-select'}),
        }

class AziendaModuliForm(forms.ModelForm):
    """Form per l'abilitazione/disabilitazione dei moduli di compliance per l'azienda."""
    
    class Meta:
        model = Azienda
        fields = ['mod_trattamenti', 'mod_documenti', 'mod_audit', 'mod_videosorveglianza', 'mod_tia', 'mod_organigramma', 'mod_asset', 'mod_analisi_rischi', 'mod_rete', 'mod_fornitori', 'mod_whistleblowing']
        widgets = {
            'mod_trattamenti': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'mod_documenti': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'mod_audit': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'mod_videosorveglianza': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'mod_tia': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'mod_organigramma': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'mod_asset': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'mod_analisi_rischi': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'mod_rete': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'mod_fornitori': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'mod_whistleblowing': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

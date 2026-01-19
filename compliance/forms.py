from django import forms
import re
from django.db.models import Q
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _

# Importa tutti i modelli da compliance.models (modello 'NotificaIncidente' è aggiornato)
# compliance/forms.py

from .models import (
    CategoriaDati, SoggettoInteressato, Trattamento, DomandaChecklist, RispostaChecklist,
    TemplateDocumento, CategoriaDocumento, DocumentoAziendale, VersioneDocumento,
    Incidente, RichiestaInteressato,
    AuditCategoria, AuditDomanda, AuditRisposta, AuditSession,
    Compito, Asset, Software, RuoloPrivacy, Paese, ValutazioneTIA, Videosorveglianza,
    ReferenteCSIRT, ContattoInternoCSIRT, NotificaIncidente, AllegatoNotifica,
    ConfigurazioneRete, ComponenteRete,
    DomandaFornitore,                 # <--- Aggiungi questo
    RispostaQuestionarioFornitore,    # <--- Aggiungi questo (Risolve l'errore alla riga 429)
    Fornitore
)
# Importa i modelli necessari da altri moduli se usati nei form
from user_auth.models import CustomUser as User, Azienda

# ==============================================================================
# 1. FORMS PER IL REGISTRO TRATTAMENTI
# ==============================================================================

class TrattamentoForm(forms.ModelForm):
    categorie_dati_input = forms.CharField(
        required=False,
        label=_("Categorie di Dati"),
        help_text=_("Inserisci categorie separate da virgola o a capo."),
        widget=forms.Textarea(attrs={'rows': 3}),
    )
    soggetti_interessati_input = forms.CharField(
        required=False,
        label=_("Soggetti Interessati"),
        help_text=_("Inserisci soggetti interessati separati da virgola o a capo."),
        widget=forms.Textarea(attrs={'rows': 3}),
    )

    class Meta:
        model = Trattamento
        # Ho allineato i campi a quelli effettivamente presenti nel tuo models.py
        fields = [
            'nome_trattamento', 
            'tipo_ruolo',
            'finalita', 
            'categorie_dati', 
            'soggetti_interessati', 
            'destinatari_esterni',
            'tempo_conservazione',
            'misure_sicurezza'
        ]
        widgets = {
            'finalita': forms.Textarea(attrs={'rows': 3}),
            'categorie_dati': forms.CheckboxSelectMultiple(),
            'soggetti_interessati': forms.CheckboxSelectMultiple(),
            'destinatari_interni': forms.Textarea(attrs={'rows': 3}),
            'destinatari_esterni': forms.Textarea(attrs={'rows': 3}),
            'misure_sicurezza': forms.Textarea(attrs={'rows': 4}),
            'nome_trattamento': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Es. Gestione Paghe Dipendenti'}),
            'tipo_ruolo': forms.Select(attrs={'class': 'form-select'}),
            'finalita': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'id': 'id_finalita'}),
            
            # Questi due sono ManyToMany e useranno le checkbox editabili
            'categorie_dati': forms.CheckboxSelectMultiple(),
            'soggetti_interessati': forms.CheckboxSelectMultiple(),
            
            # Questi sono TextField nel modello, quindi usiamo Textarea
            'destinatari_esterni': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Es. Consulente del Lavoro, Software House Cloud...'}),
            'tempo_conservazione': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Es. 10 anni dalla cessazione del rapporto'}),
            'misure_sicurezza': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Es. Crittografia, Backup giornaliero, MFA...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('categorie_dati', None)
        self.fields.pop('soggetti_interessati', None)

        ordered_fields = [
            'nome_trattamento',
            'tipo_ruolo',
            'per_conto_di',
            'finalita',
            'categorie_dati_input',
            'soggetti_interessati_input',
            'destinatari_interni',
            'destinatari_esterni',
            'tempo_conservazione',
            'misure_sicurezza',
        ]
        self.order_fields(ordered_fields)

        if self.instance.pk:
            categorie = self.instance.categorie_dati.values_list('nome', flat=True)
            soggetti = self.instance.soggetti_interessati.values_list('nome', flat=True)
            self.fields['categorie_dati_input'].initial = ", ".join(categorie)
            self.fields['soggetti_interessati_input'].initial = ", ".join(soggetti)

    def _parse_items(self, value):
        if not value:
            return []
        items = [item.strip() for item in re.split(r'[\n,]+', value) if item.strip()]
        return list(dict.fromkeys(items))

    def _update_m2m_from_input(self, instance):
        categorie = self._parse_items(self.cleaned_data.get('categorie_dati_input'))
        soggetti = self._parse_items(self.cleaned_data.get('soggetti_interessati_input'))

        categoria_objs = [
            CategoriaDati.objects.get_or_create(nome=nome)[0] for nome in categorie
        ]
        soggetto_objs = [
            SoggettoInteressato.objects.get_or_create(nome=nome)[0] for nome in soggetti
        ]

        instance.categorie_dati.set(categoria_objs)
        instance.soggetti_interessati.set(soggetto_objs)

    def save(self, commit=True):
        instance = super().save(commit=commit)
        if commit:
            self._update_m2m_from_input(instance)
        return instance

    def save_m2m(self):
        super().save_m2m()
        self._update_m2m_from_input(self.instance)
        # Rendiamo le checkbox più carine aggiungendo una classe bootstrap via codice
        self.fields['categorie_dati'].widget.attrs.update({'class': 'form-check-input'})
        self.fields['soggetti_interessati'].widget.attrs.update({'class': 'form-check-input'})
        

# ==============================================================================
# 2. FORMS PER LA GESTIONE DOCUMENTALE
# ==============================================================================

class DocumentoAziendaleForm(forms.ModelForm):
    class Meta:
        model = DocumentoAziendale
        exclude = ['azienda', 'creato_da_template']

class VersioneDocumentoForm(forms.ModelForm):
    class Meta:
        model = VersioneDocumento
        exclude = ['documento', 'caricato_da', 'data_caricamento']

# ==============================================================================
# 3. FORMS PER INCIDENTI (DATA BREACH)
# ==============================================================================

class IncidenteForm(forms.ModelForm):
    class Meta:
        model = Incidente
        exclude = ['azienda', 'segnalato_da', 'notifica_garante_necessaria', 'notifica_interessati_necessaria']
        widgets = {
            'data_rilevamento': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'descrizione': forms.Textarea(attrs={'rows': 4}),
            'valutazione_rischio': forms.Textarea(attrs={'rows': 3}),
            'azioni_correttive': forms.Textarea(attrs={'rows': 3}),
        }

# ==============================================================================
# 4. FORMS PER RICHIESTE INTERESSATI
# ==============================================================================

class RichiestaInteressatoForm(forms.ModelForm):
    class Meta:
        model = RichiestaInteressato
        exclude = ['azienda', 'gestita_da', 'data_ricezione']
        widgets = {
            'richiesta_testo': forms.Textarea(attrs={'rows': 3}),
            'note_interne': forms.Textarea(attrs={'rows': 3}),
            'data_scadenza_risposta': forms.DateInput(attrs={'type': 'date'}),
        }

# ==============================================================================
# 5. FORMS PER AUDIT (AGGIORNATO PER REVISIONE STORICA)
# ==============================================================================

# In compliance/forms.py

class AuditChecklistForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.sessione = kwargs.pop('sessione', None)
        self.domande = kwargs.pop('domande', None)
        super().__init__(*args, **kwargs)
        
        # Dizionari per caricare i dati esistenti
        risposte_db = {}
        note_db = {}
        
        if self.sessione:
            from .models import AuditRisposta
            # Recuperiamo sia la risposta (bool) che la nota (text)
            dati_db = AuditRisposta.objects.filter(sessione=self.sessione)
            for r in dati_db:
                risposte_db[r.domanda_id] = bool(r.risposta)
                note_db[r.domanda_id] = r.note or ""

        if self.domande:
            for domanda in self.domande:
                # 1. Campo Checkbox (Sì/No)
                self.fields[f'domanda_{domanda.id}'] = forms.BooleanField(
                    label=domanda.testo,
                    required=False,
                    initial=risposte_db.get(domanda.id, False),
                    widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
                )
                # 2. NUOVO: Campo Note (Testo)
                self.fields[f'nota_{domanda.id}'] = forms.CharField(
                    required=False,
                    initial=note_db.get(domanda.id, ""),
                    widget=forms.Textarea(attrs={
                        'class': 'form-control mt-2',
                        'rows': 2,
                        'placeholder': _("Inserisci note o osservazioni...")
                    })
                )
    
    def save(self):
        from .models import AuditRisposta
        # Troviamo tutti gli ID domanda presenti nel form
        domanda_ids = set(key.split('_')[1] for key in self.cleaned_data.keys())
        
        for d_id in domanda_ids:
            valore_bool = self.cleaned_data.get(f'domanda_{d_id}', False)
            valore_nota = self.cleaned_data.get(f'nota_{d_id}', "")
            
            AuditRisposta.objects.update_or_create(
                sessione=self.sessione,
                domanda_id=d_id,
                defaults={
                    'risposta': valore_bool,
                    'note': valore_nota  # Salviamo la nota nel DB
                }
            )

# ==============================================================================
# 6. FORMS PER COMPITI
# ==============================================================================

class ConsulenteCompitoForm(forms.ModelForm):
    class Meta:
        model = Compito
        fields = ['titolo', 'descrizione', 'data_scadenza', 'priorita']
        widgets = {
            'data_scadenza': forms.DateInput(attrs={'type': 'date'}),
            'descrizione': forms.Textarea(attrs={'rows': 3}),
        }

# ==============================================================================
# 7. FORMS PER GESTIONE UTENTI (Consulente)
# ==============================================================================

class ConsulenteCreaReferenteForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        labels = {
            'email': _("Email (Sarà anche Username)"),
        }

class ReferenteStudenteForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Allinea sempre lo username all'email per rispettare il vincolo di unicità
        instance.username = self.cleaned_data.get('email', instance.username)
        if commit:
            instance.save()
        return instance

# ==============================================================================
# 8. FORMS PER CONFIGURAZIONE MODULI (Azienda)
# ==============================================================================

class AziendaModuliForm(forms.ModelForm):
    class Meta:
        model = Azienda
        fields = [
            'mod_trattamenti', 'mod_documenti', 'mod_audit', 'mod_videosorveglianza', 
            'mod_tia', 'mod_organigramma', 'mod_csirt', 'mod_cruscotto', 
            'mod_incidenti', 'mod_richieste', 'mod_formazione', 'mod_storico_audit',
            'mod_asset', 'mod_analisi_rischi', 'mod_rete', 'mod_fornitori', 'mod_whistleblowing'
        ]
        labels = {
            'mod_trattamenti': _("Registro Trattamenti (GDPR)"),
            'mod_documenti': _("Gestione Documenti"),
            'mod_audit': _("Checklist Audit Compliance"),
            'mod_videosorveglianza': _("Videosorveglianza (Checklist)"),
            'mod_tia': _("TIA (Trasferimento Dati Extra-UE)"),
            'mod_organigramma': _("Organigramma Privacy (Ruoli)"),
            'mod_csirt': _("Gestione CSIRT (NIS2)"),
            'mod_cruscotto': _("Cruscotto di Sintesi/Semaforo"),
            'mod_incidenti': _("Segnalazione Data Breach"),
            'mod_richieste': _("Richieste Interessati"),
            'mod_formazione': _("Gestione Formazione Dipendenti"),
            'mod_storico_audit': _("Storico Sessioni Audit"),
            'mod_asset': _("Asset Aziendali"),
            'mod_analisi_rischi': _("Analisi Rischi"),
            'mod_rete': _("Configurazione Rete"),
            'mod_fornitori': _("Fornitori"),
            'mod_whistleblowing': _("Whistleblowing"),
        }

# ==============================================================================
# 9. FORMS NIS2 (CSIRT)
# ==============================================================================

class ReferenteCSIRTForm(forms.ModelForm):
    class Meta:
        model = ReferenteCSIRT
        exclude = ['azienda', 'referente_user']
        widgets = {
            'motivo_esterno': forms.Textarea(attrs={'rows': 3}),
            'data_nomina': forms.DateInput(attrs={'type': 'date'}),
        }

class ContattoInternoCSIRTForm(forms.ModelForm):
    class Meta:
        model = ContattoInternoCSIRT
        exclude = ['azienda']
        widgets = {
            'note': forms.Textarea(attrs={'rows': 2}),
        }

class NotificaIncidenteForm(forms.ModelForm):
    class Meta:
        model = NotificaIncidente
        fields = [
            'titolo_incidente',
            'data_incidente',
            'descrizione_danno',
            # Nuovi campi di Caratterizzazione (ACN/NIST)
            'categoria_incidente',
            'impatto_stimato',
            'severita_incidente',
            'playbook_associato',
            # Campi di gestione
            'stato',
            'valutazione_rischio',
            'azioni_correttive',
            'data_notifica',
        ]
        widgets = {
            'data_incidente': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'data_notifica': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'descrizione_danno': forms.Textarea(attrs={'rows': 3}),
            'valutazione_rischio': forms.Textarea(attrs={'rows': 3}),
            'azioni_correttive': forms.Textarea(attrs={'rows': 3}),
        }

class NotificaIncidenteUpdateForm(forms.ModelForm):
    class Meta:
        model = NotificaIncidente
        fields = [
            'categoria_incidente',
            'impatto_stimato',
            'severita_incidente',
            'playbook_associato',
            'stato',
            'valutazione_rischio',
            'azioni_correttive',
            'data_notifica',
        ]
        widgets = {
            'data_notifica': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'valutazione_rischio': forms.Textarea(attrs={'rows': 3}),
            'azioni_correttive': forms.Textarea(attrs={'rows': 3}),
        }

class CSIRTTemplateForm(forms.ModelForm):
    """ Form per l'upload del template di nomina CSIRT in ImpostazioniSito """
    class Meta:
        from courses.models import ImpostazioniSito 
        model = ImpostazioniSito
        fields = ['template_nomina_csirt']

# ==============================================================================
# 10. FORMS INFRASTRUTTURA/ASSET (NIS2)
# ==============================================================================

class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        exclude = ['azienda']

class SoftwareForm(forms.ModelForm):
    class Meta:
        model = Software
        exclude = ['azienda']

class RuoloPrivacyForm(forms.ModelForm):
    class Meta:
        model = RuoloPrivacy
        exclude = ['azienda']

class TIAForm(forms.ModelForm):
    class Meta:
        model = ValutazioneTIA
        exclude = ['azienda', 'compilato_da', 'data_valutazione', 'esito_calcolato']
        widgets = {
            'descrizione_dati': forms.Textarea(attrs={'rows': 3}),
            'note': forms.Textarea(attrs={'rows': 3}),
        }

class VideosorveglianzaForm(forms.ModelForm):
    class Meta:
        model = Videosorveglianza
        exclude = ['azienda', 'compilato_da', 'data_compilazione', 'stato_conformita']
        widgets = {
            'azioni_richieste': forms.Textarea(attrs={'rows': 3}),
        }

class ConfigurazioneReteForm(forms.ModelForm):
    class Meta:
        model = ConfigurazioneRete
        exclude = ['azienda']
        widgets = {
            'segmentazione_rete': forms.Textarea(attrs={'rows': 3}),
        }
        
# Formset per i Componenti di Rete
ComponenteReteFormSet = inlineformset_factory(
    ConfigurazioneRete, 
    ComponenteRete, 
    fields=(
        'nome_componente', 
        'tipo', 
        'indirizzo_ip', 
        'criticita', 
        'descrizione_funzione'
    ),
    extra=1,
    can_delete=True
)

# Formset per i Ruoli Privacy
RuoloPrivacyFormSet = inlineformset_factory(
    Azienda,
    RuoloPrivacy,
    fields=('ruolo_tipo', 'nome_cognome', 'contatti', 'atto_nomina'),
    extra=1,
    can_delete=True
)
# ==============================================================================
# 11. FORMS SECURITY VENDOR (CLUSIT)
# ==============================================================================

class RispostaQuestionarioFornitoreForm(forms.ModelForm):
    class Meta:
        model = RispostaQuestionarioFornitore
        fields = ['valore_risposta', 'note']
        widgets = {
            'valore_risposta': forms.Select(choices=[
                (1.0, _('Sì (Pieno)')), 
                (0.5, _('Parziale')), 
                (0.0, _('No / Assente'))
            ], attrs={'class': 'form-select'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

# ==============================================================================
# 12. FORMS FORNITORI
# ==============================================================================

class FornitoreForm(forms.ModelForm):
    class Meta:
        model = Fornitore
        fields = ['ragione_sociale', 'email_contatto', 'servizio_fornito']
        widgets = {
            'ragione_sociale': forms.TextInput(attrs={'class': 'form-control'}),
            'email_contatto': forms.EmailInput(attrs={'class': 'form-control'}),
            'servizio_fornito': forms.TextInput(attrs={'class': 'form-control'}),
        }

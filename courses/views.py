from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.decorators import login_required, user_passes_test 
from django.contrib.auth.hashers import make_password
from django.db.models import Prefetch, Count
from django.utils import timezone 
from django.conf import settings 
from django.http import HttpResponse, Http404
from django.template.loader import get_template, render_to_string
from xhtml2pdf import pisa
from io import BytesIO
from .models import Attestato
from .models import ImpostazioniSito
from .models import Corso, Modulo, Quiz, Attestato
from .models import RegistroFormazione
import base64
import pandas as pd
import random
import string
import os
import uuid
import openpyxl

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.core.mail import send_mail 
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.files.base import ContentFile 
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.views import PasswordResetView, LoginView
from django.urls import reverse_lazy

# Importazioni dei modelli (corrette)
from user_auth.models import CustomUser, Azienda
from courses.models import (
    Corso, IscrizioneCorso, Modulo, ProgressoModulo,
    Quiz, Domanda, Risposta, Attestato, ImpostazioniSito
)
from compliance.models import CategoriaDocumento, DocumentoAziendale, VersioneDocumento
from user_auth.forms import ProfiloStudenteForm, AziendaProfileForm, SecurityLoginForm

# RIMOZIONE DELLA RIGA BLOCCANTE: L'errore era qui, perché genera_attestato_pdf
# è definito in questo stesso file (Sezione 5) e non deve essere importato da views.py.
# from user_auth.views import genera_attestato_pdf 


# --- 1. Logica di Supporto (funzioni helper) ---
def mia_funzione_api():
    config = ImpostazioniSito.objects.get(pk=1)
    api_key = config.pentest_tools_api_key
def trigger_set_password_email(request, user):
    """
    Invia l'email usando il backend configurato in settings.py.
    """
    # Logica Email (lasciata invariata)
    try:
        current_site = get_current_site(request)
        domain = current_site.domain
        protocol = 'https' if request.is_secure() else 'http'
        
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        context = {
            'email': user.email, 'domain': domain, 'protocol': protocol,
            'uid': uid, 'token': token, 'user': user,
        }

        subject = render_to_string('registration/password_reset_subject.txt', context).strip()
        body = render_to_string('registration/password_reset_email.html', context)
        
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False 
        )
        return True

    except Exception as e:
        print(f"--- [DEBUG EMAIL] ERRORE CRITICO: {e} ---")
    return False


def generate_strong_password(length=12):
    # Logica Generazione Password (lasciata invariata)
    if length < 12: length = 12
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special = string.punctuation
    password = [random.choice(lowercase), random.choice(uppercase), random.choice(digits), random.choice(special)]
    all_chars = lowercase + uppercase + digits + special
    remaining_length = length - 4
    password.extend(random.choice(all_chars) for _ in range(remaining_length))
    random.shuffle(password)
    return "".join(password)

def is_admin(user): return user.is_authenticated and user.ruolo == 'ADMIN'
def is_studente(user): return user.is_authenticated and user.ruolo == 'STUDENTE' and not user.is_staff
def is_profilo_user(user): 
    if not user.is_authenticated or user.is_staff: return False
    return user.ruolo in ['STUDENTE', 'REFERENTE', 'CONSULENTE']

# --- 2. Viste Admin (Importazione Excel) ---
@transaction.atomic
def import_student_excel(request): 
    template_name = 'admin/import_excel.html' 
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        try:
            df = pd.read_excel(excel_file); df = df.fillna('')
            df.columns = df.columns.str.lower().str.strip()
            required_cols = ['nome', 'cognome', 'email', 'azienda']
            if not all(col in df.columns for col in required_cols):
                messages.error(request, f"File non valido. Colonne richieste: {', '.join(required_cols)}")
                return render(request, template_name)
            created_count = 0
            for index, row in df.iterrows():
                email = str(row['email']).lower().strip()
                azienda_nome = str(row['azienda']).strip()
                if not email: continue
                azienda_obj, _ = Azienda.objects.get_or_create(nome=azienda_nome) 
                user, created = CustomUser.objects.update_or_create(
                    username=email, 
                    defaults={
                        'email': email, 'first_name': row.get('nome', ''), 'last_name': row.get('cognome', ''),
                        'ruolo': 'STUDENTE', 'azienda': azienda_obj, 'is_active': True,
                        'numero_telefono': row.get('numero telefono', row.get('telefono', '')),
                    }
                )
                if created:
                    user.set_unusable_password(); user.save()
                    trigger_set_password_email(request, user); created_count += 1
            messages.success(request, f"Importazione completata! Creati {created_count} nuovi profili.")
        except Exception as e:
            messages.error(request, f"Errore: {e}")
    return render(request, template_name)

# --- 3. Viste Studente ---
@login_required(login_url='/login/')
def dashboard_studente(request):
    user = request.user
    if user.ruolo == 'CONSULENTE': return redirect('compliance:dashboard_consulente') 
    if user.ruolo == 'REFERENTE': return redirect('compliance:dashboard_compliance') 
    if user.is_staff: return redirect('admin:index') 
    if user.ruolo != 'STUDENTE': return redirect('login') 
    
    iscrizioni = IscrizioneCorso.objects.filter(studente=user.id, corso__stato='A').select_related('corso')
    corsi_con_progresso = []
    for iscrizione in iscrizioni:
        corso = iscrizione.corso
        moduli_totali = Modulo.objects.filter(corso=corso).count()
        moduli_completati = ProgressoModulo.objects.filter(iscrizione=iscrizione, completato=True).count()
        percentuale = int((moduli_completati / moduli_totali) * 100) if moduli_totali > 0 else 0
        corsi_con_progresso.append({'iscrizione': iscrizione, 'percentuale': percentuale})
    context = {'corsi_con_progresso': corsi_con_progresso, 'studente_name': user.get_full_name() or user.username}
    return render(request, 'dashboard_studente.html', context)

@login_required(login_url='/auth/login/')
@user_passes_test(is_studente)
def corso_dettaglio(request, corso_id):
    iscrizione = get_object_or_404(IscrizioneCorso, studente=request.user.id, corso__id=corso_id)
    corso = iscrizione.corso
    moduli = Modulo.objects.filter(corso=corso).order_by('ordine').prefetch_related(
        Prefetch('progressi', queryset=ProgressoModulo.objects.filter(iscrizione=iscrizione), to_attr='progresso_personale'), 'media', 'quiz' 
    )
    moduli_list = []; moduli_completati_count = 0; modulo_sbloccato = True
    for modulo in moduli:
        progresso = modulo.progresso_personale[0] if modulo.progresso_personale else None
        is_completato = progresso and progresso.completato
        moduli_list.append({'modulo': modulo, 'is_completato': is_completato, 'is_sbloccato': modulo_sbloccato, 'media_items': modulo.media.all(), 'ha_quiz': bool(modulo.quiz)})
        if is_completato: moduli_completati_count += 1
        if not is_completato: modulo_sbloccato = False
    
    tutti_moduli_completati = (moduli_completati_count == len(moduli_list))
    test_finale = corso.quiz 
    attestato_ottenuto = Attestato.objects.filter(iscrizione=iscrizione).first()
    if tutti_moduli_completati and not test_finale and not attestato_ottenuto:
        attestato, created = Attestato.objects.get_or_create(iscrizione=iscrizione, defaults={'codice_univoco': generate_strong_password(10)}) 
        attestato_ottenuto = attestato 
        if not iscrizione.completato:
            iscrizione.completato = True; iscrizione.data_completamento = timezone.now(); iscrizione.save()
            messages.success(request, f"Corso '{corso.nome}' completato! Ora puoi scaricare il tuo attestato.")
    context = {'corso': corso, 'moduli_list': moduli_list, 'tutti_moduli_completati': tutti_moduli_completati, 'test_finale': test_finale, 'attestato_ottenuto': attestato_ottenuto}
    return render(request, 'corso_dettaglio.html', context)

@login_required(login_url='/auth/login/')
@user_passes_test(is_studente)
def completa_modulo(request, modulo_id):
    modulo = get_object_or_404(Modulo, pk=modulo_id)
    iscrizione = get_object_or_404(IscrizioneCorso, studente=request.user.id, corso=modulo.corso)
    if modulo.quiz:
        messages.error(request, "Questo modulo richiede il superamento di un quiz."); return redirect('corso_dettaglio', corso_id=modulo.corso.id)
    if modulo.ordine > 1:
        try:
            modulo_precedente = Modulo.objects.get(corso=modulo.corso, ordine=modulo.ordine - 1)
            if not ProgressoModulo.objects.filter(iscrizione=iscrizione, modulo=modulo_precedente, completato=True).exists():
                messages.error(request, "Devi completare il modulo precedente."); return redirect('corso_dettaglio', corso_id=modulo.corso.id)
        except Modulo.DoesNotExist: pass
    progresso, created = ProgressoModulo.objects.get_or_create(iscrizione=iscrizione, modulo=modulo)
    if not progresso.completato: progresso.completato = True; progresso.save()
    messages.success(request, f"Modulo '{modulo.titolo}' completato!"); return redirect('corso_dettaglio', corso_id=modulo.corso.id)

# --- 4. Viste Test Finale / Quiz Modulo ---
@login_required(login_url='/auth/login/')
@user_passes_test(is_studente)
def take_test(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    domande = quiz.domande.all().prefetch_related('risposte')
    
    if request.method == 'POST':
        punteggio = 0
        totale_domande = domande.count()
        
        for domanda in domande:
            risposta_id = request.POST.get(f'domanda_{domanda.id}')
            if risposta_id:
                # CORREZIONE: usiamo 'is_corretta' come da tuo modello
                if domanda.risposte.filter(id=risposta_id, is_corretta=True).exists():
                    punteggio += 1
        
        percentuale = (punteggio / totale_domande * 100) if totale_domande > 0 else 0
        
        if percentuale >= quiz.punteggio_minimo:
            # Recuperiamo l'iscrizione dello studente
            from .models import IscrizioneCorso, ProgressoModulo
            iscrizione = get_object_or_404(IscrizioneCorso, studente=request.user, corso=quiz.modulo.corso)
            
            # Aggiorniamo o creiamo il progresso
            progresso, created = ProgressoModulo.objects.get_or_create(
                iscrizione=iscrizione, 
                modulo=quiz.modulo
            )
            progresso.completato = True
            progresso.data_completamento = timezone.now() # Registriamo quando è finito
            progresso.save()
            
            messages.success(request, f"Ottimo! Test superato con il {percentuale:.0f}%. Il modulo è sbloccato.")
        else:
            messages.error(request, f"Test non superato ({percentuale:.0f}%). Riprova per sbloccare il modulo successivo.")
            
        return redirect('dettaglio_corso', course_id=quiz.modulo.corso.id)

    return render(request, 'courses/take_test.html', {'quiz': quiz, 'domande': domande})
@login_required(login_url='/auth/login/')
@user_passes_test(is_studente)
@transaction.atomic
def submit_test(request, quiz_id):
    if request.method != 'POST': return redirect('dashboard_studente')
    quiz = get_object_or_404(Quiz, pk=quiz_id); corso_associato = quiz.modulo.corso
    iscrizione = get_object_or_404(IscrizioneCorso, studente=request.user.id, corso=corso_associato)
    domande = quiz.domande.all(); totale_domande = domande.count()
    if totale_domande == 0: messages.error(request, "Test non configurato."); return redirect('corso_dettaglio', corso_associato.id)
    punteggio_corretto = 0
    try:
        for domanda in domande:
            risposta_inviata_id = request.POST.get(f'domanda_{domanda.id}')
            if not risposta_inviata_id: raise ValueError(f"Risposta mancante per: {domanda.testo}")
            risposta_selezionata = Risposta.objects.get(pk=risposta_inviata_id)
            if risposta_selezionata.domanda == domanda and risposta_selezionata.is_corretta:
                punteggio_corretto += 1
        punteggio_percentuale = (punteggio_corretto / totale_domande) * 100
        punteggio_minimo = quiz.punteggio_minimo
        if punteggio_percentuale >= punteggio_minimo:
            # Quiz Modulo Superato
            modulo = quiz.modulo
            progresso, created = ProgressoModulo.objects.get_or_create(iscrizione=iscrizione, modulo=modulo)
            if not progresso.completato: progresso.completato = True; progresso.save()
            messages.success(request, f"Quiz '{modulo.titolo}' superato!"); 
            
            return redirect('corso_dettaglio', corso_associato.id)

        else:
            messages.error(request, f"Test non superato. Punteggio: {punteggio_percentuale:.0f}%. Minimo: {punteggio_minimo}%. Riprova."); return redirect('corso_dettaglio', corso_associato.id)
    except (Risposta.DoesNotExist, ValueError) as e:
        messages.error(request, f"Errore invio test: {e}. Riprova."); return redirect(request.path) 
        
@login_required(login_url='/login/')
@user_passes_test(is_studente)
def test_result(request, attestato_id):
    attestato = get_object_or_404(Attestato, pk=attestato_id, iscrizione__studente=request.user)
    context = {'attestato': attestato, 'corso': attestato.iscrizione.corso, 'studente': attestato.iscrizione.studente}
    return render(request, 'test_result.html', context)

# --- 5. Generazione PDF Attestato (Funzioni di base) ---
def link_callback(uri, rel):
    sUrl = settings.MEDIA_URL; sRoot = settings.MEDIA_ROOT  
    if uri.startswith(sUrl): path = os.path.join(sRoot, uri.replace(sUrl, ""))
    else: sUrl = settings.STATIC_URL; sRoot = settings.STATIC_ROOT
    if sRoot and uri.startswith(sUrl): path = os.path.join(sRoot, uri.replace(sUrl, ""))
    else: return uri 
    if not os.path.isfile(path): return None
    return path

def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src); html  = template.render(context_dict); result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result, link_callback=link_callback) 
    if not pdf.err: return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

@login_required(login_url='/login/') 
def genera_attestato_pdf(request, attestato_id): # <--- FUNZIONE DEFINITA QUI
    """ VISTA PRINCIPALE PER GENERARE E ARCHIVIARE IL PDF DELL'ATTESTATO """
    attestato = get_object_or_404(Attestato, pk=attestato_id)
    if not request.user.is_staff and attestato.iscrizione.studente != request.user:
        messages.error(request, "Non autorizzato."); return redirect('dashboard_studente')

    # Recupero configurazioni
    try:
        config_globale = ImpostazioniSito.objects.get(pk=1)
    except ImpostazioniSito.DoesNotExist:
        messages.error(request, "Configurazione sito mancante."); return redirect('dashboard_studente')

    studente = attestato.iscrizione.studente
    azienda = studente.azienda
    corso_completato = attestato.iscrizione.corso 
    
    # Placeholder per il recupero di logo e colore (Adatta ai tuoi modelli)
    logo_da_usare = (azienda and azienda.logo_attestato) or config_globale.logo_principale
    colore = config_globale.colore_primario
    config_testi = {'attestato_titolo': "ATTESTATO DI COMPLETAMENTO", 'attestato_introduzione': "certifica che...", 'attestato_corpo': "ha completato il corso"} # Sostituisci con i campi reali del tuo ImpostazioniSito
    
    logo_base64 = None
    if logo_da_usare and hasattr(logo_da_usare, 'path'):
        try:
            with open(logo_da_usare.path, "rb") as image_file:
                logo_data = image_file.read()
                logo_base64 = base64.b64encode(logo_data).decode("utf-8")
        except IOError: pass
            
    context = {'attestato': attestato, 'corso': corso_completato, 'studente': studente, 'config': config_testi, 'logo_base64': logo_base64, 'colore_primario': colore}
    pdf = render_to_pdf('attestato_template.html', context)
    
    if pdf:
        try:
            if azienda:
                cat_attestati, _ = CategoriaDocumento.objects.get_or_create(nome="Attestati di Formazione")
                doc_nome = f"Attestato: {corso_completato.nome} - {studente.get_full_name()}"
                doc_aziendale, doc_created = DocumentoAziendale.objects.get_or_create(azienda=azienda, categoria=cat_attestati, nome=doc_nome)
                
                pdf_filename = f"Attestato_{studente.username}_{corso_completato.id}.pdf"
                pdf_content_file = ContentFile(pdf.content, name=pdf_filename)
                
                # Salvataggio della Versione
                VersioneDocumento.objects.create(documento=doc_aziendale, file=pdf_content_file, note_versione=f"Generato il {timezone.now().strftime('%d/%m/%Y')}", caricato_da=studente)
                
        except Exception as e:
            print(f"--- ERRORE Salvataggio Attestato in Gestione Documentale: {e} ---")
            
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"Attestato_{attestato.iscrizione.corso.nome}_{studente.username}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    messages.error(request, "Impossibile generare il PDF."); return redirect('test_result', attestato_id=attestato.id)

# --- 6. VISTE CUSTOM PER IL LOGIN/PROFILO (USATE IN user_auth/views.py) ---

@login_required(login_url='/login/')
@user_passes_test(is_profilo_user)
def profilo_studente(request):
    # Logica Profilo
    password_form = PasswordChangeForm(request.user)
    profilo_form = ProfiloStudenteForm(instance=request.user)
    azienda_form = None
    if request.user.ruolo == 'REFERENTE':
        if not request.user.azienda: messages.error(request, _("Utente non associato a un'azienda.")); return redirect('login')
        azienda_form = AziendaProfileForm(instance=request.user.azienda)

    if request.method == 'POST':
        # Logica POST
        if 'submit_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save(); update_session_auth_hash(request, user); messages.success(request, 'Password cambiata!'); return redirect('profilo_studente')
            else: messages.error(request, 'Errore modifica password.')
        
        elif 'submit_profilo' in request.POST:
            profilo_form = ProfiloStudenteForm(request.POST, instance=request.user)
            if profilo_form.is_valid(): profilo_form.save(); messages.success(request, 'Profilo aggiornato!'); return redirect('profilo_studente')

        elif 'submit_azienda' in request.POST and request.user.ruolo == 'REFERENTE':
            azienda_form = AziendaProfileForm(request.POST, request.FILES, instance=request.user.azienda)
            if azienda_form.is_valid(): azienda_form.save(); messages.success(request, 'Dati azienda aggiornati.'); return redirect('profilo_studente')

    if request.user.ruolo == 'CONSULENTE': dashboard_url = 'dashboard_consulente'
    elif request.user.ruolo == 'REFERENTE': dashboard_url = 'dashboard_compliance'
    else: dashboard_url = 'dashboard_studente'
    
    context = {'profilo_form': profilo_form, 'password_form': password_form, 'azienda_form': azienda_form, 'dashboard_url': dashboard_url}
    return render(request, 'profilo_studente.html', context)
@login_required
def avvia_scansione_deashed(request, azienda_id):
    azienda = get_object_or_404(Azienda, pk=azienda_id)
    dominio = request.GET.get('dominio_manuale')

    # Se il dominio non c'è, rimaniamo sulla pagina e attiviamo il modulo
    if not dominio:
        return render(request, 'compliance/analisi_vulnerabilita.html', {
            'azienda': azienda,
            'richiedi_dominio': True  # Questo è il "segnale" per il template
        })

    # Se il dominio c'è, procediamo con la logica tecnica
    # ... resto del codice ...

    # Se arriviamo qui, abbiamo il dominio e possiamo chiamare l'API
    # risultati = search_dehashed(dominio)
    
    messages.success(request, f"Scansione avviata per: {dominio}")
    return render(request, 'compliance/analisi_vulnerabilita.html', {
        'azienda': azienda,
        'risultati': "Risultati simulati per " + dominio # Sostituisci con i dati reali
    })
from django.shortcuts import render, get_object_or_404
from .utils import get_dns_report  # Importiamo la funzione creata prima
from user_auth.models import Azienda # Assicurati che l'import sia corretto

def analisi_dns_view(request, azienda_id):
    """
    Gestisce la pagina dedicata all'analisi DNS di un'azienda. 🌐
    """
    # 1. Recuperiamo l'azienda specifica
    azienda = get_object_or_404(Azienda, id=azienda_id)
    
    # 2. Leggiamo il dominio dal parametro 'domain' nell'URL (es: ?domain=google.it)
    dominio = request.GET.get('domain')
    risultati = None
    errore = None

    # 3. Se l'utente ha fornito un dominio, facciamo l'analisi
    if dominio:
        dati_api = get_dns_report(dominio)
        
        # Controlliamo se l'API ha restituito un errore
        if isinstance(dati_api, dict) and "error" in dati_api:
            errore = dati_api["error"]
        else:
            risultati = dati_api

    # 4. Passiamo tutto al template HTML
    context = {
        'azienda': azienda,
        'dominio': dominio,
        'risultati': risultati,
        'errore': errore,
    }
    return render(request, 'analisi_dns.html', context)
def dettaglio_corso(request, course_id):
    # 1. Recuperiamo il corso e l'iscrizione dello studente
    corso = get_object_or_404(Corso, id=course_id)
    iscrizione = get_object_or_404(IscrizioneCorso, studente=request.user, corso=corso)
    
    # 2. Recuperiamo tutti i moduli del corso in ordine
    moduli_queryset = corso.moduli.all().order_by('ordine')
    
    moduli_list = []
    tutti_completati = True
    
    # 3. Costruiamo la lista con la logica di sblocco (propedeuticità)
    # Un modulo è sbloccato se è il primo o se quello precedente è completato
    ultimo_completato = True 
    
    for modulo in moduli_queryset:
        # Controlliamo il progresso per questo specifico modulo
        progresso, created = ProgressoModulo.objects.get_or_create(
            iscrizione=iscrizione, 
            modulo=modulo
        )
        
        is_completato = progresso.completato
        # Sbloccato se il precedente era finito
        is_sbloccato = ultimo_completato 
        
        if not is_completato:
            tutti_completati = False
        
        # Prepariamo i media con le icone corrette per il template
        media_items = []
        for m in modulo.media.all():
            icon_type = 'file'
            if m.file.name.lower().endswith('.pdf'):
                icon_type = 'pdf'
            elif m.file.name.lower().endswith(('.mp4', '.mov', '.avi')):
                icon_type = 'video'
            
            media_items.append({
                'titolo': m.nome,
                'file': m.file,
                'icon_type': icon_type
            })

        moduli_list.append({
            'modulo': modulo,
            'is_completato': is_completato,
            'is_sbloccato': is_sbloccato,
            'media_items': media_items,
            'ha_quiz': hasattr(modulo, 'quiz'),
        })
        
        # Il prossimo sarà sbloccato solo se questo è completato
        ultimo_completato = is_completato

    # --- Inizio blocco generazione attestato ---
    attestato = Attestato.objects.filter(iscrizione=iscrizione).first()

    if tutti_completati and not attestato:
        # Tutto ciò che segue deve essere indentato (spostato a destra)
        import uuid
        codice = str(uuid.uuid4()).split('-')[0].upper()
        attestato = Attestato.objects.create(
            iscrizione=iscrizione,
            codice_univoco=f"CERT-{corso.id}-{codice}"
        )
        # Aggiorniamo anche lo stato dell'iscrizione
        iscrizione.completato = True
        iscrizione.data_completamento = timezone.now()
        iscrizione.save()
    # --- Fine blocco ---

    context = {
        'corso': corso,
        'moduli_list': moduli_list,
        'tutti_moduli_completati': tutti_completati,
        'attestato_ottenuto': attestato,
    }
    
    return render(request, 'corso_dettaglio.html', context)
def completa_modulo(request, modulo_id):
    # Logica per segnare il modulo come completato nel database
    return redirect(request.META.get('HTTP_REFERER', 'dashboard_studente'))

def take_test(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    domande = quiz.domande.all().prefetch_related('risposte')
    
    if request.method == 'POST':
        punteggio_ottenuto = 0
        totale_domande = domande.count()
        
        # 1. Calcolo del punteggio
        for domanda in domande:
            # Recuperiamo l'ID della risposta inviata dall'utente per questa domanda
            risposta_scelta_id = request.POST.get(f'domanda_{domanda.id}')
            
            if risposta_scelta_id:
                # Verifichiamo se la risposta scelta è quella segnata come 'is_corretta'
                is_giusta = domanda.risposte.filter(id=risposta_scelta_id, is_corretta=True).exists()
                if is_giusta:
                    punteggio_ottenuto += 1
        
        # 2. Calcolo percentuale
        percentuale = (punteggio_ottenuto / totale_domande * 100) if totale_domande > 0 else 0
        
        # 3. Verifica superamento e salvataggio
        if percentuale >= quiz.punteggio_minimo:
            from .models import IscrizioneCorso, ProgressoModulo
            
            # Recuperiamo l'iscrizione dello studente
            iscrizione = get_object_or_404(IscrizioneCorso, studente=request.user, corso=quiz.modulo.corso)
            
            # Aggiorniamo il progresso del modulo specifico
            progresso, created = ProgressoModulo.objects.get_or_create(
                iscrizione=iscrizione, 
                modulo=quiz.modulo
            )
            progresso.completato = True
            progresso.data_completamento = timezone.now()
            progresso.save()
            
            messages.success(request, f"Complimenti! Hai superato il test con il {percentuale:.0f}% e sbloccato il modulo successivo.")
        else:
            messages.error(request, f"Punteggio insufficiente ({percentuale:.0f}%). Riprova per sbloccare il prossimo modulo.")
            
        return redirect('dettaglio_corso', course_id=quiz.modulo.corso.id)

    context = {
        'quiz': quiz,
        'domande': domande,
    }
    return render(request, 'courses/take_test.html', context)
def genera_attestato_pdf(request, attestato_id):
    attestato = get_object_or_404(Attestato, id=attestato_id)
    iscrizione = attestato.iscrizione
    studente = iscrizione.studente
    corso = iscrizione.corso
    
    # Recuperiamo il logo dalle impostazioni
    config = ImpostazioniSito.objects.first()
    logo_path = None
    if config and config.logo_principale:
        # Costruiamo il percorso assoluto sul disco per xhtml2pdf
        logo_path = config.logo_principale.path

    context = {
        'studente': studente.get_full_name() or studente.username,
        'corso': corso.nome,
        'data': attestato.data_rilascio,
        'codice': attestato.codice_univoco,
        'logo_path': logo_path,
        'colore_primario': config.colore_primario if config else '#005a9c',
    }

    template = get_template('courses/attestato_pdf.html')
    html = template.render(context)

    result = BytesIO()
    # xhtml2pdf ha bisogno di link_callback per gestire i percorsi dei file (immagini)
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        filename = f"Attestato_{studente.username}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    return HttpResponse("Errore PDF", status=400)
@login_required
def registro_aziendale_view(request):
    # 1. Recuperiamo l'azienda collegata al referente (User -> AdminReferente -> Azienda)
    # Nota: uso getattr o un controllo per sicurezza
    try:
        azienda_referente = request.user.admin_referente.azienda
    except AttributeError:
        messages.error(request, "Non sei autorizzato a vedere questo registro.")
        return redirect('dashboard_home') # O la tua home

    # 2. Se il referente invia il form per un inserimento manuale
    if request.method == 'POST':
        titolo = request.POST.get('titolo_corso')
        dipendente_id = request.POST.get('studente_id')
        data = request.POST.get('data_completamento')
        ore = request.POST.get('durata_ore')
        
        # Salvataggio manuale
        RegistroFormazione.objects.create(
            azienda=azienda_referente,
            studente_id=dipendente_id, # ID dell'utente selezionato
            titolo_corso=titolo,
            data_completamento=data,
            durata_ore=ore,
            fonte='M', # Identificato come manuale
            note=request.POST.get('note', "Inserimento manuale da referente")
        )
        messages.success(request, "Corso esterno aggiunto al registro con successo.")
        return redirect('courses:registro_aziendale')

    # 3. Carichiamo tutto il registro (automatici + manuali) di quell'azienda
    registro = RegistroFormazione.objects.filter(azienda=azienda_referente).order_by('-data_completamento')
    
    # 4. Passiamo anche la lista dei dipendenti dell'azienda per il menu a tendina del form
    dipendenti = azienda_referente.dipendenti.all() # Assicurati che esista il related_name 'dipendenti' in CustomUser

    context = {
        'registro': registro,
        'dipendenti': dipendenti,
        'azienda': azienda_referente
    }
    
    return render(request, 'dashboard/registro_formazione.html', context)
@login_required
def esporta_registro_excel(request):
    try:
        azienda = request.user.admin_referente.azienda
    except AttributeError:
        return HttpResponse("Non autorizzato", status=403)

    # Creazione Workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Registro Formazione"

    # Intestazioni
    headers = ['Dipendente', 'Corso', 'Data Completamento', 'Ore', 'Fonte', 'Note']
    ws.append(headers)

    # Dati
    registro = RegistroFormazione.objects.filter(azienda=azienda).order_by('-data_completamento')
    for voce in registro:
        ws.append([
            voce.studente.get_full_name(),
            voce.titolo_corso,
            voce.data_completamento.strftime('%d/%m/%Y'),
            voce.durata_ore,
            "Piattaforma" if voce.fonte == 'A' else "Manuale",
            voce.note or ""
        ])

    # Formattazione minima (opzionale: larghezza colonne)
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except: pass
        ws.column_dimensions[column].width = max_length + 2

    # Preparazione risposta
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=Registro_Formazione_{azienda.nome}.xlsx'
    wb.save(response)
    return response
@login_required
def elimina_voce_registro(request, voce_id):
    # Recuperiamo la voce assicurandoci che appartenga all'azienda del referente
    try:
        azienda_referente = request.user.admin_referente.azienda
        voce = get_object_or_404(RegistroFormazione, id=voce_id, azienda=azienda_referente)
        
        # Sicurezza: permettiamo di eliminare solo i record manuali
        if voce.fonte == 'M':
            titolo = voce.titolo_corso
            voce.delete()
            messages.success(request, f"La voce '{titolo}' è stata eliminata correttamente.")
        else:
            messages.error(request, "Non è possibile eliminare una voce generata automaticamente dal sistema.")
            
    except AttributeError:
        messages.error(request, "Azione non consentita.")
    
    return redirect('courses:registro_aziendale')

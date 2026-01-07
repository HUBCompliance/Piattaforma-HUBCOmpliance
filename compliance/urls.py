from django.urls import path
from . import views

urlpatterns = [
    # Consulente
    path('consulente/', views.dashboard_consulente, name='dashboard_consulente'), 
    path('consulente/add-referente/<int:azienda_id>/', views.consulente_add_referente, name='consulente_add_referente'),
    path('consulente/crea-compito/<int:azienda_id>/', views.consulente_crea_compito, name='consulente_crea_compito'),
    path('consulente/gestisci-moduli/<int:azienda_id>/', views.consulente_gestisci_moduli, name='consulente_gestisci_moduli'),

    # Dashboard
    path('dashboard/', views.dashboard_compliance, name='dashboard_compliance'),

    # Audit
    path('audit/create/', views.audit_create, name='audit_create'),
    path('audit/checklist/<int:session_pk>/', views.audit_checklist, name='audit_checklist'),
    path('audit/export-pdf/<int:session_pk>/', views.export_audit_pdf, name='export_audit_pdf'),
    path('audit/archive/<int:session_pk>/', views.archive_audit_to_repository, name='archive_audit_to_repository'),
    path('audit/export-pdf/<int:session_pk>/', views.export_audit_pdf, name='export_audit_pdf'),

    # Security Checklist
    path('security-checklist/', views.security_checklist_view, name='security_checklist_init'),
    path('security-checklist/<int:audit_id>/', views.security_checklist_view, name='security_checklist_view'),
    path('security-checklist/<int:audit_id>/salva-area/', views.salva_area_security, name='salva_area_security'),
    path('security/audit/<int:audit_id>/pdf/', views.export_security_pdf, name='export_security_pdf'),
    path('import/controls/', views.import_controls_excel, name='import_controls_excel'),
    path('import/download-template/', views.download_template_excel, name='download_template_excel'),
    path('security-checklist/init/', views.security_checklist_init, name='security_checklist_init'),
    path('security-checklist/<int:audit_id>/', views.security_checklist_view, name='security_checklist_view'),

    # Trattamenti
    path('trattamenti/nuovo/', views.trattamento_create, name='trattamento_create'),
    path('trattamenti/modifica/<int:pk>/', views.trattamento_update, name='trattamento_update'),
    path('trattamenti/checklist/<int:pk>/', views.checklist_trattamento, name='checklist_trattamento'),
    path('trattamenti/export/excel/', views.export_trattamenti_excel, name='export_trattamenti_excel'),
    path('trattamenti/', views.trattamento_list, name='trattamento_list'), 
    path('asset/', views.asset_list, name='asset_list'),
    
    # Documenti
    path('documenti/', views.documento_list, name='documento_list'),
    path('documenti/nuovo/', views.documento_create, name='documento_create'),
    path('documenti/dettaglio/<int:doc_pk>/', views.documento_dettaglio, name='documento_dettaglio'),
    path('documenti/versione/carica/<int:doc_pk>/', views.versione_create, name='versione_create'),
    path('documenti/template/download/<int:template_pk>/', views.download_template, name='download_template'),
    
    # Incidenti
    path('incidenti/', views.incidente_list, name='incidente_list'),
    path('incidenti/nuovo/', views.incidente_create, name='incidente_create'),
    path('incidenti/dettaglio/<int:pk>/', views.incidente_dettaglio, name='incidente_dettaglio'),

    # Formazione
    path('formazione/', views.gestione_formazione, name='gestione_formazione'),
    path('formazione/studente/nuovo/', views.studente_create, name='studente_create'),
    path('formazione/studente/modifica/<int:studente_pk>/', views.studente_update, name='studente_update'),
    path('formazione/studente/importa-excel/', views.referente_import_excel, name='referente_import_excel'),
    
    # Richieste
    path('richieste/', views.richiesta_list, name='richiesta_list'),
    path('richieste/nuova/', views.richiesta_create, name='richiesta_create'),
    path('richieste/dettaglio/<int:pk>/', views.richiesta_dettaglio, name='richiesta_dettaglio'),
    path('richieste/chiudi/<int:pk>/', views.richiesta_chiudi, name='richiesta_chiudi'),

    # Compiti
    path('compito/completa/<int:compito_pk>/', views.compito_completa, name='compito_completa'),
    
    # Asset
    path('asset/', views.asset_list, name='asset_list'),
    path('asset/nuovo/', views.asset_create, name='asset_create'),
    path('asset/modifica/<int:pk>/', views.asset_update, name='asset_update'),
    path('software/nuovo/', views.software_create, name='software_create'),
    path('software/modifica/<int:pk>/', views.software_update, name='software_update'),
    path('asset/export/excel/', views.export_asset_excel, name='export_asset_excel'),

    # Organigramma
    path('organigramma/', views.organigramma_view, name='organigramma_view'),
    path('organigramma/nuovo/', views.organigramma_create, name='organigramma_create'),
    path('organigramma/elimina/<int:pk>/', views.organigramma_delete, name='organigramma_delete'),

    # TIA
    path('tia/', views.tia_list, name='tia_list'),
    path('tia/nuova/', views.tia_create, name='tia_create'),
    path('tia/dettaglio/<int:pk>/', views.tia_detail, name='tia_detail'),
    path('tia/download-ai/<int:pk>/', views.tia_generate_doc_ai, name='tia_generate_doc_ai'),
    
    # Videosorveglianza
    path('videosorveglianza/', views.video_list, name='video_list'),
    path('videosorveglianza/nuova/', views.video_create, name='video_create'),
    path('videosorveglianza/dettaglio/<int:pk>/', views.video_detail, name='video_detail'),
    path('videosorveglianza/download-doc/<int:pk>/<str:tipo_doc>/', views.download_video_doc, name='download_video_doc'),
    path('videosorveglianza/elimina/<int:pk>/', views.video_delete, name='video_delete'),
    
    # Rischi
    path('rischi-guida/', views.analisi_rischi_guida, name='analisi_rischi_guida'),

    # Chat AI
    path('gemini-chat/', views.gemini_chat, name='gemini_chat'),
    
    # CSIRT (Modulo 7)
    path('csirt/dashboard/', views.csirt_dashboard, name='csirt_dashboard'),
    path('csirt/notifica/nuova/', views.csirt_notifica_create, name='csirt_notifica_create'),
    path('csirt/download-nomina/', views.download_csirt_nomina, name='download_csirt_nomina'),
    path('csirt/notifica/<int:pk>/dettaglio/', views.csirt_notifica_dettaglio, name='csirt_notifica_dettaglio'),
    
    
    # === QUESTA È LA RIGA MANCANTE ===
    path('csirt/upload-template/', views.csirt_upload_template, name='csirt_upload_template'),
    path('csirt/config-rete/', views.configurazione_rete_view, name='configurazione_rete_view'),
    path('csirt/ai-query/', views.csirt_ai_query, name='csirt_ai_query'),
    path('csirt/dehashed-query/', views.csirt_dehashed_query, name='csirt_dehashed_query'),
    path('csirt/pentest-tools-query/', views.csirt_pentest_tools_query, name='csirt_pentest_tools_query'),

    # Strumenti Tecnici per il Consulente
    path('consulente/analisi-vulnerabilita/', views.analisi_vulnerabilita_view, name='analisi_vulnerabilita_view'),
    path('consulente/monitoraggio-eventi/', views.monitoraggio_eventi_view, name='monitoraggio_eventi_view'),
    path('consulente/alert-configurazione/', views.alert_configurazione, name='alert_configurazione'),
    ]
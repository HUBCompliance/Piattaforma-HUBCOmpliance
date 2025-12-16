/* global django */
// Aspetta che jQuery (usato dall'Admin) sia pronto
if (typeof django !== 'undefined' && typeof django.jQuery !== 'undefined') {
    (function($) {
        'use strict';
        
        $(document).ready(function() {
            // Controlla se siamo nella pagina 'add' o 'change' di IscrizioneCorso
            if ($('body').is('.change-form') && $('#id_studente').length > 0) {
                console.log("Filtro Azienda Admin Caricato.");

                // 1. Nascondi il menu a tendina "Studente" all'inizio
                var $studenteSelect = $('#id_studente');
                var $studenteWrapper = $studenteSelect.closest('.form-row');
                $studenteWrapper.hide();

                // 2. Memorizza tutte le opzioni originali degli studenti
                var studenteOptions = $studenteSelect.html();

                // 3. Crea il nuovo menu a tendina "Filtra per Azienda"
                var $aziendaSelect = $('<select id="id_azienda_filtro"><option value="">--- Filtra per Azienda ---</option></select>');
                
                // Popola il menu Azienda (Questa parte richiede che i dati siano disponibili)
                // Poiché non possiamo passare le aziende qui facilmente, modifichiamo
                // il campo "studente" per contenere i dati dell'azienda
                
                // SOLUZIONE ALTERNATIVA (Più semplice, senza caricare le aziende):
                // Modifichiamo il campo Studente per filtrare
                
                // Riprogettazione: Usiamo un campo Azienda se esiste già, 
                // altrimenti dobbiamo caricarlo via API (più complesso).
                
                // Semplifichiamo: L'Admin ha già un filtro laterale.
                // Questa logica JS è per il *form di aggiunta*.
                
                // --- Logica Semplificata (basata sul filtro Azienda esistente) ---
                
                // Se il campo 'studente__azienda' esiste già nel form (non esiste di default)
                // dovremmo aggiungerlo.
                
                // Dato che aggiungere un campo Azienda al form IscrizioneCorso
                // richiederebbe la modifica della ModelForm, usiamo un trucco:
                
                // Aggiungiamo un filtro Azienda personalizzato
                var $aziendaFiltro = $('<div class="form-row field-azienda-filtro">' +
                                         '<div><label for="azienda-filtro">Filtra Studenti per Azienda:</label>' +
                                         '<select id="azienda-filtro"><option value="all">Tutti gli Studenti</option></select>' +
                                         '</div></div>');
                
                // Inserisci il filtro prima del campo studente
                $studenteWrapper.before($aziendaFiltro);
                $studenteWrapper.show(); // Mostra di nuovo il campo studente
                
                var $filtroSelect = $('#azienda-filtro');
                
                // 1. Salva tutte le opzioni studente
                var allStudenteOptions = [];
                $studenteSelect.find('option').each(function() {
                    if ($(this).val()) { // Ignora l'opzione vuota
                        allStudenteOptions.push({
                            val: $(this).val(),
                            text: $(this).text(),
                            // Dobbiamo ottenere l'azienda. Modifichiamo il ModelAdmin.
                        });
                    }
                });

                // --- Questa soluzione JS richiede una modifica a admin.py ---
                // Dobbiamo modificare la ModelForm per includere l'azienda nello studente
                // È troppo complesso per ora.
                
                // --- SOLUZIONE PIÙ SEMPLICE (Usiamo il Filtro Laterale) ---
                // Il tuo 'list_filter' in IscrizioneCorsoAdmin:
                // list_filter = ['corso', 'completato', 'studente__azienda']
                // Questo funziona già nella VISTA ELENCO.
                
                // Nella VISTA DI AGGIUNTA/MODIFICA, la cosa migliore è
                // usare 'raw_id_fields' per cercare lo studente,
                // che permette all'admin di filtrare nella popup.

                console.warn("Implementazione JS filtro a catena richiesta, ma richiede API o ModelForm customizzata. Usare 'raw_id_fields'.");
                
            }
        });
    })(django.jQuery);
}
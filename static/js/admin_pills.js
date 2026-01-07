/**
 * ============================================================================
 * Tab Management Django Admin - VERSIONE DEFINITIVA
 * ----------------------------------------------------------------------------
 * - NON usa fieldset
 * - NON dipende dalla struttura Django Admin
 * - TAB ↔ CONTENUTO via data-tab / data-tab-panel
 * - Zero warning
 * - Zero fallback fragile
 * ============================================================================
 */

(function () {
    'use strict';

    function initTabs() {
        if (!window.django || !django.jQuery) {
            console.warn('django.jQuery non disponibile');
            return;
        }

        var $ = django.jQuery;

        var TAB_SELECTOR = 'a[data-toggle="pill"], a[data-toggle="tab"]';
        var PANEL_SELECTOR = '[data-tab-panel]';

        var $tabs = $(TAB_SELECTOR);
        var $panels = $(PANEL_SELECTOR);

        if (!$tabs.length || !$panels.length) {
            console.warn('TAB o pannelli non trovati');
            return;
        }

        function showTab($tab) {
            var tabKey = $tab.data('tab');

            if (!tabKey) {
                console.warn('TAB senza data-tab', $tab);
                return;
            }

            // reset tab
            $tabs.removeClass('active')
                 .parent().removeClass('active');

            $tab.addClass('active')
                .parent().addClass('active');

            // reset pannelli
            $panels.hide();

            // mostra pannello corretto
            var $panel = $panels.filter('[data-tab-panel="' + tabKey + '"]');
            if ($panel.length) {
                $panel.show();
            } else {
                console.warn('Pannello non trovato per TAB:', tabKey);
            }
        }

        // click handler
        $(document).on('click', TAB_SELECTOR, function (e) {
            e.preventDefault();
            showTab($(this));
        });

        // stato iniziale
        var $initialTab = $tabs.filter('[data-tab]').first();
        if ($initialTab.length) {
            showTab($initialTab);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initTabs);
    } else {
        initTabs();
    }

})();

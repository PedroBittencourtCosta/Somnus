// core/static/core/js/hide_alternativas.js
(function() {
    'use strict';
    // O Django Admin usa django.jQuery em vez de $
    const $ = window.django ? django.jQuery : null;

    if (!$) return; // Se o jQuery não estiver pronto, sai da função

    $(document).ready(function() {
        const tipoSelect = $('#id_tipo');
        // O ID padrão do inline no Django Admin segue o padrão: id_do_modelo_set-group
        const alternativaGroup = $('#alternativa_set-group');

        function toggleAlternativas(value) {
            if (value === 'TX') { // 'TX' é o valor de Texto Livre
                alternativaGroup.hide();
            } else {
                alternativaGroup.show();
            }
        }

        if (tipoSelect.length) {
            // Executa ao mudar a opção
            tipoSelect.on('change', function() {
                toggleAlternativas($(this).val());
            });
            // Executa ao carregar a página (caso já venha selecionado)
            toggleAlternativas(tipoSelect.val());
        }
    });
})();
// Default options for JqueryUI
$(document).ready(function () {
    $.extend($.ui.dialog.prototype.options, {
        closeOnEscape: true,
        autoOpen: false,
        close: function() {
            // Permit scrolling after closing
            $('body').removeClass('stop-scrolling');
        },
        open: function() {
            // Forbid scrolling after opening
            $('body').addClass('stop-scrolling');

            // "Close" and "Download" buttons as Bootstrap buttons
            $('.ui-dialog')
                .find('.ui-button-text-only')
                .addClass('btn btn-primary')
                .removeClass('ui-state-default');

            // Blur all
            $('.ui-dialog').find('input, select, button').blur();
        }
    });
});

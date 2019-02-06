$(document).ready(function () {
    // Prevent CSS conflict with Bootstrap
    // $.fn.button.noConflict();

    var overwrite_confirm = $("#overwrite_confirm");
    var overwrite_was_confirmed = false;

    var all_submits = $(':submit');
    var submit_button = $('#submit');

    overwrite_confirm.dialog({
        height:250,
        modal: true,
        buttons: [
        {
            text: 'Overwrite',
            id: 'overwrite_confirm_submit_button',
            click: function() {
                overwrite_was_confirmed = true;
                all_submits.removeAttr("disabled");
                submit_button.trigger('click');
                all_submits.attr('disabled', 'disabled');
                // Disable all buttons during submission
                $('.ui-button').button('disable');
                // Change cursor to thinking
                $('.ui-front').css('cursor', 'wait');
            }
        },
        {
            text: 'Cancel',
            click: function() {
               $(this).dialog("close");
            }
        }],
        close: function() {
            $.ui.dialog.prototype.options.close();
            all_submits.removeAttr("disabled");
        },
        open: function() {
            // var dialog_submit_button = $('#overwrite_confirm_submit_button');
            $.ui.dialog.prototype.options.open();
            // dialog_submit_button.button('disable');
            //
            // setTimeout(function() {
            //     dialog_submit_button.button('enable');
            //     dialog_submit_button.focus();
            // }, 1500);
        }
    });
    overwrite_confirm.removeProp('hidden');

    // TODO MAKE SURE THIS DOES NOT INTERRUPT OTHER TRIGGERS
    $('form').submit(function(event) {
        if (!overwrite_was_confirmed) {
            // Stop propagation
            event.preventDefault();
            overwrite_confirm.dialog('open');
        }
    });
});

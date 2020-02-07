$(document).ready(function () {
    var history_dialog = $('#history_dialog');
    var history_dialog_button = $('#open_history_dialog');

    history_dialog.dialog({
        width: 800,
        height: 800,
        buttons: [
            {
                text: 'Close',
                click: function() {
                    $(this).dialog("close");
                }
            }
        ],
    });
    history_dialog.removeProp('hidden');

    history_dialog_button.click(function() {
        history_dialog.dialog('open');
    })
});

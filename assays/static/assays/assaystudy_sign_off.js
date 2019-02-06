$(document).ready(function() {
    var sign_off_confirm = $("#sign_off_confirm");

    var sign_off_confirm_warning = $('#sign_off_confirm_warning');

    var mark_reviewed_buttons = $('.mark_reviewed_button_group');

    var signed_off_selector = null;
    var mark_reviewed_label = null;
    var mark_reviewed_check = null;

    var mark_reviewed_label_text = '';
    var sign_off_confirm_warning_html = '';

    var dialog_title = 'Study Approval';

    function set_labels(owner) {
        if (signed_off_selector.prop('checked')) {
            // mark_reviewed_check.show();
            if (owner) {
                mark_reviewed_label_text = 'Click Here to Sign Off on this Study';
                sign_off_confirm_warning_html = 'Removing the Sign Off will allow permitted users to continue editing the Study\'s data.' +
                    '<br><br>It will also keep the data hidden from external users.' +
                    '<br><br>Are you sure you want to change the Sign Off status?';
            }
            else {
                mark_reviewed_label_text = 'Click Here to Approve this Study for Release';
                sign_off_confirm_warning_html = 'Removing the Approval will prevent consortium viewers from viewing this Study\'s data.' +
                    '<br><br>Are you sure you want to change the Approval status?';
            }
        }
        else {
            // mark_reviewed_check.hide();
            if (owner) {
                mark_reviewed_label_text = 'Click Here to Remove Sign Off';
                sign_off_confirm_warning_html = 'Signing Off will prevent anyone, including you, from editing this Study and the data associated with it.' +
                    '<br><br>Signing Off will also allow consortium viewers to view this Study\'s data (granted all Stakeholders Approve as well).' +
                    '<br><br>Additionally, after one year\'s time, the Study will become publicly available.' +
                    '<br><br>Are you sure you want to change the Sign Off status?';
            }
            else {
                mark_reviewed_label_text = 'Click Here to Revoke your Approval';
                sign_off_confirm_warning_html = 'Approving will allow consortium viewers to view this Study\'s data (granted all other Stakeholders Approve as well).' +
                    '<br><br>Additionally, after one year\'s time, the Study will become publicly available.' +
                    '<br><br>Are you sure you want to change the Approval status?';
            }
        }
    }

    function apply_labels() {
        if (signed_off_selector.prop('checked')) {
            mark_reviewed_check.show();
        }
        else {
            mark_reviewed_check.hide();
        }

        mark_reviewed_label.text(mark_reviewed_label_text);
    }

    function get_warning() {
        sign_off_confirm_warning.html(sign_off_confirm_warning_html);
    }

    sign_off_confirm.dialog({
        title: dialog_title,
        height:600,
        width:450,
        modal: true,
        buttons: [
        {
            text: 'Yes',
            id: 'sign_off_confirm_submit_button',
            click: function() {
                signed_off_selector.prop('checked', !signed_off_selector.prop('checked'));
                apply_labels();
                $(this).dialog('close');
            }
        },
        {
            text: 'Cancel',
            click: function() {
               $(this).dialog("close");
            }
        }],
        open: function() {
            get_warning();
            $.ui.dialog.prototype.options.open();
        }
    });
    sign_off_confirm.removeProp('hidden');

    mark_reviewed_buttons.click(function() {
        signed_off_selector = $(this).parent().parent().find('input');
        mark_reviewed_label = $(this).parent().parent().find('.mark_reviewed_label');
        mark_reviewed_check = $(this).parent().parent().find('.mark_reviewed_check');

        // Set initial labels
        set_labels($(this).hasClass('owner'));

        sign_off_confirm.dialog('open');
    });

    // Contrived, hide all checks:
    $('.mark_reviewed_check').hide();
});

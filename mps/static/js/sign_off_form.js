$(document).ready(function() {
    // Prevent CSS conflict with Bootstrap
    // $.fn.button.noConflict();

    var sign_off_confirm = $("#sign_off_confirm");
    var study_submit = $('#study_submit').val();

    var sign_off_confirm_warning = $('#sign_off_confirm_warning');
    var mark_reviewed_label = $('#mark_reviewed_label');
    var mark_reviewed_check = $('#mark_reviewed_check');
    var mark_reviewed_button_group = $('#mark_reviewed_button_group');

    var signed_off_selector = $('#id_signed_off');

    // var dialog_title = '';
    var dialog_title = 'Entry Validation';

    // if (study_submit) {
    //     dialog_title = 'Study Sign Off';
    // }
    // else {
    //     dialog_title = 'Entry Validation';
    // }

    // function set_labels() {
    //     if (signed_off_selector.prop('checked')) {
    //         mark_reviewed_check.show();
    //         if (study_submit) {
    //             mark_reviewed_label.text('Click Here to Remove Sign Off');
    //             sign_off_confirm_warning.html(
    //                 'Removing the Sign Off will again allow users to edit this Study and the data associated with it.' +
    //                 '<br><br>Are you sure you want to change the Sign Off status?'
    //             );
    //
    //         }
    //         else {
    //             mark_reviewed_label.text('Click Here to Remove Validated Mark');
    //             sign_off_confirm_warning.html(
    //                 'If you continue, this entry will no longer be marked as Validated.' +
    //                 '<br><br>Are you sure you want to change the validated status?'
    //             );
    //         }
    //     }
    //     else {
    //         mark_reviewed_check.hide();
    //         if (study_submit) {
    //             mark_reviewed_label.text('Click Here to Sign Off on this Study');
    //             sign_off_confirm_warning.html(
    //                 'Signing Off will prevent anyone, including you, from editing this Study and the data associated with it.' +
    //                 '<br><br>Signing Off will also provide view access to your data to consortium groups.' +
    //                 '<br><br>Are you sure you want to change the Sign Off status?'
    //             );
    //
    //         }
    //         else {
    //             mark_reviewed_label.text('Click Here to Mark this Entry as Validated');
    //             sign_off_confirm_warning.html(
    //                 'If this is checked, the entry will be marked as Validated.' +
    //                 '<br><br>Are you sure you want to change the validated status?'
    //             );
    //         }
    //     }
    // }

    function set_labels() {
        if (signed_off_selector.prop('checked')) {
            mark_reviewed_check.show();
            mark_reviewed_label.text('Click Here to Remove Validated Mark');
            sign_off_confirm_warning.html(
                'If you continue, this entry will no longer be marked as Validated.' +
                '<br><br>Are you sure you want to change the validated status?'
            );
        }
        else {
            mark_reviewed_check.hide();
            mark_reviewed_label.text('Click Here to Mark this Entry as Validated');
            sign_off_confirm_warning.html(
                'If this is checked, the entry will be marked as Validated.' +
                '<br><br>Are you sure you want to change the validated status?'
            );
        }
    }

    sign_off_confirm.dialog({
        title: dialog_title,
        height:450,
        width:450,
        modal: true,
        buttons: [
        {
            text: 'Yes',
            id: 'sign_off_confirm_submit_button',
            click: function() {
                // Need to indicate that a change has ocurred as well
                signed_off_selector.prop('checked', !signed_off_selector.prop('checked')).trigger('change');
                set_labels();
                $(this).dialog('close');
            }
        },
        {
            text: 'Cancel',
            click: function() {
               $(this).dialog("close");
            }
        }]
    });
    sign_off_confirm.removeProp('hidden');

    mark_reviewed_button_group.click(function() {
        sign_off_confirm.dialog('open');
    });

    // Set initial labels
    set_labels();
});

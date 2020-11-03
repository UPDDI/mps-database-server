// NOT REALLY A GOOD PLACE, BUT I DEFINE SIGILS HERE
// Sigils identify special columns for charting
window.SIGILS = {
    INTERVAL_SIGIL: '     ~@i',
    // Obviously can't do this
    // INTERVAL_1_SIGIL: window.SIGILS.INTERVAL_SIGIL + '1',
    // INTERVAL_2_SIGIL: window.SIGILS.INTERVAL_SIGIL + '2',
    SHAPE_SIGIL: '     ~@s',
    TOOLTIP_SIGIL: '     ~@t',
    COMBINED_VALUE_SIGIL: '~@|'
};
// Unusual, but avoids some issues
window.SIGILS.INTERVAL_1_SIGIL = window.SIGILS.INTERVAL_SIGIL + '1';
window.SIGILS.INTERVAL_2_SIGIL = window.SIGILS.INTERVAL_SIGIL + '2';

// TODO NEEDS TO BE REVISED ALONG WITH HELP
$(document).ready(function () {
    // Prevent CSS conflict with Bootstrap
    // CRUDE
    $.fn.button.noConflict();

    // CRUDE: INJECT GET PARAM PROCESSOR INTO JQUERY
    $.urlParam = function(name) {
        var results = new RegExp('[\?&]' + name + '=([^&#]*)').exec(window.location.href);
        if (results == null) {
           return '';
        }
        return decodeURI(results[1]) || '';
    };

    // Discern what anchor to add to the help URL by looking at current url
    var url = window.location.href;
    var anchor = '';

    var view_help = $('#view_help');

    // TODO GET ANCHOR
    anchor = $('title').attr('data-help-anchor');

    view_help.attr(
        'onclick',
        "window.open('/help/" +
        anchor +
        "','help','toolbars=0,width=1000,height=760,left=200,top=200,scrollbars=1,resizable=1')"
    );

    // Navbar select
    var navbar = $('#autocollapse');

    // Bind a listener to the navbar that causes a collapse if it is oversized
    function autocollapse() {
        navbar.removeClass('collapsed');
        if (navbar.innerHeight() > 51) {
            navbar.addClass('collapsed');
        }
    }

    // Remove navbar etc. if this is a popup
    if ($.urlParam('popup') !== '1') {
        $(document).on('ready', autocollapse);
        $(window).on('resize', autocollapse);
    }
    // else {
    //     // Get rid of footer in popup
    //     $('#footer').remove();
    // }

    // Close if set to close
    if ($.urlParam('popup') == '1' && $.urlParam('close') == '1') {
        // Return pk etc.
        // SLOPPY
        // CATEGORICALLY A BAD PLACE FOR THIS
        // NOT DRY HANDLING
        // If cellsample
        // This will run even before it is closed (in case user closes the window early)
        if ($.urlParam('model') === 'CellSample' || $.urlParam('model') === 'AssayReference') {
            // SLOPPY
            window.opener.TABLES.add_new_row_to_selection_list(
                $.urlParam('app'),
                $.urlParam('model'),
                $.urlParam('new_pk'),
                decodeURIComponent($.urlParam('new_name'))
            );
        }
        else {
            // Crude propagation
            var current_window = window.opener;
            while (current_window) {
                // SLOPPY
                current_window.SELECTIZE.refresh_dropdown(
                    $.urlParam('app'),
                    $.urlParam('model'),
                    $.urlParam('new_pk'),
                    decodeURIComponent($.urlParam('new_name'))
                );

                // Crude special exception for Study
                // If this is AssayTarget or AssayMethod AND is the final window
                if (!current_window.opener && ($.urlParam('model') === 'AssayTarget' || $.urlParam('model') === 'AssayMethod')) {
                    // Categories, Methods, and Targets are related
                    // As a result, we need to refresh those relationships
                    // This is an expedient means of doing so, but is admittedly odd
                    // Please see assaystudy_add.js
                    current_window.ASSAYS.refresh_assay_relationships();
                }

                current_window = current_window.opener;
            }
        }

        setTimeout(function() {
             window.close();
        }, 3000)
    }

    // Crude: Triggers to spawn popups
    $(document).on('click', '.popup-link', function() {
        window.open(
            $(this).attr('data-href'),
            $(this).attr('data-window-name'),
            // Defaults for now
            'toolbars=0,width=1000,height=760,left=200,top=200,scrollbars=1,resizable=1'
        )
    });
});

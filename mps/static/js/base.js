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
    view_help.attr(
        'onclick',
        "window.open('/help/"
        + anchor +
        "','win','toolbars=0,width=1200,height=760,left=200,top=200,scrollbars=1,resizable=1')"
    );

    if (url.indexOf('/assaymatrix/') > -1) {
        anchor = '#matrices'
    }
    else if (url.indexOf('/assaymatrixitem/') > -1) {
        anchor = '#matrixitems'
    }
    else if (url.indexOf('/upload/') > -1) {
        anchor = '#uploadingdata'
    }
    else if (url.indexOf('/studyconfiguration/') > -1) {
        anchor = '#studyconfigurations'
    }
    else if (url.indexOf('/model/') > -1) {
        anchor = '#mpsmodels'
    }
    else if (url.indexOf('/diseases/') > -1) {
        anchor = '#diseasemodels'
    }
    else if (url.indexOf('/device/') > -1) {
        anchor = '#devices'
    }
    else if (url.indexOf('/table/') > -1) {
        anchor = '#bioactivities'
    }
    else if (url.indexOf('/drugtrials/') > -1) {
        anchor = '#drugtrials'
    }
    else if (url.indexOf('adverse_events/') > -1) {
        anchor = '#adverseevents'
    }
    else if (url.indexOf('compare_adverse_events/') > -1) {
        anchor = '#compareadverseevents'
    }
    else if (url.indexOf('/report/') > -1) {
        anchor = '#compoundreport'
    }
    else if (url.indexOf('/compounds/') > -1) {
        anchor = '#chemicaldata'
    }
    else if (url.indexOf('/heatmap/') > -1) {
        anchor = '#heatmap'
    }
    else if (url.indexOf('/cluster/') > -1) {
        anchor = '#cluster'
    }
    else if (url.indexOf('/celltype/') > -1) {
        anchor = '#cellsamples'
    }
    else if (url.indexOf('/cellsubtype/') > -1) {
        anchor = '#cellsamples'
    }
    else if (url.indexOf('/cellsample/') > -1) {
        anchor = '#cellsamples'
    }
    else if (url.indexOf('/targets/') > -1) {
        anchor = '#assaymts'
    }
    else if (url.indexOf('/methods/') > -1) {
        anchor = '#assaymts'
    }
    else if (url.indexOf('/assaymatrixitem/') > -1) {
        anchor = '#intrastudy'
    }
    else if (url.indexOf('/assaymatrix/') > -1) {
        anchor = '#intrastudy'
    }
    else if (url.indexOf('/images/') > -1) {
        anchor = '#intrastudy'
    }
    else if (url.indexOf('/assaystudy/') > -1) {
        anchor = '#intrastudy'
    }
    else if (url.indexOf('/summary/') > -1) {
        anchor = '#intrastudy'
    }
    else if (url.indexOf('/graphing_reproducibility/') > -1) {
        anchor = '#interstudy'
    }

    view_help.attr(
        'onclick',
        "window.open('/help/" +
        anchor +
        "','win','toolbars=0,width=1000,height=760,left=200,top=200,scrollbars=1,resizable=1')"
    );

    // Bind a listener to the navbar that causes a collapse if it is oversized
    var navbar = $('#autocollapse');

    function autocollapse() {
        navbar.removeClass('collapsed');
        if (navbar.innerHeight() > 51) {
            navbar.addClass('collapsed');
        }
    }

    $(document).on('ready', autocollapse);
    $(window).on('resize', autocollapse);
});

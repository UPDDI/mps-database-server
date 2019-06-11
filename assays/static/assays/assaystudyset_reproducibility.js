$(document).ready(function() {
    window.INTER_REPRO.study_set_id = Math.floor(window.location.href.split('/')[5]);
    window.INTER_REPRO.call = 'fetch_data_points_from_study_set';

    // Load core chart package
    google.charts.load('current', {'packages':['corechart']});
    // Set the callback
    google.charts.setOnLoadCallback(window.INTER_REPRO.show_repro);

    // On load
    document.getElementById('id_current_url_input').value = window.location.href

    // On click of copy to URL button (DEPRECATED)
    $('#id_copy_url_button').click(function() {
        var current_url = document.getElementById('id_current_url_input'); current_url.select();
        document.execCommand('copy');
    });
});

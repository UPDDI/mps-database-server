$(document).ready(function() {
    window.INTER_REPRO.call = 'fetch_data_points_from_filters';

    // Load core chart package
    google.charts.load('current', {'packages':['corechart']});
    // Set the callback

    google.charts.setOnLoadCallback(window.INTER_REPRO.show_repro);
});

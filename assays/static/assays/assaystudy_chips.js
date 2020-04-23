// TODO WE ARE NOW CALLING THEM GROUPS AGAIN, I GUESS
$(document).ready(function () {
    // TEMPORARY
    var series_data_selector = $('#id_series_data');

    // FULL DATA
    // TEMPORARY
    var full_series_data = JSON.parse(series_data_selector.val());

    if (series_data_selector.val() === '{}') {
        full_series_data = {
            series_data: [],
            // Plates is an array, kind of ugly, but for the moment one has to search for the current plate on the plate page
            plates: [],
            // The ID needs to be in individual chip objects, they don't exist initially (unlike plates!)
            chips: []
        };
    }

    // TODO WE NEED TO SPLIT OUT MATRIX ITEM DATA
    var chip_data = full_series_data.chips;

    // SERIES DATA
    var series_data = full_series_data.series_data;

    function build_chip_table() {
        $.each(chip_data, function(index, chip) {

        });
    }

    build_chip_table();
});

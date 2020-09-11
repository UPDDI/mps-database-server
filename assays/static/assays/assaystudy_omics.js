//GLOBAL-SCOPE
window.OMICS = {
    draw_plots: null
};

$(document).ready(function () {
    // Load core chart package
    google.charts.load('current', {'packages': ['corechart']});
    google.charts.load('visualization', '1', {'packages': ['imagechart']});
    // Set the callback
    google.charts.setOnLoadCallback(fetchOmicsData);

    // FILE-SCOPE VARIABLES
    var study_id = Math.floor(window.location.href.split('/')[5]);

    function fetchOmicsData(){
        window.spinner.spin(
            document.getElementById("spinner")
        );

        $.ajax(
            "/assays_ajax/",
            {
                data: {
                    call: 'fetch_omics_data',
                    csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken,
                    study_id: study_id,
                },
                type: 'POST',
            }
        )
        .success(function(data) {
            // console.log("DATA", data)

            if (!('error' in data)) {
                window.OMICS.omics_data = JSON.parse(JSON.stringify(data))
                window.OMICS.draw_plots(window.OMICS.omics_data, true, 0, 0, 0, 0, 0, 0, 0);
            } else {
                console.log(data['error']);
                // Stop spinner
                window.spinner.stop();
            }

        })
        .fail(function(xhr, errmsg, err) {
            // Stop spinner
            window.spinner.stop();

            alert('An error has occurred, please try different selections.');
            console.log(xhr.status + ": " + xhr.responseText);
        });
    }
});
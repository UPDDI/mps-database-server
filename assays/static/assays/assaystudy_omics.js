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
            console.log("DATA", data)

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

            alert('An error has occurred, failed to retrieve omics data.');
            console.log(xhr.status + ": " + xhr.responseText);
        });
    }

    // On checkbox click, toggle relevant chart.
    // Dynamically generated content does not work with a typical JQuery selector in some cases, hence this.
    $(document).on('click', '.big-checkbox', function() {
        $("#ma-"+$(this).data("checkbox-id")).parent().toggle();
        $("#volcano-"+$(this).data("checkbox-id")).parent().toggle();
    })

    $("#download-filtered-data").click(function() {
        alert("Filtered data download in development.\nPlease check back soon!");
    //     window.spinner.spin(
    //         document.getElementById("spinner")
    //     );
    //
    //     $.ajax(
    //         "/assays_ajax/",
    //         {
    //             data: {
    //                 call: 'download_filtered_omics_data',
    //                 csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken,
    //                 study_id: study_id,
    //             },
    //             type: 'POST',
    //         }
    //     )
    //     .success(function(data) {
    //         console.log("DATA", data)
    //
    //         if (!('error' in data)) {
    //
    //         } else {
    //             console.log(data['error']);
    //             // Stop spinner
    //             window.spinner.stop();
    //         }
    //
    //     })
    //     .fail(function(xhr, errmsg, err) {
    //         // Stop spinner
    //         window.spinner.stop();
    //
    //         alert('An error has occurred, failed to download omics data.');
    //         console.log(xhr.status + ": " + xhr.responseText);
    //     });
    })
});

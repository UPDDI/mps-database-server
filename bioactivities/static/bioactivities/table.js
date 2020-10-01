$(document).ready(function () {
    function table(data) {
        // Show graphic
        $('#graphic').prop('hidden',false);
        // Hide error
        $('#error_message').prop('hidden',true);

        // Clear old (if present)
        $('#full').dataTable().fnDestroy();
        $('#table').html('');

//        // Set href
//        $('#download').attr('href',link);

        for (var i in data) {
            var bio = data[i];
            //console.log(bio);
            var row = "<tr>";
            row += "<td><a href='/compounds/"+bio.compoundid+"'>" + bio.compound + "</a></td>";
            row += "<td>" + bio.target + "</td>";
            row += "<td>" + bio.organism + "</td>";
            row += "<td>" + bio.activity_name + "</td>";

            if (!FILTER.pubchem) {
                row += "<td>" + bio.operator + "</td>";
            }
            else {
                row += "<td>=</td>";
            }

            row += "<td>" + bio.standardized_value + "</td>";

            if (!FILTER.pubchem) {
                row += "<td>" + bio.standardized_units + "</td>";
            }
            else {
                row += "<td>µM</td>";
            }

            row += "<td><a href='https://www.ebi.ac.uk/chembl/assay/inspect/"+bio.chemblid+"'>" + bio.chemblid + "</a></td>";
            row += "<td><a href='https://pubchem.ncbi.nlm.nih.gov/assay/assay.cgi?aid="+bio.pubchem_id+"'>" + bio.pubchem_id + "</a></td>";

            row += "<td>" + bio.notes + "</td>";
            row += "<td class='text-danger'>" + bio.data_validity + "</td>";
//            row += "<td>" + bio.bioactivity_type + "</td>";
//            row += "<td>" + bio.value + "</td>";
//            row += "<td>" + bio.units + "</td>";
            row += "</tr>";
            $('#table').append(row);
        }

        $('#full').DataTable({
            dom: '<Bl<"row">frptip>',
            fixedHeader: {headerOffset: 50},
            responsive: true,
            "iDisplayLength": 100,
            // Needed to destroy old table
            "bDestroy": true,
            order: [
                [0, 'asc'],
                [6, 'asc'],
                [5, 'asc']
            ]
        });
    }

    function submit() {
        // Clear all filters
        // bioactivities_filter = [];
        // targets_filter = [];
        // compounds_filter = [];
        //
        // // Get bioactivities
        // $("#bioactivities input[type='checkbox']:checked").each( function() {
        //     bioactivities_filter.push({"name":this.value, "is_selected":this.checked});
        // });
        //
        // // Get targets
        // $("#targets input[type='checkbox']:checked").each( function() {
        //     targets_filter.push({"name":this.value, "is_selected":this.checked});
        // });
        //
        // // Get compounds
        // $("#compounds input[type='checkbox']:checked").each( function() {
        //     compounds_filter.push({"name":this.value, "is_selected":this.checked});
        // });

        // Hide Selection html
        $('#selection').prop('hidden',true);
        // Hide error
        $('#error_message').prop('hidden',true);

        // Show spinner
        window.spinner.spin(
            document.getElementById("spinner")
        );

        $.ajax({
            url:  '/bioactivities/gen_table/',
            type: 'POST',
            dataType: 'json',
            data: {
                form: JSON.stringify({
                    'exclude_questionable': FILTER.exclude_questionable,
                    'pubchem': FILTER.pubchem,
                    'bioactivities_filter': FILTER.bioactivities_filter,
                    'targets_filter': FILTER.targets_filter,
                    'compounds_filter': FILTER.compounds_filter,
                    'target_types_filter': FILTER.target_types,
                    'organisms_filter': FILTER.organisms
                }),
                csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
            },
            success: function (json) {
                // Stop spinner
                window.spinner.stop();
                //console.log(json);

                if (json.data_json) {
                    //console.log(json);
                    table(json.data_json);
                    //table(json.data_json, json.table_link);
//                    document.location.hash = "display";

                    if (json.length > 5000) {
                        $('#overflow').prop('hidden', false);
                        $('#length').html('Displaying 5000 of ' + json.length);
                    }
                    else {
                        $('#overflow').prop('hidden', true);
                        $('#length').html('');
                    }

                    // Ensure table header (if present) is shown
                    $('#table_header').show();
                }
                else {
                    if (json.error) {
                        $('#error').html(json.error);
                    }
                    // Show error
                    $('#error_message').prop('hidden',false);
                    // Show Selection
                    $('#selection').prop('hidden',false);
                }

            },
            error: function (xhr, errmsg, err) {
                // Stop spinner
                window.spinner.stop();

                console.log(xhr.status + ": " + xhr.responseText);

                // Show error
                $('#error_message').prop('hidden',false);
                // Show Selection
                $('#selection').prop('hidden',false);
            }
        });
    }

//    var pubchem_header = '<tr>' +
//        '<th>Compound</th>' +
//        '<th>Target</th>' +
//        '<th>Organism</th>' +
//        '<th>Activity Name</th>' +
//        '<th>Standard Value (μm)</th>' +
//        '<th>ChEMBL Link</th>' +
//        '<th>PubChem Link</th>' +
//        '</tr>';
//
//    var chembl_header = '<tr>' +
//        '<th>Compound</th>' +
//        '<th>Target</th>' +
//        '<th>Organism</th>' +
//        '<th>Activity Name</th>' +
//        '<th>Operator</th>' +
//        '<th>Standard Value</th>' +
//        '<th>Standard Units</th>' +
//        '<th>ChEMBL Link</th>' +
//        '<th>PubChem Link</th>' +
//        '</tr>';

    var targets_filter = [];
    var compounds_filter = [];
    var bioactivities_filter = [];

    $('#submit').click(function(evt) {
        submit();
    });
});

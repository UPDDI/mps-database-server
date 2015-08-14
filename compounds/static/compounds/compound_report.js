// The compound report must be able to:
// 1.) Employ some method to filter desired compounds (will resemble list display with checkboxes)
// 2.) Display all of the requested compound data in the desired table
// 3.) Display D3 "Sparklines" for every assay for the given compound (TODO LOOK AT D3 TECHNIQUE)

$(document).ready(function () {
    // Middleware token for CSRF validation
    var middleware_token = getCookie('csrftoken');

    // Object of all selected compounds
    var compounds = {};

    var width = 100;
    var height = 25;
    var x = d3.scale.linear().range([0, width]);
    var y = d3.scale.linear().range([height, 0]);
    var line = d3.svg.line()
             .interpolate("basis")
             .x(function(d) { return x(d.time); })
             .y(function(d) { return y(d.value); });

    function sparkline(elem_id, plot) {
        data = [];
        for (var time in plot) {
            var value = +plot[time];
            var x_time = +time;
            data.push({'time':x_time, 'value':value});
        }

        // Sort by time
        data = _.sortBy(data, function(obj){ return +obj.time });

        x.domain(d3.extent(data, function(d) { return d.time; }));
        y.domain(d3.extent(data, function(d) { return d.value; }));

        d3.select(elem_id)
            .append('svg')
            .attr('width', width)
            .attr('height', height)
            .append('path')
            .datum(data)
            .attr('class', 'sparkline')
            .attr('d', line);
    }

    // AJAX call for getting data
    function get_data() {
        $.ajax({
            url: "/compounds_ajax",
            type: "POST",
            dataType: "json",
            data: {
                call: 'fetch_compound_report',
                compounds: JSON.stringify(compounds),
                csrfmiddlewaretoken: middleware_token
            },
            success: function (json) {
                // Stop spinner
                window.spinner.stop();
                // Build table
                build_table(json);
            },
            error: function (xhr, errmsg, err) {
                // Stop spinner
                window.spinner.stop();
                console.log(xhr.status + ": " + xhr.responseText);
            }
        });
    }

    function build_table(data) {
        // Show graphic
        $('#results_table').prop('hidden',false);

        // Clear old (if present)
        $('#results_table').dataTable().fnDestroy();
        $('#results_body').html('');

        for (var compound in data) {
            var values = data[compound].table;
            var plot = data[compound].plot;

            var row = "<tr>";

            row += "<td><a href='/compounds/"+values['id']+"'>" + compound + "</a></td>";
            row += "<td>" + values['Dose (xCmax)'] + "</td>";
            row += "<td>" + values['cLogP']  + "</td>";
            row += "<td>" + values['Pre-clinical Findings'] + "</td>";
            row += "<td>" + values['Clinical Findings'] + "</td>";

            row += "<td>" + 'TODO' + "</td>";

            row += "<td>";
            for (var assay in plot) {
                row += '<div>' + assay + '<span id='+compound+'_'+assay+'></span></div>';
            }
            row += "</td>";

            row += "</tr>";
            $('#results_body').append(row);

            for (var assay in plot) {
                sparkline('#'+compound+'_'+assay, plot[assay]);
            }
        }

        $('#results_table').DataTable({
            dom: 'T<"clear">frtip',
            "iDisplayLength": 100,
            // Needed to destroy old table
            "bDestroy": true,
            "order": [[ 0, "asc" ]],
            "aoColumnDefs": [
                {
                    "bSortable": false,
                    "aTargets": [6]
                }
            ]
        });

        // Swap positions of filter and length selection
        $('.dataTables_filter').css('float','left');
        // Reposition download/print/copy
        $('.DTTT_container').css('float', 'none');
    }

    // Submission
    function submit() {
        // Hide Selection html
        $('#selection').prop('hidden',true);
        // Show spinner
        window.spinner.spin(
            document.getElementById("spinner")
        );
        get_data();
    }

    // Checks whether the submission button was clicked
    $('#submit').click(function() {
        submit();
    });

    // Tracks the clicking of checkboxes to fill compounds
    $('.checkbox').change( function() {
        var compound = this.value;
        if (this.checked) {
            compounds[compound] = compound;
        }
        else {
            delete compounds[compound]
        }
    });

    window.onhashchange = function() {
        if (location.hash != '#show') {
            $('#graphic').prop('hidden', true);
            $('#selection').prop('hidden', false);
        }
        else {
            $('#graphic').prop('hidden', false);
            $('#selection').prop('hidden', true);
        }
    };
});

$(document).ready(function() {
    $('#cellsamples').DataTable({
        dom: '<Bl<"row">frptip>',
        fixedHeader: {headerOffset: 50},
        responsive: true,
        "iDisplayLength": 50,
        // Initially sort on ID
        "order": [ 1, "desc" ],
        "aoColumnDefs": [
            {
                "bSortable": false,
                "aTargets": [0]
            },
            {
                "width": "10%",
                "targets": [0]
            }
        ]
    });
});

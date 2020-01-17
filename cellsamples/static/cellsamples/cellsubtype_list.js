$(document).ready(function() {
    $('#cellsubtypes').DataTable({
        dom: '<Bl<"row">frptip>',
        fixedHeader: {headerOffset: 50},
        responsive: true,
        "iDisplayLength": 50,
        // Initially sort on organ
        "order": [ 1, "asc" ],
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

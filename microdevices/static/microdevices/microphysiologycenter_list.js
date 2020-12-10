$(document).ready(function() {
    $('#centers').DataTable({
        "iDisplayLength": 100,
        fixedHeader: {headerOffset: 50},
        responsive: true,
        "order": [[ 1, "asc" ]],
        "aoColumnDefs": [
            {
                "bSortable": false,
                "aTargets": [0, 1]
            },
            {
                "width": "10%",
                "targets": [0]
            },
            {
                targets: [4],
                className: 'none',
            }
        ]
    });
});

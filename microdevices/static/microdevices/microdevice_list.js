$(document).ready(function() {
    $('#microdevices').DataTable({
        "iDisplayLength": 100,
        fixedHeader: {headerOffset: 50},
        responsive: true,
        "order": [[ 2, "asc" ]],
        "aoColumnDefs": [
            {
                "bSortable": false,
                "aTargets": [0, 1]
            },
            {
                "width": "10%",
                "targets": [0]
            }
        ]
    });
});

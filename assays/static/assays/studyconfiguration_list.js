$(document).ready(function() {
    $('#studyconfigurations').DataTable( {
        fixedHeader: {headerOffset: 50},
        responsive: true,
        "iDisplayLength": 50,
        "order": [[ 1, "asc" ]],
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

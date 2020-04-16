$(document).ready(function() {
    $('#plates').DataTable({
        "iDisplayLength": 10,
        dom: 'B<"row">lfrtip',
        fixedHeader: {headerOffset: 50},
        responsive: false,
        // Initially sort on start date (descending), not ID
        "order": [[1, "asc"], [2, "desc"]],
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

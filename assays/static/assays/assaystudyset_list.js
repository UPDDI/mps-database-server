$(document).ready(function() {
    window.TABLE = $('#study_sets').DataTable({
        "iDisplayLength": 100,
        "sDom": '<B<"row">lfrtip>',
        fixedHeader: {headerOffset: 50},
        responsive: true,
        "order": [[1, "asc"]],
        "aoColumnDefs": [
            {
                "className": "dt-center",
                "bSortable": false,
                "width": '5%',
                "targets": [0]
            },
            {
                "bSortable": false,
                "aTargets": [0]
            },
        ]
    });
});

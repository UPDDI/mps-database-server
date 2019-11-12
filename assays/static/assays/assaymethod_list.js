$(document).ready(function() {
    window.TABLE = $('#methods-table').DataTable({
        "iDisplayLength": 100,
        "sDom": '<B<"row">lfrtip>',
        fixedHeader: {headerOffset: 50},
        responsive: true,
        "order": [[2, "asc"]],
        "aoColumnDefs": [
            {
                "className": "dt-center",
                "targets": [0, 1, 2, 5]
            },
            {
                "bSortable": false,
                "aTargets": [0, 1]
            },
            {
                "responsivePriority": 1,
                "bSortable": false,
                "width": '5%',
                "aTargets": [0]
            },
            {
                "responsivePriority": 1,
                "width": '15%',
                "aTargets": [1,3]
            },
            {
                "responsivePriority": 3,
                "width": '10%',
                "aTargets": [2]
            },
            {
                "responsivePriority": 4,
                "bSortable": false,
                "width": '45%',
                "aTargets": [4]
            },
            {
                "responsivePriority": 2,
                "width": '5%',
                "aTargets": [5]
            }
        ]
    });
});

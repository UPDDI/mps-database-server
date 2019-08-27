$(document).ready(function() {
    window.TABLE = $('#models').DataTable({
        "iDisplayLength": 100,
        "sDom": '<B<"row">lfrtip>',
        fixedHeader: {headerOffset: 50},
        responsive: true,
        "order": [[5, "asc"], [4, "asc"], [2, "desc"]],
        "aoColumnDefs": [
            {
                "bSortable": false,
                "aTargets": [0, 1]
            },
            {
                'className': 'none',
                'targets': [8]

            },
            // {
            //     'sortable': true,
            //     'visible': false,
            //     'targets': [9]
            // },
            {
                "width": "10%",
                "targets": [0, 1]
            }
        ]
    });
});

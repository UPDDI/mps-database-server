$(document).ready(function() {
    window.TABLE = $('#methods-table').DataTable({
        "iDisplayLength": 100,
        "sDom": '<Bl<"row">frptip>',
        fixedHeader: {headerOffset: 50},
        responsive: true,
        "order": [[2, "asc"]],
        "aoColumnDefs": [
            {
                "className": "dt-center",
                // Do not center description
                "targets": [0, 1, 2, 4]
            },
            {
                "bSortable": false,
                "aTargets": [0, 1]
            },
            {
                "responsivePriority": 1,
                "bSortable": false,
                "width": '5%',
                "aTargets": [0, 1]
            },
            // ?
            // {
            //     "responsivePriority": 1,
            //     "width": '15%',
            //     "aTargets": [3]
            // },
            {
                "responsivePriority": 1,
                "width": '20%',
                "aTargets": [2]
            },
            {
                "responsivePriority": 4,
                // Why isn't the supplier sortable?
                // "bSortable": false,
                // Why is the supplier so huge?
                // "width": '45%',
                "aTargets": [4]
            },
            {
                "responsivePriority": 2,
                // Increase width of description
                "width": '45%',
                "aTargets": [5]
            }
        ]
    });
});

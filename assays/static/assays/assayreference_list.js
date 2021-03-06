$(document).ready(function() {
    window.TABLE = $('#references-table').DataTable({
        "iDisplayLength": 25,
        fixedHeader: {headerOffset: 50},
        responsive: true,
        "order": [[2, "asc"]],
        "aoColumnDefs": [
            {
                "className": "dt-center",
                "bSortable": false,
                "width": '5%',
                "targets": [0, 1]
            },
            {
                'className': 'none',
                "targets": [5]
            }
        ]
    });
});

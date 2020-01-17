$(document).ready(function() {
    var target_table = $('#target_table');

    target_table.DataTable({
        dom: '<Bl<"row">frptip>',
        fixedHeader: {headerOffset: 50},
        responsive: true,
        "order": [[4, "desc"], [ 2, "asc" ], [3, "asc"], [0, "asc"]],
        "iDisplayLength": 100
    });
});

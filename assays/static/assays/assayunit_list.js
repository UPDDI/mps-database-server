$(document).ready(function() {
    window.TABLE = $('#units-table').DataTable({
        "iDisplayLength": 100,
        fixedHeader: {headerOffset: 50},
        responsive: true,
        "order": [[1, "asc"]],
    });
});

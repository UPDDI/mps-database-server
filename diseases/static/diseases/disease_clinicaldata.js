// Define a custom sorting order
// Note that special characters must be escaped
$(document).ready(function() {
    $.fn.dataTable.ext.type.order['frequency-range-pre'] = function (d) {
        switch (d) {
            case '&lt; 0.01%':         return 1;
            case '0.01 - &lt; 0.1%':   return 2;
            case '0.1 - &lt; 1%':      return 3;
            case '1 - &lt; 10%':       return 4;
            case '&gt;= 10%':          return 5;
        }
        return 0;
    };

    window.TABLE = $('#drugtrials').DataTable({
        dom: 'B<"row">lfrtip',
        fixedHeader: {headerOffset: 50},
        responsive: true,
        "iDisplayLength": 50,
        "deferRender": true,
        // Initially sort on compound, not arbitrary ID
        "order": [[ 2, "asc" ], [ 1, "asc"]],
        // Apply custom sorting priorities to frequency column
        "columnDefs": [{
            "type": "frequency-range",
            "targets": 8
        }],
        "aoColumnDefs": [
            {
                "bSortable": false,
                "aTargets": [0]
            },
            {
                "width": "10%",
                "targets": [0]
            },
            // {
            //     "targets": [11],
            //     "visible": false,
            //     "searchable": true
            // },
            {
                responsivePriority: 1,
                targets: [0, 2]
            }
        ]
    });
});

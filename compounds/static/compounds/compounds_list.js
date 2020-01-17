$(document).ready(function() {
    // Shrinks the name column when on small screen (illegible otherwise)
    function resize() {
        if($(document).width() < 335) {
            $('.text-wrapped').css('font-size', '11px');
            $($.fn.dataTable.tables(true)).DataTable().responsive.recalc();
        }
        else {
            $('.text-wrapped').css('font-size', '14px');
            $($.fn.dataTable.tables(true)).DataTable().responsive.recalc();
        }
    }

    window.TABLE = $('#compounds').DataTable({
        dom: '<Bl<"row">frptip>',
        fixedHeader: {headerOffset: 50},
        responsive: true,
        "order": [[ 2, "asc" ]],
        "aoColumnDefs": [
            {
                "bSortable": false,
                "aTargets": [0, 1]
            },
            // {
            //     "targets": [4, 9],
            //     "visible": false,
            //     "searchable": true
            // },
            {
                "targets": [
                    4,
                    9,
                    10,
                    11,
                    12,
                    13,
                    14,
                    15,
                    16,
                    17,
                    18,
                    19,
                ],
                "visible": false,
                "searchable": true
            },
            {
                "width": "5%",
                "targets": [0, 1]
            },
            {
                responsivePriority: 1,
                targets: [0, 2]
            },
            {
                responsivePriority: 2,
                targets: [1]
            }
        ],
        "iDisplayLength": 25
    });

    // Initial resize
    resize();

    // Run resize function on resize
    $(window).resize(function() {
      resize();
    });

    // Crude way to deal with resizing from images
    // TODO TODO TODO REFACTOR
    setTimeout(function() {
         $($.fn.dataTable.tables(true)).DataTable().fixedHeader.adjust();
    }, 500);
});

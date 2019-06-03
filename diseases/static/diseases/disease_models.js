$(document).ready(function() {

    //TODO Filter studies based on currently relevant organ models.
    // // The respective checkboxes
    // var show_mps = $('#show_mps');
    // var show_epa = $('#show_epa');
    // var show_tctc = $('#show_tctc');
    // var show_unassigned = $('#show_unassigned');
    //
    // // Whether the checkbox for a filter is checked
    // var filters = {
    //     'MPS': show_mps.prop('checked'),
    //     'EPA': show_epa.prop('checked'),
    //     'TCTC': show_tctc.prop('checked'),
    //     'Unassigned': show_unassigned.prop('checked')
    // };

    var  data_table = $('#studies').DataTable( {
        dom: 'B<"row">lfrtip',
        fixedHeader: {headerOffset: 50},
        responsive: true,
        "iDisplayLength": 50,
        // Initially sort on start date (descending), not ID
        "order": [ 2, "desc" ],
        "aoColumnDefs": [
            {
                "bSortable": false,
                "aTargets": [0]
            },
            {
                "width": "10%",
                "targets": [0]
            },
            {
                "type": "numeric-comma",
                "targets": [5, 6]
            },
            {
                'className': 'none',
                'targets': [7]
            }
        ]
    });

    window.TABLE = $('#models').DataTable({
        "iDisplayLength": 100,
        "sDom": '<B<"row">lfrtip>',
        fixedHeader: {headerOffset: 50},
        responsive: true,
        "order": [[3, "asc"], [2, "asc"]],
        "aoColumnDefs": [
            {
                "bSortable": false,
                "aTargets": [0, 1]
            },
            // {
            //     'sortable': true,
            //     'visible': false,
            //     'targets': [7]
            // },
            {
                "width": "5%",
                "targets": [0, 1]
            }
        ]
    });

    $($.fn.dataTable.tables(true)).DataTable().fixedHeader.adjust();
});

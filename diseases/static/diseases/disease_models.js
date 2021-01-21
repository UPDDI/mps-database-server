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

    $('#models').DataTable({
        "iDisplayLength": 100,
        fixedHeader: {headerOffset: 50},
        responsive: true,
        "order": [[3, "asc"], [2, "asc"]],
        "aoColumnDefs": [
            {
                "bSortable": false,
                "aTargets": [0, 1]
            },
            {
                "width": "5%",
                "targets": [0, 1]
            },
            {
                'className': 'none',
                'targets': [6]
            },
        ]
    });
});

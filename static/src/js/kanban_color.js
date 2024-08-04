odoo.define('meat_processing.kanban_color', function (require) {
    "use strict";

    var KanbanRecord = require('web.KanbanRecord');

    KanbanRecord.include({
        kanban_get_color: function (state) {
            switch (state) {
                case 'draft':
                    return 'bg-warning';
                case 'processing':
                    return 'bg-info';
                case 'done':
                    return 'bg-success';
                case 'cancelled':
                    return 'bg-danger';
                default:
                    return '';
            }
        }
    });
});

odoo.define('meat_processing.kanban_color', function (require) {
    'use strict';

    var KanbanRecord = require('web.KanbanRecord');

    KanbanRecord.include({
        kanban_get_color: function (state) {
            switch (state) {
                case 'draft':
                    return 'o_kanban_color_draft';
                case 'processing':
                    return 'o_kanban_color_processing';
                case 'done':
                    return 'o_kanban_color_done';
                case 'cancelled':
                    return 'o_kanban_color_cancelled';
                default:
                    return '';
            }
        },
    });
});

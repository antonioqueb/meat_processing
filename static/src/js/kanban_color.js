// meat_processing/static/src/js/kanban_color.js
odoo.define('meat_processing.kanban_color', function (require) {
    "use strict";

    var KanbanRecord = require('web.KanbanRecord');

    KanbanRecord.include({
        _render: function () {
            this._super.apply(this, arguments);
            var state = this.recordData.state;
            this.$el.addClass('o_kanban_color_' + state);
        }
    });
});

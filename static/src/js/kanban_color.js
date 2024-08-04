odoo.define('meat_processing.kanban_color', function (require) {
    "use strict";

    var KanbanRecord = require('web.KanbanRecord');

    KanbanRecord.include({
        _render: function () {
            this._super.apply(this, arguments);
            var state = this.recordData.state;
            this.$el.addClass('o_kanban_color_' + state);
            this.$el.hover(
                function() {
                    $(this).css("box-shadow", "0 6px 12px rgba(0, 0, 0, 0.2)");
                }, function() {
                    $(this).css("box-shadow", "0 4px 8px rgba(0, 0, 0, 0.1)");
                }
            );
        }
    });
});

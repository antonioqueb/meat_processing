/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { KanbanRecord } from '@web/views/kanban/kanban_record';

function getColorClass(state) {
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
}

patch(KanbanRecord.prototype, 'meat_processing.KanbanRecord', {
    setup() {
        this._super.apply(this, arguments);
    },
    get classes() {
        const baseClasses = this._super;
        return `${baseClasses} ${getColorClass(this.props.record.data.state)}`;
    }
});

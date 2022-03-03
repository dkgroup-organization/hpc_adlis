from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval

import logging
_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    bom_id = fields.Many2one('mrp.bom', string='BOM', domain="[('product_id', '=', product_id)]")

    def update_bom_id(self):
        """Update bom"""
        for line in self:
            if line.product_id.bom_id:
                line.bom_id = line.product_id.bom_id
            elif line.product_template_id.bom_id:
                line.product_id.create_bom()
                line.bom_id = line.product_id.bom_id
            else:
                line.bom_id = False

            if line.product_custom_attribute_value_ids and line.bom_id:
                line.bom_id.sale_line_id = line
                _logger.info

    @api.model
    def create(self, values):
        new_line = super().create(values)
        new_line.update_bom_id()
        return new_line

    def write(self, values):
        res = super().write(values)
        if 'product_id' in list(values.keys()):
            self.update_bom_id()
        return res

    def button_open_bom(self):
        """open bom form"""
        self.ensure_one()

        if not self.bom_id:
            self.update_bom_id()

        if not self.bom_id:
            return False
        else:
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'mrp.bom',
                'res_id': self.bom_id.id or False,
                'views': [(False, 'form')],
                'view_id': False,
                'target': 'new',
                #'context': self.env.context,
            }
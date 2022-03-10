from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval

import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _action_confirm(self):
        """Add some function on order confirmation"""

        # TODO add stock rules before the validation
        # TODO add sale order line on the manufacture order
        for order in self:
            order.order_line.update_bom_id()

        for order in self:
            order.order_line.create_production()

        res = super()._action_confirm()
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    bom_id = fields.Many2one('mrp.bom', string='BOM', domain="[('product_id', '=', product_id)]")
    production_id = fields.Many2one('mrp.production', string='Production')

    def create_production(self):
        """ Create a production order"""
        for line in self:
            if not line.production_id and line.bom_id and line.product_id.jit_production:
                wo_vals = {
                    'product_id': line.product_id.id,
                    'bom_id': line.bom_id.id,
                    'origin': line.order_id.name,
                    'product_qty': line.product_uom_qty,
                    'product_uom_id': line.product_uom.id,
                }
                line.production_id = self.env['mrp.production'].create(wo_vals)
                line.production_id._onchange_move_raw()
                line.production_id._onchange_workorder_ids()





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
                line.bom_id.compute_line()

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
        self.update_bom_id()
        res_id = self.product_id.bom_id.id or False

        if not res_id:
            return {}
        else:
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'mrp.bom',
                'res_id': res_id,
                'views': [(False, 'form')],
                'view_id': False,
                'target': 'new',
            }
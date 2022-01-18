from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval

import logging
_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    bom_id = fields.Many2one('mrp.bom', string='BOM',
               domain="[('product_tmpl_id.product_variant_ids', '=', product_id),"
               "'|', ('product_id', '=', product_id), ('product_id', '=', False)]")

    @api.model
    def create(self, values):
        res = super().create(values)
        if res.product_custom_attribute_value_ids:
            bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', res.product_template_id.id),
                                              ('product_id', '=', False)], limit=1)
            if not bom:
                raise ValidationError('No Bom Exist !!! ')

            new_bom = bom.sudo().copy({})
            res.update({'bom_id': new_bom.id})
            new_bom.code = res.name
            new_bom.product_id = res.product_id
            new_bom.sale_line_id = res
            new_bom.create_attribute_value()
            new_bom.compute_line()
        return res

    def write(self, values):
        res = super().write(values)

        for line in self:
            if line.bom_id and line.product_custom_attribute_value_ids:
                line.bom_id.code = line.name
                line.bom_id.product_id = line.product_id
                line.bom_id.sale_line_id = line
                line.bom_id.create_attribute_value()
                line.bom_id.compute_line()
        return res

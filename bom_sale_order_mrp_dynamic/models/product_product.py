# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ProductProduct(models.Model):
    _inherit = "product.product"

    bom_id = fields.Many2one('mrp.bom', 'Default BOM', compute='_compute_bom_id')
    bom_line_ids = fields.One2many('mrp.bom.line', related='bom_id.bom_line_ids', string="BOM line")

    @api.depends('bom_ids')
    def _compute_bom_id(self):
        for product in self:
            bom_ids = self.env['mrp.bom']
            if product.is_product_variant:
                bom_ids = self.env['mrp.bom'].search([('product_id', '=', product.id)])
                product.bom_id = bom_ids and bom_ids[0] or bom_ids
            else:
                bom_ids = self.env['mrp.bom'].search(
                    [('product_tmpl_id', '=', product.id), ('product_id', '=', False)])
            product.bom_id = bom_ids and bom_ids[0] or bom_ids

    def create_bom(self):
        """Create default BOM"""
        res = self.env['mrp.bom']

        for product in self:
            if not product.bom_id:
                if not product.is_product_variant:
                    # New template BOM
                    bom_vals = {'product_tmpl_id': product.id, 'type': 'normal'}
                    new_bom = self.env['mrp.bom'].create(bom_vals)
                    new_bom.create_attribute_value()
                    product.bom_id = new_bom
                    res |= new_bom
                else:
                    if product.product_tmpl_id.bom_id:
                        copy_bom = product.product_tmpl_id.bom_id
                    else:
                        copy_bom = product.product_tmpl_id.create_bom()
                    new_bom = copy_bom.copy()
                    new_bom.product_id = product
                    new_bom.create_attribute_value()
                    product.bom_id = new_bom
                    res |= new_bom
        return res

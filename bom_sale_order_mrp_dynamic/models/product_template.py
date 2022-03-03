# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    bom_id = fields.Many2one('mrp.bom', 'Template Bill of material', compute='get_tmpl_bom_id', store=True)
    bom_line_ids = fields.One2many('mrp.bom.line', related='bom_id.bom_line_ids', string="BOM line")
    template_code = fields.Char('Template code')

    def get_tmpl_bom_id(self):
        for product in self:
            bom_ids = self.env['mrp.bom'].search(
                [('product_tmpl_id', '=', product.id), ('product_id', '=', False)])
            product.bom_id = bom_ids and bom_ids[0] or bom_ids

    def create_bom(self):
        """Create Template BOM"""
        res = self.env['mrp.bom']

        for product_tmpl in self:

            if product_tmpl.is_product_variant:
                raise UserError("product.template create_bom")

            if not product_tmpl.bom_id:
                product_tmpl.get_tmpl_bom_id()

            if not product_tmpl.bom_id:
                # New template BOM
                bom_vals = {'product_tmpl_id': product_tmpl.id, 'type': 'normal'}
                new_bom = self.env['mrp.bom'].create(bom_vals)
                new_bom.create_attribute_value()
                product_tmpl.bom_id = new_bom
                res |= new_bom

        return res

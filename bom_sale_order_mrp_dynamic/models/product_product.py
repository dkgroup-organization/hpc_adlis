# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = "product.product"

    bom_id = fields.Many2one('mrp.bom', 'BOM', compute='get_bom_id', store=True)
    bom_line_ids = fields.One2many('mrp.bom.line', related='bom_id.bom_line_ids', string="BOM line")

    def get_bom_id(self):
        for product in self:
            bom_ids = self.env['mrp.bom'].search([('product_id', '=', product.id)])
            product.bom_id = bom_ids and bom_ids[0] or bom_ids

    def create_bom(self, default=None):
        "Create BOM with information from template BOM"
        for product in self:
            # Check starting condition
            if not product.is_product_variant:
                raise UserError("product.product create_bom error")
            if not product.bom_id:
                product.get_bom_id()
            if product.bom_id:
                continue

            if not product.product_tmpl_id.bom_id:
                product.product_tmpl_id.get_tmpl_bom_id()
                if not product.product_tmpl_id.bom_id:
                    raise UserError("There is no template of bill of material for this product: %s"
                                    "\n Please, create bill of material on the template product before" % product.name)

            # Create new BOM based on template BOM
            new_bom = product.product_tmpl_id.bom_id.copy(default or {})
            unlink_line = self.env['mrp.bom.line']

            # adjust BOM line with constraints, mrp.bom._check_bom_lines() must be ok
            for bom_line in new_bom.bom_line_ids:
                # Check the constraint
                constraint_attribute = {}
                # list the attribute needed
                for attribute_value in bom_line.bom_product_template_attribute_value_ids:
                    if attribute_value.attribute_id.id not in list(constraint_attribute.keys()):
                        constraint_attribute[attribute_value.attribute_id.id] = attribute_value
                    else:
                        constraint_attribute[attribute_value.attribute_id.id] |= attribute_value
                # Check the attribute needed
                for attribute_value in product.product_template_attribute_value_ids:
                    if attribute_value.attribute_id.id in list(constraint_attribute.keys()):
                        if attribute_value not in constraint_attribute[attribute_value.attribute_id.id]:
                            unlink_line |= bom_line

            # Update line
            unlink_line.unlink()
            for bom_line in new_bom.bom_line_ids:
                bom_line.bom_product_template_attribute_value_ids = False
            # update bom
            new_bom.product_id = product
            product.bom_id = new_bom
            new_bom.create_attribute_value()
            new_bom.compute_line()





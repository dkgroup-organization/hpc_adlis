
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval
import unicodedata

import logging
_logger = logging.getLogger(__name__)


class MrpRoutingWorkcenterGroup(models.Model):
    _name = 'mrp.routing.workcenter.group'
    _description = 'Work Center operation group'

    name = fields.Char('name')


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    group_id = fields.Many2one('mrp.routing.workcenter.group', 'Group')
    python_compute = fields.Text(string='Python Code', default="",
                                 help="Compute the new time.\n\n"
                                      ":param line: actual operation line\n"
                                      ":param attribute: dictionary with attribute value\n\n"
                                      "Return value by create variable:\n"
                                      "time_cycle_manual = float\n")

    parent_product_tmpl_id = fields.Many2one('product.template', 'Parent Product Template',
                                             related='bom_id.product_tmpl_id')
    possible_bom_product_template_attribute_value_ids = fields.Many2many('product.template.attribute.value', compute='_compute_possible_bom_product_template_attribute_value_ids')
    bom_product_template_attribute_value_ids = fields.Many2many(
        'product.template.attribute.value', string="Apply on Variants", ondelete='restrict',
        domain="[('id', 'in', possible_bom_product_template_attribute_value_ids)]",
        help="BOM Product Variants needed to apply this line.")

    @api.depends(
        'parent_product_tmpl_id.attribute_line_ids.value_ids',
        'parent_product_tmpl_id.attribute_line_ids.attribute_id.create_variant',
        'parent_product_tmpl_id.attribute_line_ids.product_template_value_ids.ptav_active',
    )
    def _compute_possible_bom_product_template_attribute_value_ids(self):
        for line in self:
            line.possible_bom_product_template_attribute_value_ids = line.parent_product_tmpl_id.valid_product_template_attribute_line_ids._without_no_variant_attributes().product_template_value_ids._only_active()

    def compute_line(self, data={}):
        """ Compute the python code on template to complete the product value"""
        return self.env['product.template'].compute_python_code(self)
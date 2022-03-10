# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval
import logging
_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = "product.product"

    bom_id = fields.Many2one('mrp.bom', 'BOM', compute='get_bom_id', store=True)
    bom_line_ids = fields.One2many('mrp.bom.line', related='bom_id.bom_line_ids', string="BOM line")
    compute_input = fields.Char('Compute input')
    compute_output = fields.Char('Compute output')

    def compute_python_old(self, data={}):
        """ Compute the python code on template to complete the product value"""
        for product in self:
            res = {}
            if product.python_compute:
                localdict = data.copy()
                localdict.update({'product': product})
                if product.bom_id:
                    localdict.update(product.bom_id.get_attribute_value())

                # Check ambiguity
                for attribute, value in localdict.items():
                    if hasattr(product, attribute):
                        raise ValidationError(
                            "The parameters name %s is reserved on product" % attribute)

                # Execute safe code, return localdict with result
                safe_eval(product.python_compute, localdict, mode="exec", nocopy=True)

                for attribute, value in localdict.items():
                    if len(attribute) and attribute[0] == "_":
                        continue
                    if hasattr(product, attribute):
                        try:
                            setattr(product, attribute, value)
                        except:
                            _logger.warning("This value cannot be loading product.id = %s value : %s; %s" % (product.id, attribute, value))

    def compute_python_code(self, data={}):
        """ Compute the python code on template to complete the product value"""
        return self.env['product.template'].compute_python_code(self)

    def get_bom_id(self):
        for product in self:
            bom_ids = self.env['mrp.bom'].search([('product_id', '=', product.id)])
            product.bom_id = bom_ids and bom_ids[0] or bom_ids

    def create_bom(self, default=None):
        "Create BOM with information from template BOM"

        def check_constraint_attribute(lines, product):
            """ Unlink line when constraint is not ok, the lines can be :
            """
            unlink_line = self.env[lines._name]

            for line in lines:
                # Check the constraint
                constraint_attribute = {}
                # list the attribute needed
                for attribute_value in line.bom_product_template_attribute_value_ids:
                    if attribute_value.attribute_id.id not in list(constraint_attribute.keys()):
                        constraint_attribute[attribute_value.attribute_id.id] = attribute_value
                    else:
                        constraint_attribute[attribute_value.attribute_id.id] |= attribute_value
                # Check the attribute needed
                for attribute_value in product.product_template_attribute_value_ids:
                    if attribute_value.attribute_id.id in list(constraint_attribute.keys()):
                        if attribute_value not in constraint_attribute[attribute_value.attribute_id.id]:
                            unlink_line |= line
            # Update line
            for line in lines:
                line.bom_product_template_attribute_value_ids = False
            unlink_line.unlink()

        # start
        for product in self:
            # Check starting condition
            if not product.bom_id:
                product.get_bom_id()
            if product.bom_id:
                continue
            if not product.product_tmpl_id.bom_id:
                product.product_tmpl_id.get_tmpl_bom_id()
                if not product.product_tmpl_id.bom_id:
                    continue
            # Create new BOM based on template BOM
            new_bom = product.product_tmpl_id.bom_id.copy(default or {})
            check_constraint_attribute(new_bom.bom_line_ids, product)
            check_constraint_attribute(new_bom.operation_ids, product)

            # update bom
            new_bom.product_id = product
            product.bom_id = new_bom
            new_bom.create_attribute_value()
            new_bom.compute_line()





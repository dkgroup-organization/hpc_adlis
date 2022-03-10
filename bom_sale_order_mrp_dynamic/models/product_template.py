# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    bom_id = fields.Many2one('mrp.bom', 'Template Bill of material', compute='get_tmpl_bom_id', store=True)
    bom_line_ids = fields.One2many('mrp.bom.line', related='bom_id.bom_line_ids', string="BOM line")
    template_code = fields.Char('Template code')
    jit_production = fields.Boolean('JIT production', default=True)
    python_compute = fields.Text(string='Python Code', default="",
                                 help="Compute variant value.\n\n"
                                      ":param attribute: dictionary with attribute value\n\n"
                                      "Return value by create variable:\n"
                                      "product_list_price = float\n"
                                      "product_lst_price = float\n"
                                      "product_price = float\n"
                                      "product_price_extra = float\n"
                                      "product_standard_price = float\n"
                                      "product_code = float\n"
                                       )

    @api.model
    def compute_python_code(self, objects,  data={}):
        """ Compute the python code on set of object with field  python_compute """
        res = {}
        for obj in objects:
            res[obj.id] = {}
            if hasattr(obj, 'python_compute') and obj.python_compute:
                localdict = data.copy()
                localdict.update({'object': obj})
                if hasattr(obj, 'bom_id') and obj.bom_id:
                    localdict.update(obj.bom_id.get_attribute_value())

                # Check ambiguity
                for attribute, value in localdict.items():
                    if hasattr(obj, attribute):
                        raise ValidationError(
                            "The parameters name (%s) is reserved on object %s" % (attribute, obj._name))

                # Execute safe code, return localdict with result
                safe_eval(obj.python_compute, localdict, mode="exec", nocopy=True)

                for attribute, value in localdict.items():
                    if len(attribute) and attribute[0] == "_":
                        continue

                    res[obj.id].update({attribute: value})

                    if hasattr(obj, attribute):
                        try:
                            setattr(obj, attribute, value)
                        except:
                            _logger.warning("This value cannot be loading %s.id = %s value : %s; %s"
                                             % (obj.id, obj._name, attribute, value))
        return res

    def update_variant_compute(self, data={}):
        """ Update all variant price if python_compute_price is defined"""
        for product_tmpl in self:
            for product in product_tmpl.product_variant_ids:
                self.compute_python_code(product, data)

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

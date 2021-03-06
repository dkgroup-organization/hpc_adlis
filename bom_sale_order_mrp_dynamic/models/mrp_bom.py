
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval

import logging
_logger = logging.getLogger(__name__)


def convert_to_float(text):
    "convert to float"
    out_str = ""
    for char in text:
        if char.isnumeric() or char in [',', '.']:
            out_str += char
        # TODO: Use Country decimal notation
    out_str = out_str.replace(',', '.')
    return float(out_str or 0.0)


class MrpBomParameter(models.Model):
    _name = "mrp.bom.parameter"
    _description = "Parameter value for computing and search"

    bom_id = fields.Many2one('mrp.bom', 'Bill of materials')
    attribute_id = fields.Many2one('product.attribute', 'Attribute')
    name = fields.Char('name')
    value = fields.Char('Value')

    @api.onchange('value')
    def onchange_value(self):
        """on change convert to float if needed"""
        if self.attribute_id.convert_type == 'float':
            self.value = convert_to_float(self.value)


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    parameter_ids = fields.One2many('mrp.bom.parameter', 'bom_id', string='Parameters')
    sale_line_id = fields.Many2one('sale.order.line', "Sale line")
    sale_id = fields.Many2one('sale.order', 'Sale order', related='sale_line_id.order_id')

    def compute_line(self, data={}):
        """Compute the line"""
        for bom in self:
            for line in bom.bom_line_ids:
                line.compute_line(data=data)

    def get_attribute_value(self):
        """Get attribute value with conversion to float or text"""
        self.ensure_one()
        res = {}
        for line in self.parameter_ids:
            # Exception for use with bom.line.compute_line(): ['product_qty', 'product_id']:
            if line.name in ['product_qty', 'product_id']:
                raise ValidationError("The parameters name product_id or product_qty is reserved for output value")
            if line.attribute_id and line.attribute_id.convert_type == 'float':
                value = convert_to_float(line.value)
            else:
                value = line.value
            res.update({line.name: value})
        return res

    def update_custom_value(self):
        """ Get custom value"""
        self.ensure_one()
        res = {}
        for custom in self.sale_line_id.product_custom_attribute_value_ids:
            custom_attribute = custom.custom_product_template_attribute_value_id.attribute_id
            custom_value = custom.custom_value
            res.update({str(custom_attribute.id): custom_value})
        for line in self.parameter_ids:
            if str(line.attribute_id.id) in list(res.keys()):
                line.value = res[str(line.attribute_id.id)]
                line.onchange_value()
        return res

    def create_attribute_value(self):
        """Get attribute value with conversion to float or text"""
        for bom in self:
            for line in self.product_id.product_template_attribute_value_ids:
                attribute_id = line.attribute_id.id
                condition = [('bom_id', '=', bom.id), ('attribute_id', '=', attribute_id)]
                parameter_ids = self.env['mrp.bom.parameter'].search(condition)

                if not parameter_ids:
                    parameters_vals = {
                        'bom_id': bom.id,
                        'attribute_id': attribute_id,
                        'name': line.attribute_id.name,
                        'value': line.name,
                    }
                    parameter = self.env['mrp.bom.parameter'].create(parameters_vals)
                else:
                    parameter = parameter_ids[0]
                    parameter.value = line.name
                parameter.onchange_value()
            bom.update_custom_value()


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    python_compute = fields.Text(string='Python Code', default="",
                                 help="Compute the new quantity and product.\n\n"
                                      ":param BOM_line: actual BOM line\n"
                                      ":param attribute: dictionary with attribute value\n\n"
                                      "Return value by create variable:\n"
                                      "product_qty = float\n"
                                      "product_id = product.product recordset singleton\n")

    def compute_line(self, data={}):
        """Compute the line"""

        for BOM_line in self:

            if BOM_line.python_compute:
                localdict = data.copy()
                localdict.update(BOM_line.bom_id.get_attribute_value())
                localdict.update({'BOM_line': BOM_line})
                # Execute safe code, return localdict with result
                safe_eval(BOM_line.python_compute, localdict, mode="exec", nocopy=True)

                if localdict.get('product_id'):
                    BOM_line.product_id = localdict['product_id']

                if localdict.get('product_qty'):
                    BOM_line.product_qty = localdict['product_qty']





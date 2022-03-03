# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.osv import expression

class InventoryLine(models.Model):
    _inherit = "stock.inventory.line"

    packaging_qty = fields.Float("Pack Qty", default=1.0)
    product_packaging = fields.Many2one('product.packaging', string='Package', default=False, check_company=True)

    @api.onchange('packaging_qty')
    def _onchange_packaging_qty(self):
        "change qty if package is set"
        self.ensure_one()
        if self.product_packaging:
            self.product_qty = self.packaging_qty * self.product_packaging.qty
        else:
            self.product_qty = self.packaging_qty

    @api.onchange('product_packaging')
    def _onchange_product_packaging(self):
        self.ensure_one()
        if self.product_packaging:
            self.packaging_qty = 1.0
        self._onchange_packaging_qty()

class Inventory(models.Model):
    _inherit = "stock.inventory"

    packaging_qty = fields.Float("Pack Qty", default=1.0)
    product_packaging = fields.Many2one('product.packaging', string='Package', default=False, check_company=True)

    def _get_quantities(self):
        """Return quantities group by product_id, location_id, lot_id, package_id and owner_id

        :return: a dict with keys as tuple of group by and quantity as value
        :rtype: dict
        """
        self.ensure_one()
        if self.location_ids:
            domain_loc = [('id', 'child_of', self.location_ids.ids)]
        else:
            domain_loc = [('company_id', '=', self.company_id.id), ('usage', 'in', ['internal', 'transit'])]
        locations_ids = [l['id'] for l in self.env['stock.location'].search_read(domain_loc, ['id'])]

        domain = [('company_id', '=', self.company_id.id),
                  ('quantity', '!=', '0'),
                  ('location_id', 'in', locations_ids)]
        if self.prefill_counted_quantity == 'zero':
            domain.append(('product_id.active', '=', True))

        if self.product_ids:
            domain = expression.AND([domain, [('product_id', 'in', self.product_ids.ids)]])

        fields = ['product_id', 'location_id', 'lot_id', 'package_id', 'owner_id', 'quantity:sum', 'packaging_qty', 'product_packaging']
        group_by = ['product_id', 'location_id', 'lot_id', 'package_id', 'owner_id', 'product_packaging']

        quants = self.env['stock.quant'].read_group(domain, fields, group_by, lazy=False)
        return {(
                    quant['product_id'] and quant['product_id'][0] or False,
                    quant['location_id'] and quant['location_id'][0] or False,
                    quant['lot_id'] and quant['lot_id'][0] or False,
                    quant['package_id'] and quant['package_id'][0] or False,
                    quant['product_packaging'] and quant['product_packaging'][0] or False,
                    quant['owner_id'] and quant['owner_id'][0] or False):
                    (quant['quantity'], quant['packaging_qty'])for quant in quants
                }

    def _get_inventory_lines_values(self):
        """Return the values of the inventory lines to create for this inventory.

        :return: a list containing the `stock.inventory.line` values to create
        :rtype: list
        """
        self.ensure_one()
        quants_groups = self._get_quantities()
        vals = []
        for (product_id, location_id, lot_id, package_id, product_packaging, owner_id), (quantity, packaging_qty) in quants_groups.items():
            line_values = {
                'inventory_id': self.id,
                'product_qty': 0 if self.prefill_counted_quantity == "zero" else quantity,
                'theoretical_qty': quantity,
                'prod_lot_id': lot_id,
                'partner_id': owner_id,
                'product_id': product_id,
                'location_id': location_id,
                'package_id': package_id,
                'product_packaging': product_packaging,
                'packaging_qty': packaging_qty,
            }
            line_values['product_uom_id'] = self.env['product.product'].browse(product_id).uom_id.id
            vals.append(line_values)
        if self.exhausted:
            vals += self._get_exhausted_inventory_lines_vals({(l['product_id'], l['location_id']) for l in vals})
        return vals

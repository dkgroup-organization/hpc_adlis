# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    packaging_qty = fields.Float("Pack Qty", default=1.0)
    product_packaging = fields.Many2one('product.packaging', string='Package', default=False, check_company=True)

    @api.model
    def _get_inventory_fields_create(self):
        """ Returns a list of fields user can edit when he want to create a quant in `inventory_mode`.
        """
        return ['product_id', 'location_id', 'lot_id', 'package_id', 'owner_id', 'inventory_quantity', 'packaging_qty', 'product_packaging']

    @api.model
    def _get_inventory_fields_write(self):
        """ Returns a list of fields user can edit when he want to edit a quant in `inventory_mode`.
        """
        return ['inventory_quantity', 'packaging_qty', 'product_packaging']

    def _onchange_packaging_qty(self):
        "change qty if package is set"
        self.ensure_one()
        if self.product_packaging:
            self.inventory_quantity = self.packaging_qty * self.product_packaging.qty
        else:
            self.inventory_quantity = self.packaging_qty

    @api.onchange('product_packaging')
    def _onchange_product_packaging(self):
        self.ensure_one()
        if self.product_packaging:
            self.packaging_qty = 1.0
        self._onchange_packaging_qty()

    def write(self, vals):
        """ Override to handle the "inventory mode" and create the inventory move. """
        allowed_fields = self._get_inventory_fields_write()
        if self._is_inventory_mode() and any(field for field in allowed_fields if field in vals.keys()):
            if any(quant.location_id.usage == 'inventory' for quant in self):
                # Do nothing when user tries to modify manually a inventory loss
                return
            if any(field for field in vals.keys() if field not in allowed_fields):
                raise UserError(_("Quant's editing is restricted, you can't do this operation."))
            self = self.sudo()
            if vals.get('product_packaging'):
                product_packaging_id = vals['product_packaging']
                product_packaging_qty = self.env['product.packaging'].browse(product_packaging_id).qty
                if vals.get('packaging_qty'):
                    vals['inventory_quantity'] = vals['packaging_qty'] * product_packaging_qty
                else:
                    vals['inventory_quantity'] = self.packaging_qty * product_packaging_qty
            else:
                if vals.get('packaging_qty'):
                    if self.product_packaging and self.product_packaging.qty:
                        vals['inventory_quantity'] = vals['packaging_qty'] * self.product_packaging.qty
                    else:
                        vals['inventory_quantity'] = vals['packaging_qty']
            return super(StockQuant, self).write(vals)

        return super(StockQuant, self).write(vals)

    @api.model
    def create(self, vals):
        """ Override to handle the "inventory mode" and create a quant as
        superuser the conditions are met.
        """
        if self._is_inventory_mode() and 'inventory_quantity' in vals:
            allowed_fields = self._get_inventory_fields_create()
            if any(field for field in vals.keys() if field not in allowed_fields):
                raise UserError(_("Quant's creation is restricted, you can't do this operation."))
            inventory_quantity = vals.pop('inventory_quantity')

            # Create an empty quant or write on a similar one.
            product = self.env['product.product'].browse(vals['product_id'])
            location = self.env['stock.location'].browse(vals['location_id'])
            lot_id = self.env['stock.production.lot'].browse(vals.get('lot_id'))
            package_id = self.env['stock.quant.package'].browse(vals.get('package_id'))
            owner_id = self.env['res.partner'].browse(vals.get('owner_id'))
            quant = self._gather(product, location, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=True)
            if quant:
                quant = quant[0]
            else:
                quant = self.sudo().create(vals)

            # Set the `inventory_quantity` field to create the necessary move.
            if vals.get('product_packaging'):
                if vals.get('packaging_qty'):
                    product_packaging_id = vals['product_packaging']
                    product_packaging_qty = self.env['product.packaging'].browse(product_packaging_id).qty
                    inventory_quantity = vals['packaging_qty'] * product_packaging_qty
            else:
                if vals.get('packaging_qty'):
                    if self.product_packaging and self.product_packaging.qty:
                        inventory_quantity = vals['packaging_qty'] * self.product_packaging.qty
                    else:
                        inventory_quantity = vals['packaging_qty']
            # Set the `inventory_quantity` field to create the necessary move.
            if quant:
                quant.product_packaging = vals['product_packaging']
                quant.packaging_qty = vals['packaging_qty']
                quant.inventory_quantity = inventory_quantity
            return quant
        res = super(StockQuant, self).create(vals)
        if self._is_inventory_mode():
            res._check_company()
        return res

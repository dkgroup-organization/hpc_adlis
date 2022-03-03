# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    packaging_qty = fields.Float("Pack Qty", default=1.0)
    product_packaging = fields.Many2one('product.packaging', string='Package', default=False, check_company=True)

    def _prepare_account_move_line(self, move=False):
        res = super()._prepare_account_move_line(move)

        if self.product_packaging.qty:
            res['product_packaging'] = self.product_packaging.id
            res['packaging_qty'] = res['quantity'] / self.product_packaging.qty
        else:
            res['product_packaging'] = False
            res['packaging_qty'] = res['quantity']

        return res

    @api.onchange('packaging_qty')
    def onchange_packaging_qty(self):
        "change qty if package is set"
        if self.product_packaging:
            self.product_qty = self.packaging_qty * self.product_packaging.qty
        else:
            self.product_qty = self.packaging_qty

    @api.onchange('product_packaging')
    def _onchange_product_packaging(self):
        if self.product_packaging:
            self.packaging_qty = 1.0
        self.onchange_packaging_qty()

    @api.onchange('product_id')
    def onchange_product_id(self):
        if not self.product_id:
            return

        # Reset date, price and quantity since _onchange_quantity will provide default values
        self.price_unit = self.product_qty = 0.0

        self._product_id_change()

        self._suggest_quantity()
        self._onchange_quantity()

        self.product_packaging = None
        self.packaging_qty = 1.0

        if self.product_id.sale_unit:
            for line in self.product_id.packaging_ids:
                if line.sale_unit == self.product_id.sale_unit:
                    self.product_packaging = line.id
                    self.product_qty = self.product_packaging.qty
                    break

    def _prepare_stock_moves(self, picking):
        res = super(PurchaseOrderLine, self)._prepare_stock_moves(picking)

        if self.product_packaging.qty:
            res[0]['product_packaging'] = self.product_packaging.id
            res[0]['packaging_qty'] = res[0]['product_uom_qty'] / self.product_packaging.qty
        else:
            res[0]['packaging_qty'] = res[0]['product_uom_qty']
            res[0]['product_packaging'] = False

        return res



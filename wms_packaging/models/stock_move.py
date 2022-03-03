# -*- coding: utf-8 -*-

from odoo import models, fields, api

import logging
_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    packaging_qty = fields.Float("UV Qty")
    product_packaging = fields.Many2one('product.packaging', string="UV")

    @api.onchange('packaging_qty')
    def onchange_packaging_qty(self):
        "change qty if package is set"
        if self.product_packaging:
            self.product_uom_qty = self.packaging_qty * self.product_packaging.qty
        else:
            self.product_uom_qty = self.packaging_qty

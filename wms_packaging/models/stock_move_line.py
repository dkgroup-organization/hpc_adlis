# -*- coding: utf-8 -*-

from odoo import api, exceptions, fields, models, _


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def _get_aggregated_product_quantities(self, **kwargs):

        aggregated_move_lines = super(StockMoveLine, self)._get_aggregated_product_quantities(**kwargs)

        i = 0
        list_packaging_qty = self.move_id.mapped('packaging_qty')
        list_product_packaging = self.move_id.mapped('product_packaging')
        for aggregated_move_line in aggregated_move_lines:
            aggregated_move_lines[aggregated_move_line]['packaging_qty'] = list_packaging_qty[i]
            aggregated_move_lines[aggregated_move_line]['product_packaging'] = list_product_packaging[i].name
            i = i + 1

        return aggregated_move_lines

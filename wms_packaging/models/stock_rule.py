# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, company_id, values):
        move_values = super(StockRule, self)._get_stock_move_values(product_id, product_qty, product_uom, location_id, name, origin, company_id, values)
        if move_values.get('sale_line_id'):
            sale_line_id = self.env['sale.order.line'].browse(move_values['sale_line_id'])

            if sale_line_id and sale_line_id.product_packaging.qty:
                move_values['product_packaging'] = sale_line_id.product_packaging.id
                move_values['packaging_qty'] = move_values['product_uom_qty'] / sale_line_id.product_packaging.qty
            else:
                move_values['packaging_qty'] = move_values['product_uom_qty']
                move_values['product_packaging'] = False
        return move_values

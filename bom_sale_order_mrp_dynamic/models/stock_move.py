from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _prepare_procurement_values(self):
        values = super()._prepare_procurement_values()

        if self.sale_line_id and self.sale_line_id.bom_id:
            values['bom_id'] = self.sale_line_id.bom_id
        return values

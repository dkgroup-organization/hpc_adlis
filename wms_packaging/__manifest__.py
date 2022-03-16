# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'WMS packaging',
    'version': '14.0.1',
    'category': 'Base',
    'summary': 'WMS packaging',
    'description': """
This module contains the customization packaging

    """,
    'depends': ['sale', 'stock', 'sale_stock', 'delivery', 'account'],
    'data': [
    	"views/account_move_views.xml",
    	"views/stock_picking_views.xml",
    	"views/sale_order_views.xml",
    	"views/purchase_order_views.xml",
    	"views/stock_quant_views.xml",
    	"views/stock_inventory_line.xml",
    	"report/sale_order_report_template.xml",
    	"report/report_invoice.xml",
    	"report/report_deliveryslip.xml",
    	"report/purchase_report_template.xml",
    ],
    'demo': [

    ],
    'installable': True,
    'auto_install': False
}

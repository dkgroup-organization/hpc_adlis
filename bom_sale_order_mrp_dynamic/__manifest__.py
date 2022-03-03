# -*- coding: utf-8 -*-
{
    'name': "Create BoM in sale order line with dynamic attributes ",

    'summary': """
        create BOM in your sale order with dynamic attributes
        """,

    'description': """
        Add BOM to Sale order line with dynamic attributes. Also you can view the Sale order in your Manufacture order
    """,

    'author': "Abdelghani khalidi",
    'category': 'Sales',
    'version': '14.0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale_management', 'mrp'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_view.xml',
        'views/product_view.xml',
        'views/mrp_bom_view.xml',
        'views/mrp_routing_workcenter_view.xml',
        'views/mrp_routing_workcenter_group_view.xml',
        'views/product_attribute_view.xml',
    ],
    # only loaded in demonstration mode
}

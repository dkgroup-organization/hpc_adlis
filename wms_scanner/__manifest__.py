# 2020 Joannes Landy <joannes.landy@opencrea.fr>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'WMS Scanner',
    'summary': 'Allows managing barcode readers with complex scenarios',
    'version': '13.0.1.0.1',
    'category': 'Generic Modules/Inventory Control',
    'website': 'https://opencrea.fr',
    'author': 'OpenCrea',
    'license': 'AGPL-3',
    'application': True,
    'installable': True,
    'depends': [
        'product',
        'stock',
    ],
    'data': [
        #'security/stock_scanner_security.xml',
        #
        #'data/stock_scanner.xml',
        #'data/ir_cron.xml',
        #'data/scenarios/Login/Login.scenario',
        #'data/scenarios/Logout/Logout.scenario',
        #'data/scenarios/Stock/Stock.scenario',
        #'wizard/res_config_settings.xml',

        #'views/scanner_scenario.xml',
        #'views/scanner_scenario_step.xml',
        #'views/scanner_scenario_transition.xml',
        #'views/scanner_hardware.xml',
        
        'views/wms_scenario.xml',
        'views/wms_menu.xml',

        'views/menu.xml',
        'views/wms_scanner_menu_template.xml',
        'views/wms_scanner_scenario_template.xml',
        'views/wms_scanner_blank_template.xml',
        'views/wms_scanner_zxing_template.xml',
        'views/wms_scanner_zxing2_template.xml',

        'security/ir.model.access.csv',

    ],
    'demo': [
    ],
    'images': [
    ],
}

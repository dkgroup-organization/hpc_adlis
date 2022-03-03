# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import urllib

SRC_PATH = 'stock_http_scanner/static/src/'
IMG_PATH = SRC_PATH + 'img/'
CSS_FILE = SRC_PATH + "css/screen_240.css"
IMG_FLAG = {'fr_FR': 'flag-fr.jpg', 'en_US': 'flag-gb.jpg', 'nl_BE': 'flag-be.jpg', 'de_DE': 'flag-de.jpg'}


class WmsSession(models.Model):
    _name = "wms.session"
    _description = "Scanner session"

    def _default_warehouse(self):
        "find the user warehouse"
        return self.env['stock.warehouse'].search([])[0]

    name = fields.Char('Session', required=True, index=True)
    ip = fields.Char('IP', index=True)
    debug = fields.Boolean('Debug')
    start_date = fields.Datetime('Start Date')
    end_date = fields.Datetime('End Date')

    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse', default=_default_warehouse)
    css = fields.Char('CSS', default=CSS_FILE)

    state = fields.Selection(string='Status', selection=[
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),
        ('confirm', 'In Progress'),
        ('done', 'Done')],
        copy=False, index=True, readonly=True,
        default='draft')

    def index(self, response, scanner_data):
        "start new response"

        data = {
            'response': response,
            'scanner_data': scanner_data,
            'img_path': IMG_PATH,
            }

        list_function = list(dir(self))

        try:
            if not response:
                data = self.menu_main(data)

            elif response.get('menu') or scanner_data.get('menu'):
                function_name = 'menu_' + (response.get('menu') or scanner_data.get('menu'))
                #Load menu, the function name must start with menu_
                if function_name in list_function:
                    data = eval('self.' + function_name + '(data)')
                else:
                    data = self.page_blank(data)

            elif response.get('page'):
                function_name = 'page_' + response['page']
                #show page, the function name must start with page_
                if function_name in list_function:
                    data = eval('self.' + function_name + '(data)')
                else:
                    data = self.page_blank(data)

            elif response.get('configure'):
                #Execute configuration
                if response['configure'] == 'debug':
                    self.debug = not self.debug
                    data = self.menu_configure(data)
                elif response['configure'] == 'logout':
                    data.update({'logout': True})
                elif response['configure'] == 'return_wms':
                    data.update({'return_wms': True})
                elif response['configure'] == 'language':
                    language = self.env['res.lang'].browse(int(response['id']))
                    if self.env.user.lang != language.code:
                        self.env.user.write({'lang': language.code})
                        data.update({'logout': True})
                    else:
                        data = self.menu_configure(data)
                elif response['configure'] == 'screen':
                    if response.get('size', '') == '240':
                        self.css = SRC_PATH + "css/screen_240.css"
                        data = self.menu_main(data)
                    elif response.get('size', '') == '320':
                        self.css = SRC_PATH + "css/screen_320.css"
                        data = self.menu_main(data)
                    elif response.get('size', '') == '480':
                        self.css = SRC_PATH + "css/screen_480.css"
                        data = self.menu_main(data)
                    else:
                        data = self.menu_screen(data)
                else:
                    data = self.page_blank(data)

            else:
                data = self.page_blank(data)

        except:
            data = self.page_blank(data)
            data['error'] = 'Server error'

        #Screen Size
        if self.css:
            data['css'] = self.css or CSS_FILE

        #Debug mode
        if self.debug:
            data = self.page_debug(data)

        return data

    def menu_main(self, data):
        "Create data main menu"
        #header table data
        data['page_header'] = {'left_img': 'run-build-configure.jpg', 'left_href': '?menu=configure', 'logo_img': 'logo.jpg', 'right_name': self.env.user.name}
        data['scanner_data'] = {'menu_main': True}

        menu = []
        menu.append({'left_img': 'scan_codebarre.jpg', 'left_href': '?page=scaninfo', 'right_txt': _('Information')})
        menu.append({'left_img': 'zoom-3.jpg', 'left_href': '?page=receipt', 'right_txt': _('Receipt')})
        menu.append({'left_img': 'product_move.jpg', 'left_href': '?page=product_move', 'right_txt': _('Moving')})
        menu.append({'left_img': 'product_inventory.jpg', 'left_href': '?page=product_inventory', 'right_txt': _('Inventory')})
        menu.append({'left_img': 'edit-paste-4.jpg', 'left_href': '?page=preparation', 'right_txt': _('Preparation')})
        #menu.append({'left_img': 'expedition.jpg', 'left_href': '?page=expedition', 'right_txt': _('Expedition')})
        menu.append({'left_img': 'pack.jpg', 'left_href': '?menu=packing', 'right_txt': _('Packing')})

        data.update({'menu': menu})

        return data

    def menu_screen(self, data):
        "screen menu"
        data['page_header'] = {'left_img': 'run-build-configure.jpg', 'left_href': '?menu=configure', 'logo_img': 'logo.jpg', 'right_name': self.env.user.name}

        menu = []
        menu.append({'left_img': 'view-fullscreen-8.jpg', 'left_href': '?configure=screen&size=240', 'right_txt': _('Screen 240 px')})
        menu.append({'left_img': 'view-fullscreen-8.jpg', 'left_href': '?configure=screen&size=320', 'right_txt': _('Screen 320 px')})
        menu.append({'left_img': 'view-fullscreen-8.jpg', 'left_href': '?configure=screen&size=480', 'right_txt': _('Screen 480 px')})
        data.update({'menu': menu})

        return data

    def menu_language(self, data):
        "language menu"
        #header table data
        data['page_header'] = {'left_img': 'run-build-configure.jpg', 'left_href': '?menu=configure', 'logo_img': 'logo.jpg', 'right_name': self.env.user.name}

        menu = []
        for language in self.env['res.lang'].search([('active', '=', True)]):
            menu_item = {'left_href': '?configure=language&id=' + str(language.id), 'right_txt': language.display_name}

            if language.code in IMG_FLAG:
                menu_item['left_img'] = IMG_FLAG[language.code]

            menu.append(menu_item)

        data.update({'menu': menu})

        return data

    def menu_configure(self, data):
        "choice language"

        "Create data configure menu"
        #header table data
        data['page_header'] = {'left_img': 'go-home-5.jpg', 'left_href': '?menu=main', 'logo_img': 'logo.jpg', 'right_name': self.env.user.name}

        menu = []
        menu.append({'left_img': 'view-choose-3.jpg', 'left_href': '?configure=return_wms', 'right_txt': _('Return to WMS')})
        menu.append({'left_img': 'user-exit.jpg', 'left_href': '?configure=logout', 'right_txt': _('Disconnect')})

        #language
        menu_item = {'left_href': '?menu=language', 'right_txt': _('Language')}
        if self.env.user.lang in IMG_FLAG:
            menu_item['left_img'] = IMG_FLAG[self.env.user.lang]
        menu.append(menu_item)

        menu.append({'left_img': 'view-fullscreen-8.jpg', 'left_href': '?configure=screen', 'right_txt': _('Screen size')})
        menu.append({'left_img': 'scan.jpg', 'left_href': '?page=zxing', 'right_txt': _('Scanner ZXING')})
        menu.append({'left_img': 'tools-report-bug.jpg', 'left_href': '?configure=debug', 'right_txt': _('Mode debug')})
        data.update({'menu': menu})

        return data

    def menu_packing(self, data):
        "screen menu"
        data['page_header'] = {'left_img': 'go-home-5.jpg', 'left_href': '?menu=main', 'logo_img': 'logo.jpg', 'right_name': self.env.user.name}

        menu = []
        menu.append({'left_img': 'printer.jpg', 'left_href': '?page=pack_print', 'right_txt': _('Print pack label')})
        menu.append({'left_img': 'pack_add.jpg', 'left_href': '?page=pack_add', 'right_txt': _('Add Product')})
        menu.append({'left_img': 'pack_supp.jpg', 'left_href': '?page=pack_supp', 'right_txt': _('Pick Product')})
        menu.append({'left_img': 'software-update-unavailable.jpg', 'left_href': '?page=pack_delete', 'right_txt': _('Unpack all products')})
        menu.append({'left_img': 'pack_inventory.jpg', 'left_href': '?page=pack_inventory', 'right_txt': _('Pack Inventory')})
        menu.append({'left_img': 'pack_move.jpg', 'left_href': '?page=pack_move', 'right_txt': _('Pack move')})
        data.update({'menu': menu})

        return data

    def menu_product(self, data):
        "screen menu"
        data['page_header'] = {'left_img': 'go-home-5.jpg', 'left_href': '?menu=main', 'logo_img': 'logo.jpg', 'right_name': self.env.user.name}

        menu = []
        menu.append({'left_img': 'product_move.jpg', 'left_href': '?page=product_move', 'right_txt': _('Move product')})
        menu.append({'left_img': 'product_inventory.jpg', 'left_href': '?page=product_inventory', 'right_txt': _('Product inventory')})
        data.update({'menu': menu})

        return data

    def page_zxing(self, data):
        "Install google play scanner zxing"
        #https://play.google.com/store/apps/details?id=com.google.zxing.client.android

        #init value
        page_data = self.page_init_value(data)
        scan = self.read_scan(data)

        #Define scan_type to return
        map_scan_type = {'install_zxing': 'none'}

        #Start
        if page_data['scenario_step'] == 'start':
            page_data['scenario_step'] = 'install_zxing'
            scan = {}

        #Scan Warning
        if scan.get('type', 'none') != 'none' and scan.get('warning'):
            page_data['warning'] = scan['warning']
            scan = {}

        #Install ZXING
        if page_data['scenario_step'] == 'install_zxing':
            page_data['origin_message'] = _('Go to this address to install Android scanner')
            page_data['origin_message'] += '<br/><center><a href="market://details?id=com.google.zxing.client.android">'
            page_data['origin_message'] += '<h1>Google Play<br/>Scanner ZXING</h1></a></center>'
            page_data['scenario_step'] = 'install_zxing'
            scan = {}

        #Return value
        page_data['scan_type'] = map_scan_type.get(page_data.get('scenario_step', 'start'), 'none')
        data.update(self.page_update_data(page_data))
        return data

    def page_debug(self, data):
        "page Debug"

        def list_dict(sub_data):
            "list data"
            if not sub_data:
                html = ""
            if type(sub_data) is dict:
                html = "<ul>"
                for key in list(sub_data.keys()):
                    if type(sub_data[key]) in [list, dict]:
                        html += '<li><b>%s: </b></li>' % (key)
                        html += list_dict(sub_data[key])
                    else:
                        html += '<li><b>%s: </b>%s</li>' % (key, sub_data[key])
                html += "</ul>"

            elif type(sub_data) is list:
                html = "<ul>"
                for idx, item in enumerate(sub_data):
                    if type(item) in [list, dict]:
                        html += '<li>[%s]:</li>' % (idx)
                        html += list_dict(item)
                    else:
                        html += '<li>[%s]: %s</li>' % (idx, item)
                html += "</ul>"

            else:
                html = "<li>%s</li>" % (sub_data)
            return html

        html = "<b>" + _("-- DATA --") + "</b><br/>" + list_dict(data)

        data.update({'debug_html': html})
        return data

    def page_scaninfo(self, data):
        "Information on barcode"
        #print "===page_scaninfo====", data

        #init value
        scan = self.read_scan(data)
        page_data = {
            'page': 'scaninfo',
            'scenario_step': 'scan_barcode',
            'scan_type': 'search'}

        #STEP 1: scan_barcode
        if scan.get('type', 'error') != 'error':
            condition = []
            if scan['type'] == 'product':
                page_data['product_id'] = scan['product'].id
                condition.append(['location_id.usage', '=', 'internal'])
                condition.append(['product_id', '=', scan['product'].id])
            elif scan['type'] == 'location':
                page_data['location_id'] = scan['location'].id
                condition.append(['location_id.usage', '=', 'internal'])
                condition.append(['location_id', '=', scan['location'].id])
            elif scan['type'] == 'pack':
                if scan['pack'].location_id:
                    page_data['pack_location_id'] = scan['pack'].location_id.id
                page_data['pack_id'] = scan['pack'].id
                condition.append(['id', 'in', [x.id for x in scan['pack'].children_quant_ids]])

            if condition:
                quants = self.env['stock.quant'].search(condition)
                if quants:
                    page_data['quant_ids'] = [x.id for x in quants]

        else:
            page_data['warning'] = _('This barcode is unknow: %s' % (scan.get('code')))

        scan = {}

        #Return value
        data.update(self.page_update_data(page_data))
        return data

    def read_scan(self, data):
        "Decode scan and return associated objects, use scan_type to search"
        res = {'base_code': '', 'code': '', 'type': 'error', 'value': 0, 'encoding': 'any'}

        def is_ascii(scan):
            try:
                scan.decode('ascii')
                return True
            except:
                return False

        #Scan-type is defined ?
        if not data['response'].get('scan'):
            res['type'] = 'none'
        elif data['response'].get('scan_type', 'none') == 'none':
            res['type'] = 'none'
        elif not is_ascii(data['response']['scan']):
            res.update({'warning': _("The barcode is unreadable")})
        elif data['response'].get('scan_type'):
            res.update(self.decode_scan_type(data['response']['scan'], data['response']['scan_type']))
        else:
            res['type'] = 'error'
        return res

    def decode_scan_type(self, scan, scan_type=False):
        "decode the barcode with scan_type and return associated objects"
        res = {'base_code': scan, 'code': scan, 'type': 'error', 'value': 0, 'encoding': 'any'}

        #TYPE: float
        if scan_type == 'float':
            try:
                res.update({'value': float(scan), 'type': 'float'})
            except:
                res.update({'warning': _("This value is not valid: %s" % (scan))})
        #TYPE: location
        elif scan_type == 'location':
            location_ids = self.env['stock.location'].search([('barcode', '=', scan)]) or \
                self.env['stock.location'].search([('name', '=', scan)])
            if len(location_ids) == 1:
                res.update({'location': location_ids[0], 'type': 'location'})
            else:
                res.update({'warning': _("There is a error with this barcode location: %s" % (scan))})
        #TYPE: printer
        elif scan_type == 'printer':
            printer_ids = self.env['printing.printer'].search([('barcode', '=', scan)]) or \
                self.env['printing.printer'].search([('name', '=', scan)])
            if len(printer_ids) == 1:
                res.update({'printer': printer_ids[0], 'type': 'printer'})
            else:
                res.update({'warning': _("There is a error with this barcode printer: %s" % (scan))})
        #TYPE: product
        elif scan_type == 'product':
            product_ids = self.env['product.product'].search([('barcode', '=', scan)]) or \
                    self.env['product.product'].search([('default_code', '=', scan)])
            if len(product_ids) == 1:
                res.update({'product': product_ids[0], 'type': 'product'})
            elif len(product_ids) > 1:
                res.update({'warning': _("This barcode reference %s products?") % (len(product_ids))})
            else:
                pack_ids = self.env['stock.quant.package'].search([('name', '=', scan)])
                if len(pack_ids) == 1:
                    res.update({'pack': pack_ids[0], 'type': 'pack'})
                else:
                    res.update({'warning': _("This barcode product is unknow: %s" % (scan))})
        #TYPE: picking_in
        elif scan_type == 'picking_in':
            picking_ids = self.env['stock.picking'].search([('name', '=', scan), ('picking_type_id.code', '=', 'incoming')])
            if len(picking_ids) == 1:
                res.update({'picking': picking_ids[0], 'type': 'picking_in'})
            else:
                res.update({'warning': _("This receipt is unknow: %s" % (scan))})

        #TYPE: picking_out expedition
        elif scan_type == 'picking_expedition':
            picking_ids = self.env['stock.picking'].search([('name', '=', scan), ('expedition', '=', True), ('picking_type_id.code', '=', 'outgoing')])
            if len(picking_ids) == 1:
                res.update({'picking': picking_ids[0], 'type': 'picking_expedition'})
            else:
                res.update({'warning': _("This expedition is unknow: %s" % (scan))})

        #TYPE: preparation
        elif scan_type == 'preparation':
            preparation_ids = self.env['stock.picking.wave'].search([('name', '=', scan)])
            if len(preparation_ids) == 1:
                res.update({'preparation': preparation_ids[0], 'type': 'preparation'})
            else:
                res.update({'warning': _("This preparation is unknow: %s" % (scan))})
        #TYPE: pack
        elif scan_type == 'pack':
            pack_ids = self.env['stock.quant.package'].search([('name', '=', scan)])
            if len(pack_ids) == 1:
                res.update({'pack': pack_ids[0], 'type': 'pack'})
            else:
                res.update({'warning': _("This pack is unknow: %s" % (scan))})

        #TYPE: picking_id
        elif scan_type == 'picking_id':
            picking = self.env['stock.picking'].browse(int(scan))
            res.update({'picking': picking, 'type': 'picking_id'})
        #TYPE: location_id
        elif scan_type == 'location_id':
            location = self.env['stock.location'].browse(int(scan))
            res.update({'location': location, 'type': 'location'})
        #TYPE: product_id
        elif scan_type == 'product_id':
            product = self.env['product.product'].browse(int(scan))
            res.update({'product': product, 'type': 'product'})
        #TYPE: pack_id
        elif scan_type == 'pack_id':
            pack = self.env['stock.quant.package'].browse(int(scan))
            res.update({'pack': pack, 'type': 'pack'})
        #TYPE: preparation_id
        elif scan_type == 'preparation_id':
            preparation = self.env['stock.picking.wave'].browse(int(scan))
            res.update({'preparation': preparation, 'type': 'preparation'})

        #TYPE: search
        elif scan_type == 'search':
            for search_type in ['location', 'pack', 'product', 'picking_in', 'preparation']:
                search_res = self.decode_scan_type(scan, search_type)
                if search_res.get('type') != 'error':
                    return search_res
        #print "===decode_scan_type==", res
        return res

    def page_product_inventory(self, data):
        "Step operation for inventory"

        #Init value
        page_data = self.page_init_value(data)
        scan = self.read_scan(data)

        #Define scan_type to return
        map_scan_type = {
            'scan_no_start': 'none',
            'scan_location_origin_id': 'location',
            'scan_product_origin_id': 'product',
            'scan_origin_qty': 'float',
            'scan_inventory_validation': 'none',
            }

        #Start
        if page_data['scenario_step'] == 'start':
            inventory = self.get_default_inventory(page_data)
            if inventory.get('warning'):
                page_data = {
                    'page': 'product_inventory',
                    'scenario_step': 'scan_no_start',
                    'warning': inventory.get('warning'),
                    }
            elif inventory.get('inventory_id'):
                page_data = {
                            'page': 'product_inventory',
                            'inventory_id': inventory.get('inventory_id'),
                            'scenario_step': 'scan_location_origin_id',
                            }
                scan = {}

        #Scan Warning
        if scan.get('type', 'none') != 'none' and scan.get('warning'):
            page_data['warning'] = scan['warning']
            scan = {}

        #STEP 1: scan_location_origin_id
        if page_data['scenario_step'] == 'scan_location_origin_id':
            if scan.get('type', '') == 'location':
                page_data['location_origin_id'] = scan['location'].id
                page_data['scenario_step'] = 'scan_product_origin_id'
                scan = {}

        #STEP 2: scan_product_origin_id
        if page_data['scenario_step'] == 'scan_product_origin_id':
            if scan.get('type', '') == 'product':
                page_data['product_origin_id'] = scan['product'].id
                existings = self.env['stock.inventory.line'].search([
                    ('product_id', '=', page_data.get('product_origin_id')),
                    ('inventory_id.state', '=', 'confirm'),
                    ('inventory_id', '!=', page_data.get('inventory_id')),
                    ('location_id', '=', page_data.get('location_origin_id'))
                    ])
                if existings:
                    page_data['warning'] = _("You cannot have two inventory adjustements in state 'in Progess' with the same product" +
                              " and the same location.<br/> Please first validate the previous inventory: ")
                    for existing in existings:
                        page_data['warning'] += '<br/>' + existing.inventory_id.name

                page_data['scenario_step'] = 'scan_origin_qty'
                scan = {}

        #STEP 3: scan_origin_qty
        if page_data['scenario_step'] == 'scan_origin_qty':
            if scan.get('type', '') == 'float' and scan['value']:
                page_data['origin_qty'] = scan['value']
                page_data['scenario_step'] = 'scan_inventory_validation'
                scan = {}

        #STEP 4: scan_inventory_validation
        if page_data['scenario_step'] == 'scan_inventory_validation':
            if data['response'].get('button') and data['response']['button'] == 'ok':
                if self.action_inventory_product(page_data):
                    page_data = {
                        'page': 'product_inventory',
                        'inventory_id': page_data['inventory_id'],
                        'scenario_step': 'scan_location_origin_id',
                        'origin_message': _('The inventory is registred, you can do a new product inventory'),
                        }
                else:
                    page_data['warning'] = _('There is an error with this inventory line')
                scan = {}

        page_data['scan_type'] = map_scan_type.get(page_data.get('scenario_step', 'start'), 'none')
        data.update(self.page_update_data(page_data))
        return data

    def page_pack_inventory(self, data):
        "Step operation for inventory"

        #Init value
        page_data = self.page_init_value(data)
        scan = self.read_scan(data)

        #Define scan_type to return
        map_scan_type = {
            'scan_no_start': 'none',
            'scan_pack_id': 'pack',
            'scan_location_origin_id': 'location',
            'scan_product_origin_id': 'product',
            'scan_origin_qty': 'float',
            'scan_inventory_validation': 'none',
            }

        #Start
        if page_data['scenario_step'] == 'start':
            page_data = {
                'page': 'pack_inventory',
                'scenario_step': 'scan_pack_id',
                }
            scan = {}

        #Scan Warning
        if scan.get('type', 'none') != 'none' and scan.get('warning'):
            page_data['warning'] = scan['warning']
            scan = {}

        #STEP 1: scan_pack_origin_id
        if page_data['scenario_step'] == 'scan_pack_id':
            if scan.get('type', '') == 'pack':
                page_data['pack_origin_id'] = scan['pack'].id
                page_data['location_origin_id'] = scan['pack'].location_id and scan['pack'].location_id.id or False
                inventory = self.get_default_inventory(page_data)
                if inventory.get('warning'):
                    page_data = {
                        'page': 'pack_inventory',
                        'scenario_step': 'scan_no_start',
                        'warning': inventory.get('warning'),
                        }
                elif inventory.get('inventory_id'):
                    page_data['inventory_id'] = inventory.get('inventory_id')
                    if page_data['location_origin_id']:
                        page_data['scenario_step'] = 'scan_product_origin_id'
                    else:
                        page_data['scenario_step'] = 'scan_location_origin_id'
                scan = {}

        #STEP 1: scan_location_origin_id
        if page_data['scenario_step'] == 'scan_location_origin_id':
            if scan.get('type', '') == 'location':
                page_data['location_origin_id'] = scan['location'].id
                page_data['scenario_step'] = 'scan_product_origin_id'
                scan = {}

        #STEP 2: scan_product_origin_id
        if page_data['scenario_step'] == 'scan_product_origin_id':
            if scan.get('type', '') == 'product':
                page_data['product_origin_id'] = scan['product'].id
                existings = self.env['stock.inventory.line'].search([
                    ('product_id', '=', page_data.get('product_origin_id')),
                    ('inventory_id.state', '=', 'confirm'),
                    ('inventory_id', '!=', page_data.get('inventory_id')),
                    ('location_id', '=', page_data.get('location_origin_id'))
                    ])
                if existings:
                    page_data['warning'] = _("You cannot have two inventory adjustements in state 'in Progess' with the same product")
                    page_data['warning'] += _(" and the same location. Please first validate the previous inventory: ")
                    for existing in existings:
                        page_data['warning'] += existing.inventory_id.name

                page_data['scenario_step'] = 'scan_origin_qty'
                scan = {}

        #STEP 3: scan_origin_qty
        if page_data['scenario_step'] == 'scan_origin_qty':
            if scan.get('type', '') == 'float' and scan['value']:
                page_data['origin_qty'] = scan['value']
                page_data['scenario_step'] = 'scan_inventory_validation'
                scan = {}

        #STEP 4: scan_inventory_validation
        if page_data['scenario_step'] == 'scan_inventory_validation':
            if data['response'].get('button') and data['response']['button'] == 'ok':
                if self.action_inventory_product(page_data):
                    page_data = {
                        'page': 'pack_inventory',
                        'inventory_id': page_data['inventory_id'],
                        'pack_origin_id': page_data['pack_origin_id'],
                        'location_origin_id': page_data['location_origin_id'],
                        'scenario_step': 'scan_product_origin_id',
                        'origin_message': _('The inventory line is registred, you can do a new product inventory in this pack'),
                        }
                else:
                    page_data['warning'] = _('There is an error with this inventory line')
                scan = {}

        page_data['scan_type'] = map_scan_type.get(page_data.get('scenario_step', 'start'), 'none')
        data.update(self.page_update_data(page_data))
        return data

    def page_pack_add(self, data):
        "Page page_pack_add"

        #Init value
        page_data = self.page_init_value(data)
        scan = self.read_scan(data)

        #Define scenario_step and scan_type to return
        map_scan_type = {
            'scan_pack_id': 'pack',
            'scan_location_origin_id': 'location',
            'scan_product_origin_id': 'product',
            'scan_origin_qty': 'float',
            'scan_location_dest_id': 'location',
            'scan_move_validation': 'none',
            'scan_label_qty': 'float',
            'scan_pack_validation': 'none',
            }

        #STEP 0: start
        if page_data['scenario_step'] == 'start':
            page_data['scenario_step'] = 'scan_pack_id'
            scan = {}

        #Scan Warning
        if scan.get('type', 'none') != 'none' and scan.get('warning'):
            page_data['warning'] = scan['warning']
            scan = {}

        #STEP 1: scan_pack_id
        if page_data['scenario_step'] == 'scan_pack_id':
            if scan.get('type', '') == 'pack':
                page_data['pack_dest_id'] = scan['pack'].id
                if not scan['pack'].location_id or scan['pack'].location_id.usage == 'internal':
                    page_data['scenario_step'] = 'scan_location_origin_id'
                else:
                    page_data['warning'] = _("This package is out of the warehouse, it can't be changed!")
                scan = {}

        #STEP 2: scan_location_origin_id
        if page_data['scenario_step'] == 'scan_location_origin_id':
            if scan.get('type', '') == 'location':
                page_data['location_origin_id'] = scan['location'].id
                page_data['scenario_step'] = 'scan_product_origin_id'
                scan = {}

        #STEP 3: scan_product_origin_id
        if page_data['scenario_step'] == 'scan_product_origin_id':
            if scan.get('type', '') == 'product':
                page_data['product_origin_id'] = scan['product'].id
                if self.check_product_quantity(page_data):
                    page_data['scenario_step'] = 'scan_origin_qty'
                    scan = {}
                else:
                    page_data['warning'] = _('This product is not in this location')
                    scan = {}

        #STEP 4: scan_origin_qty
        if page_data['scenario_step'] == 'scan_origin_qty':
            if scan.get('type', '') == 'float':
                page_data['origin_qty'] = scan['value']
                if self.check_product_quantity(page_data):
                    page_data['location_dest_id'] = self.warehouse_id.wh_pack_stock_loc_id.id
                    page_data['scenario_step'] = 'scan_pack_validation'
                    scan = {}
                else:
                    page_data['warning'] = _('There is not enought quantity')
                    scan = {}

        #STEP 5: scan_pack_validation
        if page_data['scenario_step'] == 'scan_pack_validation':
            if data['response'].get('button') and data['response']['button'] == 'ok':
                if self.check_product_quantity(page_data):
                    self.action_move_product(page_data)
                    page_data = {
                        'page': 'pack_add',
                        'pack_dest_id': page_data['pack_dest_id'],
                        'scenario_step': 'scan_location_origin_id',
                        'origin_message': _('The product is in the pack, you can add a new product'),
                        }
                    scan = {}

        #Return value
        page_data['scan_type'] = map_scan_type.get(page_data.get('scenario_step', 'start'), 'none')
        data.update(self.page_update_data(page_data))
        return data

    def page_pack_supp(self, data):
        "Page page_pack_supp"

        #Init value
        page_data = self.page_init_value(data)
        scan = self.read_scan(data)

        #Define scenario_step and scan_type to return
        map_scan_type = {
            'scan_pack_id': 'pack',
            'scan_location_origin_id': 'location',
            'scan_product_origin_id': 'product',
            'scan_origin_qty': 'float',
            'scan_location_dest_id': 'location',
            'scan_move_validation': 'none',
            'scan_label_qty': 'float',
            'scan_pack_validation': 'none',
            }

        #STEP 0: start
        if page_data['scenario_step'] == 'start':
            page_data['scenario_step'] = 'scan_pack_id'
            scan = {}

        #Scan Warning
        if scan.get('type', 'none') != 'none' and scan.get('warning'):
            page_data['warning'] = scan['warning']
            scan = {}

        #STEP 1: scan_pack_id
        if page_data['scenario_step'] == 'scan_pack_id':
            if scan.get('type', '') == 'pack':
                if scan['pack'].location_id and scan['pack'].location_id.usage != 'internal':
                    page_data['warning'] = _("This package is out of the warehouse, it can't be changed!")
                elif scan['pack'].quant_ids:
                    page_data['pack_origin_id'] = scan['pack'].id
                    page_data['location_origin_id'] = scan['pack'].location_id.id
                    page_data['scenario_step'] = 'scan_product_origin_id'
                    scan = {}
                else:
                    page_data['warning'] = _('This pack is empty')

        #STEP 2: scan_product_origin_id
        if page_data['scenario_step'] == 'scan_product_origin_id':
            if scan.get('type', '') == 'product':
                page_data['product_origin_id'] = scan['product'].id
                if self.check_product_quantity(page_data):
                    page_data['scenario_step'] = 'scan_origin_qty'
                    scan = {}
                else:
                    page_data['warning'] = _('This product is not in this pack')
                    scan = {}

        #STEP 3: scan_origin_qty
        if page_data['scenario_step'] == 'scan_origin_qty':
            if scan.get('type', '') == 'float':
                page_data['origin_qty'] = scan['value']
                if self.check_product_quantity(page_data):
                    page_data['location_dest_id'] = page_data['location_origin_id']
                    page_data['scenario_step'] = 'scan_location_dest_id'
                    scan = {}
                else:
                    page_data['warning'] = _('There is not enought quantity')
                    scan = {}

        #STEP 4: scan_location_dest_id
        if page_data['scenario_step'] == 'scan_location_dest_id':
            if scan.get('type', '') == 'location':
                page_data['location_dest_id'] = scan['location'].id
                page_data['scenario_step'] = 'scan_pack_validation'
                scan = {}

        #STEP 5: scan_pack_validation
        if page_data['scenario_step'] == 'scan_pack_validation':
            if data['response'].get('button') and data['response']['button'] == 'ok':
                if self.check_product_quantity(page_data):
                    if self.action_move_product(page_data):
                        product = self.env['product.product'].browse(page_data['product_origin_id'])
                        product_qty = page_data['origin_qty']
                        page_data = {
                            'page': 'pack_supp',
                            'pack_origin_id': page_data['pack_origin_id'],
                            'location_origin_id': page_data['location_origin_id'],
                            'scenario_step': 'scan_product_origin_id',
                            }
                        page_data['origin_message'] = _('The product:<br/> %s %s<br/>') % (product_qty, product.name)
                        page_data['origin_message'] += _('is out of the pack.<br/>You can pick another product')
                        scan = {}
                    else:
                        page_data['warning'] = _('The mouvement is not registred')
                        scan = {}
                else:
                    page_data['warning'] = _('There is not enought quantity')
                    scan = {}

        #Return value
        page_data['scan_type'] = map_scan_type.get(page_data.get('scenario_step', 'start'), 'none')
        data.update(self.page_update_data(page_data))
        return data

    def page_pack_delete(self, data):
        "Page page_pack_delete"

        #Init value
        page_data = self.page_init_value(data)
        #return self.menu_packing(data)
        scan = self.read_scan(data)

        #Define scenario_step and scan_type to return
        map_scan_type = {
            'scan_pack_id': 'pack',
            'scan_pack_delete': 'none',
            }

        #STEP 0: start
        if page_data['scenario_step'] == 'start':
            page_data['scenario_step'] = 'scan_pack_id'
            scan = {}

        #STEP 1: scan_pack_id
        if page_data['scenario_step'] == 'scan_pack_id':
            if scan.get('type', '') == 'pack':
                page_data['pack_dest_id'] = scan['pack'].id
                page_data['scenario_step'] = 'scan_pack_delete'

                scan = {}

        #STEP 3: scan_pack_validation
        if page_data['scenario_step'] == 'scan_pack_delete':
            if data['response'].get('button') and data['response']['button'] == 'ok':
                package = self.env['stock.quant.package'].browse(page_data['pack_dest_id'])
                package.mapped('quant_ids').sudo().write({'package_id': package.parent_id.id})
                package.mapped('children_ids').write({'parent_id': package.parent_id.id})

                page_data = {
                    'page': 'pack_delete',
                    'scenario_step': 'scan_pack_id',
                    'origin_message': _('The pack is deleting, you can delete another pack'),
                    }
                scan = {}

        #Return value
        page_data['scan_type'] = map_scan_type.get(page_data.get('scenario_step', 'start'), 'none')
        data.update(self.page_update_data(page_data))
        return data

    def page_pack_move(self, data):
        "Page page_pack_delete"

        #Init value
        page_data = self.page_init_value(data)
        #return self.menu_packing(data)
        scan = self.read_scan(data)

        #Define scenario_step and scan_type to return
        map_scan_type = {
            'scan_pack_id': 'pack',
            'scan_pack_location_dest_id': 'location',
            'scan_pack_move_ok': 'none',
            }

        #STEP 0: start
        if page_data['scenario_step'] == 'start':
            page_data['scenario_step'] = 'scan_pack_id'
            scan = {}

        #STEP 1: scan_pack_id
        if page_data['scenario_step'] == 'scan_pack_id':
            if scan.get('type', '') == 'pack':
                if scan['pack'].parent_id:
                    page_data['warning'] = _('This pack is inside another pack. Please, move the parent pack: %s' % (scan['pack'].parent_id.name))
                    scan = {}
                elif scan['pack'].location_id and scan['pack'].location_id.usage != 'internal':
                    page_data['warning'] = _("This package is out of the warehouse, it can't be changed!")
                else:
                    page_data['pack_dest_id'] = scan['pack'].id
                    page_data['scenario_step'] = 'scan_pack_location_dest_id'
                    scan = {}

        #STEP 2: scan_location_origin_id
        if page_data['scenario_step'] == 'scan_pack_location_dest_id':
            if scan.get('type', '') == 'location':
                page_data['location_dest_id'] = scan['location'].id
                page_data['scenario_step'] = 'scan_pack_move_ok'
                scan = {}

        #STEP 3: scan_pack_validation
        if page_data['scenario_step'] == 'scan_pack_move_ok':
            if data['response'].get('button') and data['response']['button'] == 'ok':

                package_vals = {
                    'location_dest_id': page_data['location_dest_id'],
                    'package_ids': [(6, 0, [page_data['pack_dest_id']])],
                    }

                pack_move = self.env['stock.quant.package.move'].create(package_vals)
                if pack_move.action_apply():
                    page_data = {
                        'page': 'pack_move',
                        'scenario_step': 'scan_pack_id',
                        'origin_message': _('The pack is moving, you can move another pack'),
                        }
                scan = {}

        #Return value
        page_data['scan_type'] = map_scan_type.get(page_data.get('scenario_step', 'start'), 'none')
        data.update(self.page_update_data(page_data))
        return data

    def page_pack_print(self, data):
        "Page page_pack_print"

        #Init value
        page_data = self.page_init_value(data)
        #return self.menu_packing(data)
        scan = self.read_scan(data)

        #Define scenario_step and scan_type to return
        map_scan_type = {
            'scan_printer_id': 'printer',
            'scan_label_qty': 'float',
            'scan_print_validation': 'none',
            }

        #STEP 0: start
        if page_data['scenario_step'] == 'start':
            page_data['scenario_step'] = 'scan_printer_id'
            scan = {}

        #Scan Warning
        if scan.get('type', 'none') != 'none' and scan.get('warning'):
            page_data['warning'] = scan['warning']
            scan = {}

        #STEP 1: scan_printer_id
        if page_data['scenario_step'] == 'scan_printer_id':
            printer_ids = self.env['printing.printer'].search([])
            if len(printer_ids) == 1:
                page_data['printer_id'] = printer_ids[0].id
                page_data['scenario_step'] = 'scan_label_qty'

            elif scan.get('type', '') == 'printer':
                page_data['printer_id'] = scan['printer'].id
                page_data['scenario_step'] = 'scan_label_qty'
                scan = {}

        #STEP 2: scan_label_qty
        if page_data['scenario_step'] == 'scan_label_qty':
            if scan.get('type', '') == 'float':
                if scan['value'] > 0.0:
                    page_data['label_qty'] = scan['value']
                    pack_ids = []
                    for label_qty in range(int(page_data['label_qty'])):
                        #Create new pack
                        pack_name = self.env['ir.sequence'].next_by_code('stock.quant.package')
                        #location_id = self.warehouse_id.wh_pack_stock_loc_id.id
                        pack = self.env['stock.quant.package'].sudo().create({'name': pack_name})
                        pack_ids.append(pack.id)

                    self.env['label.template'].with_context(
                        printer_id=page_data['printer_id'],
                        active_model='stock.quant.package',
                        active_ids=pack_ids).print_zebra()

                    page_data['scenario_step'] = 'scan_print_validation'
                    page_data['origin_message'] = _('The label is printing')
                    scan = {}

                else:
                    page_data['warning'] = _('There is not enought quantity')
                    scan = {}

        #STEP 3: scan_print_validation
        if page_data['scenario_step'] == 'scan_print_validation':
            if data['response'].get('button'):
                if data['response']['button'] == 'ok':
                    page_data = {
                        'menu': 'pack_print',
                        'printer_id': page_data['printer_id'],
                        }
                    scan = {}

        #Return value
        page_data['scan_type'] = map_scan_type.get(page_data.get('scenario_step', 'start'), 'none')
        data.update(self.page_update_data(page_data))
        return data

    def page_product_move(self, data):
        "Page page_product_move"

        #Init value
        page_data = self.page_init_value(data)
        scan = self.read_scan(data)

        #Define scenario_step and scan_type to return
        map_scan_type = {
            'scan_location_origin_id': 'location',
            'scan_product_origin_id': 'product',
            'scan_origin_qty': 'float',
            'scan_location_dest_id': 'location',
            'scan_move_validation': 'none',
            }

        #STEP 0: start
        if page_data['scenario_step'] == 'start':
            page_data['scenario_step'] = 'scan_location_origin_id'
            scan = {}

        #Scan Warning
        if scan.get('type', 'none') != 'none' and scan.get('warning'):
            page_data['warning'] = scan['warning']
            scan = {}

        #STEP 1: scan_location_origin_id
        if page_data['scenario_step'] == 'scan_location_origin_id':
            if scan.get('type', '') == 'location':
                page_data['location_origin_id'] = scan['location'].id
                page_data['scenario_step'] = 'scan_product_origin_id'
                scan = {}

        #STEP 2: scan_product_origin_id
        if page_data['scenario_step'] == 'scan_product_origin_id':
            if scan.get('type', '') == 'product':
                page_data['product_origin_id'] = scan['product'].id
                if self.check_product_quantity(page_data):
                    page_data['scenario_step'] = 'scan_origin_qty'
                    scan = {}
                else:
                    page_data['warning'] = _('This product is not in this location')
                    scan = {}

        #STEP 3: scan_origin_qty
        if page_data['scenario_step'] == 'scan_origin_qty':
            if scan.get('type', '') == 'float':
                page_data['origin_qty'] = scan['value']
                if self.check_product_quantity(page_data):
                    page_data['scenario_step'] = 'scan_location_dest_id'
                    scan = {}
                else:
                    page_data['warning'] = _('There is not enought quantity')
                    scan = {}

        #STEP 4: scan_location_dest_id
        if page_data['scenario_step'] == 'scan_location_dest_id':
            if scan.get('type', '') == 'location':
                page_data['location_dest_id'] = scan['location'].id
                page_data['scenario_step'] = 'scan_move_validation'
                scan = {}

        #STEP 5: scan_move_validation
        if page_data['scenario_step'] == 'scan_move_validation':
            if data['response'].get('button') and data['response']['button'] == 'ok':
                if self.check_product_quantity(page_data):
                    self.action_move_product(page_data)
                    page_data = {
                        'page': 'product_move',
                        'scenario_step': 'scan_location_origin_id',
                        'origin_message': _('The mouvement is registred, you can do a new move'),
                        }
                    scan = {}

        #Return value
        page_data['scan_type'] = map_scan_type.get(page_data.get('scenario_step', 'start'), 'none')
        data.update(self.page_update_data(page_data))
        return data

    def page_blank(self, data):
        "Step operation for example"

        #init value
        page_data = self.page_init_value(data)
        scan = self.read_scan(data)

        #Define scan_type to return
        map_scan_type = {'under_construction': 'none'}

        #Start
        if page_data['scenario_step'] == 'start':
            page_data['origin_message'] = _('This page is under construction')
            page_data['scenario_step'] = 'under_construction'
            scan = {}

        #Scan Warning
        if scan.get('type', 'none') != 'none' and scan.get('warning'):
            page_data['warning'] = scan['warning']
            scan = {}

        #Return value
        page_data['scan_type'] = map_scan_type.get(page_data.get('scenario_step', 'start'), 'none')
        data.update(self.page_update_data(page_data))
        return data

    def page_preparation(self, data):
        "Step operation for preparation: stock.picking.wave"

        #init value
        page_data = self.page_init_value(data)
        scan = self.read_scan(data)

        #Define scan_type to return
        map_scan_type = {
            'scan_preparation_id': 'preparation',
            'scan_choice_preparation_validation': 'none',
            'scan_location_origin_id': 'location',
            'scan_product_origin_id': 'product',
            'scan_origin_qty': 'float',
            'scan_product_todo_id': 'product',
            'scan_todo_qty': 'float',
            'scan_todo_qty_validation': 'none',
            'scan_result_package_id': 'pack',
            'operation_end': 'operation_end',
            }

        #STEP 0: start
        if page_data['scenario_step'] == 'start':
            page_data['scenario_step'] = 'scan_preparation_id'
            scan = {}

        #STEP 0.1: next operation
        if data['response'].get('button') and data['response']['button'] == 'next':

            if page_data.get('operation_id'):
                operation = self.env['stock.pack.operation'].browse(page_data.get('operation_id'))
                operation.passed = True

            operation_id = self.get_next_operation_id(page_data)

            if operation_id:
                page_data = {
                    'page': 'preparation',
                    'preparation_id': page_data['preparation_id'],
                    'operation_id': operation_id,
                    'scenario_step': 'scan_location_origin_id',
                    'origin_message': _('New mouvement to do'),
                    }
                page_data['pack_dest_id'] = self.get_last_package(page_data)
                scan = {}
            else:
                page_data.pop('operation_id', None)
                page_data['scenario_step'] = 'operation_end'
                page_data['button_message'] = _('All mouvements is done')

            scan = {}

        #Scan Warning
        #if scan.get('type', 'none') != 'none' and scan.get('warning'):
        if scan.get('warning'):
            page_data['warning'] = scan['warning']
            scan = {}

        #STEP 1: scan_preparation_id
        if page_data['scenario_step'] == 'scan_preparation_id':
            if scan.get('type', '') == 'preparation':
                if scan['preparation'].state == 'in_progress':
                    page_data['preparation_id'] = scan['preparation'].id
                    page_data['scenario_step'] = 'scan_choice_preparation_validation'
                    page_data['origin_message'] = _('Start Preparation ?') + '<ul>'

                    for picking in scan['preparation'].picking_ids:
                        page_data['origin_message'] += '<li>' + picking.name + ' - ' + (picking.partner_id and picking.partner_id.name or '') + '</li>'

                    page_data['origin_message'] += '</ul>'
                    scan = {}
                else:
                    page_data['warning'] = _("This preparation is done or cancel, you can't change it'")
                scan = {}

        #STEP 2: scan_choice_preparation_validation
        if page_data['scenario_step'] == 'scan_choice_preparation_validation':
            if data['response'].get('button') and data['response']['button'] == 'ok':
                preparation = self.env['stock.picking.wave'].browse(page_data.get('preparation_id'))
                preparation.user_id = self.env.user
                for picking in preparation.picking_ids:
                    if picking.state in ['draft', 'waiting', 'confirmed', 'partialy_available']:
                        picking.action_assign

                operation_id = self.get_next_operation_id(page_data)

                if operation_id:
                    page_data['operation_id'] = operation_id
                    page_data['pack_dest_id'] = self.get_last_package(page_data)
                    page_data['scenario_step'] = 'scan_location_origin_id'
                else:
                    page_data.pop('operation_id', None)
                    page_data['scenario_step'] = 'operation_end'

                scan = {}

        #STEP 3: scan_location_origin_id
        if page_data['scenario_step'] == 'scan_location_origin_id':
            if scan.get('type', '') == 'location':
                operation = self.env['stock.pack.operation'].browse(page_data.get('operation_id'))
                if operation.location_id == scan['location']:
                    page_data['location_origin_id'] = scan['location'].id
                    page_data['scenario_step'] = 'scan_product_origin_id'
                else:
                    page_data['warning'] = _('It is not the good location: %s' % (scan['location'].name))
                scan = {}

        #STEP 4: scan_product_origin_id
        if page_data['scenario_step'] == 'scan_product_origin_id':
            if scan.get('type', '') == 'product':
                operation = self.env['stock.pack.operation'].browse(page_data.get('operation_id'))
                if operation.product_id == scan['product']:
                    page_data['product_origin_id'] = scan['product'].id
                    if self.check_product_quantity(page_data):
                        page_data['scenario_step'] = 'scan_origin_qty'
                        scan = {}
                    else:
                        page_data['warning'] = _('This product is not in this location')
                        scan = {}
                else:
                    page_data['warning'] = _('It is not the good product %s' % (scan['product'].name))
                scan = {}

        #STEP 5: scan_todo_qty
        if page_data['scenario_step'] == 'scan_origin_qty':
            if scan.get('type', '') == 'float':
                operation = self.env['stock.pack.operation'].browse(page_data.get('operation_id'))
                page_data['origin_qty'] = scan['value']
                if not self.check_product_quantity(page_data):
                    page_data['warning'] = _('There is not enought quantity in this location')
                    scan = {}
                elif operation.product_qty != scan['value']:
                    page_data['warning'] = _('There is not the good quantity')
                    scan = {}
                elif operation.product_qty == scan['value']:
                    page_data['scenario_step'] = 'scan_result_package_id'
                else:
                    page_data['warning'] = _('There is not the good quantity: %s' % (scan['value']))
                scan = {}

        #STEP 6: scan_result_package_id
        if page_data['scenario_step'] == 'scan_result_package_id':
            operation = self.env['stock.pack.operation'].browse(page_data.get('operation_id'))
            if operation.picking_id.wave_id.wave_type in ['direct_picking']:
                page_data['result_package_id'] = False
                operation.qty_done = page_data['origin_qty']
                operation.result_package_id = False
                page_data['scenario_step'] = 'next_operation'
            elif operation.picking_id.wave_id.wave_type in ['picking_pack']:
                if scan.get('type', '') == 'pack':
                    #Check pack
                    page_data['result_package_id'] = scan['pack'].id
                    if self.check_operation_dest_package(page_data):
                        operation.result_package_id = scan['pack']
                        operation.qty_done = page_data['origin_qty']
                        page_data['scenario_step'] = 'next_operation'
                    else:
                        page_data['result_package_id'] = False
                        page_data['warning'] = _('This package is not used for this picking')
                    scan = {}

        #STEP 7: next_operation
        if page_data['scenario_step'] == 'next_operation':
            if page_data.get('operation_id'):
                operation = self.env['stock.pack.operation'].browse(page_data.get('operation_id'))
                operation.passed = True

            #Move product to output
            self.action_move_to_output(page_data)

            operation_id = self.get_next_operation_id(page_data)

            if operation_id:
                page_data = {
                    'page': 'preparation',
                    'preparation_id': page_data['preparation_id'],
                    'operation_id': operation_id,
                    'scenario_step': 'scan_location_origin_id',
                    'origin_message': _('New mouvement to do'),
                    }
                page_data['pack_dest_id'] = self.get_last_package(page_data)
                scan = {}
            else:
                page_data.pop('operation_id', None)
                page_data['scenario_step'] = 'operation_end'
                page_data['button_message'] = _('All mouvements is done')

            scan = {}

        #STEP 8: operation_end
        if page_data['scenario_step'] == 'operation_end':
            if data['response'].get('button') and data['response']['button'] == 'ok':

                if self.preparation_done(page_data):
                    page_data = {
                        'page': 'preparation',
                        'scenario_step': 'scan_preparation_id',
                        'origin_message': _('You can do a new preparation, the previous preparation is finish'),
                        }
                else:
                    page_data = {
                        'page': 'preparation',
                        'scenario_step': 'scan_preparation_id',
                        }
                    page_data['origin_message'] = _("You can do a new preparation, the previous preparation is finish.<br/>")
                    page_data['origin_message'] += _("Some product have to be complete later.")
            else:
                page_data['button_message'] = _('All mouvements is done')

            scan = {}

        #Return value
        page_data['scan_type'] = map_scan_type.get(page_data.get('scenario_step', 'start'), 'none')
        data.update(self.page_update_data(page_data))
        return data

    def get_last_package(self, page_data):
        "return the last result_package used for this picking"
        if page_data.get('operation_id'):
            operation = self.env['stock.pack.operation'].browse(page_data.get('operation_id'))
            condition = [('result_package_id', '!=', False), ('picking_id', '=', operation.picking_id.id)]
            operation_ids = self.env['stock.pack.operation'].search(condition)
            operation_ids.sorted('write_date')

            if operation_ids:
                return operation_ids[0].result_package_id.id
            else:
                return False
        else:
            return False

    def check_operation_dest_package(self, page_data={}):
        "check product qty in origin location"
        if page_data.get('operation_id') and page_data.get('result_package_id'):
            operation = self.env['stock.pack.operation'].browse(page_data.get('operation_id'))

            for line in operation.picking_id.pack_operation_product_ids:
                if line.result_package_id.id == page_data.get('result_package_id'):
                    return True

            if operation.picking_id.wave_id:
                for picking in operation.picking_id.wave_id.picking_ids:
                    for line in picking.pack_operation_product_ids:
                        if line.result_package_id.id == page_data.get('result_package_id'):
                            if line.picking_id != picking.id:
                                return False

            package = self.env['stock.quant.package'].browse(page_data.get('result_package_id'))
            if package.children_quant_ids:
                return False
            else:
                return True
        else:
            return False



    def preparation_done(self, page_data):
        "close all picking"
        preparation = self.env['stock.picking.wave'].browse(page_data.get('preparation_id'))
        pickings = preparation.mapped('picking_ids').filtered(lambda picking: picking.state not in ('cancel', 'done'))

        if any(picking.state != 'assigned' for picking in pickings):
            return False

        preparation.write({'state': 'done'})
        pickings.sudo().write({'state': 'assigned', 'expedition': True})
        return True

    def get_next_operation_id(self, page_data):
        "return operation to do"
        preparation = self.env['stock.picking.wave'].browse(page_data.get('preparation_id'))
        operation_id = False
        sequence = 0
        operation_passed = False

        for picking in preparation.picking_ids:
            for operation in picking.pack_operation_product_ids:
                if operation.passed:
                    if operation_passed:
                        operation_passed |= operation
                    else:
                        operation_passed = operation
                elif operation.product_qty > operation.qty_done:
                    if not sequence or sequence > operation.location_id.sequence:
                        sequence = operation.location_id.sequence
                        operation_id = operation.id

        if not operation_id and operation_passed:
            operation_passed.write({'passed': False})
            return self.get_next_operation_id(page_data)

        return operation_id

    def page_expedition(self, data):
        "Step operation for receipt"

        #init value
        page_data = self.page_init_value(data)
        scan = self.read_scan(data)

        #Define scan_type to return
        map_scan_type = {
            'scan_picking_in_id': 'picking_expedition',
            'scan_choice_picking_validation': 'none',
            'scan_product_todo_id': 'product',
            'scan_todo_qty': 'float',
            'scan_todo_qty_validation': 'none',
            }

        #STEP 0: start
        if page_data['scenario_step'] == 'start':
            page_data['scenario_step'] = 'scan_picking_expedition_id'
            scan = {}

        #Scan Warning
        if scan.get('type', 'none') != 'none' and scan.get('warning'):
            page_data['warning'] = scan['warning']
            scan = {}

        #STEP 1: scan_picking_expedition_id
        if page_data['scenario_step'] == 'scan_picking_expedition_id':
            if scan.get('type', '') in ['picking_expedition', 'picking_id']:
                if scan['picking'].state in ['assigned', 'confirmed', 'partialy_available']:
                    page_data['picking_id'] = scan['picking'].id
                    page_data['scenario_step'] = 'scan_choice_picking_validation'
                    page_data['origin_message'] = _('Start expedition scanning ?')
                    scan = {}
                else:
                    page_data['warning'] = _("This expedition is done or cancel, you can't change it'")
                    scan = {}

        #STEP 2: scan_choice_picking_validation
        if page_data['scenario_step'] == 'scan_choice_picking_validation':
            if data['response'].get('button') and data['response']['button'] == 'ok':
                self.action_init_qty_todo(page_data)
                page_data['scenario_step'] = 'scan_product_todo_id'
                scan = {}

        #STEP 3: scan_product_todo_id
        if page_data['scenario_step'] == 'scan_product_todo_id':
            if scan.get('type', '') == 'product':
                page_data['product_origin_id'] = scan['product'].id
                scan = {}
                if self.check_product_todo(page_data):
                    page_data['scenario_step'] = 'scan_todo_qty'
                else:
                    page_data['warning'] = _('This product is not expected !')
            elif scan.get('type', '') == 'pack':
                page_data['pack_origin_id'] = scan['pack'].id
                scan = {}
                if self.check_product_todo(page_data):
                    page_data['scenario_step'] = 'scan_todo_qty_validation'
                else:
                    page_data['warning'] = _('This pack is not expected !')

        #STEP 4: scan_todo_qty
        if page_data['scenario_step'] == 'scan_todo_qty':
            if scan.get('type', '') == 'float':
                page_data['origin_qty'] = scan['value']
                if self.check_expedition_quantity(page_data):
                    page_data['scenario_step'] = 'scan_todo_qty_validation'
                else:
                    page_data['warning'] = _('There is not the good quantity: %s' % (scan['value']))
                scan = {}

        #STEP 5: scan_choice_picking_validation
        if page_data['scenario_step'] == 'scan_todo_qty_validation':
            if data['response'].get('button') and data['response']['button'] == 'ok':
                if self.action_valide_qty_todo(page_data):
                    if self.check_expedition(page_data):
                        page_data = {
                        'page': 'expedition',
                        'scenario_step': 'scan_picking_expedition_id',
                        'origin_message': _('You can do a new expedition, the previous is finish'),
                        }
                        scan = {}
                    else:
                        page_data = {
                            'page': 'expedition',
                            'picking_id': page_data['picking_id'],
                            'scenario_step': 'scan_product_todo_id',
                            'origin_message': _('The mouvement is registred, you can do a new scan'),
                            }
                        scan = {}


        #Return value
        page_data['scan_type'] = map_scan_type.get(page_data.get('scenario_step', 'start'), 'none')
        data.update(self.page_update_data(page_data))
        return data

    def page_receipt(self, data):
        "Step operation for receipt"

        #init value
        page_data = self.page_init_value(data)
        scan = self.read_scan(data)

        #Define scan_type to return
        map_scan_type = {
            'scan_picking_in_id': 'picking_in',
            'scan_choice_picking_validation': 'none',
            'scan_product_todo_id': 'product',
            'scan_todo_qty': 'float',
            'scan_todo_qty_validation': 'none',
            }

        #STEP 0: start
        if page_data['scenario_step'] == 'start':
            page_data['scenario_step'] = 'scan_picking_in_id'
            scan = {}

        #Scan Warning
        if scan.get('type', 'none') != 'none' and scan.get('warning'):
            page_data['warning'] = scan['warning']
            scan = {}

        #STEP 1: scan_picking_in_id
        if page_data['scenario_step'] == 'scan_picking_in_id':
            if scan.get('type', '') in ['picking_in', 'picking_id']:
                if scan['picking'].state in ['assigned', 'confirmed', 'partialy_available']:
                    page_data['picking_id'] = scan['picking'].id
                    page_data['scenario_step'] = 'scan_choice_picking_validation'
                    page_data['origin_message'] = _('Start receipt scanning ?')
                    scan = {}
                else:
                    page_data['warning'] = _("This receipt is done or cancel, you can't change it'")
                    scan = {}

        #STEP 2: scan_choice_picking_validation
        if page_data['scenario_step'] == 'scan_choice_picking_validation':
            if data['response'].get('button') and data['response']['button'] == 'ok':
                #TODO user_id on picking_id ?
                page_data['scenario_step'] = 'scan_product_todo_id'
                scan = {}

        #STEP 3: scan_product_todo_id
        if page_data['scenario_step'] == 'scan_product_todo_id':
            if scan.get('type', '') == 'product':
                page_data['product_origin_id'] = scan['product'].id
                scan = {}
                if self.check_product_todo(page_data):
                    page_data['scenario_step'] = 'scan_todo_qty'
                else:
                    page_data['scenario_step'] = 'add_product_todo_validation'
                    page_data['button_message'] = _('This product is not expected ! Do you want to add it on receipt ?')

        #STEP 3.1: add_product_todo_validation
        if page_data['scenario_step'] == 'add_product_todo_validation':
            if data['response'].get('button') and data['response']['button'] == 'ok':
                page_data['scenario_step'] = 'scan_todo_qty'
                self.action_add_product_todo(page_data)
                scan = {}
            if data['response'].get('button') and data['response']['button'] == 'no':
                page_data['scenario_step'] = 'scan_product_todo_id'
                del page_data['product_origin_id']
                scan = {}

        #STEP 4: scan_todo_qty
        if page_data['scenario_step'] == 'scan_todo_qty':
            if  scan.get('type', '') == 'float':
                page_data['origin_qty'] = scan['value']
                page_data['scenario_step'] = 'scan_todo_qty_validation'
                scan = {}

        #STEP 5: scan_choice_picking_validation
        if page_data['scenario_step'] == 'scan_todo_qty_validation':
            if data['response'].get('button') and data['response']['button'] == 'ok':
                if self.action_add_qty_todo(page_data):
                    page_data = {
                        'page': 'receipt',
                        'picking_id': page_data['picking_id'],
                        'scenario_step': 'scan_product_todo_id',
                        'origin_message': _('The mouvement is registred, you can do a new scan'),
                        }
                    scan = {}

        #Return value
        page_data['scan_type'] = map_scan_type.get(page_data.get('scenario_step', 'start'), 'none')
        data.update(self.page_update_data(page_data))
        return data

    def page_update_data(self, page_data):
        "finalyse page data"
        data = {}
        data['page_header'] = self.configure_page_header(page_data)
        data['page_body'] = self.configure_page_body(page_data)
        data['scanner_data'] = page_data
        return data

    def page_init_value(self, data):
        #Init value for page
        page = data['response'].get('page', 'blank')
        #Button Cancel
        if data['response'].get('button') and data['response']['button'] == 'cancel':
            data['scanner_data'] = {}

        #Return previous session data
        if data['scanner_data'].get('page', 'none') == page:
            page_data = data['scanner_data']
        else:
            page_data = {'page': page}

        #Start scenario_step
        if not page_data.get('scenario_step'):
            page_data['scenario_step'] = 'start'

        #delete previous scan_type, Warning, message, zxing
        for key in ['warning', 'origin_message', 'button_message', 'scan_type', 'zxing', 'error']:
            if page_data.get(key):
                del page_data[key]

        return page_data

    def configure_page_header(self, page_data):
        "configure image and link for qweb header page"
        #Default
        page_header = {}
        page_header['left_img'] = 'go-home-5.jpg'
        page_header['left_href'] = '?menu=main'
        page_header['right_img'] = 'construction.jpg'
        page_header['right_name'] = self.env.user.name
        page_header['right_txt'] = _('Function configure_page_header')

        #Choice header images
        if page_data.get('page') == 'construction':
            page_header['right_txt'] = _('Under construction')
            page_header = {'goback': True}

        if page_data.get('page') == 'scaninfo':
            page_header['right_img'] = 'scan_codebarre.jpg'
            page_header['right_txt'] = _('Barcode information')

        if page_data.get('page') == 'product_move':
            page_header['right_img'] = 'product_move.jpg'
            page_header['right_txt'] = _('Move product')

        if page_data.get('page') == 'receipt':
            page_header['right_img'] = 'zoom-3.jpg'
            page_header['right_txt'] = _('Receipt')

        if page_data.get('page') == 'expedition':
            page_header['right_img'] = 'expedition.jpg'
            page_header['right_txt'] = _('Expedition')

        if page_data.get('page') == 'pack_print':
            page_header['right_img'] = 'printer.jpg'
            page_header['right_txt'] = _('Print pack label')

        if page_data.get('page') == 'pack_add':
            page_header['right_img'] = 'pack_add.jpg'
            page_header['right_txt'] = _('Add product')

        if page_data.get('page') == 'pack_supp':
            page_header['right_img'] = 'pack_supp.jpg'
            page_header['right_txt'] = _('Pick product')

        if page_data.get('page') == 'pack_inventory':
            page_header['right_img'] = 'pack_inventory.jpg'
            page_header['right_txt'] = _('Pack inventory')

        if page_data.get('page') == 'pack_delete':
            page_header['right_img'] = 'software-update-unavailable.jpg'
            page_header['right_txt'] = _('Unpack products')

        if page_data.get('page') == 'pack_move':
            page_header['right_img'] = 'pack_move.jpg'
            page_header['right_txt'] = _('Move pack')

        if page_data.get('page') == 'preparation':
            page_header['right_img'] = 'edit-paste-4.jpg'
            page_header['right_txt'] = _('Preparation')
            if page_data.get('operation_id'):
                operation = self.env['stock.pack.operation'].browse(page_data['operation_id'])
                page_header['right_txt'] = operation.picking_id.name
                page_header['right_name'] = operation.picking_id.partner_id and operation.picking_id.partner_id.name or ''

        if page_data.get('page') == 'zxing':
            page_header['right_img'] = 'scan.jpg'
            page_header['right_txt'] = _('Install scanner')

        if page_data.get('page') == 'product_inventory':
            page_header['right_img'] = 'product_inventory.jpg'
            page_header['right_txt'] = _('Inventory')
            if page_data.get('inventory_id'):
                inventory = self.env['stock.inventory'].browse(page_data['inventory_id'])
                if inventory.user_id:
                    page_header['right_txt'] = _('Partial Inventory')
                else:
                    page_header['right_txt'] = _('GENERAL INVENTORY !')

        if page_data.get('picking_id'):
            picking = self.env['stock.picking'].browse(page_data['picking_id'])
            page_header['right_txt'] = picking.name
            page_header['right_name'] = picking.partner_id and picking.partner_id.name or ''

        return page_header

    def configure_page_body(self, page_data):
        "configure image, message and link for qweb page_body"
        ###### Create html page ####
        #Page default icon
        page = {}
        page['left_img'] = 'construction.jpg'
        page['right_html'] = _('Function: configure_page_body')
        #page['csrf_token'] = request.csrf_token()

        #Show warning
        if page_data.get('warning'):
            page['warning'] = page_data['warning']
        #Show message
        if page_data.get('origin_message'):
            page['origin_message'] = page_data['origin_message']

        #Define the scan type to return by the form
        if page_data.get('scan_type'):
            page['scan_type'] = page_data.get('scan_type')

        #Default page
        if not page_data.get('scenario_step'):
            page_data['scenario_step'] = 'under_construction'

        #Page blank
        if page_data['scenario_step'] == 'under_construction':
            page['go_back'] = True

        #Zxing page info install
        if page_data['scenario_step'] == 'install_zxing':
            page['left_img'] = 'scan.jpg'
            page['hide_scan'] = True

        #zxing android plugin
        if page_data.get('scan_type') and page_data.get('page'):
            base_url = self.env['ir.config_parameter'].get_param('web.base.url')
            url = base_url + '/scanner?page=' + page_data['page'] + '&scan_type=' + page_data['scan_type'] + '&scan={CODE}'
            page['zxing'] = 'zxing://scan/?' + urllib.urlencode({'ret': url})

        #Asck scan_barcode information
        if page_data['scenario_step'] == 'scan_barcode':
            page['left_img'] = 'scan_codebarre.jpg'
            page['right_html'] = _("Scan barcode to get information")
            if page_data.get('product_id'):
                page['info_product'] = self.env['product.product'].browse(page_data['product_id'])
            if page_data.get('location_id'):
                page['info_location'] = self.env['stock.location'].browse(page_data['location_id'])
            if page_data.get('pack_location_id'):
                page['info_pack_location'] = self.env['stock.location'].browse(page_data['pack_location_id'])
            if page_data.get('pack_id'):
                page['info_pack'] = self.env['stock.quant.package'].browse(page_data['pack_id'])
            if page_data.get('quant_ids'):
                page['quants'] = self.env['stock.quant'].browse(page_data['quant_ids'])

        #Asck picking_in_id
        if page_data['scenario_step'] == 'scan_picking_expedition_id':
            page['left_img'] = 'edit-paste-4.jpg'
            page['right_html'] = _("Scan barcode Expedition or choice one in the list")
            page['picking_ids'] = self.get_default_picking_ids(page_data, 'expedition')

        #Asck picking_in_id
        if page_data['scenario_step'] == 'scan_picking_in_id':
            page['left_img'] = 'edit-paste-4.jpg'
            page['right_html'] = _("Scan barcode Receipt or choice one in the list")
            page['picking_ids'] = self.get_default_picking_ids(page_data, 'incoming')

        #Asck pack_id
        if page_data['scenario_step'] in ['scan_pack_id']:
            page['left_img'] = 'pack.jpg'
            page['right_html'] = _("Scan barcode pack")

        #Asck result_package_id
        if page_data['scenario_step'] in ['scan_result_package_id']:
            page['location_origin_id'] = self.env['stock.location'].browse(page_data['location_origin_id'])
            page['product_origin_id'] = self.env['product.product'].browse(page_data['product_origin_id'])
            page['origin_qty'] = page_data['origin_qty']
            page['left_img'] = 'pack.jpg'
            page['right_html'] = _("Scan barcode pack")

        #Show pack_id
        if page_data.get('pack_dest_id') or page_data.get('pack_origin_id'):
            page['pack_id'] = self.env['stock.quant.package'].browse(page_data.get('pack_dest_id') or page_data.get('pack_origin_id'))
            if not page_data.get('preparation_id'):
                page['quants'] = self.env['stock.quant'].search([('package_id', '=', page_data.get('pack_dest_id', 0))])

        #Asck picking or preparation choice validation, operation_end
        if page_data['scenario_step'] in ['scan_choice_picking_validation', 'operation_end', 'scan_choice_preparation_validation']:
            page['hide_scan'] = True
            page['button_message'] = page_data.get('button_message', '')
            page['button_ok'] = _("Valide")
            page['button_cancel'] = _("Cancel")

        #just a message picking scan_print_validation
        if page_data['scenario_step'] in ['scan_print_validation']:
            page['hide_scan'] = True
            if page_data.get('printer_id'):
                page['printer_id'] = self.env['printing.printer'].browse(page_data['printer_id'])

        #Asck scan_preparation_id
        if page_data['scenario_step'] == 'scan_preparation_id':
            page['left_img'] = 'edit-paste-4.jpg'
            page['right_html'] = _("Scan barcode Preparation")
            page['preparation_ids'] = self.get_default_preparation_ids(page_data)

        #Asck source location
        if page_data['scenario_step'] == 'scan_location_origin_id':
            page['left_img'] = 'location.jpg'
            page['right_html'] = _("Scan source product location barcode")
            page['default_location_ids'] = self.get_default_location_ids(page_data)

        #Asck source product
        if page_data['scenario_step'] == 'scan_product_origin_id':
            page['location_origin_id'] = self.env['stock.location'].browse(page_data['location_origin_id'])
            page['left_img'] = 'product.jpg'
            page['right_html'] = _("Scan product barcode")
            page['button_cancel'] = _("Cancel")

        #Asck todo product
        if page_data['scenario_step'] == 'scan_product_todo_id':
            page['left_img'] = 'product.jpg'
            page['right_html'] = _("Scan product barcode")
            page['button_cancel'] = _("Cancel")

        #Asck Add product todo
        if page_data['scenario_step'] == 'add_product_todo_validation':
            page['product_origin_id'] = self.env['product.product'].browse(page_data['product_origin_id'])
            page['hide_scan'] = True
            page['button_message'] = page_data.get('button_message', '')
            page['button_ok'] = _("Add this Product")
            page['button_no'] = _("No")

        #Asck qty todo
        if page_data['scenario_step'] == 'scan_todo_qty':
            page['product_origin_id'] = self.env['product.product'].browse(page_data['product_origin_id'])
            page['left_img'] = 'qty.jpg'
            page['right_html'] = _("Enter quantity")
            page['button_cancel'] = _("Cancel")

        #Asck qty todo validation
        if page_data['scenario_step'] == 'scan_todo_qty_validation':
            if page_data.get('location_origin_id'):
                page['location_origin_id'] = self.env['stock.location'].browse(page_data['location_origin_id'])
            if page_data.get('product_origin_id'):
                page['product_origin_id'] = self.env['product.product'].browse(page_data['product_origin_id'])
                page['origin_qty'] = page_data['origin_qty']

            page['hide_scan'] = True
            page['button_message'] = page_data.get('button_message', '')
            page['button_ok'] = _("Valide")
            page['button_cancel'] = _("Cancel")

        #Asck qty of product
        if page_data['scenario_step'] == 'scan_origin_qty':
            page['location_origin_id'] = self.env['stock.location'].browse(page_data['location_origin_id'])
            page['product_origin_id'] = self.env['product.product'].browse(page_data['product_origin_id'])
            page['left_img'] = 'qty.jpg'
            page['right_html'] = _("Enter quantity")
            page['button_cancel'] = _("Cancel")

        #Asck qty of label
        if page_data['scenario_step'] == 'scan_printer_id':
            page['left_img'] = 'printer.jpg'
            page['right_html'] = _("Scan printer barcode")
            page['button_cancel'] = _("Cancel")

        #Asck qty of label
        if page_data['scenario_step'] == 'scan_label_qty':
            page['printer_id'] = self.env['printing.printer'].browse(page_data['printer_id'])
            page['left_img'] = 'qty.jpg'
            page['right_html'] = _("Enter quantity of new label to print")
            page['button_cancel'] = _("Cancel")

        #Asck destination location
        if page_data['scenario_step'] == 'scan_location_dest_id':
            page['location_origin_id'] = self.env['stock.location'].browse(page_data['location_origin_id'])
            page['product_origin_id'] = self.env['product.product'].browse(page_data['product_origin_id'])
            page['origin_qty'] = page_data['origin_qty']
            page['left_img'] = 'location.jpg'
            page['right_html'] = _("Scan destination location barcode")
            page['button_cancel'] = _("Cancel")

            page['default_location_ids'] = self.get_default_location_ids(page_data)
            page['default_location_ids'].append(self.get_default_scrap_id(page_data))

        #Asck pack destination location
        if page_data['scenario_step'] == 'scan_pack_location_dest_id':
            page['left_img'] = 'location.jpg'
            page['right_html'] = _("Scan destination location barcode")
            page['default_location_ids'] = self.get_default_location_ids(page_data)
            page['default_location_ids'].append(self.get_default_scrap_id(page_data))
            page['button_cancel'] = _("Cancel")

        #Asck move validation
        if page_data['scenario_step'] in ['scan_move_validation', 'scan_pack_validation']:
            page['location_origin_id'] = self.env['stock.location'].browse(page_data['location_origin_id'])
            page['product_origin_id'] = self.env['product.product'].browse(page_data['product_origin_id'])
            page['origin_qty'] = page_data['origin_qty']
            page['location_dest_id'] = self.env['stock.location'].browse(page_data['location_dest_id'])
            page['hide_scan'] = True
            page['button_ok'] = _("Valide")
            page['button_cancel'] = _("Cancel")

        #Asck pack delete validation
        if page_data['scenario_step'] in ['scan_pack_delete']:
            page['hide_scan'] = True
            page['button_ok'] = _("Valide")
            page['button_cancel'] = _("Cancel")

        #Asck pack move validation
        if page_data['scenario_step'] in ['scan_pack_move_ok']:
            page['location_dest_id'] = self.env['stock.location'].browse(page_data['location_dest_id'])
            page['hide_scan'] = True
            page['button_ok'] = _("Valide")
            page['button_cancel'] = _("Cancel")

        #Asck inventory validation
        if page_data['scenario_step'] == 'scan_inventory_validation':
            page['location_origin_id'] = self.env['stock.location'].browse(page_data['location_origin_id'])
            page['product_origin_id'] = self.env['product.product'].browse(page_data['product_origin_id'])
            page['origin_qty'] = page_data['origin_qty']
            page['hide_scan'] = True
            page['button_ok'] = _("Valide")
            page['button_cancel'] = _("Cancel")

        #just a warning scan_no_start
        if page_data['scenario_step'] in ['scan_no_start']:
            page['hide_scan'] = True

        #Show current operation information
        if page_data.get('operation_id'):
            page['operation_id'] = self.env['stock.pack.operation'].browse(page_data['operation_id'])
            page['button_next'] = _("Pass")
            if page_data['scenario_step'] == 'scan_location_origin_id':
                page['right_html'] = _("Scan location: ") + "<strong>" + page['operation_id'].location_id.name + "<strong>"
                if page.get('default_location_ids'):
                    page['default_location_ids'] = set(page.get('default_location_ids')) & set(page['operation_id'].location_id)
            if page_data['scenario_step'] == 'scan_product_origin_id':
                page['right_html'] = _("Scan product: ") + "<strong>[" + (page['operation_id'].product_id.default_code or '') + ']<br/>'
                page['right_html'] += page['operation_id'].product_id.name + "</strong>"
            if page_data['scenario_step'] == 'scan_origin_qty':
                page['right_html'] = _("Scan quantity: ") + "<strong>" + str(page['operation_id'].product_qty) + "</strong>"
            if page_data['scenario_step'] == 'scan_result_package_id':
                page['right_html'] = _("Scan current Pack or a new empty pack")

        return page

    def check_expedition(self, page_data={}):
        "check product todo in picking"
        if page_data.get('picking_id'):
            operation_ids = self.env['stock.pack.operation'].search([('picking_id', '=', page_data['picking_id'])])
            if operation_ids:
                finish = True
                for operation in operation_ids:
                    if operation.product_qty != operation.qty_done:
                        finish = False
                if finish:
                    for move in operation.picking_id.move_lines:
                        move.sudo().action_done()
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False

    def check_product_todo(self, page_data={}):
        "check product todo in picking"
        if page_data.get('picking_id') and page_data.get('product_origin_id'):
            operation_ids = self.env['stock.pack.operation'].search([('product_id', '=', page_data['product_origin_id']),
                ('picking_id', '=', page_data['picking_id'])])
            if operation_ids:
                return True
            else:
                return False
        elif page_data.get('picking_id') and page_data.get('pack_origin_id'):
            operation_ids = self.env['stock.pack.operation'].search([('result_package_id', '=', page_data['pack_origin_id']),
                ('picking_id', '=', page_data['picking_id'])])
            if operation_ids:
                return True
            else:
                return False
        else:
            return False

    def check_expedition_quantity(self, page_data={}):
        "check product qty in origin picking"
        if not page_data.get('product_origin_id') or page_data.get('pack_origin_id') or page_data.get('prodlot_origin_id'):
            return False
        elif page_data.get('origin_qty') and page_data.get('product_origin_id'):
            operation_ids = self.env['stock.pack.operation'].search([('product_id', '=', page_data['product_origin_id']),
                ('picking_id', '=', page_data['picking_id'])])
            total_qty = 0
            for operation in operation_ids:
                total_qty += operation.product_qty
            if total_qty == page_data.get('origin_qty'):
                return True
            else:
                return False

    def check_product_quantity(self, page_data={}):
        "check product qty in origin location"
        #check information
        total_qty = 0.0
        quant_ids = []
        condition = []
        if not page_data.get('location_origin_id') or not page_data.get('product_origin_id'):
            return False
        else:
            condition = [['location_id', '=', page_data.get('location_origin_id')]]
            condition.append(['product_id', '=', page_data.get('product_origin_id')])

            if page_data.get('prodlot_origin_id') and page_data.get('pack_origin_id'):
                #TODO: check prodlot qty
                condition.append(['lot_id', '=', page_data.get('prodlot_origin_id')])
                condition.append(['package_id', '=', page_data.get('pack_origin_id')])
                return False
            elif page_data.get('prodlot_origin_id'):
                #TODO: check prodlot qty
                condition.append(['lot_id', '=', page_data.get('prodlot_origin_id')])
                return False
            elif page_data.get('pack_origin_id'):
                condition.append(['package_id', '=', page_data.get('pack_origin_id')])
            else:
                condition.append(['package_id', '=', False])

        if page_data.get('page', 'none') == 'pack_add':
            condition.append(['package_id', '=', False])
            condition.append(('reservation_id', '=', False))

        if condition:
            quant_ids = self.env['stock.quant'].search(condition)

            for quant in quant_ids:
                total_qty += quant.qty

            if total_qty <= 0.0:
                return False
            else:
                if not page_data.get('origin_qty'):
                    return True
                elif page_data['origin_qty'] <= total_qty:
                    return True
                else:
                    return False
        return False

    def action_inventory_product(self, page_data={}):
        "Add product inventory line"

        if page_data.get('inventory_id'):
            inventory = self.env['stock.inventory'].browse(page_data['inventory_id'])
            if inventory.state != 'confirm':
                return False

            product_id = page_data.get('product_origin_id')
            package_id = page_data.get('pack_origin_id')
            location_id = page_data.get('location_origin_id')
            product_qty = page_data.get('origin_qty')

            if product_id and location_id and (product_qty > 0.0):
                inventory_line_ids = self.env['stock.inventory.line'].search(
                    [('inventory_id', '=', inventory.id),
                    ('product_id', '=', product_id),
                    ('location_id', '=', location_id)
                    ])
                if len(inventory_line_ids) > 1:
                    return False
                if len(inventory_line_ids) == 1:
                    inventory_line_ids.write({'product_qty': product_qty})
                    return True
                else:
                    #create new line
                    values = {
                        'inventory_id': inventory.id,
                        'product_id': product_id,
                        'location_id': location_id,
                        'package_id': package_id,
                        'product_qty': product_qty,
                        }
                    existings = self.env['stock.inventory.line'].search([
                        ('product_id', '=', values.get('product_id')),
                        ('inventory_id.state', '=', 'confirm'),
                        ('location_id', '=', values.get('location_id')),
                        ('package_id', '=', values.get('package_id')),
                        ('prod_lot_id', '=', values.get('prod_lot_id'))])
                    if existings:
                        return False
                    else:
                        self.env['stock.inventory.line'].create(values)
                        return True

        return False

    def action_valide_qty_todo(self, page_data={}):
        "Add product qty todo in picking"
        if page_data.get('picking_id') and page_data.get('product_origin_id') and page_data.get('origin_qty'):
            operation_ids = self.env['stock.pack.operation'].search([
                ('product_id', '=', page_data['product_origin_id']),
                ('picking_id', '=', page_data['picking_id'])])
            for operation in operation_ids:
                operation.qty_done = operation.product_qty
                return True
        elif page_data.get('picking_id') and page_data.get('pack_origin_id'):
            operation_ids = self.env['stock.pack.operation'].search([
                ('picking_id', '=', page_data['picking_id']),
                ('result_package_id', '=', page_data['pack_origin_id'])])
            for operation in operation_ids:
                operation.qty_done = operation.product_qty
                return True
        return False

    def action_init_qty_todo(self, page_data={}):
        "init product qty todo to zero"

        if page_data.get('picking_id'):
            operation_ids = self.env['stock.pack.operation'].search([('picking_id', '=', page_data['picking_id'])])
            for operation in operation_ids:
                operation.sudo().write({'qty_done': 0.0})
            return True
        return False

    def action_add_qty_todo(self, page_data={}):
        "Add product qty todo in picking"
        if page_data.get('picking_id') and page_data.get('product_origin_id') and page_data.get('origin_qty'):
            picking = self.env['stock.picking'].browse(page_data['picking_id'])
            product = self.env['product.product'].browse(page_data['product_origin_id'])
            operation_ids = self.env['stock.pack.operation'].search([('product_id', '=', product.id), ('picking_id', '=', picking.id)])
            if len(operation_ids) == 1:
                operation_ids[0].qty_done = operation_ids[0].qty_done + page_data['origin_qty']
                return True
            else:
                return False
        return False

    def action_add_product_todo(self, page_data={}):
        "Add product todo in picking"
        if page_data.get('picking_id') and page_data.get('product_origin_id'):
            picking = self.env['stock.picking'].browse(page_data['picking_id'])
            product = self.env['product.product'].browse(page_data['product_origin_id'])
            operation_id = self.env['stock.pack.operation'].create({
                'product_id': product.id,
                'product_uom_id': product.uom_id.id,
                'picking_id': picking.id,
                'location_id': picking.location_id.id,
                'location_dest_id': picking.location_dest_id.id,
                })
            return operation_id
        return False

    def action_move_to_output(self, page_data={}):
        "write a product move"

        #Check if picking move for scanner is in progress or create one
        picking = self.env['stock.picking'].picking_scanner()

        operation_id = self.env['stock.pack.operation'].browse(page_data.get('operation_id'))

        if page_data.get('product_origin_id'):
            product = self.env['product.product'].browse(page_data.get('product_origin_id'))
        else:
            return False

        move_vals = {
            'picking_id': picking.id,
            'product_id': product.id,
            'name': product.partner_ref,
            'product_uom': product.uom_id.id,
            'location_id': page_data.get('location_origin_id'),
            'location_dest_id': self.warehouse_id.wh_output_stock_loc_id.id,
            'product_uom_qty': page_data.get('origin_qty'),
            }

        new_move_id = self.env['stock.move'].sudo().create(move_vals)

        #Unreserve quant
        reserved_quant_ids = []
        for link in operation_id.linked_move_operation_ids:
            reserved_quant_ids.append(link.reserved_quant_id.id)
            link.reserved_quant_id.sudo().write({'reservation_id': new_move_id.id})
            link.move_id.sudo().write({'location_id': move_vals['location_dest_id']})

        #Change the operation location
        operation_id.sudo().write({'location_id': move_vals['location_dest_id']})

        #move product
        new_move_id.sudo().write({'reserved_quant_ids': [(6, 0, reserved_quant_ids)]})
        new_move_id.sudo().action_confirm()
        new_move_id.sudo().action_done()

        #Reserve quant
        for link in operation_id.linked_move_operation_ids:
            link.reserved_quant_id.sudo().write({'reservation_id': link.move_id.id})

        if page_data.get('result_package_id'):
            pack_dest = self.env['stock.quant.package'].browse(page_data['result_package_id'])
            for quant in new_move_id.quant_ids:
                quant.sudo().write({'package_id': pack_dest.id})
            operation_id.sudo().write({'package_id': page_data['result_package_id']})

        return True

    def action_move_product(self, page_data={}):
        "write a product move"
        #Check if picking move is in progress or create one
        picking = self.env['stock.picking'].picking_scanner()

        if page_data.get('product_origin_id'):
            product = self.env['product.product'].browse(page_data.get('product_origin_id'))

            move_vals = {
                'picking_id': picking.id,
                'product_id': product.id,
                'name': product.partner_ref,
                'product_uom': product.uom_id.id,
                'location_id': page_data.get('location_origin_id'),
                'location_dest_id': page_data.get('location_dest_id'),
                'product_uom_qty': page_data.get('origin_qty'),
                }

            if page_data.get('pack_origin_id'):
                quant_ids = self.env['stock.quant'].search([
                    ['package_id', '=', page_data.get('pack_origin_id')],
                    ['product_id', '=', product.id],
                    ])
                move_vals['reserved_quant_ids'] = [(6, 0, [x.id for x in quant_ids])]

            if page_data.get('page', 'none') == 'pack_add':
                quant_ids = self.env['stock.quant'].search([
                    ['location_id', '=', page_data.get('location_origin_id')],
                    ['product_id', '=', product.id],
                    ['reservation_id', '=', False],
                    ['package_id', '=', False],
                    ])
                move_vals['reserved_quant_ids'] = [(6, 0, [x.id for x in quant_ids])]

            if page_data.get('pack_dest_id'):
                pack_dest = self.env['stock.quant.package'].browse(page_data['pack_dest_id'])
                if pack_dest.location_id:
                    move_vals['location_dest_id'] = pack_dest.location_id.id

            new_move_id = self.env['stock.move'].sudo().create(move_vals)
            new_move_id.sudo().action_confirm()
            new_move_id.sudo().action_done()

            if page_data.get('pack_dest_id'):
                for quant in new_move_id.quant_ids:
                    quant.sudo().write({'package_id': pack_dest.id})

            return True
        else:
            return False

    def get_default_location_ids(self, page_data):
        "return fonctionnal location like quality, input, output"
        location_ids = []

        if self.warehouse_id.wh_input_stock_loc_id and self.warehouse_id.wh_input_stock_loc_id.active:
            location_ids.append(self.warehouse_id.wh_input_stock_loc_id)
        if self.warehouse_id.wh_qc_stock_loc_id and self.warehouse_id.wh_qc_stock_loc_id.active:
            location_ids.append(self.warehouse_id.wh_qc_stock_loc_id)
        if self.warehouse_id.wh_pack_stock_loc_id and self.warehouse_id.wh_pack_stock_loc_id.active:
            location_ids.append(self.warehouse_id.wh_pack_stock_loc_id)
        if self.warehouse_id.wh_output_stock_loc_id and self.warehouse_id.wh_output_stock_loc_id.active:
            location_ids.append(self.warehouse_id.wh_output_stock_loc_id)

        return location_ids

    def get_default_scrap_id(self, page_data):
        "return scrap location"
        scrap_location_ids = self.env['stock.location'].search([('scrap_location', '=', True)])
        return scrap_location_ids[0]

    def get_default_preparation_ids(self, page_data, limit=10):
        "return preparation to choice"
        preparation_ids = self.env['stock.picking.wave'].search([
            ('state', '=', 'in_progress'),
            '|', ('user_id', '=', self.env.user.id), ('user_id', '=', False)], limit=limit)
        return preparation_ids

    def get_default_picking_ids(self, page_data, type_code='incoming'):
        "return picking in to choice"
        if type_code == 'incoming':
            picking_ids = self.env['stock.picking'].search([('picking_type_id.code', '=', type_code),
                    ('state', 'in', ['assigned', 'confirmed', 'partialy_available'])], order="min_date")
        elif type_code == 'expedition':
            picking_ids = self.env['stock.picking'].search([('expedition', '=', True)], order="min_date")
        return picking_ids

    def get_default_inventory(self, page_data):
        "return current inventory"
        res = {}

        inventory_ids = self.env['stock.inventory'].search(
            [('user_id', '=', False), ('state', '=', 'confirm'),
            ('filter', '=', 'none')])

        if len(inventory_ids) == 1:
            res['inventory_id'] = inventory_ids[0].id
            inventory_ids = self.env['stock.inventory'].search([('user_id', '!=', False), ('state', '=', 'confirm')])
            if inventory_ids:
                res['warning'] = _('Some partials inventories are opening!<br/>Please, close partial inventory before start a general inventory')
                for inventory in inventory_ids:
                    res['warning'] += '<br/>' + inventory.name

        elif len(inventory_ids) > 1:
            res['warning'] = _('Some generales inventories are opening. It is ambiguous.')
            res['warning'] += _('<br/>Please, Keep only one general inventory opening before start')
            for inventory in inventory_ids:
                res['warning'] += '<br/>' + inventory.name

        else:
            #Search if personnal inventory is in progress
            condition = [('user_id', '=', self.env.user.id), ('state', '=', 'confirm')]

            if page_data.get('pack_origin_id'):
                condition.append(('filter', '=', 'pack'))
                condition.append(('package_id', '=', page_data.get('pack_origin_id')))
            else:
                condition.append(('filter', '=', 'partial'))

            inventory_ids = self.env['stock.inventory'].search(condition)

            if len(inventory_ids) == 1:
                res['inventory_id'] = inventory_ids[0].id
                if inventory_ids[0].date < fields.Datetime.now()[:10] + ' 00:00:00':
                    res['warning'] = _('The date of your inventory is %s. It is ambiguous.') % inventory_ids[0].date
                    res['warning'] += _('Please, check and close this old inventory before start a new one.')

            elif len(inventory_ids) > 1:
                res['warning'] = _('Some partials inventories are opening!<br/>Please, close old inventories before start a new one')
                for inventory in inventory_ids:
                    res['warning'] += '<br/>' + inventory.name
            else:
                #create personnal inventory
                inventory_vals = {'filter': 'partial',
                            'user_id': self.env.user.id,
                            'name': _('Partial inventory - ') + self.env.user.name}

                if page_data.get('pack_origin_id'):
                    inventory_vals['filter'] = 'pack'
                    inventory_vals['package_id'] = page_data.get('pack_origin_id')
                    pack = self.env['stock.quant.package'].browse(page_data.get('pack_origin_id'))
                    inventory_vals['name'] = _('Pack inventory - ') + pack.name + ' - ' + self.env.user.name

                inventory = self.env['stock.inventory'].create(inventory_vals)
                inventory.prepare_inventory()
                res['inventory_id'] = inventory.id
        return res


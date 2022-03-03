# -*- coding: utf-8 -*-

import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

SRC_PATH = 'wms_scanner'
IMG_PATH = SRC_PATH + '/static/src/img/'
CSS_FILE = SRC_PATH + "/static/src/css/screen_240.css"
IMG_FLAG = {'fr_FR': 'flag-fr.jpg', 'en_US': 'flag-gb.jpg', 'nl_BE': 'flag-be.jpg', 'de_DE': 'flag-de.jpg'}

class WmsController(http.Controller):

    @http.route(['/scanner'], type='http', auth='user', redirect='/web/login?redirect=%2Fscanner', csrf=False)
    def index(self, debug=False, **k):

        # Check if user is logged
        if not request.session.uid:
            return http.local_redirect('/web/login?redirect=%2Fscanner')

        # Create session Data, data store the objects to use in the qweb template
        data = self.init_data()

        # Scenario analyse, complete data
        data = self.start_scenario(data)

        # Qweb render
        if data.get('function'):
            return self.session_function(data)
        else:
            return self.render_QWEB(data)

    def start_scenario(self, data):
        "Analyse response"
        # get the scanner response
        response = dict(request.params) or {}

        if not response:
            # first time go to main menu
            data = self.main_menu()
        else:
            if response.get('menu'):
                if response['menu'] <= '0' or not response['menu'].isdigit():
                    # main menu (menu=0) or not defined, go to main menu
                    data = self.main_menu()
                else:
                    # list the childs menus
                    menu_ids = request.env['wms.menu'].search([('id', '=', int(response['menu']))])
                    if menu_ids:
                        menu = menu_ids[0]
                        if menu.menu_type in ['wms', 'logout']:
                            # Return session_function
                            data['function'] = menu.menu_type
                        elif menu.menu_type == 'scanner':
                            data['qweb_template'] = 'wms_scanner.scanner_zxing2'
                        else:
                            # return childs menus
                            data['menu'] = request.env['wms.menu'].search([('parent_id', '=', menu.id)])
                    else:
                        data = self.main_menu()

            elif response.get('scenario'):
                # Go to the scenario
                if response['scenario'] <= '0' or not response['scenario'].isdigit():
                    # scenario not defined, go to main menu
                    data = self.main_menu()
                else:
                    scenario_ids = request.env['wms.scenario'].search([('id', '=', int(response['scenario']))])
                    if scenario_ids:
                        data = scenario_ids[0].do_scenario(data)
                    else:
                        # scenario not defined, go to main menu
                        data = self.main_menu()
            else:
                # To defined or some error
                data = self.main_menu()

        return data

    def init_data(self):
        "initialise data"
        data = {
            'user': request.env['res.users'].browse(request.uid),
            #'img_path': IMG_PATH,
            }
        return data

    def main_menu(self):
        "return to main menu"
        data = self.init_data()
        data['menu'] = request.env['wms.menu'].search([('parent_id', '=', False)])
        request.session['scenario_data'] = {}
        return data

    def session_function(self, data):
        "Specific menu function"
        function_name = data.get('function', '?')
        if function_name == 'logout':
            # return to login page
            return self.session_logout(data)
        elif function_name == 'wms':
            # Return to Odoo
            return http.local_redirect('/web')
        else:
            # To defined or some error
            return self.session_logout(data)

    def session_logout(self, data):
        "close the session, log information"
        request.session['scenario_data'] = {}
        request.session.logout()
        return http.local_redirect('/web/login?redirect=%2Fscanner')

    def session_information(self):
        "log information about this session"
        # TODO request.httprequest.environ get IP
        session_ids = request.env['wms.session'].search([('name', '=', request.session.sid)])
        if not session_ids:
            session = request.env['wms.session'].create({'name': request.session.sid})
        else:
            session = session_ids[0]

        return session

    def session_debug(self, data):
        "Debug information, return data in html"
        debug = "<b>QWEB DATA:</b><br/>" + request.env['wms.scenario'].data_debug(data)
        return debug

    def render_QWEB(self, data):
        "render the HMTL with QWEB"
        if data.get('qweb_template'):
            return request.render(data['qweb_template'], data)
        elif data.get('menu'):
            return request.render('wms_scanner.wms_scanner_menu_template', data)
        elif data.get('scenario'):
            return request.render('wms_scanner.wms_scanner_scenario_template', data)
        else:
            data.update({'debug': self.session_debug(data)})
            return request.render('wms_scanner.scanner_scenario_blank', data)


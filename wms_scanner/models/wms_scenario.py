# 2020 Joannes Landy <joannes.landy@opencrea.fr>
# Based on the work of sylvain Garancher <sylvain.garancher@syleam.fr>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from odoo import models, api, fields
from odoo import _
from odoo.http import request

import logging
logger = logging.getLogger('wms_scanner')


class WmsScenario(models.Model):
    _name = 'wms.scenario'
    _description = 'Scenario for scanner'
    _order = 'sequence'

    name = fields.Char(
        string='Name',
        required=True,
        translate=True,
        help='Appear on barcode reader screen.')
    sequence = fields.Integer(
        string='Sequence',
        default=100,
        required=False,
        help='Sequence order.')
    scenario_image = fields.Char('Image filename', default='construction.jpg')

    debug_mode = fields.Boolean(
        string='Debug mode')
    active = fields.Boolean(
        string='Active',
        default=True,
        help='If check, this object is always available.')
    step_ids = fields.One2many(
        comodel_name='wms.scenario.step',
        inverse_name='scenario_id',
        string='Scenario',
        ondelete='cascade',
        help='Step of the scenario.')
    warehouse_ids = fields.Many2many(
        comodel_name='stock.warehouse',
        relation='scanner_scenario_warehouse_rel',
        column1='scenario_id',
        column2='warehouse_id',
        string='Warehouses',
        help='Warehouses for this scenario.')
    notes = fields.Text(
        string='Notes',
        help='Store different notes, date and title for modification, etc...')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_id.id,
        ondelete='restrict',
        help='Company to be used on this scenario.')
    group_ids = fields.Many2many(
        comodel_name='res.groups',
        relation='scanner_scenario_res_groups_rel',
        column1='scenario_id',
        column2='group_id',
        string='Allowed Groups',
        default=lambda self: [self.env.ref('stock.group_stock_user').id])
    user_ids = fields.Many2many(
        comodel_name='res.users',
        relation='scanner_scenario_res_users_rel',
        column1='scenario_id',
        column2='user_id',
        string='Allowed Users')

    def copy(self, default=None):
        default = default or {}
        default['name'] = _('Copy of %s') % self.name

        scenario_new = super(WmsScenario, self).copy(default)
        step_news = {}
        for step in self.step_ids:
            step_news[step.id] = step.copy(
                {'scenario_id': scenario_new.id}).id
        for trans in self.env['wms.scenario.transition'].search(
                [('scenario_id', '=', self.id)]):
            trans.copy({'from_id': step_news[trans.from_id.id],
                        'to_id': step_news[trans.to_id.id]})
        return scenario_new

    def open_diagram(self):
        "open the diagram view"
        self.ensure_one()
        view_id = self.env.ref('wms_scanner.view_wms_scenario_diagram').id

        action = {
            'name': _('Scenario'),
            'view_type': 'form',
            'view_mode': 'diagram_plus',
            "views": [[view_id, "diagram_plus"]],
            'res_model': 'wms.scenario',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
            }
        return action

    def get_session_data(self):
        "get data by session, so one session data by scanner"
        return request.session.get('scenario_data', {})

    def save_session_data(self, scenario_data):
        "save data by session, so one session data by scanner"
        request.session['scenario_data'] = scenario_data

    def get_scanner_response(self):
        "get the response of the scanner, only one scanner by session"
        return dict(request.params) or {}

    def do_scenario(self, data):
        "execute the scenario"
        self.ensure_one()
        data['scenario'] = self
        scenario_data = self.get_session_data()

        # init data if first time
        if not scenario_data or scenario_data.get('scenario', 0) != self.id:
            # start new scenario
            step_ids = self.env['wms.scenario.step'].search(
                    [('scenario_id', '=', self.id), ('action_scanner', '=', 'start')])
            if step_ids:
                scenario_data = {'scenario': self.id, 'step': step_ids[0].id}
            else:
                scenario_data = {'scenario': self.id}
                # There is no starting step
                debug = _("There is no starting step in this scenario")
                data.update({'debug': debug})

        # Get the current step of the scenario
        step_ids = self.env['wms.scenario.step'].search(
                    [('scenario_id', '=', self.id),
                     ('id', '=', scenario_data.get('step', 0))])
        if step_ids:
            data['step'] = step_ids[0]
            if step_ids[0].action_scanner == 'start':
                self.save_session_data({'scenario': self.id, 'step': step_ids[0].id})
            data = self.continue_scenario(data)

        # Add debug information if exist
        data = self.scenario_debug(data)

        return data

    def compute_step(self, scenario_data, data, transitions_tested):
        "check transition and update scenario_data of the current step"
        self.ensure_one()
        step_id = scenario_data.get('step')
        step = self.env['wms.scenario.step'].browse(step_id)
        print('-------Step-------', step.name)

        # Check transition, return next step
        for transition in step.out_transition_ids:
            # prevent infinite loop
            if transition in transitions_tested:
                # There is a infinite loop
                debug = data.get('debug', '')
                debug += "<br/>" + _("There is a infinite loop in this scenario!")
                data.update({'debug': debug})
                break
            else:
                transitions_tested |= transition

            # Check if python code to execute
            if step.python_code:
                scenario_data, data = step.run(scenario_data, data)

            # Check if one transition is ok
            if transition.check(scenario_data, data):
                print('-------transition-------', transition.name)
                scenario_data['step'] = transition.to_id.id
                scenario_data, data, transitions_tested = self.compute_step(
                                    scenario_data, data, transitions_tested)
                break

        # return the new current step
        return scenario_data, data, transitions_tested

    def continue_scenario(self, data):
        "Check the response, and choice the next step"
        self.ensure_one()
        scenario_data = self.get_session_data()
        transitions_tested = self.env['wms.scenario.transition']

        # <<<< Compute user response >>>>
        step = self.env['wms.scenario.step'].browse(scenario_data.get('step'))
        response = self.get_scanner_response()

        # check button
        if response.get('button'):
            # do button action
            pass
        # check scan
        elif step.action_scan:
            # do scan response
            scenario_data, data = step.read_scan(scenario_data, data)
        # to defined
        else:
            pass

        if data.get('warning'):
            return data
        else:
            # Defined next step
            scenario_data, data, transitions_tested = self.compute_step(scenario_data, data, transitions_tested)
            if data.get('warning'):
                return data
            else:
                # Save result and update qweb data
                self.save_session_data(scenario_data)
                data['step'] = self.env['wms.scenario.step'].browse(scenario_data.get('step'))

        return data

    def scenario_debug(self, data):
        "add debug informations on qweb data"
        self.ensure_one()
        if self.debug_mode:
            debug = data.get('debug', '')
            debug += "</b><b>INPUT DATA:</b><br/>" + self.format_debug(self.get_scanner_response())
            debug += "<b>SESSION DATA:</b><br/>" + self.format_debug(self.get_session_data())
            debug += "<b>QWEB DATA:</b><br/>" + self.format_debug(data)
            data.update({'debug': debug})
        return data

    @api.model
    def format_debug(self, sub_data):
        "Debug information, return sub_data in html"
        if not sub_data:
            html = ""
        if type(sub_data) is dict:
            html = "<ul>"
            for key in list(sub_data.keys()):
                if type(sub_data[key]) in [list, dict]:
                    html += '<li><b>%s: </b></li>' % (key)
                    html += self.data_debug(sub_data[key])
                else:
                    html += '<li><b>%s: </b>%s</li>' % (key, sub_data[key])
            html += "</ul>"

        elif type(sub_data) is list:
            html = "<ul>"
            for idx, item in enumerate(sub_data):
                if type(item) in [list, dict]:
                    html += '<li>[%s]:</li>' % (idx)
                    html += self.data_debug(item)
                else:
                    html += '<li>[%s]: %s</li>' % (idx, item)
            html += "</ul>"

        else:
            html = "<li>%s</li>" % (sub_data)
        return html



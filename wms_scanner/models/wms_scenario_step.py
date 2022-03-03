# 2020 Joannes Landy <joannes.landy@opencrea.fr>
# Based on the work of sylvain Garancher <sylvain.garancher@syleam.fr>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from string import printable

from odoo.tools.safe_eval import safe_eval, test_python_expr
from odoo import models, api, fields
from odoo.exceptions import MissingError, UserError, ValidationError
from odoo import _

logger = logging.getLogger('wms_scanner')


class WmsScenarioStep(models.Model):
    _name = 'wms.scenario.step'
    _description = 'Step for scenario'

    name = fields.Char(
        string='Name',
        help='Name of the step.')
    action_scanner = fields.Selection(
        [('none', 'Not defined'),
         ('start', 'start'),
         ('end', 'end'),
         ('message', 'Message to user'),
         ('top_message', 'Top message'),
         ('question', 'Question to user'),
         ('scan_quantity', 'Enter quantity'),
         ('scan_text', 'Enter description'),
         ('scan_model', 'Scan model'),
         ('python_code', 'Python code'),
         ],
        string="Scanner action",
        translate=True,
        default="none")
    action_model = fields.Many2one('ir.model',
                                   string="model")
    action_scan = fields.Boolean('Scan input',
                                 compute='compute_action_scan')
    action_variable = fields.Char('Variable to use')
    action_message = fields.Char('Message',
                                 translate=True)
    action_image = fields.Char('Image filename',
                               default='construction.jpg')
    button_ok = fields.Boolean('Button OK')
    button_ok_text = fields.Char('Button OK',
                                 default='OK',
                                 translate=True)
    button_cancel = fields.Boolean('Button Cancel')
    button_cancel_text = fields.Char('Button Cancel',
                                     default='Cancel',
                                     translate=True)
    button_skip = fields.Boolean('Button Skip')
    button_skip_text = fields.Char('Button Skip',
                                   default='Skip',
                                   translate=True)
    scenario_id = fields.Many2one(
        comodel_name='wms.scenario',
        string='Scenario',
        required=True,
        ondelete='cascade',
        help='Scenario for this step.')
    out_transition_ids = fields.One2many(
        comodel_name='wms.scenario.transition',
        inverse_name='from_id',
        string='Outgoing transitions',
        ondelete='cascade',
        help='Transitions which goes to this step.')
    in_transition_ids = fields.One2many(
        comodel_name='wms.scenario.transition',
        inverse_name='to_id',
        string='Incoming transitions',
        ondelete='cascade',
        help='Transitions which goes to the next step.')
    python_code = fields.Text(
        string='Python code',
        help='Python code to execute.')
    scenario_notes = fields.Text(related='scenario_id.notes', readonly=False)

    bgcolor_expr = fields.Char('Background color expression')
    bg_color = fields.Char('Background color')
    fg_color = fields.Char('Foreground color')
    rectangle = fields.Boolean('Rectangle')

    @api.constrains('python_code')
    def _check_python_code(self):
        for step in self.sudo().filtered('python_code'):
            msg = test_python_expr(expr=step.python_code.strip(), mode="exec")
            if msg:
                raise ValidationError(msg)

    @api.depends('action_scanner')
    def compute_action_scan(self):
        "use scanner input for this action?"
        for step in self:
            if step.action_scanner in [
                    'none', 'message', 'question',
                    'end', 'start', 'python_code']:
                step.action_scan = False
            else:
                step.action_scan = True

    @api.onchange('action_scanner')
    def onchange_action_scanner(self):
        "initialise step attributs, suggest default value"
        self.action_message = ""
        self.action_model = False
        self.action_variable = False
        self.action_image = 'construction.jpg'

    def read_scan(self, scenario_data={}, data={}):
        "Decode scan and return associated objects"
        self.ensure_one()
        response = self.scenario_id.get_scanner_response()
        scan = response.get('scan', '')

        def is_alphanumeric(scan):
            "check the scan string"
            res = True
            for scan_char in scan:
                if scan_char not in printable:
                    res = False
                    break
            return res

        if not scan:
            data['warning'] = _('The barcode is empty')
        elif not self.action_variable:
            data['warning'] = _('This scenario is currently under construction.'
                                'Some parameters are not set. (variable)')
        elif self.action_scanner == 'scan_text':
            scenario_data[self.action_variable] = scan
        elif not is_alphanumeric(scan):
            data['warning'] = _('The barcode is unreadable')
        elif self.action_scanner == 'scan_quantity':
            try:
                quantity = float(scan)
                scenario_data[self.action_variable] = quantity
            except:
                data['warning'] = _('Please, enter a numeric value')
        elif self.action_scanner == 'scan_model':
            if self.action_model:
                list_field = list(dir(self.env[self.action_model.model]))
                for search_field in ['barcode', 'default_code', 'code', 'name']:
                    if search_field in list_field:
                        condition = [(search_field, '=', scan)]
                        result_ids = self.env[self.action_model.model].search(condition)
                        if len(result_ids) == 1:
                            scenario_data[self.action_variable] = result_ids[0].id
                            break
                        elif len(result_ids) > 1:
                            scenario_data, data = self.read_scan_duplicate(scenario_data, data)
                if not scenario_data.get(self.action_variable):
                    data['warning'] = _('The barcode is unknow')
            else:
                data['warning'] = _('This scenario is currently under construction.'
                                    'Some parameters are not set. (model)')
        else:
            data['warning'] = _('The barcode is unknow')

        return scenario_data, data

    def read_scan_duplicate(self, scenario_data, data):
        "Function to return value when the scan found duplicat object"
        return scenario_data, data

    def run(self, scenario_data={}, data={}):
        "Eval the python code"
        self.ensure_one()
        eval_context = {'scenario_data': scenario_data, 'data': data}
        safe_eval(self.python_code.strip(), eval_context, mode="exec", nocopy=True)
        return eval_context.get('scenario_data', {}), eval_context.get('data', {})

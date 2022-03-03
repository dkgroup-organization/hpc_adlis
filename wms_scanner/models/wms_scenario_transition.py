# 2020 Joannes Landy <joannes.landy@opencrea.fr>
# Based on the work of sylvain Garancher <sylvain.garancher@syleam.fr>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import sys
import traceback
from odoo import models, api, fields, exceptions
from odoo import _
from odoo.tools.safe_eval import expr_eval
import logging
logger = logging.getLogger('wms_scanner')


class ScannerScenarioTransition(models.Model):
    _name = 'wms.scenario.transition'
    _description = 'Transition for scenario'
    _order = 'sequence'

    # ===========================================================================
    # COLUMNS
    # ===========================================================================
    name = fields.Char(
        string='Name',
        required=True,
        help='Name of the transition.')
    sequence = fields.Integer(
        string='Sequence',
        default=0,
        required=False,
        help='Sequence order.')
    from_id = fields.Many2one(
        comodel_name='wms.scenario.step',
        string='From',
        required=True,
        ondelete='cascade',
        help='Step which launches this transition.')
    to_id = fields.Many2one(
        comodel_name='wms.scenario.step',
        string='To',
        required=True,
        ondelete='cascade',
        help='Step which is reached by this transition.')
    condition = fields.Char(
        string='Condition',
        required=True,
        default='True',
        help='The transition is followed only if this condition is evaluated '
             'as True.')
    scenario_id = fields.Many2one(
        comodel_name='wms.scenario',
        string='Scenario',
        required=False,
        related="from_id.scenario_id",
        store=True,
        ondelete='cascade',
        readonly=True)

    @api.constrains('condition')
    def _check_condition_syntax(self):
        """
        Syntax check the python condition of a transition
        """
        for transition in self:
            try:
                compile(transition.condition, '<string>', 'eval')
            except SyntaxError as exception:
                logger.error(''.join(traceback.format_exception(
                    sys.exc_info()[0],
                    sys.exc_info()[1],
                    sys.exc_info()[2],
                )))
                raise exceptions.ValidationError(
                    _('Error in condition for transition "%s"'
                      ' at line %d, offset %d:\n%s') % (
                        transition.name,
                        exception.lineno,
                        exception.offset,
                        exception.msg,
                    ))

        return True

    def check(self, scenario_data, data):
        "Check the condition transition"
        self.ensure_one()
        previews_variable = self.from_id.action_variable
        if previews_variable:
            if scenario_data.get(previews_variable):
                return True
            else:
                return False
        else:
            if expr_eval(self.condition):
                return True
            else:
                return False

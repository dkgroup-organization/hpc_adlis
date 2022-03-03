# 2020 Joannes Landy <joannes.landy@opencrea.fr>
# Based on the work of sylvain Garancher <sylvain.garancher@syleam.fr>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from odoo import models, api, fields
import os
import logging
logger = logging.getLogger('wms_scanner')


class WmsMenu(models.Model):
    _name = 'wms.menu'
    _description = 'Menu for scanner'
    _order = 'sequence'

    # ===========================================================================
    # COLUMNS
    # ===========================================================================

    name = fields.Char(
        string='name',
        translate=True,
        required=True)
    parent_id = fields.Many2one(
        comodel_name='wms.menu',
        string='Parent menu')
    sequence = fields.Integer(
        string='Sequence',
        default=1,
        required=False,
        help='Sequence order.')
    image_file = fields.Char(
        string='Image filename',
        default='construction.jpg')
    menu_type = fields.Selection(
        [('menu', 'Menu'), ('scenario', 'Scenario'), ('logout', 'Logout'), ('wms', 'Return to WMS'), ('scanner', 'Test scanner')],
        string="type",
        default="menu")
    scenario_id = fields.Many2one(
        comodel_name='wms.scenario',
        string='Scenario',
        help='Scenario for this menu.')
    menu_code = fields.Char(
        string='Code',
        compute='_compute_menu_code')
    active = fields.Boolean(
        string='Active',
        default=True,
        help='If check, this menu is available.')
    warehouse_ids = fields.Many2many(
        comodel_name='stock.warehouse',
        relation='wms_menu_warehouse_rel',
        column1='menu_id',
        column2='warehouse_id',
        string='Warehouses',
        help='Warehouses for this menu.')
    notes = fields.Text(
        string='Notes',
        help='Store different notes, date and title for modification, etc...')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_id.id,
        ondelete='restrict',
        help='Company to be used on this menu.')
    group_ids = fields.Many2many(
        comodel_name='res.groups',
        relation='wms_menu_res_groups_rel',
        column1='menu_id',
        column2='group_id',
        string='Allowed Groups',
        default=lambda self: [self.env.ref('stock.group_stock_user').id])
    user_ids = fields.Many2many(
        comodel_name='res.users',
        relation='wms_menu_res_users_rel',
        column1='menu_id',
        column2='user_id',
        string='Allowed Users')

    def _compute_menu_code(self):
        "return the href of this menu"
        for menu in self:
            if menu.menu_type in ['menu', 'logout', 'wms', 'scanner']:
                menu.menu_code = '?menu=%s' % (menu.id)
            elif menu.menu_type == 'scenario':
                menu.menu_code = '?scenario=%s' % (menu.scenario_id.id or 0)
            else:
                menu.menu_code = '?menu=0'

# -*- coding: utf-8 -*-

import base64
import math
import pytz
import tempfile
import codecs
import datetime
import csv

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
log = logging.getLogger(__name__).info
_logger = logging.getLogger(__name__)

FORMAT_ENCODING = [('utf-8', 'utf-8'), ('windows-1252', 'windows-1252'), ('latin1', 'latin1'),
    ('latin2', 'latin2'), ('utf-16', 'utf-16'), ('windows-1251', 'windows-1251')]
FORMAT_SEPARATOR = [(';', 'Semicolon'), (',', 'Comma'), ('\t', 'Tab')]
FORMAT_DATE = [('ddmmyy', 'ddmmyy'), ('dd/mm/yyyy', 'dd/mm/yyyy'), ('yyyy-mm-dd', 'yyyy-mm-dd'),
    ('yyyymmdd', 'yyyymmdd'), ('mm/dd/yyyy', 'mm/dd/yyyy')]
MAP_MONTH_NAME = {'janv': '01', u'f\xe9vr': '02', 'mars': '03', 'avr': '04', 'mai': '05',
        'juin': '06', 'juil': '07', u'ao\xfbt': '08', 'sept': '09', 'oct': '10',
        'nov': '11', u'd\xe9c': '12'}

MIN_COLUMN = 2
FLOAT_PRECISION = 0.01
TIMEZONE = "Europe/Paris"


def to_float(text_number):
    "always return float, if error return 0.0"
    try:
        res = float(str(text_number).replace(' ', '').replace(',', '.').replace('%', '')) or 0.0
    except:
        res = 0.0
    return res


def quotechar(text, quotechar='"'):
    "return text without quotechar"
    if len(text) >= 2:
        if text[0] == quotechar and text[-1] == quotechar:
            return text[1:-1]
        else:
            return text
    else:
        if text:
            return text
        else:
            return ''


def to_bool(text):
    "return bool"
    text = text.strip().lower() or '?'
    if text in ["yes", "oui", "1"]:
        return True
    else:
        return False


class ImportData(models.TransientModel):
    _name = "import.data"
    _description = "CSV file import"

    name = fields.Char('Name')
    import_date = fields.Datetime('Date of the import')
    import_date_todo = fields.Boolean("Import date todo")
    filename = fields.Char('File Name')
    check_field = fields.Char('Reference field')

    file_binary = fields.Binary('Import File', required=True)

    data = fields.Binary('Data')
    configuration = fields.Text("configuration")
    type_import = fields.Char("Type")
    type_import_html = fields.Html("Description")
    preview = fields.Text(string='Preview', help="Content of the file", readonly=True, default='')
    content = fields.Text(string='content', help="Content of the file", readonly=True, default='')

    encoding = fields.Selection(FORMAT_ENCODING, 'Encoding')
    delimiter = fields.Selection(FORMAT_SEPARATOR, string="Delimiter")
    quotechar = fields.Char('Quotechar')
    header = fields.Integer('Header', help='First row contains the label of the column, pass some lines before start')
    date = fields.Selection(FORMAT_DATE, string="Date")
    decimal = fields.Selection([(',', 'comma'), ('.', 'point')], string="Decimale")
    error = fields.Text('Import error', readonly=True)
    model_id = fields.Many2one('ir.model', 'Model object')
    active_id = fields.Integer('Active id')
    example_file = fields.Char("Example file")

    def button_import(self):
        "import the data"
        for wizard in self:
            wizard.error = ''
            if wizard.model_id.model == "product.category":
                wizard.import_product_category()
            if wizard.model_id.model == "account.tax":
                wizard.import_tax()
            if wizard.model_id.model == "product.product":
                wizard.import_product_variant()

    @api.model
    def default_get(self, fields):
        "default value"
        res = super().default_get(fields)

        default = {
            'encoding': 'utf-8',
            'delimiter': ';',
            'quotechar': '"',
            'header': 0,
            'date': 'yyyy-mm-dd',
            'decimal': '.',
            }
        optional = ['import_date_todo', 'type_import', 'configuration']

        context = dict(self._context or {})
        for key_name in list(default.keys()) + optional:
            if context.get(key_name):
                default[key_name] = context.get(key_name)

        model_name = context.get("model_name")
        if model_name:
            model_ids = self.env['ir.model'].search([('model', '=', model_name)])
            if model_ids:
                default['model_id'] = model_ids[0].id
            if model_name == "account.tax":
                default['configuration'] = "ID Externe;account;Séquence;Nom de la taxe;Type de taxe;Portée de la taxe;Étiquettes sur les factures;Code du pays"


        res.update(default)
        return res

    @api.onchange('encoding', 'header', 'check_field')
    def _onchange_configuration(self):
        "save the csv file on local disque"
        if self.file_binary:
            self._onchange_file()

    @api.onchange('file_binary')
    def _onchange_file(self):
        "save the csv file on local disque"
        if self.file_binary:

            #Save data on disk
            if not self.filename:
                file_name = tempfile.mkstemp('.in.csv', 'odoo-', '/tmp')[1]
                csvfile = open(file_name, 'wb')
                csvfile.write(base64.b64decode(self.file_binary))
                csvfile.close()
                self.filename = file_name
            else:
                file_name = self.filename

            content = ''
            #Detect encoding by test, use the encoding defined in first test
            if self.encoding and (self.encoding, self.encoding) != FORMAT_ENCODING[0]:
                list_encoding = [(self.encoding, self.encoding)] + FORMAT_ENCODING
            else:
                list_encoding = FORMAT_ENCODING

            for encoding_format in list_encoding:
                try:
                    csvfilein = open(file_name, 'r', encoding=encoding_format[0])
                    content = csvfilein.read()
                    csvfilein.close()
                    self.encoding = encoding_format[0]
                except:
                    self.encoding = False

                if self.encoding:
                    break

            #load data
            if self.encoding and content:
                data = content.split('\n')

                #detect the first row by the name of column: check_field
                if self.check_field:
                    self.header = 0
                    for line in data:
                        if self.check_field in line:
                            break
                        else:
                            self.header += 1

                        if self.header > 50:
                            raise UserError(_('There is an error when loading the header of the file, The field <%s> is not finding.' % (self.check_field)))

                #load data
                if self.header and len(data) > self.header:
                    data = data[self.header:]

                if len(data) < 1:
                    raise UserError(_('There is no data.'))

                header = data[0]
                #detect delimiter
                if self.delimiter in header:
                    pass
                elif ';' in header:
                    self.delimiter = ';'
                elif ',' in header:
                    self.delimiter = ','
                elif '\t' in header:
                    self.delimiter = '\t'
                else:
                    raise UserError(_('There is an error when loading the header of the file, check the delimiter configuration.'))

                #save the csv in file
                file_name_out = file_name.replace('.in.csv', '.out.csv')
                csvfileout = open(file_name_out, 'w', encoding=self.encoding)
                for row in data:
                    csvfileout.write(row + '\n')
                csvfileout.close()
                self.filename = file_name_out

                #load csv data
                csv_data = self.load_data()[self.id]

                if len(header.split(self.delimiter)) > 15:
                    # preview text
                    nb_line = 0
                    html_preview = ""
                    for line in data:
                        html_preview += line + '%s<br/>'
                        self.preview = html_preview
                        nb_line += 1
                        if nb_line > 10:
                            break
                else:
                    #preview html
                    html_preview = ""
                    html_preview += "<thead><tr>"
                    csv_header = []
                    for csv_field in header.split(self.delimiter):
                        csv_field = quotechar(csv_field, quotechar=self.quotechar)
                        html_preview += '<td>%s</td>' % (csv_field)
                        csv_header.append(csv_field.strip())
                    html_preview += "</tr></thead>"

                    nb_line = 0
                    for line in csv_data:
                        html_preview += "<tr>"
                        for csv_field in csv_header:
                            if csv_field in list(line.keys()):
                                html_preview += "<td>%s</td>" % (line[csv_field])
                            else:
                                html_preview += "<td></td>"
                        html_preview += "</tr>"
                        nb_line += 1
                        if nb_line > 10:
                            break

                    self.preview = '<table class="o_list_view table table-condensed table-bordered">' + html_preview + "</table>"
            else:
                raise UserError(_('There is an error when loading the file, check the encoding character configuration.'))
        else:
            self.filename = ''
            self.preview = ''

    def load_data(self, lower=False):
        "Load data in a list of dictionnary"
        res = {}
        # Start
        for wizard in self:
            res[wizard.id] = []

            with open(wizard.filename, encoding=wizard.encoding) as csvfile:
                spamreader = csv.reader(csvfile, delimiter=wizard.delimiter, quotechar=wizard.quotechar)

                data = []
                header = []
                for row in spamreader:
                    if row:
                        line = {}
                        if not header:
                            for csv_field in row:
                                if lower:
                                    header.append(csv_field.strip().lower())
                                else:
                                    header.append(csv_field.strip())
                        else:
                            for i, csv_field in enumerate(header):
                                line[csv_field] = row[i].strip()
                            data.append(line)
                res[wizard.id] = data
        return res

    def import_product_category(self):
        "start import"
        load_data = self.load_data()
        # Start
        for wizard in self:
                line = 1
                data = load_data[wizard.id]

                for data_line in data:
                    # Type;Code famille;Intitulé de la famille;Rmq;Ventes France;Taux Fce;Ventes CEE;Taux CEE;Ventes Hors CEE;Taux Hors CEE;Achat France ;Taux Fce;Achat CEE;Taux CEE;Achat hors CEE
                    categ_vals = {}
                    line += 1

                    # Check the name
                    name = data_line['Intitulé de la famille']
                    categ_ids = self.env['product.category'].search([('name', '=', name)])
                    if not categ_ids:
                        categ_ids = self.env['product.category'].search([('name', '=', name + ' ')])
                        if categ_ids:
                            categ_ids.write({'name': name})
                        else:
                            raise UserError(_("This category don't exist: %s" % (name)))

                    # Load data
                    if len(categ_ids) == 1:
                        account_data = {
                            'code_income_fr': data_line['Ventes France'] or '707100',
                            'code_income_cee': data_line['Ventes CEE'],
                            'code_income_export': data_line['Ventes Hors CEE'],
                            'code_expense_fr': data_line['Achat France'] or '607100',
                            'code_expense_cee': data_line['Achat CEE'],
                            'code_expense_export': data_line['Achat hors CEE'],
                        }

                        # Check account
                        account = {}
                        for account_key in list(account_data.keys()):
                            code = account_data[account_key]
                            if code:
                                account_ids = self.env['account.account'].search([('code', '=', code)])
                                if not account_ids:
                                    raise UserError(_("This account don't exist: %s" % (code)))
                                account[code] = account_ids[0]

                        # Update category
                        category = categ_ids[0]

                        if account_data.get('code_expense_fr'):
                            category.property_account_expense_categ_id = account[account_data.get('code_expense_fr')]
                        if account_data.get('code_income_fr'):
                            category.property_account_income_categ_id = account[account_data.get('code_income_fr')]

                        # Load position fiscal
                        pf_fr = self.env.ref('l10n_fr.1_fiscal_position_template_domestic')
                        pf_cee_b2c = self.env.ref('l10n_fr.1_fiscal_position_template_intraeub2c')
                        pf_cee_b2b = self.env.ref('l10n_fr.1_fiscal_position_template_intraeub2b')
                        pf_export = self.env.ref('l10n_fr.1_fiscal_position_template_import_export')

                        pf_config = [
                            (pf_cee_b2c, account_data.get('code_expense_fr'), account_data.get('code_expense_cee')),
                            (pf_cee_b2b, account_data.get('code_expense_fr'), account_data.get('code_expense_cee')),
                            (pf_export, account_data.get('code_expense_fr'), account_data.get('code_expense_export')),
                            (pf_cee_b2c, account_data.get('code_income_fr'), account_data.get('code_income_cee')),
                            (pf_cee_b2b, account_data.get('code_income_fr'), account_data.get('code_income_cee')),
                            (pf_export, account_data.get('code_income_fr'), account_data.get('code_income_export')),
                        ]

                        for config in pf_config:

                            if config[1] and config[2]:
                                account1 = account[config[1]]
                                account2 = account[config[2]]
                                p_fiscal = config[0]
                                condition = [('position_id', '=', p_fiscal.id),
                                             ('account_src_id', '=', account1.id),
                                             ('account_dest_id', '=', account2.id)]
                                config_line_ids = p_fiscal.account_ids.search(condition)

                                if not config_line_ids:
                                    line_conf_vals = {
                                        'position_id': p_fiscal.id,
                                        'account_src_id': account1.id,
                                        'account_dest_id': account2.id,
                                    }
                                    p_fiscal.account_ids.create(line_conf_vals)

                    # self._cr.commit()

    def import_tax(self):
        "start import"
        load_data = self.load_data()
        # Start
        for wizard in self:
                line = 1
                data = load_data[wizard.id]


                for data_line in data:
                    # ID Externe;Séquence;Nom de la taxe;Type de taxe;Portée de la taxe;Étiquettes sur les factures;Code du pays
                    categ_vals = {}
                    line += 1
                    log("%s" % (data_line))


    def import_product_variant(self):
        "start import"
        load_data = self.load_data()
        # Start
        for wizard in self:
                nb_line = 1
                data = load_data[wizard.id]
                if not data:
                    continue

                attributes = {}
                # load the attribute
                for key in list(data[0].keys()):
                    if key[0] == '#':
                        attributes[key[1:]] = 0

                # check the attribute
                for attribute_name in list(attributes.keys()):
                    attribute_ids = self.env['product.attribute'].search([('name', '=', attribute_name)])
                    if len(attribute_ids) == 1:
                        attributes[attribute_name] = attribute_ids[0]
                    elif len(attribute_ids) > 1:
                        raise UserError(_('Please, 2 attributes have the same name: %s' % (attribute_name)))
                    else:
                        raise UserError(_('Please, create this attribute before load value: %s' % (attribute_name)))

                product_template = {}
                # Check the product template
                for data_line in data:
                    template_code = data_line.get('template_code', '')
                    if template_code not in list(product_template.keys()):
                        product_template_ids = self.env['product.template'].search([('template_code', '=', template_code)])
                        if product_template_ids:
                            product_template[template_code] = product_template_ids[0]
                            for line in product_template_ids[0].attribute_line_ids:
                                if data_line.get('#' + line.attribute_id.name, '?????????') == '?????????':
                                    raise UserError(_('Please, add this column value: %s\n on your import file' % ('#' + line.attribute_id.name)))

                        else:
                            raise UserError(_('Please, create this Product template before load value: %s' % (template_code)))

                for data_line in data:
                    # Load data_line
                    template_code = data_line.get('template_code', '')

                    default_code = data_line.get('default_code', '')
                    barcode = data_line.get('barcode', '')
                    lst_price = data_line.get('lst_price', '')
                    standard_price = data_line.get('standard_price', '')
                    product = product_template[template_code]

                    # load attribute value, create value if not exist,

                    attribute_value_ids = {}
                    import_combination = self.env['product.attribute.value']
                    for line in product.attribute_line_ids:
                        attribute_value = data_line.get('#' + line.attribute_id.name).strip() or '-'
                        attribute_value_ids[line.attribute_id.name] = False
                        if attribute_value:
                            value_id = False
                            for line_value in line.attribute_id.value_ids:
                                if line_value.name == attribute_value:
                                    value_id = line_value
                                    break
                            if not value_id:
                                att_vals = {
                                    'name': attribute_value,
                                    'attribute_id': line.attribute_id.id,
                                }
                                value_id = line.attribute_id.value_ids.create(att_vals)
                                line.write({'value_ids': [(4, value_id.id)]})
                            else:
                                if value_id not in line.value_ids:
                                    line.write({'value_ids': [(4, value_id.id)]})
                            attribute_value_ids[line.attribute_id.name] = value_id
                            import_combination |= value_id
                        else:
                            raise UserError(_('Please, complete this value on line %s: %s' % (nb_line, line.attribute_id.name)))

                    # Find the product variant
                    def get_combination(test_variant):
                        "return set of attribute value"
                        test_combination = self.env['product.attribute.value']
                        for test_value in test_variant.product_template_attribute_value_ids:
                            test_combination |= test_value.product_attribute_value_id
                        return test_combination

                    # first case search by default_code, update
                    # second case search by attribute on variant with no default_code
                    condition = [('product_tmpl_id', '=', product.id), ('default_code', '=', default_code)]
                    variant_ids = self.env['product.product'].search(condition)

                    variant = False
                    if variant_ids:
                        variant = variant_ids[0]
                    else:
                        for test_variant in product.product_variant_ids:
                            if default_code and test_variant.default_code:
                                # don't search if default code is defined
                                continue

                            if import_combination == get_combination(test_variant):
                                variant = test_variant
                                break

                    # Check the attribute value
                    product_template_attribute_value_ids = []
                    for line in product.attribute_line_ids:
                        condition = [
                            ('attribute_line_id', '=', line.id),
                            ('product_attribute_value_id', '=', attribute_value_ids[line.attribute_id.name].id)
                        ]
                        att_val_ids = self.env['product.template.attribute.value'].search(condition)
                        if att_val_ids:
                            product_template_attribute_value_ids.append(att_val_ids[0].id)

                        variant_vals = {
                            'product_tmpl_id': product.id,
                            'default_code': default_code or False,
                            'barcode': barcode or False,
                            'lst_price': lst_price,
                            'standard_price': standard_price,
                        }

                    if not variant:
                        # Create the variant
                        variant_vals['product_tmpl_id'] = product.id
                        variant_vals['product_template_attribute_value_ids'] = [(6,0,product_template_attribute_value_ids)]
                        variant = self.env['product.product'].create(variant_vals)
                    else:
                        # update the variant
                        if import_combination != get_combination(variant):
                            variant_vals['product_template_attribute_value_ids'] = [(6,0,product_template_attribute_value_ids)]
                        variant.write(variant_vals)

                    nb_line += 1



    def import_purchase_price(self):
        "start import"
        load_data = self.load_data(lower=True)
        # Start
        for wizard in self:
            if load_data[wizard.id]:
                data = load_data[wizard.id]
                log(data)
                for data_line in data:
                    log(data_line)
                    sku = data_line.get('sku')
                    price = to_float(data_line.get('price'))

                    if sku and price:
                        product_ids = self.env['product.template'].search([('sku', '=', sku)])
                        if len(product_ids) > 1:
                            raise UserError(_('There 2 product with the same SKU code: %s' % (sku)))
                        elif len(product_ids) == 1:
                            product_ids[0].standard_price = price
                        else:
                            log("no product: %s" % (sku))
                    else:
                        log("void line: %s %s" % (sku, price))

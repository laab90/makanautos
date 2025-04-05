# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class ResCompany(models.Model):
    _inherit = 'res.company'


    fe_user = fields.Char(string='EI User')
    fe_key_webservice = fields.Char(string='EI Key WebServise')
    fe_sign_token = fields.Char(string='Sign Token')
    fe_other_email = fields.Char(string="Other Email")
    fe_establishment_ids = fields.One2many('res.company.establishment', 'company_id', string='Establishments')
    fe_phrase_ids = fields.Many2many('account.fe.phrase', string='Phrase', required=True)


    def _get_headers(self):
        headers = {'Content-Type': 'application/json'}
        if not self.fe_user and not self.fe_key_webservice:
            raise ValidationError(_("Error. credentials aren't setted"))
        headers.update( {'usuario': self.fe_user, 'llave': self.fe_key_webservice} )
        return headers

    def _get_sign_token(self):
        if not self.fe_sign_token:
            raise ValidationError(_("Error. Token isn't setted"))
        return {"llave": self.fe_sign_token,
                "alias": self.fe_user}


class ResCompanyEstablishment(models.Model):
    _name = 'res.company.establishment'
    _description = 'Company Establishment'
    _rec_name = 'fe_tradename'

    fe_tradename = fields.Char(string='Tradename', required=True)
    fe_code = fields.Integer(string="Establishment Code", required=True)
    company_id = fields.Many2one('res.company', string='Company')
    export_code = fields.Char(string='Export Code')
    fe_tradename_street = fields.Char(string='Direccion')
    fe_tradename_city = fields.Char(string='Municipio')
    fe_tradename_state_id = fields.Many2one('res.country.state',string='Departamento')
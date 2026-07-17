# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    l10n_ve_rif = fields.Char(
        string='RIF / Cédula',
        help="Formato: V-123456789, J-12345678-9, E-123456789"
    )
    
    l10n_ve_person_type = fields.Selection([
        ('V', 'Natural Venezolano (V)'),
        ('E', 'Natural Extranjero (E)'),
        ('J', 'Jurídico Nacional (J)'),
        ('G', 'Gobierno (G)'),
        ('P', 'Pasaporte (P)'),
    ], string='Tipo de Persona', default='V')

    l10n_ve_taxpayer_type = fields.Selection([
        ('ordinary', 'Contribuyente Ordinario'),
        ('special', 'Contribuyente Especial'),
        ('exempt', 'No Sujeto / Exento'),
    ], string='Tipo de Contribuyente', default='ordinary')

    @api.depends('l10n_ve_rif', 'l10n_ve_person_type')
    @api.onchange('l10n_ve_rif', 'l10n_ve_person_type')
    def _compute_native_vat_sync(self):
        """ 
        Sincroniza el RIF personalizado con el campo nativo 'vat' de Odoo.
        Garantiza que la plantilla sale.report_saleorder_document_copy_2 
        y las facturas impriman el RIF sin alterar sus XML.
        """
        for partner in self:
            if partner.l10n_ve_rif:
                rif_clean = partner.l10n_ve_rif.strip().upper()
                
                # Si el usuario ya incluyó el prefijo con guion (ej. 'J-40068331-9'), lo dejamos tal cual
                if any(rif_clean.startswith(p + '-') for p in ['V', 'E', 'J', 'G', 'P']):
                    partner.vat = rif_clean
                else:
                    # Si solo ingresó los números, le agregamos el prefijo seleccionado de forma limpia
                    prefix = partner.l10n_ve_person_type or 'V'
                    partner.vat = f"{prefix}-{rif_clean}"
            else:
                partner.vat = False

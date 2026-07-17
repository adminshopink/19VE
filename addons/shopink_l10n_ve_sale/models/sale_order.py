# -*- coding: utf-8 -*-
import urllib.parse
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Desactivamos la firma y el pago en línea por defecto para evitar auto-confirmaciones desde el portal
    require_signature = fields.Boolean(default=False, store=True)
    require_payment = fields.Boolean(default=False, store=True)

    l10n_ve_customer_rif = fields.Char(
        string='RIF del Cliente',
        compute='_compute_l10n_ve_customer_fiscal_data',
        store=True,
        readonly=False
    )
    
    l10n_ve_taxpayer_type = fields.Selection([
        ('ordinary', 'Contribuyente Ordinario'),
        ('special', 'Contribuyente Especial'),
        ('exempt', 'No Sujeto / Exento'),
    ], string='Tipo de Contribuyente', compute='_compute_l10n_ve_customer_fiscal_data', store=True, readonly=False)

    @api.depends('partner_id')
    def _compute_l10n_ve_customer_fiscal_data(self):
        for order in self:
            if order.partner_id:
                order.l10n_ve_customer_rif = order.partner_id.l10n_ve_rif
                order.l10n_ve_taxpayer_type = order.partner_id.l10n_ve_taxpayer_type
            else:
                order.l10n_ve_customer_rif = False
                order.l10n_ve_taxpayer_type = False

    def action_send_whatsapp(self):
        """ Genera el enlace de WhatsApp y redirige al usuario """
        self.ensure_one()
        if not self.partner_id.phone and not self.partner_id.mobile:
            raise UserError(_("El cliente no tiene un número de teléfono o celular registrado."))
        
        # Limpieza básica del número telefónico (tomamos mobile si existe, si no phone)
        phone = self.partner_id.mobile or self.partner_id.phone
        clean_phone = ''.join(c for c in phone if c.isdigit())
        
        # Si el número no tiene código de país, le agregamos el de Venezuela (58) por defecto
        if len(clean_phone) == 10 and clean_phone.startswith('4'):
            clean_phone = '58' + clean_phone
        elif len(clean_phone) == 11 and clean_phone.startswith('04'):
            clean_phone = '58' + clean_phone[1:]

        # Construcción del mensaje personalizado
        saludo = f"Hola *{self.partner_id.name}*,\n\n"
        cuerpo = f"Te hacemos llegar la cotización *{self.name}* por un monto total de *{self.currency_id.symbol or ''}{self.amount_total:,.2f}*.\n\n"
        
        # Generamos el link del portal para que puedan ver/descargar el PDF en línea
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        portal_url = f"{base_url}/my/orders/{self.id}"
        link = f"Puedes revisar los detalles y descargar el PDF aquí:\n{portal_url}\n\n"
        
        despedida = "¡Muchas gracias por tu confianza! Quedamos atentos a tus comentarios."
        
        mensaje_completo = saludo + cuerpo + link + despedida
        
        # Codificamos el texto para URL
        encoded_message = urllib.parse.quote(mensaje_completo)
        whatsapp_url = f"https://api.whatsapp.com/send?phone={clean_phone}&text={encoded_message}"
        
        # Retornamos una acción de Odoo para abrir una nueva pestaña del navegador
        return {
            'type': 'ir.actions.act_url',
            'url': whatsapp_url,
            'target': 'new',
        }

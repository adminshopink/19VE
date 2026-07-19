# -*- coding: utf-8 -*-
from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Campos relacionados directos
    # 'payment_ids' es una relación automática si existe la relación en el modelo
    # Pero como queremos buscar por el memo/referencia, usaremos campos normales 
    # que alimentaremos desde el pago al confirmar.
    last_payment_memo = fields.Char(string='Referencia de Pago', readonly=True)
    last_payment_journal = fields.Char(string='Banco/Diario', readonly=True)
    commercial_payment_state = fields.Selection([
        ('unpaid', 'No Pagado'),
        ('partial', 'Pago Parcial'),
        ('paid', 'Totalmente Pagado')
    ], string='Estado de Pago (Comercial)', default='unpaid', readonly=True)

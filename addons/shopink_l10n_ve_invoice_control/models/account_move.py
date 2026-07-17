# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = 'account.move'

    # Campo propio para el Número de Control del SENIAT
    l10n_ve_control_number = fields.Char(
        string='Número de Control', 
        copy=False, 
        tracking=True,
        help="Número de control correlativo exigido por el SENIAT"
    )

    def action_post(self):
        """ 
        Sobrescribe la validación nativa. Ejecuta primero el proceso de Odoo 
        y solo si se publica con éxito, consume e inyecta la secuencia fiscal.
        """
        # 1. Ejecutamos el super de Odoo. Si hay un error contable, la transacción aborta aquí.
        res = super(AccountMove, self).action_post()

        # 2. Una vez publicado el documento de forma segura, asignamos el número de control
        for move in self:
            if move.move_type in ('out_invoice', 'out_refund') and not move.l10n_ve_control_number:
                # Extrae el siguiente número consecutivo de la secuencia oficial
                control_num = self.env['ir.sequence'].next_by_code('l10n_ve.control.number')
                # Escribimos directo para evitar re-disparar métodos de cómputo en un estado 'posted'
                move.write({'l10n_ve_control_number': control_num})

        return res

    def button_draft(self):
        """
        Cumplimiento Providencia SNAT/2024/000121:
        Evita que una factura ya emitida/publicada con número de control 
        pueda ser revertida a borrador para su modificación.
        """
        for move in self:
            if move.move_type in ('out_invoice', 'out_refund') and move.state == 'posted':
                raise UserError(_(
                    "Por regulaciones de la Providencia SENIAT 000121, las facturas emitidas "
                    "no pueden ser modificadas ni revertidas a borrador. "
                    "Cualquier ajuste debe realizarse mediante una Nota de Crédito o Débito."
                ))
        return super(AccountMove, self).button_draft()

    def unlink(self):
        """
        Garantiza la trazabilidad impidiendo la eliminación física de 
        documentos que ya han entrado en el flujo contable/fiscal.
        """
        for move in self:
            if move.state != 'draft':
                raise UserError(_(
                    "No es posible eliminar un documento que no esté en estado borrador. "
                    "Se debe mantener la trazabilidad exigida por el SENIAT."
                ))
        return super(AccountMove, self).unlink()

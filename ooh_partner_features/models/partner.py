from odoo import models, fields, api,_

class resPartner(models.Model):
    _inherit = 'res.partner'
    def get_full_unpaid_invoices(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoices',
            'view_mode': 'tree',
            'res_model': 'account.move',
            'domain': [('partner_id', '=', self.id)],
            'context': "{'create': False}"
        }
    invoice_count = fields.Integer(compute='compute_count')


    def compute_count(self):
        unpaid=0.00
        invoices = self.env['account.move'].search([('state','=','posted'),("payment_state", "in", ["not_paid", "partial"]),('partner_id', '=', self.id)])
        for record in invoices:
            unpaid+=record.amount_residual
        return self.sudo().write({'invoice_count':unpaid})
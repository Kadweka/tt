from odoo import models, fields, api,_
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)
class AccountMove(models.Model):
    _inherit = 'account.move'
    def compute_bank_balance(self):
        bill=0.00
        invoice=0.00
        lines = self.env['home.bank'].search([("state","=","active"),('customer_id.id', '=', self.partner_id.id)])
        if lines:
            return self.sudo().write({'acc_balance':lines.account_total})
    acc_balance=fields.Float(string="H.B.balance",compute="compute_bank_balance")
    unpaid_invoices=fields.Float(string="We owe Him")
    unpaid_bills=fields.Float(string="He owes Us")



class SaleOrder(models.Model):
    _inherit = 'sale.order'
    def compute_bank_balance(self):
        lines = self.env['home.bank'].search([("state","=","active"),('customer_id.id', '=', self.partner_id.id)])
        if lines:
            return self.sudo().write({'acc_balance':lines.account_total})
    acc_balance=fields.Float(string="H.B.balance",compute="compute_bank_balance")
    unpaid_invoices=fields.Float(string="We owe Him")
    unpaid_bills=fields.Float(string="He owes Us")
from odoo import models, fields, api, _
from datetime import datetime

import logging

_logger = logging.getLogger(__name__)


class TransactionWizard(models.TransientModel):
    _name = "register.transaction.wizard"
    _description = "Record Payments"

    def _get_active_id(self):
        active_id = self.env['home.bank'].search([('id', '=', self.env.context.get('account_id'))])
        self.account_line=active_id
    amount = fields.Float(string="Amount")
    account_line = fields.Many2one('home.bank', string="Transaction Lines")
    date = fields.Date(string="Line Date", default=datetime.now(), readonly=True)
    transact_type = fields.Selection([
        ('deposit', 'Deposit'),
        ('inv_payment', 'Invoice Payment'),
        ('Widrawal', 'Widrawal'),
        ('lending', 'Loan'),
    ], default='deposit')

    # property_account_receivable_id
    def add_transaction(self):
        move_lines = []
        active_id = self.env['home.bank'].search([('id', '=', self.env.context.get('account_id'))])
        if self.transact_type == "deposit":
            lines = self.env['home.bank.line'].create({
                "amount": self.amount,
                "account_line": active_id.id,
                "date": self.date,
                "transact_type": self.transact_type
            })
            if lines:
                account_move_lines = [{
                    "account_id": lines.account_line.customer_id.property_account_payable_id.id,
                    "name": self.transact_type,
                    "debit": 0.00,
                    "partner_id": lines.account_line.customer_id.id,
                    "credit": lines.amount,
                }, {
                    "account_id": lines.account_line.income_journal_id.id,
                    "name": 0,
                    'partner_id': lines.account_line.customer_id.id,
                    "debit": lines.amount,
                    "credit": 0.00
                }]
                move_id = self.env['account.move'].create({
                    "ref": lines.ref,
                    "journal_id": lines.account_line.income_journal_id.id,
                    "date": lines.date,
                })
                [move_lines.append((0, 0, {"account_id": y['account_id'], "name": y['name'], "debit": y['debit'],
                                           "credit": y['credit'], "partner_id": y['partner_id']})) for y in
                 account_move_lines]
                move_id.line_ids = move_lines
                move_id.action_post()
            return True
        if self.transact_type == "Widrawal":
            if self.amount > active_id.account_total:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'THE WIDRAWAL IS REJECTED!!',
                        'message': 'YOU CANNOT WIDRAW MORE THAN YOU HAVE IN YOUR ACCOUNT,PLEASE BORROW A LOAN INSTEAD!!',
                        'type': 'danger',
                        "sticky": False,
                    }
                }
            else:
                lines = self.env['home.bank.line'].create({
                    "amount": self.amount,
                    "account_line": active_id.id,
                    "date": self.date,
                    "transact_type": self.transact_type
                })
                if lines:
                    account_move_lines = [{
                        "account_id": lines.account_line.customer_id.property_account_receivable_id.id,
                        "name": self.transact_type,
                        "debit": lines.amount,
                        "partner_id": lines.account_line.customer_id.id,
                        "credit": 0.00,
                    }, {
                        "account_id": lines.account_line.outcome_journal_id.id,
                        "name": self.transact_type,
                        'partner_id': lines.account_line.customer_id.id,
                        "debit": 0.00,
                        "credit": lines.amount
                    }]
                    move_id = self.env['account.move'].create({
                        "ref": lines.ref,
                        "journal_id": lines.account_line.outcome_journal_id.id,
                        "date": lines.date,
                    })
                    [move_lines.append((0, 0, {"account_id": y['account_id'], "name": y['name'], "debit": y['debit'],
                                               "credit": y['credit'], "partner_id": y['partner_id']})) for y in
                     account_move_lines]
                    move_id.line_ids = move_lines
                    move_id.action_post()
                return True
        if self.transact_type == "lending":
            lines = self.env['home.bank.line'].create({
                "amount": self.amount,
                "account_line": active_id.id,
                "date": self.date,
                "transact_type": self.transact_type
            })
            if lines:
                account_move_lines = [{
                    "account_id": lines.account_line.customer_id.property_account_receivable_id.id,
                    "name": self.transact_type,
                    "debit": lines.amount,
                    "partner_id": lines.account_line.customer_id.id,
                    "credit": 0.00,
                }, {
                    "account_id": lines.account_line.outcome_journal_id.id,
                    "name": self.transact_type,
                    'partner_id': lines.account_line.customer_id.id,
                    "debit": 0.00,
                    "credit": lines.amount
                }]
                move_id = self.env['account.move'].create({
                    "ref": lines.ref,
                    "journal_id": lines.account_line.outcome_journal_id.id,
                    "date": lines.date,
                })
                [move_lines.append((0, 0, {"account_id": y['account_id'], "name": y['name'], "debit": y['debit'],
                                           "credit": y['credit'], "partner_id": y['partner_id']})) for y in
                 account_move_lines]
                move_id.line_ids = move_lines
                move_id.action_post()
            return True
        if self.transact_type == "inv_payment":
            if self.amount > active_id.account_total:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'TYPE ERROR',
                        'message': 'THIS TYPE IS USED IN INVOICES MODULE ONLY!!!',
                        'type': 'danger',
                        "sticky": False,
                    }
                }
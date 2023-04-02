from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
import logging
from random import randint

_logger = logging.getLogger(__name__)


class HomeBanking(models.Model):
    _name = 'home.bank'
    _description = "Home banking"
    _inherit = ["mail.thread", 'mail.activity.mixin']

    def _prepare_closure_email(self):
        mail_user = self.env['ir.mail_server'].sudo().search([('smtp_port', '=', 465)])
        subject = f"My Account Deactivation"
        mail_obj = self.env['mail.mail']
        email_from = mail_user.smtp_user
        email_to = self.customer_id.email
        body_html = f"""
            <html>
            <body>
            <div style="margin:0px;padding: 0px;">
                <p style="padding: 0px; font-size: 13px;">
                    Dear {self.customer_id.name} !!,
                    <br/>
                    Your Account Was Successfuly Deactivated.
                    <br/> 
                    We are happy to give you the best Service.
                    <br/>
                        If you did not request this please react out to {self.customer_id.company_id.phone}
                    .
                <br/>
                </p>

                <p>
                Best Regards
                    <br/>
                {self.customer_id.company_id.name}
                
                </p>
            <br/>
            </div>
            </body>
            </html>
        """
        mail = mail_obj.sudo().create({
            'body_html': body_html,
            'subject': subject,
            'email_from': email_from,
            'email_to': email_to
        })
        mail.send()
        return mail

    def _prepare_activation_email(self):
        mail_user = self.env['ir.mail_server'].sudo().search([('smtp_port', '=', 465)])
        subject = f"SuccessFully Ativation of your account"
        mail_obj = self.env['mail.mail']
        email_from = mail_user.smtp_user
        email_to = self.customer_id.email
        body_html = f"""
            <html>
            <body>
            <div style="margin:0px;padding: 0px;">
                <p style="padding: 0px; font-size: 13px;">
                    Dear {self.customer_id.name} !!,
                    <br/>
                    Your Account Was Successfuly Activated.
                    <br/> 
                    We are happy to give you the best Service.
                    <br/>
                    Incase of any querries please Feel free to reach out to {self.customer_id.company_id.email}
                    .
                <br/>
                </p>

                <p>
                Best Regards
                    <br/>
                {self.customer_id.company_id.name}
                
                </p>
            <br/>
            </div>
            </body>
            </html>
        """
        mail = mail_obj.sudo().create({
            'body_html': body_html,
            'subject': subject,
            'email_from': email_from,
            'email_to': email_to
        })
        mail.send()
        return mail

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('home.bank') or _('New')
        res = super(HomeBanking, self).create(vals)
        # existing = self.env["home.bank"].sudo().search([("customer_id", "=", res.customer_id.id)])
        # if existing:
        #     _logger.info(existing.name)
        #     raise ValidationError(_("THERE IS AN EXISTING ACCOUNT FOR THAT CUSTOMER"))
        return res

    # def get_customers_with_no_account(self):
    #     existing_users=[]
    #     accounts = self.env['home.bank'].search([('state', 'in', ['processing', 'inactive', 'active'])])
    #     [existing_users.append(x.customer_id.id) for x in accounts]
    #     _logger.error(accounts.customer_id.id)
    #     _logger.error("TESTING THE OUTCOME RESULTS")
    #     _logger.error(existing_users)
    #     self.customer_id = self.customer_id.search([('id', 'not in', existing_users)])
    #     # return True
    #     return True

    def calculate_account_blc(self):
        debit = 0.00
        credit = 0.00
        entries = self.env['account.move.line'].sudo().search([('partner_id.id', '=', self.customer_id.id), (
            "account_id.user_type_id.type", "in", ["receivable", "payable"]), ("parent_state", "=", "posted")])
        for x in entries:
            debit += x.debit
            credit += x.credit
        self.account_total = credit - debit
        return True

        # sale_journal = self.env['account.journal'].search([('code', '=', 'HMBNK'), ("type", "=", "purchase")])

    def _get_move_lines_for_account(self):
        self.move_line_ids = self.move_line_ids.search(
            [('partner_id.id', '=', self.customer_id.id),
             ("account_id.user_type_id.type", "in", ["receivable", "payable"])])
        return True

    state = fields.Selection([
        ('processing', 'PROCESSING'),
        ('inactive', 'INACTIVE'),
        ('active', 'ACTIVE'),
    ], default='processing', tracking=True)
    name = fields.Char(readonly=True, string="Account Number", tracking=True)
    date = fields.Date(string="Order Date", default=datetime.now(), readonly=True, tracking=True)
    customer_id = fields.Many2one('res.partner', string="Customer", tracking=True)
    traction_lines = fields.One2many('home.bank.line', 'account_line', tracking=True)
    account_total = fields.Float(string="Account Balance", tracking=True, compute='calculate_account_blc')
    currency_id = fields.Many2one('res.currency', string="Customer", tracking=True)
    income_journal_id = fields.Many2one('account.journal', string="Income journal")
    outcome_journal_id = fields.Many2one('account.journal', string="Outcome Journal")
    move_line_ids = fields.One2many("account.move.line", 'home_bank_id', compute="_get_move_lines_for_account")

    def action_activate(self):
        if self.state == "processing":
            self.write({"state": "active"})
            self._prepare_activation_email()

    def action_deactivate(self):
        self.calculate_account_blc()
        if self.state == "active" and self.account_total > 0 or self.account_total < 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'ACCOUNT CLOSURE ERROR',
                    'message': 'YOU CANNOT CLOSE AND ACCOUNT THAT HAS FUNDS',
                    'type': 'danger',
                    "sticky": False,
                }
            }
        if self.state == "active" and self.account_total == 0:
            self.write({'state': "inactive"})
            self._prepare_closure_email()

    def action_reactivate(self):
        if self.state == "inactive":
            self.write({'state': "active"})
            self._prepare_activation_email()

    def action_post_transaction(self):
        return {
            'name': _('New Transaction'),
            'res_model': 'register.transaction.wizard',
            'view_mode': 'form',
            'context': {
                'active_model': 'home.bank',
                'account_id': self.ids,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }


class HomeBankingLine(models.Model):
    _name = 'home.bank.line'
    _description = "Requesting for Materials Transactions"
    _inherit = ["mail.thread", 'mail.activity.mixin']

    def _get_default_color(self):
        return randint(1, 11)

    @api.model
    def create(self, vals):
        if vals.get('ref', _('New')) == _('New'):
            vals['ref'] = self.env['ir.sequence'].next_by_code('home.bank.line') or _('New')
        res = super(HomeBankingLine, self).create(vals)
        return res

    ref = fields.Char(string="Transac Ref", tracking=True, readonly=True)
    amount = fields.Float(string="Amount", tracking=True, readonly=True)
    partner_id = fields.Char(string="Partner", related="account_line.customer_id.email", tracking=True, readonly=True)
    account_line = fields.Many2one('home.bank', string="Transaction Lines", readonly=True)
    date = fields.Date(string="Line Date", default=datetime.now(), readonly=True, tracking=True)
    transact_type = fields.Selection([
        ('deposit', 'Deposit'),
        ('inv_payment', 'Invoice Payment'),
        ('Widrawal', 'Widrawal'),
        ('lending', 'Lending'),
    ], default='deposit', tracking=True, readonly=True)
    state = fields.Selection([
        ('valid', 'Valid'),
        ('void', 'Void'),
    ], default='valid', tracking=True, readonly=True)
    color = fields.Integer('Color', default=_get_default_color, tracking=True, readonly=True)


class MoveLine(models.Model):
    _inherit = 'account.move.line'

    home_bank_id = fields.Many2one("home.bank", string="Bank related")

    def action_void(self):
        if self.state == "valid" and self.transact_type == "Widrawal":
            value = self.account_line.account_total + self.amount
            self.write({"state": "void"})
            if self.state == "void":
                self.account_line.write({"account_total": value})
        if self.state == "valid" and self.transact_type == "deposit":
            value = self.account_line.account_total - self.amount
            self.write({"state": "void"})
            if self.state == "void":
                self.account_line.write({"account_total": value})
        if self.state == "valid" and self.transact_type == "lending":
            value = self.account_line.account_total + self.amount
            self.write({"state": "void"})
            if self.state == "void":
                self.account_line.write({"account_total": value})


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'
    _description = "Extending the payment register model"

    pay_mode = fields.Selection([
        ('cash', 'USE CASH ON HAND'),
        ('use_acc_balance', 'CASH IN HOME BANKING'),
    ], default='cash', tracking=True)

    def register_payments(self):
        move_lines = []
        if self.pay_mode == "cash":
            self.action_create_payments()
        if self.pay_mode == "use_acc_balance":
            invoice = self.env['account.move'].search([("name", "=", self.communication)])
            user = self.env['home.bank'].search([("customer_id.id", "=", invoice.partner_id.id)])
            if user:
                lines = self.env['home.bank.line'].create({
                    "amount": self.amount,
                    "account_line": user.id,
                    "date": self.payment_date,
                    "transact_type": "inv_payment"
                })
                if lines:
                    account_move_lines = [{
                        "account_id": lines.account_line.customer_id.property_account_receivable_id.id,
                        "name": lines.transact_type,
                        "debit": lines.amount,
                        "partner_id": lines.account_line.customer_id.id,
                        "credit": 0.00,
                    }, {
                        "account_id": self.journal_id.id,
                        "name": lines.transact_type,
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
                    self.action_create_payments()
                return True
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'CUSTOMER HOME BANKING ERROR',
                        'message': 'SEEMS LIKE THAT CUSTOMER DOES NOT USE HOME BANKING SERVICE WITH US..!',
                        'type': 'danger',
                        "sticky": False,
                    }
                }

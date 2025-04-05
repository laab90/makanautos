from odoo import fields, models, api, _

# Este modelo remplaza el attachment generado desde los automated actions 
# por ejemplo cuando un pago es realizado desde el website
class MailTemplate(models.Model):
    "Templates for sending email"
    _name = "mail.template"
    _inherit = "mail.template"
    _description = 'Email Templates'
    _order = 'name'

    @api.multi
    def send_mail(self, res_id, force_send=False, raise_exception=False, email_values=None, notif_layout=False):
        self.ensure_one()        
        Mail = self.env['mail.mail']
        Attachment = self.env['ir.attachment']
        values = self.generate_email(res_id)
        values['recipient_ids'] = [(4, pid) for pid in values.get('partner_ids', list())]
        values.update(email_values or {})
        attachment_ids = values.pop('attachment_ids', [])        
        attachments = values.pop('attachments', [])        
        # add a protection against void email_from
        if 'email_from' in values and not values.get('email_from'):
            values.pop('email_from')
        # encapsulate body
        if notif_layout and values['body_html']:
            try:
                template = self.env.ref(notif_layout, raise_if_not_found=True)
            except ValueError:
                _logger.warning('QWeb template %s not found when sending template %s. Sending without layouting.' % (notif_layout, self.name))
            else:
                record = self.env[self.model].browse(res_id)
                template_ctx = {
                    'message': self.env['mail.message'].sudo().new(dict(body=values['body_html'], record_name=record.display_name)),
                    'model_description': self.env['ir.model']._get(record._name).display_name,
                    'company': 'company_id' in record and record['company_id'] or self.env.user.company_id,
                    'record': record,
                }
                body = template.render(template_ctx, engine='ir.qweb', minimal_qcontext=True)
                values['body_html'] = self.env['mail.thread']._replace_local_links(body)
        mail = Mail.create(values)

        for attachment in attachments:
            attachment_data = {
                'name': attachment[0],
                'datas_fname': attachment[0],
                'datas': attachment[1],
                'type': 'binary',
                'res_model': 'mail.message',
                'res_id': mail.mail_message_id.id,
            }
            attachment_ids.append(Attachment.create(attachment_data).id)
        if self.model_id.name == 'Invoice':
            invoice = self.env['account.invoice'].search(
                [
                    ('id', '=', res_id),
                ]
            )
            if invoice.journal_id.is_fel:
                attachment_data = {
                    'name': str(invoice.number)+'.pdf',
                    'datas_fname': invoice.number+'.pdf',
                    'datas': invoice.file,
                    'type': 'binary',
                    'res_model': 'mail.message',
                    'res_id': mail.mail_message_id.id,
                }
                attachment_ids.append(Attachment.create(attachment_data).id)

        if attachment_ids:
            values['attachment_ids'] = [(6, 0, attachment_ids)]
            mail.write({'attachment_ids': [(6, 0, attachment_ids)]})

        if force_send:
            mail.send(raise_exception=raise_exception)
        return mail.id 

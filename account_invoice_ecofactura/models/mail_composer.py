from odoo import fields, models, api, _


# Este modelo remplaza el attachment que se envia desde el wizard de "send and print"

class MailComposer(models.TransientModel):
        _name = 'mail.compose.message'
        _inherit = 'mail.compose.message'

        @api.multi
        def send_mail(self, auto_commit=False):
            notif_layout = self._context.get('custom_layout')
            model_description = self._context.get('model_description')
            for wizard in self:
                if wizard.attachment_ids and wizard.composition_mode != 'mass_mail' and wizard.template_id:
                    new_attachment_ids = []
                    for attachment in wizard.attachment_ids:
                        if attachment in wizard.template_id.attachment_ids:
                            new_attachment_ids.append(attachment.copy({'res_model': 'mail.compose.message', 'res_id': wizard.id}).id)
                        else:
                            
                            if wizard.model == 'account.invoice':
                                invoice = self.env['account.invoice'].search(
                                    [
                                        ('id', '=', wizard.res_id),
                                    ]
                                )
                                if invoice.journal_id.is_fel:
                                    attachment_data = {
                                        'name': str(invoice.number)+'.pdf',
                                        'datas_fname': invoice.number+'.pdf',
                                        'datas': invoice.file,
                                        'type': 'binary',
                                        'res_model': 'mail.compose.message',
                                        'res_id': 0,
                                        'res_model_name': 'Email composition wizard'
                                    }
                                    new_attachment_ids.append(self.env['ir.attachment'].create(attachment_data).id)
                                else:
                                    new_attachment_ids.append(attachment.id)
                            else:
                                new_attachment_ids.append(attachment.id)
                    wizard.write({'attachment_ids': [(6, 0, new_attachment_ids)]})

                mass_mode = wizard.composition_mode in ('mass_mail', 'mass_post')

                Mail = self.env['mail.mail']
                ActiveModel = self.env[wizard.model] if wizard.model and hasattr(self.env[wizard.model], 'message_post') else self.env['mail.thread']
                if wizard.composition_mode == 'mass_post':
                    ActiveModel = ActiveModel.with_context(mail_notify_force_send=False, mail_create_nosubscribe=True)
                if mass_mode and wizard.use_active_domain and wizard.model:
                    res_ids = self.env[wizard.model].search(safe_eval(wizard.active_domain)).ids
                elif mass_mode and wizard.model and self._context.get('active_ids'):
                    res_ids = self._context['active_ids']
                else:
                    res_ids = [wizard.res_id]

                batch_size = int(self.env['ir.config_parameter'].sudo().get_param('mail.batch_size')) or self._batch_size
                sliced_res_ids = [res_ids[i:i + batch_size] for i in range(0, len(res_ids), batch_size)]

                if wizard.composition_mode == 'mass_mail' or wizard.is_log or (wizard.composition_mode == 'mass_post' and not wizard.notify):  # log a note: subtype is False
                    subtype_id = False
                elif wizard.subtype_id:
                    subtype_id = wizard.subtype_id.id
                else:
                    subtype_id = self.env['ir.model.data'].xmlid_to_res_id('mail.mt_comment')

                for res_ids in sliced_res_ids:
                    batch_mails = Mail
                    all_mail_values = wizard.get_mail_values(res_ids)
                    for res_id, mail_values in all_mail_values.items():
                        if wizard.composition_mode == 'mass_mail':
                            batch_mails |= Mail.create(mail_values)
                        else:
                            post_params = dict(
                                message_type=wizard.message_type,
                                subtype_id=subtype_id,
                                notif_layout=notif_layout,
                                add_sign=not bool(wizard.template_id),
                                mail_auto_delete=wizard.template_id.auto_delete if wizard.template_id else False,
                                model_description=model_description,
                                **mail_values)
                            if ActiveModel._name == 'mail.thread' and wizard.model:
                                post_params['model'] = wizard.model
                            ActiveModel.browse(res_id).message_post(**post_params)

                    if wizard.composition_mode == 'mass_mail':
                        batch_mails.send(auto_commit=auto_commit)

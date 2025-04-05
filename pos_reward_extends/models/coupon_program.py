# -*- coding: utf-8 -*-


from odoo import fields, models, _

class CouponProgram(models.Model):
    _inherit = 'coupon.reward'

    discount_apply_on = fields.Selection(selection_add=[
        ('specific_cheapest_products', 'On specific products, applies cheapest product'),
    ])

    #Fullyoverride to add reward product line name
    def name_get(self):
        """
        Returns a complete description of the reward
        """
        result = []
        for reward in self:
            reward_string = ""
            if reward.reward_type == 'product':
                reward_string = _("Free Product - %s", reward.reward_product_id.name)
            elif reward.reward_type == 'discount':
                if reward.discount_type == 'percentage':
                    reward_percentage = str(reward.discount_percentage)
                    if reward.discount_apply_on == 'on_order':
                        reward_string = _("%s%% discount on total amount", reward_percentage)
                    elif reward.discount_apply_on == 'specific_products':
                        if len(reward.discount_specific_product_ids) > 1:
                            reward_string = _("%s%% discount on products", reward_percentage)
                        else:
                            reward_string = _(
                                "%(percentage)s%% discount on %(product_name)s",
                                percentage=reward_percentage,
                                product_name=reward.discount_specific_product_ids.name
                            )
                    elif reward.discount_apply_on == 'cheapest_product':
                        reward_string = _("%s%% discount on cheapest product", reward_percentage)
                    elif reward.discount_apply_on == 'specific_cheapest_products':
                        reward_string = _("%s%% discount on specific cheapest product", reward_percentage)
                elif reward.discount_type == 'fixed_amount':
                    program = self.env['coupon.program'].search([('reward_id', '=', reward.id)])
                    reward_string = _(
                        "%(amount)s %(currency)s discount on total amount",
                        amount=reward.discount_fixed_amount,
                        currency=program.currency_id.name
                    )
            result.append((reward.id, reward_string))
        return result


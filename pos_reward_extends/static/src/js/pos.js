odoo.define('pos_reward_extends.pos_coupon', function (require) {
    'use strict';
    
    const models = require('point_of_sale.models');
    const rpc = require('web.rpc');
    const session = require('web.session');
    const concurrency = require('web.concurrency');
    const { Gui } = require('point_of_sale.Gui');
    const { float_is_zero,round_decimals } = require('web.utils');
    const {CouponCode, RewardsContainer, Reward } = require('pos_coupon.pos');
    const dp = new concurrency.DropPrevious();


    var _order_super = models.Order.prototype;
    models.Order = models.Order.extend({
        _calculateRewards: async function () {
            const rewardsContainer = new RewardsContainer();

            if (this._getRegularOrderlines().length === 0) {
                return rewardsContainer;
            }

            const {
                freeProductPrograms,
                fixedAmountDiscountPrograms,
                onSpecificPrograms,
                onCheapestPrograms,
                onCheapestSpecificPrograms,
                onOrderPrograms,
            } = await this._getValidActivePrograms(rewardsContainer);

            const collectRewards = (validPrograms, rewardGetter) => {
                const allRewards = [];
                for (let [program, coupon_id] of validPrograms) {
                    const [rewards, reason] = rewardGetter(program, coupon_id);
                    if (reason) {
                        const notAwarded = new Reward({ awarded: false, reason, program, coupon_id });
                        rewardsContainer.add([notAwarded]);
                    }
                    allRewards.push(...rewards);
                }
                return allRewards;
            };

            // - Gather the product rewards
            const freeProducts = collectRewards(freeProductPrograms, this._getProductRewards.bind(this));

            // - Gather the fixed amount discounts
            const fixedAmountDiscounts = collectRewards(fixedAmountDiscountPrograms, this._getFixedDiscount.bind(this));

            // - Gather the specific discounts
            const specificDiscountGetter = (program, coupon_id) => {
                return this._getSpecificDiscount(program, coupon_id, freeProducts);
            };
            const specificDiscounts = collectRewards(onSpecificPrograms, specificDiscountGetter);

            const specificCheapestDiscountGetter = (program, coupon_id) => {
                return this._getSpecificCheapestDiscount(program, coupon_id, freeProducts);
            };
            const specificCheapestDiscounts = collectRewards(onCheapestSpecificPrograms, specificCheapestDiscountGetter);

            // - Collect the discounts from on order and on cheapest discount programs.
            const globalDiscounts = [];
            const onOrderDiscountGetter = (program, coupon_id) => {
                return this._getOnOrderDiscountRewards(program, coupon_id, freeProducts);
            };
            globalDiscounts.push(...collectRewards(onOrderPrograms, onOrderDiscountGetter));
            globalDiscounts.push(...collectRewards(onCheapestPrograms, (program, coupon_id) => this._getOnCheapestProductDiscount(program, coupon_id, freeProducts)));

            // - Group the discounts by program id.
            const groupedGlobalDiscounts = {};
            for (let discount of globalDiscounts) {
                const key = [discount.program.id, discount.coupon_id].join(',');
                if (!(key in groupedGlobalDiscounts)) {
                    groupedGlobalDiscounts[key] = [discount];
                } else {
                    groupedGlobalDiscounts[key].push(discount);
                }
            }

            // - We select the group of discounts with highest total amount.
            // Note that the result is an Array that might contain more than one
            // discount lines. This is because discounts are grouped by tax.
            let currentMaxTotal = 0;
            let currentMaxKey = null;
            for (let key in groupedGlobalDiscounts) {
                const discountRewards = groupedGlobalDiscounts[key];
                const newTotal = discountRewards.reduce((sum, discReward) => sum + discReward.discountAmount, 0);
                if (newTotal > currentMaxTotal) {
                    currentMaxTotal = newTotal;
                    currentMaxKey = key;
                }
            }
            const theOnlyGlobalDiscount = currentMaxKey
                ? groupedGlobalDiscounts[currentMaxKey].filter((discountReward) => discountReward.discountAmount !== 0)
                : [];

            // - Get the messages for the discarded global_discounts
            if (theOnlyGlobalDiscount.length > 0) {
                const theOnlyGlobalDiscountKey = [
                    theOnlyGlobalDiscount[0].program.id,
                    theOnlyGlobalDiscount[0].coupon_id,
                ].join(',');
                for (let [key, discounts] of Object.entries(groupedGlobalDiscounts)) {
                    if (key !== theOnlyGlobalDiscountKey) {
                        const notAwarded = new Reward({
                            program: discounts[0].program,
                            coupon_id: discounts[0].coupon_id,
                            reason: 'Not the greatest global discount.',
                            awarded: false,
                        });
                        rewardsContainer.add([notAwarded]);
                    }
                }
            }

            // - Add the calculated rewards.
            rewardsContainer.add([
                ...freeProducts,
                ...fixedAmountDiscounts,
                ...specificDiscounts,
                ...specificCheapestDiscounts,
                ...theOnlyGlobalDiscount,
            ]);

            return rewardsContainer;
        },
        _getValidActivePrograms: async function (rewardsContainer) {
            const freeProductPrograms = [],
                fixedAmountDiscountPrograms = [],
                onSpecificPrograms = [],
                onCheapestPrograms = [],
                onOrderPrograms = [],
                onCheapestSpecificPrograms = [];

            function updateProgramLists(program, coupon_id) {
                if (program.reward_type === 'product') {
                    freeProductPrograms.push([program, coupon_id]);
                } else {
                    if (program.discount_type === 'fixed_amount') {
                        fixedAmountDiscountPrograms.push([program, coupon_id]);
                    } else if (program.discount_apply_on === 'specific_products') {
                        onSpecificPrograms.push([program, coupon_id]);
                    } else if (program.discount_apply_on === 'cheapest_product') {
                        onCheapestPrograms.push([program, coupon_id]);
                    } else if (program.discount_apply_on === 'specific_cheapest_products'){
                        onCheapestSpecificPrograms.push([program, coupon_id]);
                    }else {
                        onOrderPrograms.push([program, coupon_id]);
                    }
                }
            }

            for (let [program, coupon_id] of this._getBookedPromoPrograms()) {
                // Booked coupons from on next order promo programs do not need
                // checking of rules because checks are done before generating
                // coupons.
                updateProgramLists(program, coupon_id);
            }

            for (let [program, coupon_id] of [
                ...this._getBookedCouponPrograms(),
                ...this._getActiveOnCurrentPromoPrograms(),
            ]) {
                const { successful, reason } = await this._checkProgramRules(program);
                if (successful) {
                    updateProgramLists(program, coupon_id);
                } else {
                    // side-effect
                    const notAwarded = new Reward({ program, coupon_id, reason, awarded: false });
                    rewardsContainer.add([notAwarded]);
                }
            }
            return {
                freeProductPrograms,
                fixedAmountDiscountPrograms,
                onSpecificPrograms,
                onCheapestPrograms,
                onCheapestSpecificPrograms,
                onOrderPrograms,
            };
        },
        _getSpecificCheapestDiscount: function (program, coupon_id, productRewards) {
            const amountsToDiscount = {};
            const orderlines = this._getRegularOrderlines();
            var o_order_lines = []
            const productIdsToAccount = new Set();
            if (orderlines.length > 0) {
                for (let line of this._getRegularOrderlines()) {
                    if (program.discount_specific_product_ids.has(line.get_product().id)) {
                        o_order_lines.push(line)
                    }
                }
                const cheapestLine = this._findCheapestLine(o_order_lines, productRewards);
                if (program.discount_specific_product_ids.has(cheapestLine.get_product().id)) {
                    const key = this._getGroupKey(cheapestLine);
                    amountsToDiscount[key] = cheapestLine.price;
                    productIdsToAccount.add(cheapestLine.get_product().id);
                }
            }
            this._considerProductRewards(amountsToDiscount, productIdsToAccount, productRewards);
            return this._createDiscountRewards(program, coupon_id, amountsToDiscount);
        },
    });

});

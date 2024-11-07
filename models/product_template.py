# -*- coding: utf-8 -*-
from datetime import timedelta, datetime

from odoo import models, fields, api
import logging

from odoo.exceptions import UserError
from odoo.tools.populate import compute

_logger = logging.getLogger(__name__)


def _get_days_delta(period):
    return {'month': 30, 'fortnight': 14, 'week': 7, 'day': 1}.get(period, 30)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    demand_category_id = fields.Many2one('inventory.demand.category', string='Demand Category')
    last_sales_qty = fields.Integer(string='Last Sales Quantity')
    last_classification_date = fields.Date(string='Last Classification Date')

    def _get_order_sum(self, period='month'):
        _logger.info('Getting order sum...')

        days_delta = _get_days_delta(period)
        start_date = fields.Date.today() - timedelta(days=days_delta)

        sales = self.env['account.invoice.report'].read_group(
            domain=[
                ('invoice_date', '>=', start_date)
            ],
            fields=['product_id', 'quantity'],
            groupby=['product_id']
        )

        _logger.debug('Sales: %s', sales)

        order_sum = {
            sale['product_id']:
                sale['quantity'] for sale in sales
        }

        return order_sum

    def action_classify_products(self):
        """Reclassify products based on current sales data."""
        self.classify_products('month', True)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload'
        }

    @api.model
    def classify_products(self, period='month', generate_reordering_rules=False):
        _logger.info('Classifying products...')

        demand_categories = self.env['inventory.demand.category'].search([], order='sales_threshold desc')

        _logger.debug('Demand categories count: %s', len(demand_categories))

        order_sum = self._get_order_sum(period)

        products = self.env['product.template'].search([
            ('id', 'in', [product_id for (product_id, _) in order_sum.keys()])
        ])

        for (product_id, name), quanty in order_sum.items():
            _logger.debug('Product %s sales: %s', name, quanty)

            selected_category = None
            for demand_category in demand_categories:
                if quanty >= demand_category.sales_threshold:
                    selected_category = demand_category.id
                    break

            # save the product to the db
            if selected_category:
                product = products.browse(product_id)
                product.write({
                    'demand_category_id': selected_category,
                    'last_sales_qty': quanty,
                    'last_classification_date': datetime.now()
                })

        if generate_reordering_rules:
            self.generate_reordering_rules(products)

    def _get_replenish_location(self):
        replenish_location = self.env['stock.location'].search([
            ('usage', '=', 'internal'),
            ('replenish_location', '=', True)
        ], limit=1)

        if not replenish_location:
            _logger.error('No replenish location found, please create one')
            raise UserError('No replenish location found, please create one')

        return replenish_location

    def _get_reordering_rules(self, replenish_location):
        return self.env['stock.warehouse.orderpoint'].search([
            ('location_id', '=', replenish_location.id),
            ('company_id', '=', self.env.user.company_id.id),
            ('active', 'in', [True, False])
        ])

    def generate_reordering_rules(self, products):
        _logger.info('Generating reordering rules...')
        qty_multiple = 1

        replenish_location = self._get_replenish_location()
        reordering_rules = self._get_reordering_rules(replenish_location)

        for product in products:
            if product.demand_category_id:
                if product.qty_available > product.demand_category_id.reorder_point:
                    _logger.info('Product %s has enough stock, skipping...', product.name)
                    continue

                reordering_rule = reordering_rules.filtered(lambda r: r.product_id.id == product.id)

                if reordering_rule:
                    _logger.info('Found reordering rule for product %s, updating...', product.name)
                    reordering_rule.write({
                        'active': True,
                        'product_min_qty': product.demand_category_id.reorder_point,
                        'product_max_qty': product.demand_category_id.max_inventory,
                        'qty_multiple': qty_multiple
                    })
                else:
                    _logger.info('No reordering rule found for product %s, creating...', product.name)
                    reordering_rule = self.env['stock.warehouse.orderpoint'].create({
                        'product_id': product.id,
                        'location_id': replenish_location.id,
                        'product_min_qty': product.demand_category_id.reorder_point,
                        'product_max_qty': product.demand_category_id.max_inventory,
                        'qty_multiple': qty_multiple,
                        'company_id': self.env.user.company_id.id,
                    })

                _logger.info('Reordering rule created for product %s', product.name)
                _logger.debug('Reordering rule: %s', reordering_rule)

            # self._deactivate_obsolete_reordering_rules(products, replenish_location)

    def _deactivate_obsolete_reordering_rules(self, products, replenish_location):
        _logger.info('Deactivating obsolete reordering rules...')

        obsolete_rules = self.env['stock.warehouse.orderpoint'].search([
            ('product_id', 'not in', [product.id for product in products]),
            ('location_id', '=', replenish_location.id),
            ('company_id', '=', self.env.user.company_id.id),
            ('active', '=', True)
        ])

        for rule in obsolete_rules:
            if rule.product_id not in products:
                _logger.info('Deactivating reordering rule for product %s', rule.product_id.name)
                obsolete_rules.write({'active': False})
                _logger.info('Deactivated %s obsolete reordering rules.', len(obsolete_rules))

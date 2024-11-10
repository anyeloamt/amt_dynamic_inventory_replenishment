# -*- coding: utf-8 -*-

from odoo import models, fields

class DemandCategory(models.Model):
    _name = 'inventory.demand.category'
    _description = 'Inventory Demand Category for Dynamic Inventory Replenishment'
    _rec_name = 'category_name'

    category_name = fields.Char(string='Category Name', required=True)
    sales_threshold = fields.Integer(string='Sales Threshold', required=True)
    max_inventory = fields.Integer(string='Max Inventory', required=True)
    reorder_point = fields.Integer(string='Reorder Point', required=True)

    def action_reclassify_all_products(self):
        """Reclassify all products from demand category."""
        products = self.env['product.template'].search([])
        products.classify_products('month', True)
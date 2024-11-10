import logging
_logger = logging.getLogger(__name__)

from odoo import models, fields


class ProductReclassificationWizard(models.TransientModel):
    _name = 'product.reclassification.wizard'
    _description = 'Product Reclassification Wizard'
    
    period = fields.Selection([
        ('all', 'All'),
        ('year', 'Year'),
        ('month', 'Month'),
        ('fortnight', 'Fortnight'),
        ('week', 'Week'),
        ('day', 'Day')
    ], string='Period', default='month')
    
    generate_reordering_rules = fields.Boolean(string='Generate Reordering Rules', default=True)

    def action_reclassify_products(self):
        """Reclassify products based on current sales data for the selected period."""
        
        _logger.info('Reclassifying products for period: %s, generate reordering rules: %s', self.period, self.generate_reordering_rules)
        
        self.env['product.template'].classify_products(self.period, self.generate_reordering_rules)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'reload'
        }
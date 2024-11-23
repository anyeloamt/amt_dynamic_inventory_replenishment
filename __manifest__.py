# -*- coding: utf-8 -*-
{
    'name': 'AMT Dynamic Inventory Replenishment App',
    'version': '0.1',
    'summary': 'This module adds functionality to automatically replenish inventory based on sales',
    'description': """
        This module adds functionality to automatically replenish inventory based on sales.
    """,
    'category': 'Inventory',
    'data': [
        # views
        'views/product_views.xml',
        'views/product_reclassification_wizard_views.xml',
        'views/inventory_dashboard_views.xml',
        'views/demand_category_views.xml',

        # data
        'data/demand_category_data.xml',
        'data/cron_jobs.xml',

        # security
        'security/groups.xml',
        'security/ir.model.access.csv',
    ],
    'depends': ['sale', 'stock', 'point_of_sale'],
    'installable': True,
    'application': False,
    'license': 'OPL-1',
    'author': 'AMT MOVIL',
    'website': 'https://www.amtmovil.com'
}
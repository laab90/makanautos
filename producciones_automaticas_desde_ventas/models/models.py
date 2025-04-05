from odoo import models, fields, api

class ProductionAutomation(models.Model):
    _name = 'production.automation'
    _description = 'Production Automation Configuration'

    execution_date = fields.Date(string='Fecha')
    
    def execute_production(self):
        sales_data = self.env['account.invoice.line'].search([
            ('date_invoice', '=', self.execution_date),  # Filtro por fecha
            ('state', '=', 'draft'),  # Filtro por estado draft
        ])
        product_sales = {}
        for line in sales_data:
            product_id = line.product_id.id
            if product_id in product_sales:
                product_sales[product_id] += line.quantity
            else:
                product_sales[product_id] = line.quantity

        
        for product_id, quantity_sold in product_sales.items():
            
            production_order = self.env['mrp.production'].search([
                ('product_id', '=', product_id),  # Filtro por el producto vendido
                ('state', '=', 'draft'),  # Filtro por estado draft de la orden de producción
            ])

            if production_order:
                production_order.write({'product_qty': quantity_sold})
                
        return {'result': 'Production exitosa!'}

    
# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class StockMove(models.Model):
    _inherit = "stock.move"    
    
    def get_lot_serial(self):
        lots = self.move_line_ids.mapped('lot_id.name')
        description = ''
        if lots:
            trj = ', '.join(lots)
            description = 'Lotes/Número de Serie: ' + '\n' + trj
        return description
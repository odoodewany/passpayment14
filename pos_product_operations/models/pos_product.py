# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class pos_config(models.Model):
    _inherit = 'pos.config'

    allow_pos_product_operations = fields.Boolean(string='Allow Product Operations')
    allow_edit_product  = fields.Boolean(string='Allow user to edit/create product from pos')

class ProductProduct(models.Model):
    _inherit = 'product.product'


    @api.model
    def sync_product(self, product):
        # pos_configs = self.env['pos.config'].sudo().search([('allow_pos_sync_data', '=', True)])
        notifications = []
        # for config in pos_configs:
        notifications.append(
            ((self._cr.dbname, 'pos.sync.product', self.env.user.id), {'product': product}))
        if len(notifications) > 0:
            self.env['bus.bus'].sendmany(notifications)
        return True

    @api.model
    def create(self, vals):
        res = super(ProductProduct, self).create(vals)
        session = self.env['pos.session'].search([('state', '=', 'opened'), ('user_id', '=', self.env.uid)], limit=1)
        prod = self.with_context(display_default_code=False).search_read([('id', '=', res.id)],['type','display_name', 'lst_price', 'standard_price', 'categ_id', 'pos_categ_id', 'taxes_id',
                 'barcode', 'default_code', 'to_weight', 'uom_id', 'description_sale', 'description',
                 'product_tmpl_id','tracking', 'write_date', 'available_in_pos', 'attribute_line_ids'])
        self.sync_product(prod)
        return res

    def write(self, vals):
        res = super(ProductProduct, self).write(vals)
        session = self.env['pos.session'].search([('state', '=', 'opened'), ('user_id', '=', self.env.uid)], limit=1)
        prod = self.with_context(display_default_code=False).search_read([('id', '=', self.id)],['type','display_name', 'lst_price', 'standard_price', 'categ_id', 'pos_categ_id', 'taxes_id',
                 'barcode', 'default_code', 'to_weight', 'uom_id', 'description_sale', 'description',
                 'product_tmpl_id','tracking', 'write_date', 'available_in_pos', 'attribute_line_ids'])
        self.sync_product(prod)

        return res
        
    @api.model
    def create_from_ui(self, product):
        # image is a dataurl, get the data after the comma
        product_id = product.pop('id', False)
        product_get_id = self.browse(int(product_id))
        if product_id:
            if product_get_id.product_tmpl_id.attribute_line_ids:
                if product.get('list_price') != '':
                    if '.' in product.get('list_price'):
                        product_get_id.mapped('product_template_attribute_value_ids.price_extra')
                        len_variant = len(product_get_id.mapped('product_template_attribute_value_ids.price_extra'))
                        for i in product_get_id.mapped('product_template_attribute_value_ids'):
                            divided_price = (float(product.get('list_price'))/len_variant);
                            i.write({'price_extra' : divided_price});
                        
                        product['list_price'] = product_get_id.list_price

                    else:
                        product['price_extra'] = product.get('list_price').replace(',','.')
                        AttributePrice = self.env['product.template.attribute.value']
                        prices = AttributePrice.search([
                            ('product_attribute_value_id','in',product_get_id.product_template_attribute_value_ids.ids),
                    
                        ])
                        updated = prices.mapped('ptav_product_variant_ids');
                        
                        len_variant = len(product_get_id.mapped('product_template_attribute_value_ids.price_extra'));
                        
                        for i in product_get_id.mapped('product_template_attribute_value_ids'):
                            divided_price = (int(product['price_extra'])/len_variant);
                            i.write({'price_extra' : divided_price});

                        product['list_price'] = product_get_id.list_price;

                else:
                        product['lst_price'] = product_get_id.lst_price
            else:
                if product.get('list_price') != '':
                    product['lst_price'] = product.get('list_price')
                else:
                    product['lst_price'] = product_get_id.lst_price
        else:
            if '.' in product.get('list_price'):
                product['list_price'] = product.get('list_price')
            else:
                product['list_price'] = product.get('list_price').replace(',','.')

        if product.get('cost_price') != '':
            if '.' in product.get('cost_price'):        
                product['standard_price'] = product.get('cost_price')       
            else:   
                product['standard_price'] = product.get('cost_price').replace(',','.')
        else:
            product['standard_price'] = product_get_id.standard_price
        product['available_in_pos'] = True
        # if product.get('pos_categ_id') != False:
        #     product['categ_id'] =product.get('pos_categ_id')
        # else:
        #     product['pos_categ_id'] =product_get_id.pos_categ_id.id

        if product.get('pos_categ_id') != False:
            if int(product.get('pos_categ_id')):
                product['categ_id'] = int(product.get('pos_categ_id'))
            else:
                product['categ_id'] = False
        else:
            product['pos_categ_id'] =product_get_id.pos_categ_id.id

        if product.get('uom_id') != False:
            if int(product.get('uom_id')):
                product['uom_id'] = int(product.get('uom_id'))
                product['uom_po_id'] = int(product.get('uom_id'))
            else:
                product['uom_id'] = 1
                product['uom_po_id'] = 1
        else:
            product['uom_id'] =product_get_id.uom_id.id
            product['uom_po_id'] =product_get_id.uom_id.id

        product['barcode'] = product.get('barcode')

        if ('(') in product.get('display_name'):
            name = product.get('display_name').split('(')
            product['name'] = name[0]
        else:
            product['name'] = product.get('display_name')
        

        str_b = False

        if product.get('image_1920') != None:
            str_b = product.get('image_1920').strip("data:image/png;base64,")
            product['image_1920'] ="i"+str_b
            if product_id:  # Modifying existing product
                if product.get('cost_price'):
                    standard_price = product.pop('cost_price',0.0)
                    product.update({
                        'standard_price' : float(standard_price)
                    })

                if product['pos_categ_id']:
                    product['pos_categ_id'] = int(product['pos_categ_id'])
                else:
                    product['pos_categ_id'] = False

                if product['uom_id']:
                    product['uom_id'] = int(product['uom_id'])
                    product['uom_po_id'] = int(product['uom_id'])
                else:
                    product['uom_id'] = 1
                    product['uom_po_id'] = 1
                self.browse(int(product_id)).write(product)
            else:
                product_id = self.create({
                    'name':product.get('display_name'),
                    'available_in_pos' : True,
                    'barcode':product.get('barcode'),
                    'lst_price':float(product.get('list_price')),
                    'standard_price':float(product.get('cost_price')),
                    'pos_categ_id' :int(product.get('pos_categ_id')) if int(product.get('pos_categ_id')) else False,
                    'uom_id' :int(product.get('uom_id')) if int(product.get('uom_id')) else 1,
                    'uom_po_id' :int(product.get('uom_id')) if int(product.get('uom_id')) else 1,
                    'image_1920':"i"+str_b
                })
        else:
            if product_id:  # Modifying existing product
                if product.get('cost_price'):
                    standard_price = product.pop('cost_price',0.0)
                    product.update({
                        'standard_price' : float(standard_price)
                    })
                if product['pos_categ_id']:
                    product['pos_categ_id'] = int(product['pos_categ_id'])
                else:
                    product['pos_categ_id'] = False
                if product['uom_id']:
                    product['uom_id'] = int(product['uom_id'])
                    product['uom_po_id'] = int(product['uom_id'])
                else:
                    product['uom_id'] = 1
                    product['uom_po_id'] = 1
                self.browse(int(product_id)).write(product)
                
            else:
                product_id = self.create({
                    'name':product.get('display_name'),
                    'available_in_pos' : True,
                    'barcode':product.get('barcode'),
                    'lst_price':float(product.get('list_price',0.0)),
                    'standard_price':float(product.get('cost_price')),
                    'pos_categ_id' :int(product.get('pos_categ_id')) if int(product.get('pos_categ_id')) else False,
                    'uom_id' :int(product.get('uom_id')) if int(product.get('uom_id')) else 1,
                    'uom_po_id' :int(product.get('uom_id')) if int(product.get('uom_id')) else 1
                })
        return int(product_id)
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:    

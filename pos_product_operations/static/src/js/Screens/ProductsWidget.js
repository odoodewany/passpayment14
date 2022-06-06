odoo.define('pos_product_operations.ProductsWidget', function(require) {
	"use strict";

	const Registries = require('point_of_sale.Registries');
	const ProductsWidget = require('point_of_sale.ProductsWidget');
	var models = require('point_of_sale.models');
	let prd_list_count = 0;


	models.load_fields('product.product', ['type']);

	const BiProductsWidget = (ProductsWidget) =>
		class extends ProductsWidget {

			constructor() {
				super(...arguments);
			}

			mounted() {
				super.mounted();
				this.env.pos.on('change:is_sync', this.render, this);
                let self = this;
                self.env.services.bus_service.updateOption('pos.sync.product',self.env.session.uid);
				self.env.services.bus_service.onNotification(self,self._onProductNotification);
				self.env.services.bus_service.startPolling();
				self.env.services.bus_service._startElection();
			}

			_onProductNotification(notifications){
				let self = this;
				notifications.forEach(function (ntf) {
					ntf = JSON.parse(JSON.stringify(ntf))
					if(ntf && ntf[1]){
						if (ntf[0][1] == 'pos.sync.product'){
	                        let prod = ntf[1].product[0];
	                        let old_category_id = self.env.pos.db.product_by_id[prod.id];
	                        let new_category_id = prod.pos_categ_id[0];
	                        let stored_categories = self.env.pos.db.product_by_category_id;

							prod.pos = self.env.pos;
							if(self.env.pos.db.product_by_id[prod.id]){
	                            if(old_category_id.pos_categ_id){
	                                stored_categories[old_category_id.pos_categ_id[0]] = stored_categories[old_category_id.pos_categ_id[0]].filter(function(item) {
	                                    return item != prod.id;
	                                });
	                            }
	                            if(stored_categories[new_category_id]){
	                                stored_categories[new_category_id].push(prod.id);
	                            }
								self.env.pos.db.product_by_id[prod.id] = new models.Product({}, prod);
							}else{
								self.env.pos.db.add_products(_.map( ntf[1].product, function (prd) {
									return new models.Product({}, prd);
								}));
							}
							self.env.pos.set("is_sync",false);
						}
					}
				});
				let call = self.productsToDisplay;
				this.env.pos.set("is_sync",true);
			}
			willUnmount() {
				super.willUnmount();
				this.env.pos.off('change:is_sync', null, this);
			}
			get is_sync() {
				return this.env.pos.get('is_sync');
			}
			
		};

	Registries.Component.extend(ProductsWidget, BiProductsWidget);

	return ProductsWidget;

});

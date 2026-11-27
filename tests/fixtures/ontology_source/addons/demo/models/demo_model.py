from odoo import api, fields, models


class DemoOrder(models.Model):
    _name = "demo.order"

    product_id = fields.Many2one("product.product")
    state = fields.Selection([("draft", "Draft"), ("done", "Done")])

    @api.constrains("state")
    def _check_state(self):
        if self.state == "draft":
            self.state = "done"

    def action_start(self):
        if self.state == "draft":
            self.state = "done"
        return True

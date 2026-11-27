import { Component } from "@odoo/owl";

export class DemoPanel extends Component {
    static template = "demo.DemoPanel";

    start() {
        this.rpc("demo.order", "action_start");
    }
}

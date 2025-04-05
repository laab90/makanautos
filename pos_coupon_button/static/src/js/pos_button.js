odoo.define('mi_pos_modulo.pos_button', function (require) {
    "use strict";

    var PosModel = require('point_of_sale.models');
    var Registries = require('point_of_sale.Registries');
    var { Component } = require('web.core');

    // Crear un nuevo componente para el botón
    const CodigoPuntosButton = Component.extend({
        template: 'CodigoPuntosButton',
        button_click: function() {
            console.log('Botón Código Puntos presionado');
        },
    });

    // Agregar el botón al UI del POS
    PosModel.load_fields('pos.config', ['id']);
    Registries.Component.add(CodigoPuntosButton);

    // Aquí se pueden agregar más lógica de lo que debería hacer el botón
});

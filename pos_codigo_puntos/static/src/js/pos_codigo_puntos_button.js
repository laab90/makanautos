// static/src/js/pos_codigo_puntos_button.js
odoo.define('pos_codigo_puntos.CodigoPuntosButton', function(require) {
    'use strict';

    const { PosComponent } = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    const rpc = require('web.rpc');

    class CodigoPuntosButton extends PosComponent {
        async onClick() {
            // Realiza una llamada RPC para obtener los programas de cupones con "puntos" en el nombre
            const couponPrograms = await rpc.query({
                model: 'coupon.program',
                method: 'search_read',
                args: [[['name', 'ilike', 'puntos']], ['name', 'code']],
            });

            if (couponPrograms.length === 0) {
                this.showPopup('ErrorPopup', {
                    title: 'No se encontraron programas',
                    body: 'No hay programas de cupones con "puntos" en el nombre.',
                });
                return;
            }

            // Muestra un popup con la lista de programas para seleccionar uno
            const { confirmed, payload } = await this.showPopup('SelectionPopup', {
                title: 'Seleccione un Programa de Puntos',
                list: couponPrograms.map(program => ({ id: program.id, label: program.name, item: program })),
            });

            if (confirmed) {
                // Muestra el código del cupón y un botón para copiarlo
                const couponCode = payload.code || 'No disponible';
                await this.showPopup('ConfirmPopup', {
                    title: 'Código de Cupón',
                    body: `Código generado: ${couponCode}`,
                    confirmText: 'Copiar Código',
                    onConfirm: async () => {
                        await navigator.clipboard.writeText(couponCode);
                        this.showPopup('ConfirmPopup', {
                            title: 'Código Copiado',
                            body: 'El código ha sido copiado al portapapeles.',
                        });
                    },
                });
            }
        }
    }

    // Aquí definimos la plantilla inline
    CodigoPuntosButton.template = xml`
        <div class="control-button">
            <button t-on-click="onClick" class="button">Código Puntos</button>
        </div>`;

    ProductScreen.addControlButton({
        component: CodigoPuntosButton,
        condition: function() {
            return true;
        },
    });

    Registries.Component.add(CodigoPuntosButton);

    return CodigoPuntosButton;
});

odoo.define('custom_pos_button.CanjePuntosButton', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const rpc = require('web.rpc');

    class CanjePuntosButton extends PosComponent {
        async onClick() {
            try {
                // Consultar los programas que contienen "PUNTOS" en el nombre
                const programas = await rpc.query({
                    model: 'coupon.program',
                    method: 'search_read',
                    domain: [['name', 'ilike', 'PUNTOS']],
                    fields: ['id', 'name'],
                });

                if (programas.length === 0) {
                    this.showPopup('ErrorPopup', {
                        title: 'No hay programas',
                        body: 'No se encontraron programas de puntos disponibles.',
                    });
                    return;
                }

                // Mostrar los programas en un popup para que el usuario seleccione uno
                const { confirmed, payload } = await this.showPopup('SelectionPopup', {
                    title: 'Seleccione un programa de puntos',
                    list: programas.map(p => ({ id: p.id, label: p.name })),
                });

                if (confirmed) {
                    // Mostrar confirmación antes de generar el cupón
                    const { confirmed: confirmedGenerate } = await this.showPopup('ConfirmPopup', {
                        title: 'Confirmar Canje de Puntos',
                        body: `¿Desea generar un cupón para el programa ${payload.label}?`,
                    });

                    if (confirmedGenerate) {
                        // Generar un nuevo cupón
                        const nuevoCupon = await rpc.query({
                            model: 'coupon.coupon',
                            method: 'create',
                            args: [{
                                program_id: payload.id,
                            }],
                        });

                        // Mostrar el cupón generado y un botón para copiar al portapapeles
                        this.showPopup('ConfirmPopup', {
                            title: 'Cupón generado',
                            body: `El cupón para el programa ${payload.label} se ha generado: ${nuevoCupon.code}`,
                            confirmText: 'Copiar al portapapeles',
                            cancelText: 'Cerrar',
                            confirm: () => {
                                this._copyToClipboard(nuevoCupon.code);
                                this.showPopup('ConfirmPopup', {
                                    title: 'Cupón copiado',
                                    body: 'El código del cupón ha sido copiado al portapapeles.',
                                });
                            },
                        });
                    }
                }
            } catch (error) {
                this.showPopup('ErrorPopup', {
                    title: 'Error',
                    body: 'Ocurrió un error al generar el cupón.',
                });
            }
        }

        _copyToClipboard(text) {
            const textarea = document.createElement('textarea');
            textarea.value = text;
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
        }
    }

    CanjePuntosButton.template = 'CanjePuntosButton';

    Registries.Component.add(CanjePuntosButton);

    return CanjePuntosButton;
});

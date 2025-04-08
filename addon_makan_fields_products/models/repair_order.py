from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class RepairOrder(models.Model):
    _inherit = 'repair.order'

    
    # Campos definidos
    nif = fields.Char(string="NIF/Identificación Fiscal", related='partner_id.vat', readonly=True)
    solicitar_prueba = fields.Boolean(string="Solicitar Prueba")
    documentos = fields.Boolean(string="Documentos")
    manuales = fields.Boolean(string="Manuales")
    herramienta = fields.Boolean(string="Herramienta")
    tricket = fields.Boolean(string="Tricket")
    llanta_rep = fields.Boolean(string="Llanta de Repuesto")
    alfombra = fields.Boolean(string="Alfombra")
    encendedor = fields.Boolean(string="Encendedor")
    extintor = fields.Boolean(string="Extintor")
    ctrlalarma = fields.Boolean(string="Ctrl Alarma")
    platosaros = fields.Boolean(string="Platos/Aros")
    tanque_combustible = fields.Selection([
        ('empty', 'Vacío'),
        ('quarter', '1/4'),
        ('half', '1/2'),
        ('three_quarters', '3/4'),
        ('full', 'Full')
    ], string="Estado del Tanque de Combustible")
    kilometrajebd = fields.Char(string="Kilometraje")
    product_id = fields.Many2one('product.template', string="Producto")
    modelo = fields.Char(string="Modelo", related='product_id.modelo', store=True)
    marca = fields.Char(string="Marca", related='product_id.marca', store=True)
    chasis = fields.Char(string="Chasis", related='product_id.chasis', store=True)
    placa = fields.Char(string="Placa", related='product_id.placa', store=True)
    motor = fields.Char(string="Motor", related='product_id.motor', store=True)
    anio = fields.Integer(string="Año", related='product_id.anio', store=True)
    color = fields.Char(string="Color", related='product_id.color', store=True)
    kilometraje = fields.Float(string="Kilometraje", related='product_id.kilometraje', store=True)
    firma_cliente = fields.Binary(string="Firma Entrada")
    firma_autorizado = fields.Binary(string="Firma Salida")
    kmfinal = fields.Char(string="Km/Ml Final")
    horacarwash = fields.Datetime(string="Hora", default=fields.Datetime.now)
    firma_carwash = fields.Binary(string="Firma Carwash")
    observaciones = fields.Html(string="Observaciones")
    reporte_previo = fields.Html(string="Notas de Reporte Previo")

    # Campos de chequeo de cortesía
    media = fields.Boolean(string="Media")
    baja = fields.Boolean(string="Baja")
    alta = fields.Boolean(string="Alta")
    neblinera = fields.Boolean(string="Neblinera Delanteras y Traseras")
    retroceso = fields.Boolean(string="Retroceso")
    defrenos = fields.Boolean(string="De frenos")
    pidevias = fields.Boolean(string="Pide Vías")

    # Sección de Niveles
    aceitemootor = fields.Boolean(string="Aceite de Motor")
    refrigerante = fields.Boolean(string="Refrigerante")
    liquidofrenos = fields.Boolean(string="Líquido de Frenos")
    timonhidraulico = fields.Boolean(string="Timón Hidráulico")
    liquidochorritos = fields.Boolean(string="Líquido de Chorritos")
    plumillas = fields.Boolean(string="Plumillas")
    chorritos = fields.Boolean(string="Chorritos")
    taponesdellantas = fields.Boolean(string="Tapones de Llantas")
    presiondellantas = fields.Boolean(string="Presión de Llantas")
    llantaderepuesto = fields.Boolean(string="Llanta de Repuesto")
    copaseguridad = fields.Boolean(string="Copia de Seguridad")
    herramienta = fields.Boolean(string="Herramienta")
    testigosadvertencia = fields.Boolean(string="Testigos y Advertencias")
    bornesbateria = fields.Boolean(string="Bornes de Batería")
    cierrecentral = fields.Boolean(string="Cierre Central")
    firma_golpescarwash = fields.Binary(string="Firma Marca Golpes")
    

    objetosencontrados = fields.Char(string="Objetos Encontrados")
    notasrecepcion = fields.Char(string="Notas")

    contraseñacliente = fields.Text(
        string="Contraseña Cliente",
        default=(
            "1. La presente autorización expresa que... (contenido resumido para brevedad)"
        )
    )
    horas = fields.Float(string="Horas")
    location_id = fields.Many2one('stock.location', string="Ubicación")
    propietario = fields.Many2one(comodel_name='res.partner')
    chkmotor = fields.Boolean(string="Motor")
    chksuspension = fields.Boolean(string="Suspensión")
    chktransmision = fields.Boolean(string="Transmisión")
    chkadvertencias = fields.Boolean(string="Advertencias")
    chkaveriasentabler = fields.Boolean(string="Averías en Tablero")
    chkconfort = fields.Boolean(string="Confort")
    comentariospruebas = fields.Html(string="Comentarios")
    notaspruebas = fields.Html(string="Notas")
    noaplicatimon = fields.Boolean(string="No Aplica")
    noaplicallanta = fields.Boolean(string="No Aplica")
    noaplicacopia = fields.Boolean(string="No Aplica")
    vbtaller = fields.Selection([('1', 'Revisado')], string="Vo. Bo. Jefe de Taller", tracking=True)
    notas_internal_cierre = fields.Text(string="Notas Internas Taller Cierre")
    cierre_taller = fields.Boolean(string="Cierre Taller")
    
    # Relaciones
    order_line_ids = fields.One2many('repair.order.line.taller', 'order_id', string="Líneas de Orden de Reparación")
    repair_line_ids = fields.One2many('repair.line', 'order_id', string="Líneas de Reparación")
    
    wash_ids = fields.One2many('wash.test', 'repair_order_id', string="Lavado")
    test_ids = fields.One2many('repair.test', 'repair_order_id', string="Pruebas")
    
    order_line_ids_taller1 = fields.One2many('repair.order.table1.taller', 'order_id_taller1',
                                             string="Líneas de Tabla Taller1")
    order_line_ids_taller2 = fields.One2many('repair.order.table2.taller', 'order_id_taller2')
    
    #AGREGAR METODO DE COMPUTO PARA REPAIR ORDER EN SERVICIOS M.O HECHO POR ELDER GIRON #05/04/2025
    total_fees = fields.Monetary(
        string='Total de Servicios',
        compute='_compute_total_fees',
        currency_field='currency_id',
        store=True
    )

    count_approved_lines = fields.Monetary(
        string='Líneas Aprobadas',
        compute='_compute_total_approved_lines_amount',
        store=True
    )
    
    @api.depends('fees_lines.price_subtotal')
    def _compute_total_fees(self):
        for record in self:
            record.total_fees = sum(line.price_subtotal for line in record.fees_lines)

    #AQUI TERMINO ----------------------------------------------------------------------------------

    #SE AGREGA CALCULO SUMA DE AMBOS CAMPOS
    total_pieces_and_fees = fields.Float(string="Gran Total", compute='_compute_total_pieces_and_fees', store=True)

    @api.depends('amount_total', 'total_fees')
    def _compute_total_pieces_and_fees(self):
        for record in self:
            record.total_pieces_and_fees = record.amount_total + record.total_fees
    #AQUI TERMINO

    #METODO PARA CALCULAR LINEAS APROBADAS
    @api.depends('repair_line_ids.statuspiezas', 'repair_line_ids.price_subtotal')
    def _compute_total_approved_lines_amount(self):
        for order in self:
            # Inicializamos la suma del precio
            total_amount = 0.0

            # Buscamos las líneas de reparación con estado 'Aprobado' (statuspiezas = '2')
            approved_lines = self.env['repair.line'].search([
                ('repair_id', '=', order.id),
                ('statuspiezas', '=', '2')  # Estado Aprobado
            ])

            # Sumamos el price_subtotal de las líneas aprobadas
            for line in approved_lines:
                total_amount += line.price_subtotal  # Sumar el subtotal de cada línea aprobada

            # Asignamos la suma al campo total_approved_lines_amount
            order.count_approved_lines = total_amount
    #FIN DE METODO
    

    # Métodos
    @api.onchange('location_id')
    def _onchange_location_id(self):
        for line in self.operations:
            line.location_id = self.location_id

    def action_repair_invoice_create(self):
        _logger.info(f"Creando factura para la orden: {self.id}")

        # Buscar líneas aprobadas asociadas a esta orden
        approved_lines = self.env['repair.line'].search([
            ('repair_id', '=', self.id),
            ('statuspiezas', '=', '2')  # Solo líneas aprobadas
        ])

        # Buscar líneas de mano de obra aprobadas de repair.fee
        approved_fees = self.env['repair.fee'].search([
            ('repair_id', '=', self.id),
            ('statuspiezas', '=', '2')  # Solo líneas aprobadas
        ])

        if not approved_lines and not approved_fees:
            _logger.info(f"No se encontraron líneas aprobadas para la orden: {self.id}")
            raise UserError("No hay líneas de producto o mano de obra con estado 'Aprobado' para generar una factura.")

        # Depuración: Verificar líneas aprobadas
        _logger.info(f"Líneas aprobadas encontradas: {len(approved_lines)}")
        for line in approved_lines:
            _logger.info(
                f"Procesando línea aprobada: {line.name}, Estado: {line.statuspiezas}, Producto: {line.product_id.name}")

        # Crear líneas de factura
        invoice_lines = []

        # Agregar las líneas de productos de repair.line
        for line in approved_lines:
            if not line.product_id:
                raise UserError(f"La línea '{line.name}' no tiene un producto asociado.")

            invoice_lines.append((0, 0, {
                'name': line.name,
                'quantity': line.product_uom_qty,
                'price_unit': line.price_unit,
                'tax_ids': [(6, 0, line.tax_id.ids)] if line.tax_id else [],
                'product_uom_id': line.product_uom.id,
                'product_id': line.product_id.id,
            }))

        # Agregar las líneas de mano de obra de repair.fee
        for fee in approved_fees:
            invoice_lines.append((0, 0, {
                'product_id': fee.product_id.id,
                'name': fee.name,
                'quantity': fee.product_uom_qty,
                'price_unit': fee.price_unit,
                'product_uom_id': fee.product_uom.id,
                'tax_ids': [(6, 0, fee.tax_id.ids)] if fee.tax_id else [],
            }))

        # Crear la factura
        invoice_vals = {
            'partner_id': self.partner_id.id,
            'move_type': 'out_invoice',
            'invoice_line_ids': invoice_lines,
            'repair_ids': [(4, self.id)],
        }
        invoice = self.env['account.move'].create(invoice_vals)
        _logger.info(f"Factura creada con ID: {invoice.id}")

        # Obtener el tipo de picking adecuado
        try:
            picking_type = self.env.ref('stock.picking_type_internal')
        except ValueError:
            raise UserError(
                "No se pudo encontrar el tipo de picking 'stock.picking_type_internal'. Asegúrate de que exista o utiliza el XML ID correcto.")

        # Crear un picking para la orden de reparación
        picking_vals = {
            'partner_id': self.partner_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_id.id,
            'picking_type_id': picking_type.id,
            'origin': f'Repair Order {self.name}',
        }
        picking = self.env['stock.picking'].create(picking_vals)
        _logger.info(f"Picking creado con ID: {picking.id} para la orden de reparación: {self.id}")

        # Crear los movimientos de stock asociados al picking (solo para líneas aprobadas)
        for line in approved_lines:
            if line.statuspiezas == '2':  # Solo líneas aprobadas
                move_vals = {
                    'name': line.name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.product_uom_qty,
                    'product_uom': line.product_uom.id,
                    'location_id': self.location_id.id,
                    'location_dest_id': line.location_id.id,
                    'picking_id': picking.id,
                }
                stock_move = self.env['stock.move'].create(move_vals)
                _logger.info(
                    f"Movimiento de stock creado con ID: {stock_move.id} para el producto: {line.product_id.name}")

        # Confirmar el picking
        picking.action_confirm()
        _logger.info(f"Picking {picking.id} confirmado.")

        # Asignar el picking (reservar el stock)
        picking.action_assign()
        _logger.info(f"Picking {picking.id} asignado.")

        # Verificar los stock.move.line
        for move in picking.move_lines:
            _logger.info(f"Movimiento de stock {move.id} tiene {len(move.move_line_ids)} líneas de movimiento.")
            for move_line in move.move_line_ids:
                _logger.info(
                    f"Línea de movimiento: Producto: {move_line.product_id.name}, Cantidad: {move_line.qty_done}, Ubicación: {move_line.location_id.name} -> {move_line.location_dest_id.name}")

        # Establecer 'quantity_done' y validar el picking
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
            _logger.info(f"Cantidad realizada para el movimiento {move.id} establecida a {move.quantity_done}.")

        try:
            picking.button_validate()
            _logger.info(f"Picking {picking.id} validado y completado.")
        except UserError as e:
            _logger.error(f"Error al validar el picking {picking.id}: {e}")
            raise UserError(f"No se pudo validar la transferencia: {e}")

        # Actualizar el estado de la orden de reparación
        self.state = 'done'
        _logger.info(f"Estado de la orden {self.id} cambiado a 'done'")

        # Retornar la acción para mostrar la factura creada
        return {
            'name': 'Factura',
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'type': 'ir.actions.act_window',
        }

    def action_repair_end(self):
        """
        Finaliza la reparación:
        - Genera movimientos de inventario para las líneas aprobadas.
        - Permite que el stock se registre con cantidades negativas al finalizar.
        """
        _logger.info(f"Finalizando reparación para la orden: {self.id}")

        # Buscar líneas aprobadas de productos asociadas a esta orden
        approved_lines = self.env['repair.line'].search([
            ('repair_id', '=', self.id),
            ('statuspiezas', '=', '2')  # Solo líneas aprobadas
        ])

        # Buscar líneas de mano de obra aprobadas de repair.fee
        approved_fees = self.env['repair.fee'].search([
            ('repair_id', '=', self.id),
            ('statuspiezas', '=', '2')  # Solo líneas aprobadas
        ])

        if not approved_lines and not approved_fees:
            _logger.info(f"No se encontraron líneas aprobadas para la orden: {self.id}")
            raise UserError("No hay líneas aprobadas para finalizar la reparación.")

        _logger.info(f"Líneas de productos aprobadas: {len(approved_lines)}")
        _logger.info(f"Líneas de mano de obra aprobadas: {len(approved_fees)}")

        # Crear un picking para movimientos de inventario
        picking_type = self.env.ref('stock.picking_type_internal')
        picking_vals = {
            'partner_id': self.partner_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_id.id,
            'picking_type_id': picking_type.id,
            'origin': f'Repair Order {self.name}',
            'repair_order_id': self.id,
            'product_id_order': self.product_id.id,
        }
        picking = self.env['stock.picking'].create(picking_vals)
        _logger.info(f"Picking creado con ID: {picking.id}")

        # Crear movimientos de inventario para las líneas aprobadas
        for line in approved_lines:
            if not line.product_id:
                raise UserError(f"La línea '{line.name}' no tiene un producto asociado.")

            if line.statuspiezas != '2':  # Verificar explícitamente el estado
                continue

            move_vals = {
                'name': line.name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_uom_qty,
                'product_uom': line.product_uom.id,
                'location_id': self.location_id.id,
                'location_dest_id': line.location_dest_id.id,  # Ubicación de destino desde la línea de reparación
                'repair_id': self.id,
                'picking_id': picking.id,
            }
            stock_move = self.env['stock.move'].create(move_vals)
            _logger.info(f"Movimiento de stock creado con ID: {stock_move.id} para el producto: {line.product_id.name}")

        # Confirmar y validar el picking
        picking.action_confirm()
        picking.action_assign()

        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty

        picking.button_validate()
        _logger.info(f"Picking {picking.id} validado y completado.")

        # Actualizar stock.quant con valores de product_id_order y repair_order_id
        for line in approved_lines:
            if line.statuspiezas != '2':  # Verificar explícitamente el estado
                continue

            # Verificar la cantidad que se está asignando
            _logger.info(f"Asignando cantidad negativa para la línea '{line.name}': {line.product_uom_qty}")

            # Buscar el stock.quant existente para la ubicación y el producto
            quant = self.env['stock.quant'].search([
                ('product_id', '=', line.product_id.id),
                ('location_id', '=', self.location_id.id)  # Verifica solo la ubicación de origen
            ], limit=1)

            if quant:
                # Log para verificar la cantidad inicial
                _logger.info(f"Cantidad inicial de stock.quant {quant.id}: cantidad={quant.quantity}")

                # Asignar directamente una cantidad negativa
                #quant.quantity -= line.product_uom_qty

                # Log para verificar la cantidad después de la asignación
                _logger.info(f"Cantidad actualizada de stock.quant {quant.id}: cantidad={quant.quantity}")

                # Asignar los valores de referencia
                quant.repair_order_id = self.id
                quant.product_id_order = self.product_id.id
                _logger.info(f"Actualizado stock.quant {quant.id}: cantidad={quant.quantity}, "
                             f"repair_order_id={self.id}, product_id_order={self.product_id.id}")
            else:
                # Crear un nuevo stock.quant con cantidad negativa si no existe
                quant = self.env['stock.quant'].create({
                    'product_id': line.product_id.id,
                    'location_id': self.location_id.id,  # Solo la ubicación de origen
                    'quantity': -line.product_uom_qty,  # Stock negativo permitido
                    'repair_order_id': self.id,
                    'product_id_order': self.product_id.id,
                })
                _logger.info(f"Creado nuevo stock.quant {quant.id} con cantidad {quant.quantity} (negativo permitido).")

        # Cambiar estado de la orden a 'done'
        self.write({'state': '2binvoiced'})
        _logger.info(f"Estado de la orden {self.id} cambiado a 'done'")

    def action_redirect_to_purchase(self):
        """Redirige a la pantalla de creación de Compras"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Crear Compra',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'target': 'current',  # Cambia a 'new' si quieres que se abra en una nueva ventana emergente
        }

    def action_redirect_to_transfer(self):
        """Redirige a la pantalla de creación de Transferencias"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Crear Transferencia',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'target': 'current',  # Cambia a 'new' si quieres que se abra en una nueva ventana emergente
        }
    
    

    picking_ids = fields.Many2many(
        'stock.picking',
        string="Transferencias",
        domain="[('state', 'not in', ['cancel'])]",  # Evita mostrar transferencias canceladas
        help="Transferencias asociadas a esta orden de reparación."
    )

    purchase_ids = fields.Many2many(
        'purchase.order',
        string="Órdenes de Compra",
        help="Órdenes de compra asociadas a esta orden de reparación."
    )
    

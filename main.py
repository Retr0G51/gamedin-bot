#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot de Telegram para Gamedin - Tienda de Gaming Free Fire
Demo para Cliente
"""

import logging
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Estados para el flujo de conversación
SELECCIONAR_PRODUCTO, SELECCIONAR_CANTIDAD, INGRESAR_ID, INGRESAR_NOMBRE, INGRESAR_CONTACTO, CONFIRMAR_PEDIDO = range(6)

# =====================================================
# CONFIGURACIÓN - CAMBIAR ESTOS VALORES
# =====================================================
# Importar configuración
from config import BOT_TOKEN, GRUPO_PEDIDOS_ID, ADMIN_ID

# =====================================================
# PRODUCTOS DE FREE FIRE
# =====================================================
PRODUCTOS = {
    "diamantes": {
        "nombre": "💎 Diamantes",
        "descripcion": "Moneda premium de Free Fire",
        "cantidades": {
            "100": {"cantidad": "100", "precio": 50},
            "310": {"cantidad": "310", "precio": 150},
            "520": {"cantidad": "520", "precio": 250},
            "1080": {"cantidad": "1,080", "precio": 500},
            "2200": {"cantidad": "2,200", "precio": 1000},
            "5600": {"cantidad": "5,600", "precio": 2500}
        }
    },
    "monedas": {
        "nombre": "🪙 Monedas",
        "descripcion": "Moneda básica de Free Fire",
        "cantidades": {
            "2000": {"cantidad": "2,000", "precio": 20},
            "5000": {"cantidad": "5,000", "precio": 45},
            "10000": {"cantidad": "10,000", "precio": 85},
            "25000": {"cantidad": "25,000", "precio": 200},
            "50000": {"cantidad": "50,000", "precio": 380}
        }
    },
    "pases": {
        "nombre": "🎫 Pases de Batalla",
        "descripcion": "Pases temporada Free Fire",
        "cantidades": {
            "elite": {"cantidad": "Pase Elite", "precio": 400},
            "elite_plus": {"cantidad": "Pase Elite Plus", "precio": 800},
            "nivel_bundle": {"cantidad": "Bundle Nivel 50", "precio": 1200}
        }
    }
}

# =====================================================
# GESTOR DE BASE DE DATOS
# =====================================================
class DatabaseManager:
    def __init__(self, db_name="gamedin_pedidos.db"):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        """Inicializa la base de datos"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pedidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                producto TEXT,
                cantidad TEXT,
                id_juego TEXT,
                nombre_cliente TEXT,
                contacto_cliente TEXT,
                precio INTEGER,
                fecha DATETIME,
                estado TEXT DEFAULT 'pendiente'
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Base de datos inicializada correctamente")
    
    def guardar_pedido(self, pedido_data):
        """Guarda un pedido en la base de datos"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO pedidos (user_id, username, producto, cantidad, id_juego, 
                               nombre_cliente, contacto_cliente, precio, fecha)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', pedido_data)
        
        pedido_id = cursor.lastrowid
        conn.commit()
        conn.close()
        logger.info(f"Pedido #{pedido_id} guardado correctamente")
        return pedido_id
    
    def obtener_pedidos(self, limit=10):
        """Obtiene los últimos pedidos"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM pedidos ORDER BY fecha DESC LIMIT ?
        ''', (limit,))
        
        pedidos = cursor.fetchall()
        conn.close()
        return pedidos

# Instancia del gestor de base de datos
db = DatabaseManager()

# =====================================================
# FUNCIONES PRINCIPALES
# =====================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /start - Mensaje de bienvenida"""
    user = update.effective_user
    logger.info(f"Usuario {user.first_name} ({user.id}) inició el bot")
    
    welcome_text = f"""
🎮 **¡Bienvenido a GAMEDIN!** 🎮

Hola {user.first_name}, soy tu asistente para compras de Free Fire.

**🔥 ¿Qué puedes comprar aquí?**
• 💎 Diamantes Free Fire
• 🪙 Monedas Free Fire  
• 🎫 Pases de Batalla

**⚡ Proceso súper rápido:**
✅ Entrega inmediata
✅ Precios competitivos
✅ Atención 24/7
✅ Pago seguro

¡Elige una opción para comenzar!
    """
    
    keyboard = [
        [InlineKeyboardButton("🛒 Comprar Ahora", callback_data="hacer_pedido")],
        [InlineKeyboardButton("📋 Ver Productos", callback_data="ver_productos")],
        [InlineKeyboardButton("📞 Contacto", callback_data="contacto")],
        [InlineKeyboardButton("❓ Ayuda", callback_data="ayuda")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def mostrar_productos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra todos los productos disponibles"""
    if update.callback_query:
        await update.callback_query.answer()
        send_method = update.callback_query.message.reply_text
    else:
        send_method = update.message.reply_text
    
    catalog_text = "🎮 **CATÁLOGO GAMEDIN - FREE FIRE** 🎮\n\n"
    
    for key, producto in PRODUCTOS.items():
        catalog_text += f"**{producto['nombre']}**\n"
        catalog_text += f"📝 {producto['descripcion']}\n"
        catalog_text += "💰 **Precios:**\n"
        
        for cant_key, cant_data in producto['cantidades'].items():
            catalog_text += f"   • {cant_data['cantidad']}: ${cant_data['precio']} MXN\n"
        catalog_text += "\n"
    
    catalog_text += "⚡ **Entrega inmediata tras confirmación de pago**\n"
    catalog_text += "🎯 Para comprar, usa el botón 'Comprar Ahora'"
    
    keyboard = [
        [InlineKeyboardButton("🛒 Comprar Ahora", callback_data="hacer_pedido")],
        [InlineKeyboardButton("🏠 Menú Principal", callback_data="menu_principal")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await send_method(
        catalog_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def contacto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Información de contacto"""
    if update.callback_query:
        await update.callback_query.answer()
        send_method = update.callback_query.message.reply_text
    else:
        send_method = update.message.reply_text
    
    contact_text = """
📞 **CONTACTO - GAMEDIN**

🎮 **Tienda Gaming Profesional**
📱 **WhatsApp:** +5547999821527
📘 **Facebook:** Gamedin
🕒 **Horario:** 24 horas disponible

💳 **Métodos de pago:**
• Transferencia bancaria
• Pago móvil
• PayPal (internacional)

⚡ **Entrega:** Inmediata tras confirmación
🛡️ **Garantía:** 100% seguro y confiable

💬 **¿Dudas?**
Contáctanos por WhatsApp o Facebook
    """
    
    keyboard = [
        [InlineKeyboardButton("💬 WhatsApp", url="https://wa.me/5547999821527")],
        [InlineKeyboardButton("🏠 Menú Principal", callback_data="menu_principal")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await send_method(
        contact_text,
        reply_markup=reply_markup
    )

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Información de ayuda"""
    if update.callback_query:
        await update.callback_query.answer()
        send_method = update.callback_query.message.reply_text
    else:
        send_method = update.message.reply_text
    
    help_text = """
❓ **AYUDA - CÓMO COMPRAR**

**📱 Comandos disponibles:**
/start - Menú principal
/productos - Ver catálogo
/comprar - Hacer pedido

**🛒 ¿Cómo comprar?**
1️⃣ Presiona "Comprar Ahora"
2️⃣ Selecciona qué quieres (diamantes/monedas/pases)
3️⃣ Elige la cantidad
4️⃣ Ingresa tu ID de Free Fire
5️⃣ Proporciona tus datos
6️⃣ Confirma y paga

**🆔 ¿Cómo encontrar mi ID de Free Fire?**
• Abre Free Fire
• Ve a tu perfil (esquina superior izquierda)
• Tu ID aparece debajo de tu nickname

**⏰ Tiempo de entrega:**
Inmediato tras confirmar pago

**🔒 ¿Es seguro?**
100% seguro. Solo necesitamos tu ID, no tu contraseña.
    """
    
    keyboard = [
        [InlineKeyboardButton("🏠 Menú Principal", callback_data="menu_principal")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await send_method(
        help_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# =====================================================
# FLUJO DE COMPRAS
# =====================================================

async def iniciar_pedido(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia el proceso de compra"""
    if update.callback_query:
        await update.callback_query.answer()
        send_method = update.callback_query.message.reply_text
        user = update.callback_query.from_user
    else:
        send_method = update.message.reply_text
        user = update.effective_user
    
    logger.info(f"Usuario {user.first_name} ({user.id}) inició una compra")
    
    # Limpiar datos previos
    context.user_data.clear()
    
    selection_text = """
🛒 **COMPRAR - PASO 1/6**

🎮 **¿Qué quieres comprar para Free Fire?**

Selecciona el tipo de producto:
    """
    
    keyboard = []
    for key, producto in PRODUCTOS.items():
        keyboard.append([InlineKeyboardButton(
            producto['nombre'],
            callback_data=f"producto_{key}"
        )])
    
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_compra")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await send_method(
        selection_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return SELECCIONAR_PRODUCTO

async def seleccionar_producto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Maneja la selección del producto"""
    query = update.callback_query
    await query.answer()
    
    producto_key = query.data.replace("producto_", "")
    
    if producto_key in PRODUCTOS:
        context.user_data['producto'] = producto_key
        producto = PRODUCTOS[producto_key]
        
        logger.info(f"Usuario seleccionó producto: {producto['nombre']}")
        
        cantidad_text = f"""
🛒 **COMPRAR - PASO 2/6**

✅ **Seleccionado:** {producto['nombre']}
📝 {producto['descripcion']}

💰 **Selecciona la cantidad:**
        """
        
        keyboard = []
        for cant_key, cant_data in producto['cantidades'].items():
            keyboard.append([InlineKeyboardButton(
                f"{cant_data['cantidad']} - ${cant_data['precio']} MXN",
                callback_data=f"cantidad_{cant_key}"
            )])
        
        keyboard.append([InlineKeyboardButton("⬅️ Cambiar Producto", callback_data="hacer_pedido")])
        keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_compra")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(
            cantidad_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return SELECCIONAR_CANTIDAD
    
    return SELECCIONAR_PRODUCTO

async def seleccionar_cantidad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Maneja la selección de cantidad"""
    query = update.callback_query
    await query.answer()
    
    cantidad_key = query.data.replace("cantidad_", "")
    context.user_data['cantidad_key'] = cantidad_key
    
    producto = PRODUCTOS[context.user_data['producto']]
    cantidad_data = producto['cantidades'][cantidad_key]
    
    logger.info(f"Usuario seleccionó cantidad: {cantidad_data['cantidad']}")
    
    id_text = f"""
🛒 **COMPRAR - PASO 3/6**

✅ **Producto:** {producto['nombre']}
✅ **Cantidad:** {cantidad_data['cantidad']}
✅ **Precio:** ${cantidad_data['precio']} MXN

🆔 **Ingresa tu ID de Free Fire:**

*Ejemplo: 123456789*
*(No compartas tu contraseña, solo el ID)*
    """
    
    keyboard = [
        [InlineKeyboardButton("❓ ¿Cómo encontrar mi ID?", callback_data="ayuda_id")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_compra")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(
        id_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return INGRESAR_ID

async def ayuda_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ayuda para encontrar ID de Free Fire"""
    query = update.callback_query
    await query.answer()
    
    help_id_text = """
🆔 **¿CÓMO ENCONTRAR TU ID DE FREE FIRE?**

📱 **Pasos:**
1️⃣ Abre Free Fire
2️⃣ Toca tu avatar (esquina superior izquierda)
3️⃣ Tu ID aparece debajo de tu nickname
4️⃣ Copia los números (ej: 123456789)

⚠️ **IMPORTANTE:**
• Solo necesitamos el ID numérico
• NUNCA compartas tu contraseña
• El ID son solo números

🔒 **100% Seguro - Solo necesitamos el ID**
    """
    
    keyboard = [
        [InlineKeyboardButton("✅ Entendido", callback_data="volver_id")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(
        help_id_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def volver_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Vuelve al paso de ingresar ID"""
    query = update.callback_query
    await query.answer()
    
    # Obtener datos del contexto para mostrar el resumen
    producto = PRODUCTOS[context.user_data['producto']]
    cantidad_data = producto['cantidades'][context.user_data['cantidad_key']]
    
    id_text = f"""
🛒 **COMPRAR - PASO 3/6**

✅ **Producto:** {producto['nombre']}
✅ **Cantidad:** {cantidad_data['cantidad']}
✅ **Precio:** ${cantidad_data['precio']} MXN

🆔 **Ahora ingresa tu ID de Free Fire:**

*Solo números, ejemplo: 123456789*
*(Recuerda: NO compartas tu contraseña)*
    """
    
    keyboard = [
        [InlineKeyboardButton("❓ ¿Cómo encontrar mi ID?", callback_data="ayuda_id")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_compra")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(
        id_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return INGRESAR_ID

async def ingresar_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Maneja el ingreso del ID"""
    id_juego = update.message.text.strip()
    
    # Validar que sea numérico
    if not id_juego.isdigit() or len(id_juego) < 8:
        await update.message.reply_text(
            "❌ **ID inválido**\n\nEl ID debe ser solo números y tener al menos 8 dígitos.\n\n*Ejemplo: 123456789*"
        )
        return INGRESAR_ID
    
    context.user_data['id_juego'] = id_juego
    logger.info(f"Usuario ingresó ID: {id_juego}")
    
    producto = PRODUCTOS[context.user_data['producto']]
    cantidad_data = producto['cantidades'][context.user_data['cantidad_key']]
    
    nombre_text = f"""
🛒 **COMPRAR - PASO 4/6**

✅ **Producto:** {producto['nombre']}
✅ **Cantidad:** {cantidad_data['cantidad']}
✅ **ID Free Fire:** {id_juego}
✅ **Precio:** ${cantidad_data['precio']} MXN

👤 **Escribe tu nombre completo:**
    """
    
    await update.message.reply_text(
        nombre_text,
        parse_mode='Markdown'
    )
    
    return INGRESAR_NOMBRE

async def ingresar_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Maneja el ingreso del nombre"""
    nombre = update.message.text.strip()
    
    if len(nombre) < 2:
        await update.message.reply_text(
            "❌ Por favor, ingresa tu nombre completo (mínimo 2 caracteres)."
        )
        return INGRESAR_NOMBRE
    
    context.user_data['nombre'] = nombre
    logger.info(f"Usuario ingresó nombre: {nombre}")
    
    contacto_text = f"""
🛒 **COMPRAR - PASO 5/6**

✅ **Nombre:** {nombre}

📱 **Ingresa tu contacto:**
WhatsApp, Telegram, o cualquier forma de contactarte

*Ejemplo: +5511999888777 o @usuario*
    """
    
    await update.message.reply_text(
        contacto_text,
        parse_mode='Markdown'
    )
    
    return INGRESAR_CONTACTO

async def ingresar_contacto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Maneja el ingreso del contacto"""
    contacto = update.message.text.strip()
    
    if len(contacto) < 5:
        await update.message.reply_text(
            "❌ Por favor, proporciona un contacto válido (mínimo 5 caracteres)."
        )
        return INGRESAR_CONTACTO
    
    context.user_data['contacto'] = contacto
    
    # Preparar resumen
    producto = PRODUCTOS[context.user_data['producto']]
    cantidad_data = producto['cantidades'][context.user_data['cantidad_key']]
    
    confirmacion_text = f"""
🛒 **CONFIRMAR COMPRA - PASO 6/6**

**📋 RESUMEN DE TU PEDIDO:**

🎮 **Juego:** Free Fire
🛍️ **Producto:** {producto['nombre']}
💎 **Cantidad:** {cantidad_data['cantidad']}
🆔 **ID Free Fire:** {context.user_data['id_juego']}
👤 **Nombre:** {context.user_data['nombre']}
📱 **Contacto:** {contacto}

**💰 TOTAL A PAGAR: ${cantidad_data['precio']} MXN**

⚡ **Entrega inmediata tras confirmación de pago**

¿Confirmas tu pedido?
    """
    
    keyboard = [
        [InlineKeyboardButton("✅ Confirmar Pedido", callback_data="confirmar_si")],
        [InlineKeyboardButton("✏️ Modificar", callback_data="hacer_pedido")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_compra")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        confirmacion_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return CONFIRMAR_PEDIDO

async def confirmar_pedido(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirma el pedido final"""
    query = update.callback_query
    await query.answer()
    
    if query.data != "confirmar_si":
        return ConversationHandler.END
    
    # Preparar datos del pedido
    user = update.effective_user
    producto = PRODUCTOS[context.user_data['producto']]
    cantidad_data = producto['cantidades'][context.user_data['cantidad_key']]
    
    # Guardar en base de datos
    pedido_data = (
        user.id,
        user.username or "Sin username",
        context.user_data['producto'],
        cantidad_data['cantidad'],
        context.user_data['id_juego'],
        context.user_data['nombre'],
        context.user_data['contacto'],
        cantidad_data['precio'],
        datetime.now()
    )
    
    pedido_id = db.guardar_pedido(pedido_data)
    
    logger.info(f"Pedido #{pedido_id} confirmado para {context.user_data['nombre']}")
    
    # Mensaje de confirmación para el cliente
    confirmacion_cliente = f"""
✅ **¡PEDIDO CONFIRMADO!**

📄 **Número de pedido:** #{pedido_id}
🎮 **Juego:** Free Fire
🛍️ **Producto:** {producto['nombre']}
💎 **Cantidad:** {cantidad_data['cantidad']}
🆔 **ID:** {context.user_data['id_juego']}
💰 **Total:** ${cantidad_data['precio']} MXN

**📋 PRÓXIMOS PASOS:**
1️⃣ Te contactaremos para coordinar el pago
2️⃣ Tras confirmar pago, entrega inmediata
3️⃣ Recibirás tu compra en Free Fire

**📱 CONTACTO:**
WhatsApp: +5355059350

¡Gracias por elegir GAMEDIN! 🎮
    """
    
    keyboard = [
        [InlineKeyboardButton("💬 WhatsApp", url="https://wa.me/5547999821527")],
        [InlineKeyboardButton("🏠 Menú Principal", callback_data="menu_principal")],
        [InlineKeyboardButton("🛒 Nueva Compra", callback_data="hacer_pedido")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(
        confirmacion_cliente,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    # Notificar al grupo de administradores
    try:
        notificacion_admin = f"""
🚨 **NUEVO PEDIDO - GAMEDIN**

📄 **ID:** #{pedido_id}
👤 **Cliente:** {context.user_data['nombre']} (@{user.username or 'Sin username'})
📱 **Contacto:** {context.user_data['contacto']}
📞 **Telegram ID:** {user.id}

**🎮 PEDIDO:**
🛍️ {producto['nombre']}
💎 Cantidad: {cantidad_data['cantidad']}
🆔 ID Free Fire: {context.user_data['id_juego']}

**💰 PAGO:**
Total: ${cantidad_data['precio']} MXN

⏰ {datetime.now().strftime('%d/%m/%Y %H:%M')}

🔥 **PROCESAR Y CONTACTAR AL CLIENTE**
        """
        
        await context.bot.send_message(
            chat_id=GRUPO_PEDIDOS_ID,
            text=notificacion_admin,
            parse_mode='Markdown'
        )
        logger.info(f"Notificación enviada al grupo para pedido #{pedido_id}")
    except Exception as e:
        logger.error(f"Error enviando notificación al grupo: {e}")
    
    # Limpiar datos del usuario
    context.user_data.clear()
    
    return ConversationHandler.END

async def cancelar_compra(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela la compra actual"""
    query = update.callback_query
    await query.answer()
    
    context.user_data.clear()
    logger.info("Compra cancelada por el usuario")
    
    await query.message.reply_text(
        "❌ Compra cancelada.\n\n¿Qué deseas hacer ahora?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Menú Principal", callback_data="menu_principal")],
            [InlineKeyboardButton("🛒 Nueva Compra", callback_data="hacer_pedido")]
        ])
    )
    
    return ConversationHandler.END

async def menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Regresa al menú principal"""
    query = update.callback_query
    await query.answer()
    
    welcome_text = """
🎮 **¡Bienvenido a GAMEDIN!** 🎮

Tu tienda de confianza para Free Fire

**🔥 ¿Qué puedes comprar aquí?**
• 💎 Diamantes Free Fire
• 🪙 Monedas Free Fire  
• 🎫 Pases de Batalla

**⚡ Entrega inmediata • Precios competitivos**

¡Elige una opción para comenzar!
    """
    
    keyboard = [
        [InlineKeyboardButton("🛒 Comprar Ahora", callback_data="hacer_pedido")],
        [InlineKeyboardButton("📋 Ver Productos", callback_data="ver_productos")],
        [InlineKeyboardButton("📞 Contacto", callback_data="contacto")],
        [InlineKeyboardButton("❓ Ayuda", callback_data="ayuda")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# =====================================================
# COMANDOS DE ADMINISTRADOR
# =====================================================

async def admin_pedidos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando para ver pedidos recientes (solo admin)"""
    if str(update.effective_user.id) != ADMIN_ID:
        await update.message.reply_text("❌ No tienes permisos para este comando.")
        return
    
    pedidos = db.obtener_pedidos(10)
    
    if not pedidos:
        await update.message.reply_text("No hay pedidos registrados.")
        return
    
    texto_pedidos = "📊 **ÚLTIMOS 10 PEDIDOS**\n\n"
    
    for pedido in pedidos:
        fecha = datetime.strptime(pedido[9], '%Y-%m-%d %H:%M:%S.%f')
        texto_pedidos += f"**#{pedido[0]}** - {pedido[6]} - ${pedido[8]} MXN\n"
        texto_pedidos += f"🎮 {pedido[4]} - {pedido[3]}\n"
        texto_pedidos += f"📅 {fecha.strftime('%d/%m/%Y %H:%M')}\n\n"
    
    await update.message.reply_text(texto_pedidos, parse_mode='Markdown')

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Estadísticas básicas (solo admin)"""
    if str(update.effective_user.id) != ADMIN_ID:
        await update.message.reply_text("❌ No tienes permisos para este comando.")
        return
    
    conn = sqlite3.connect(db.db_name)
    cursor = conn.cursor()
    
    # Total de pedidos
    cursor.execute("SELECT COUNT(*) FROM pedidos")
    total_pedidos = cursor.fetchone()[0]
    
    # Total de ventas
    cursor.execute("SELECT SUM(precio) FROM pedidos")
    total_ventas = cursor.fetchone()[0] or 0
    
    # Producto más vendido
    cursor.execute("SELECT producto, COUNT(*) as cantidad FROM pedidos GROUP BY producto ORDER BY cantidad DESC LIMIT 1")
    producto_popular = cursor.fetchone()
    
    conn.close()
    
    stats_text = f"""
📊 **ESTADÍSTICAS GAMEDIN**

📦 **Total pedidos:** {total_pedidos}
💰 **Total ventas:** ${total_ventas} MXN
🎮 **Producto más vendido:** {PRODUCTOS[producto_popular[0]]['nombre'] if producto_popular else 'N/A'} ({producto_popular[1] if producto_popular else 0} unidades)

📅 **Última actualización:** {datetime.now().strftime('%d/%m/%Y %H:%M')}
    """
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

# =====================================================
# FUNCIÓN PRINCIPAL
# =====================================================

def main() -> None:
    """Función principal"""
    # Crear la aplicación
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Handler para el flujo de compras
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(iniciar_pedido, pattern="^hacer_pedido$"),
            CommandHandler("comprar", iniciar_pedido)
        ],
        states={
            SELECCIONAR_PRODUCTO: [CallbackQueryHandler(seleccionar_producto, pattern="^producto_")],
            SELECCIONAR_CANTIDAD: [CallbackQueryHandler(seleccionar_cantidad, pattern="^cantidad_")],
            INGRESAR_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ingresar_id),
                CallbackQueryHandler(volver_id, pattern="^volver_id$")
            ],
            INGRESAR_NOMBRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ingresar_nombre)],
            INGRESAR_CONTACTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, ingresar_contacto)],
            CONFIRMAR_PEDIDO: [CallbackQueryHandler(confirmar_pedido, pattern="^confirmar_")]
        },
        fallbacks=[
            CallbackQueryHandler(cancelar_compra, pattern="^cancelar_compra$"),
            CommandHandler("start", start)
        ]
    )
    
    # Agregar handlers
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("productos", mostrar_productos))
    application.add_handler(CommandHandler("ayuda", ayuda))
    application.add_handler(CommandHandler("admin_pedidos", admin_pedidos))
    application.add_handler(CommandHandler("admin_stats", admin_stats))
    
    # Callback query handlers
    application.add_handler(CallbackQueryHandler(mostrar_productos, pattern="^ver_productos$"))
    application.add_handler(CallbackQueryHandler(contacto, pattern="^contacto$"))
    application.add_handler(CallbackQueryHandler(ayuda, pattern="^ayuda$"))
    application.add_handler(CallbackQueryHandler(ayuda_id, pattern="^ayuda_id$"))
    application.add_handler(CallbackQueryHandler(menu_principal, pattern="^menu_principal$"))
    application.add_handler(CallbackQueryHandler(iniciar_pedido, pattern="^hacer_pedido$"))
    # Iniciar el bot
    print("🎮 Bot GAMEDIN iniciando...")
    print("✅ Presiona Ctrl+C para detener")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

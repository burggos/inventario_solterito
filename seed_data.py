"""
Seed script: Popula la base de datos con datos realistas desde 2015.
Ejecutar con: python manage.py shell < seed_data.py
"""
import os, sys, django, random, math
from datetime import date, datetime, timedelta
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'solterito_inventario.settings')
django.setup()

from django.utils import timezone
from django.db.models import Sum, F
from inventario.models import (
    Categoria, Producto, Movimiento, Proveedor,
    OrdenCompra, DetalleCompra, Venta, DetalleVenta
)

random.seed(42)

print("=" * 60)
print("  SEED DATA — El Solterito (2015 → 2026)")
print("=" * 60)

# ── Limpiar datos existentes (orden importa por FK) ──
print("\n[1/7] Limpiando datos existentes...")
DetalleVenta.objects.all().delete()
Venta.objects.all().delete()
DetalleCompra.objects.all().delete()
OrdenCompra.objects.all().delete()
Movimiento.objects.all().delete()
Producto.objects.all().delete()
Proveedor.objects.all().delete()
Categoria.objects.all().delete()
print("  ✔ Base de datos limpia")

# ── 1. Categorías ──
print("\n[2/7] Creando categorías...")
CATEGORIAS = [
    ("Lácteos", "Leche, queso, yogurt y derivados"),
    ("Bebidas", "Gaseosas, jugos, agua y licores"),
    ("Carnes y Embutidos", "Res, pollo, cerdo, jamón, salchichas"),
    ("Frutas y Verduras", "Frutas frescas, hortalizas, tubérculos"),
    ("Abarrotes", "Arroz, pasta, aceite, azúcar, granos"),
    ("Panadería", "Pan, galletas, tortas, hojaldres"),
    ("Aseo Personal", "Jabón, shampoo, crema dental"),
    ("Limpieza", "Detergente, cloro, desinfectante"),
    ("Snacks", "Papas, dulces, chocolates, chicles"),
    ("Congelados", "Helados, pizza, empanadas congeladas"),
]
cats = {}
for nombre, desc in CATEGORIAS:
    cats[nombre] = Categoria.objects.create(nombre=nombre, descripcion=desc)
print(f"  ✔ {len(cats)} categorías creadas")

# ── 2. Proveedores ──
print("\n[3/7] Creando proveedores...")
PROVEEDORES = [
    ("Distribuidora Andina S.A.", "andina@email.com", "3001234567", "Bogotá", "900123456-1", "Carlos Ruiz"),
    ("Lácteos del Valle", "ventas@lacteosv.com", "3109876543", "Cali", "800987654-2", "María López"),
    ("Frigorífico Nacional", "comercial@frigonal.co", "3205554433", "Medellín", "900555443-3", "Pedro Gómez"),
    ("Agrícola La Huerta", "pedidos@lahuerta.co", "3157778899", "Bucaramanga", "800777889-4", "Ana Martínez"),
    ("Importadora del Caribe", "importaciones@caribe.co", "3006667788", "Barranquilla", "900666778-5", "Luis Torres"),
    ("Panadería Industrial San José", "pedidos@sanjose.co", "3118889900", "Bogotá", "800888990-6", "Rosa Díaz"),
    ("Distribuidora Limpieza Total", "ventas@limpiezatotal.co", "3209990011", "Medellín", "900999001-7", "Jorge Vargas"),
    ("Snacks Colombia S.A.S.", "compras@snackscol.co", "3001112233", "Cali", "800111223-8", "Diana Peña"),
]
provs = []
for nombre, email, tel, ciudad, ruc, contacto in PROVEEDORES:
    p = Proveedor.objects.create(
        nombre=nombre, email=email, telefono=tel,
        direccion=f"Calle {random.randint(10,150)} #{random.randint(1,99)}-{random.randint(1,99)}, {ciudad}",
        ciudad=ciudad, ruc=ruc, contacto_principal=contacto, activo=True,
        terminos_pago=random.choice(["30 días", "60 días", "Contado", "15 días"])
    )
    provs.append(p)
print(f"  ✔ {len(provs)} proveedores creados")

# ── 3. Productos ──
print("\n[4/7] Creando productos...")
PRODUCTOS_DATA = [
    # (nombre, categoria, precio_venta, precio_costo, stock_min)
    ("Leche entera 1L", "Lácteos", 4500, 3200, 20),
    ("Queso campesino 500g", "Lácteos", 12000, 8500, 10),
    ("Yogurt natural 1L", "Lácteos", 6500, 4800, 15),
    ("Mantequilla 250g", "Lácteos", 5800, 4200, 10),
    ("Queso doble crema 1kg", "Lácteos", 22000, 16000, 8),
    ("Coca-Cola 2.5L", "Bebidas", 7500, 5500, 25),
    ("Agua cristal 600ml", "Bebidas", 2000, 1200, 40),
    ("Jugo Hit 1L", "Bebidas", 4200, 3000, 20),
    ("Cerveza Poker Six Pack", "Bebidas", 18000, 13500, 15),
    ("Gaseosa Colombiana 1.5L", "Bebidas", 5000, 3600, 20),
    ("Pechuga de pollo kg", "Carnes y Embutidos", 16000, 12000, 10),
    ("Carne molida kg", "Carnes y Embutidos", 18500, 14000, 8),
    ("Jamón tajado 500g", "Carnes y Embutidos", 12500, 9000, 10),
    ("Salchichas x12", "Carnes y Embutidos", 9500, 7000, 12),
    ("Chorizo santarrosano 500g", "Carnes y Embutidos", 14000, 10000, 8),
    ("Tomate kg", "Frutas y Verduras", 4000, 2500, 15),
    ("Cebolla kg", "Frutas y Verduras", 3500, 2200, 15),
    ("Papa criolla kg", "Frutas y Verduras", 5000, 3500, 20),
    ("Plátano maduro kg", "Frutas y Verduras", 3000, 1800, 20),
    ("Aguacate Hass unidad", "Frutas y Verduras", 5500, 3500, 15),
    ("Arroz Diana 5kg", "Abarrotes", 18000, 13000, 20),
    ("Aceite Girasol 3L", "Abarrotes", 28000, 21000, 10),
    ("Azúcar 2.5kg", "Abarrotes", 8500, 6000, 15),
    ("Lentejas 500g", "Abarrotes", 4500, 3000, 15),
    ("Pasta Doria 500g", "Abarrotes", 3500, 2500, 20),
    ("Fríjoles rojos 500g", "Abarrotes", 5000, 3500, 15),
    ("Sal Refisal 1kg", "Abarrotes", 2000, 1200, 20),
    ("Pan tajado Bimbo", "Panadería", 7500, 5500, 15),
    ("Galletas Festival x12", "Panadería", 8000, 5800, 12),
    ("Mogolla paquete x6", "Panadería", 4000, 2800, 15),
    ("Ponqué Ramo", "Panadería", 3500, 2200, 15),
    ("Jabón Protex 3 pack", "Aseo Personal", 12000, 8500, 10),
    ("Shampoo H&S 375ml", "Aseo Personal", 18000, 13000, 8),
    ("Crema dental Colgate 150ml", "Aseo Personal", 8500, 6000, 10),
    ("Desodorante Rexona", "Aseo Personal", 14000, 10000, 8),
    ("Detergente Fab 3kg", "Limpieza", 22000, 16000, 10),
    ("Cloro Clorox 1L", "Limpieza", 6000, 4200, 15),
    ("Jabón en barra Rey x3", "Limpieza", 5500, 3800, 12),
    ("Suavizante Suavitel 1L", "Limpieza", 9000, 6500, 10),
    ("Papas Margarita personal", "Snacks", 2500, 1700, 30),
    ("Chocolate Jet x6", "Snacks", 5000, 3500, 20),
    ("Chiclets Adams x3", "Snacks", 3000, 2000, 20),
    ("Galletas Oreo x4", "Snacks", 7000, 5000, 15),
    ("Chocoramo", "Snacks", 2000, 1300, 25),
    ("Helado Crem Helado 1L", "Congelados", 14000, 10000, 8),
    ("Pizza congelada familiar", "Congelados", 16000, 11000, 6),
    ("Empanadas congeladas x10", "Congelados", 12000, 8500, 8),
    ("Nuggets de pollo 500g", "Congelados", 15000, 11000, 8),
]

productos = []
for nombre, cat_name, precio, costo, stock_min in PRODUCTOS_DATA:
    prod = Producto(
        nombre=nombre,
        categoria=cats[cat_name],
        precio=Decimal(str(precio)),          # Campo base (sincronizado con precio_venta)
        precio_venta=Decimal(str(precio)),
        precio_compra=Decimal(str(costo)),
        stock=0,  # Se irá ajustando con movimientos
        stock_minimo=stock_min,
        activo=True,
        descripcion=f"Producto de {cat_name.lower()}"
    )
    prod.save()
    # Guardar costo como atributo temporal para el script
    prod._costo = costo
    productos.append(prod)
print(f"  ✔ {len(productos)} productos creados")

# ── 4. Movimientos (entradas/salidas) desde 2015 ──
print("\n[5/7] Generando movimientos de inventario (2015-2026)...")
START_DATE = date(2015, 1, 1)
END_DATE = date(2026, 4, 19)  # Hoy

# Para no disparar signals que actualicen stock, vamos a crear movimientos
# y luego ajustar el stock manualmente al final
# Stock se actualiza directamente en Movimiento.save(); no hay signal que desconectar.

movimientos_creados = 0
stock_tracker = {p.pk: 0 for p in productos}

CLIENTES = [
    "María García", "Juan Rodríguez", "Carlos Hernández", "Ana Martínez",
    "Pedro Sánchez", "Laura Gómez", "Diego López", "Carmen Torres",
    "Andrés Díaz", "Sofía Ramírez", "Luis Morales", "Patricia Castillo",
    "Roberto Vargas", "Elena Fernández", "Miguel Rojas", "Camila Restrepo",
    "José Parra", "Valentina Cruz", "Fernando Muñoz", "Daniela Ortiz",
    "Cliente General", "Cliente General", "Cliente General",  # Peso extra
]

VENDEDORES = ["Admin", "Carlos V.", "María L.", "Pedro G."]

# Generar datos mes a mes para distribución realista
current = START_DATE
mes_num = 0

# Tendencia de crecimiento: ventas suben gradualmente de 2015 a 2026
# con estacionalidad (diciembre alto, enero bajo)
def get_month_factor(year, month):
    """Factor de actividad por mes. Simula crecimiento + estacionalidad."""
    # Crecimiento anual ~8%
    year_factor = 1.0 + (year - 2015) * 0.08
    # Estacionalidad
    seasonal = {
        1: 0.7, 2: 0.75, 3: 0.85, 4: 0.9, 5: 0.95, 6: 1.0,
        7: 0.9, 8: 0.85, 9: 0.95, 10: 1.0, 11: 1.1, 12: 1.4
    }
    return year_factor * seasonal.get(month, 1.0)

ventas_bulk = []
detalles_venta_bulk = []
ordenes_bulk = []
detalles_compra_bulk = []
movimientos_bulk = []
venta_counter = 0
oc_counter = 0

while current <= END_DATE:
    year = current.year
    month = current.month
    factor = get_month_factor(year, month)
    
    # Calcular último día del mes
    if month == 12:
        last_day = date(year, 12, 31)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)
    if last_day > END_DATE:
        last_day = END_DATE
    
    days_in_month = (last_day - current).days + 1
    
    # ── Compras/Entradas: 2-5 órdenes de compra por mes ──
    num_compras = max(1, int(random.gauss(3, 1) * min(factor, 2.5)))
    for _ in range(num_compras):
        dia_compra = current + timedelta(days=random.randint(0, max(days_in_month - 1, 0)))
        proveedor = random.choice(provs)
        oc_counter += 1
        
        # Seleccionar 3-8 productos para la orden
        num_items = random.randint(3, min(8, len(productos)))
        items = random.sample(productos, num_items)
        total_oc = Decimal('0')
        
        oc = OrdenCompra(
            numero=f"OC-{oc_counter:06d}",
            proveedor=proveedor,
            estado='completada',
            notas=f"Compra regular de {proveedor.nombre}",
            usuario_creador=random.choice(VENDEDORES),
            total=Decimal('0'),
        )
        oc.save()
        # Override fecha_creacion
        OrdenCompra.objects.filter(pk=oc.pk).update(
            fecha_creacion=timezone.make_aware(datetime.combine(dia_compra, datetime.min.time().replace(hour=random.randint(7, 12))))
        )
        
        for prod in items:
            qty = random.randint(5, int(40 * min(factor, 3)))
            precio_u = Decimal(str(prod._costo)) * Decimal(str(random.uniform(0.9, 1.1)))
            precio_u = precio_u.quantize(Decimal('0.01'))
            subtotal = qty * precio_u
            total_oc += subtotal
            
            dc = DetalleCompra(
                orden_compra=oc,
                producto=prod,
                cantidad_solicitada=qty,
                cantidad_recibida=qty,
                precio_unitario=precio_u,
                subtotal=subtotal,
            )
            dc.save()
            
            # Movimiento de entrada
            hora = random.randint(7, 18)
            minuto = random.randint(0, 59)
            fecha_mov = timezone.make_aware(
                datetime.combine(dia_compra, datetime.min.time().replace(hour=hora, minute=minuto))
            )
            mov = Movimiento(
                producto=prod,
                tipo='entrada',
                cantidad=qty,
                fecha=fecha_mov,
                descripcion=f"Entrada por OC-{oc_counter:06d}",
                usuario=random.choice(VENDEDORES),
            )
            mov.save()
            movimientos_creados += 1
            stock_tracker[prod.pk] += qty
        
        OrdenCompra.objects.filter(pk=oc.pk).update(total=total_oc)
    
    # ── Ventas: 10-40 ventas por mes (crecimiento progresivo) ──
    base_ventas = int(15 * factor)
    num_ventas = max(3, int(random.gauss(base_ventas, base_ventas * 0.2)))
    
    for _ in range(num_ventas):
        dia_venta = current + timedelta(days=random.randint(0, max(days_in_month - 1, 0)))
        venta_counter += 1
        
        forma_pago = random.choices(
            ['efectivo', 'tarjeta', 'transferencia', 'credito'],
            weights=[50, 25, 15, 10]
        )[0]
        
        cliente = random.choice(CLIENTES)
        vendedor = random.choice(VENDEDORES)
        
        # 1-5 productos por venta
        num_items = random.choices([1, 2, 3, 4, 5], weights=[30, 35, 20, 10, 5])[0]
        items = random.sample(productos, min(num_items, len(productos)))
        
        total_venta = Decimal('0')
        detalles_temp = []
        venta_valida = True
        
        for prod in items:
            # Cantidad: 1-5 unidades
            qty = random.randint(1, 5)
            
            # Verificar stock disponible
            if stock_tracker[prod.pk] < qty:
                if stock_tracker[prod.pk] > 0:
                    qty = stock_tracker[prod.pk]
                else:
                    continue
            
            # Precio con posible descuento
            descuento = random.choices(
                [Decimal('0'), Decimal('5'), Decimal('10'), Decimal('15')],
                weights=[70, 15, 10, 5]
            )[0]
            precio_venta_prod = prod.precio_venta or prod.precio
            subtotal = (qty * precio_venta_prod) * (1 - descuento / 100)
            total_venta += subtotal
            
            detalles_temp.append({
                'producto': prod,
                'cantidad': qty,
                'precio_unitario': precio_venta_prod,
                'descuento_porcentaje': descuento,
                'subtotal': subtotal,
            })
            stock_tracker[prod.pk] -= qty
        
        if not detalles_temp:
            continue
        
        hora = random.randint(7, 21)
        minuto = random.randint(0, 59)
        
        # Determinar estado (98% completada, 2% cancelada)
        estado = random.choices(['completada', 'cancelada'], weights=[98, 2])[0]
        if estado == 'cancelada':
            # Devolver stock
            for d in detalles_temp:
                stock_tracker[d['producto'].pk] += d['cantidad']
        
        venta = Venta(
            numero=f"V-{venta_counter:06d}",
            cliente_nombre=cliente,
            estado=estado,
            total=total_venta,
            forma_pago=forma_pago,
            notas="" if random.random() > 0.1 else random.choice([
                "Entrega a domicilio", "Cliente frecuente", "Pago parcial",
                "Pedido telefónico", "Compra corporativa"
            ]),
            usuario_vendedor=vendedor,
        )
        venta.save()
        # Override fecha_venta
        Venta.objects.filter(pk=venta.pk).update(
            fecha_venta=timezone.make_aware(
                datetime.combine(dia_venta, datetime.min.time().replace(hour=hora, minute=minuto))
            )
        )
        
        for d in detalles_temp:
            dv = DetalleVenta(
                venta=venta,
                producto=d['producto'],
                cantidad=d['cantidad'],
                precio_unitario=d['precio_unitario'],
                descuento_porcentaje=d['descuento_porcentaje'],
                subtotal=d['subtotal'],
            )
            dv.save()
            
            # Movimiento de salida (solo si completada)
            if estado == 'completada':
                mov = Movimiento(
                    producto=d['producto'],
                    tipo='salida',
                    cantidad=d['cantidad'],
                    fecha=timezone.make_aware(
                        datetime.combine(dia_venta, datetime.min.time().replace(hour=hora, minute=minuto + 1 if minuto < 59 else minuto))
                    ),
                    descripcion=f"Venta V-{venta_counter:06d}",
                    usuario=vendedor,
                )
                mov.save()
                movimientos_creados += 1
    
    # Avanzar al siguiente mes
    if month == 12:
        current = date(year + 1, 1, 1)
    else:
        current = date(year, month + 1, 1)

print(f"  ✔ {movimientos_creados} movimientos creados")
print(f"  ✔ {venta_counter} ventas generadas")
print(f"  ✔ {oc_counter} órdenes de compra generadas")

# ── 6. Ajustar stock final de productos ──
print("\n[6/7] Ajustando stock final de productos...")
for prod in productos:
    final_stock = max(stock_tracker[prod.pk], 0)
    Producto.objects.filter(pk=prod.pk).update(stock=final_stock)
print("  ✔ Stock actualizado según movimientos")

# Signal ya no existe; no hay nada que reconectar.

# ── 7. Resumen ──
print("\n[7/7] Resumen final:")
print(f"  Categorías:       {Categoria.objects.count()}")
print(f"  Proveedores:      {Proveedor.objects.count()}")
print(f"  Productos:        {Producto.objects.count()}")
print(f"  Movimientos:      {Movimiento.objects.count()}")
print(f"  Ventas:           {Venta.objects.count()}")
print(f"  Detalles Venta:   {DetalleVenta.objects.count()}")
print(f"  Órdenes Compra:   {OrdenCompra.objects.count()}")
print(f"  Detalles Compra:  {DetalleCompra.objects.count()}")

total_inv = Producto.objects.filter(activo=True).aggregate(
    total=Sum(F('precio') * F('stock'))
)['total'] or 0
total_ventas = Venta.objects.filter(estado='completada').aggregate(t=Sum('total'))['t'] or 0
print(f"\n  Valor inventario actual: COP {total_inv:,.0f}")
print(f"  Total ventas históricas: COP {total_ventas:,.0f}")
print("\n" + "=" * 60)
print("  ✅ Seed completado exitosamente")
print("=" * 60)

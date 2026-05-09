from django import forms
from .models import Movimiento, Producto

class ProductoForm(forms.ModelForm):
    """Form for CREATING products. Includes stock_inicial which routes through Movimiento."""
    stock_inicial = forms.IntegerField(
        min_value=0, initial=0, required=False,
        label='Stock inicial',
        help_text='Se registrará como movimiento de entrada',
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-100 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 dark:placeholder-gray-400',
            'placeholder': '0'
        }),
    )

    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'categoria', 'precio', 'stock_minimo', 'imagen', 'codigo_barras']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-100 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 dark:placeholder-gray-400',
                'placeholder': 'Ej. Leche Entera'
            }),
            'descripcion': forms.Textarea(attrs={
                'rows': 3,
                'class': 'mt-1 block w-full rounded-md border-gray-100 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 dark:placeholder-gray-400',
                'placeholder': 'Descripción del producto...'
            }),
            'categoria': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-100 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200'
            }),
            'precio': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-100 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 dark:placeholder-gray-400',
                'placeholder': 'Ej. 10000 (COP)'
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-100 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 dark:placeholder-gray-400',
                'placeholder': '0'
            }),
            'stock_minimo': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-100 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 dark:placeholder-gray-400',
                'placeholder': '5'
            }),
            'codigo_barras': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-100 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 dark:placeholder-gray-400',
                'placeholder': 'Ej. 7891234567890'
            }),
            'imagen': forms.FileInput(attrs={
                'class': 'mt-1 block w-full text-sm text-gray-500 dark:text-gray-300 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary file:text-white hover:file:bg-teal-800 dark:file:bg-gray-600 dark:file:text-white dark:hover:file:bg-teal-700'
            }),
        }

class MovimientoForm(forms.ModelForm):
    """Form for manual inventory adjustments only. Sales/purchases go through POS."""
    class Meta:
        model = Movimiento
        fields = ['producto', 'tipo', 'cantidad', 'descripcion']
        widgets = {
            'descripcion': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Ej: Ajuste por conteo físico, merma, daño...',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['descripcion'].required = True
        self.fields['descripcion'].help_text = 'Obligatorio: describe el motivo del ajuste'
        input_cls = 'w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 dark:bg-gray-700 dark:text-white transition'
        for name in self.fields:
            self.fields[name].widget.attrs.setdefault('class', '')
            self.fields[name].widget.attrs['class'] = input_cls
    
    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        cantidad = cleaned_data.get('cantidad')
        producto = cleaned_data.get('producto')
        
        if tipo == 'salida' and producto and cantidad:
            if producto.stock < cantidad:
                raise forms.ValidationError(f'Stock insuficiente. Stock actual: {producto.stock}')


class ProductoEditForm(forms.ModelForm):
    """Form for EDITING products. Stock is read-only (managed via movements)."""
    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'categoria', 'precio', 'stock_minimo', 'imagen', 'codigo_barras']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-100 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 dark:placeholder-gray-400',
                'placeholder': 'Ej. Leche Entera'
            }),
            'descripcion': forms.Textarea(attrs={
                'rows': 3,
                'class': 'mt-1 block w-full rounded-md border-gray-100 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 dark:placeholder-gray-400',
                'placeholder': 'Descripción del producto...'
            }),
            'categoria': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-100 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200'
            }),
            'precio': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-100 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 dark:placeholder-gray-400',
                'placeholder': 'Ej. 10000 (COP)'
            }),
            'stock_minimo': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-100 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 dark:placeholder-gray-400',
                'placeholder': '5'
            }),
            'codigo_barras': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-100 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 dark:placeholder-gray-400',
                'placeholder': 'Ej. 7891234567890'
            }),
            'imagen': forms.FileInput(attrs={
                'class': 'mt-1 block w-full text-sm text-gray-500 dark:text-gray-300 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary file:text-white hover:file:bg-teal-800 dark:file:bg-gray-600 dark:file:text-white dark:hover:file:bg-teal-700'
            }),
        }


# ============================================================================
# FORMULARIOS PARA VENTAS Y COMPRAS
# ============================================================================

from .models import Proveedor, Cliente, OrdenCompra, DetalleCompra, Venta, DetalleVenta


class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre', 'email', 'telefono', 'direccion', 'ciudad', 'ruc', 'contacto_principal', 'terminos_pago', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 dark:bg-gray-700 dark:text-white', 'placeholder': 'Nombre del proveedor'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 dark:bg-gray-700 dark:text-white', 'placeholder': 'correo@ejemplo.com'}),
            'telefono': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 dark:bg-gray-700 dark:text-white', 'placeholder': '+56912345678'}),
            'direccion': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 dark:bg-gray-700 dark:text-white', 'rows': 3}),
            'ciudad': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 dark:bg-gray-700 dark:text-white'}),
            'ruc': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 dark:bg-gray-700 dark:text-white'}),
            'contacto_principal': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 dark:bg-gray-700 dark:text-white'}),
            'terminos_pago': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 dark:bg-gray-700 dark:text-white', 'rows': 3}),
            'activo': forms.CheckboxInput(attrs={'class': 'h-4 w-4'}),
        }


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            'nombre', 'documento', 'email', 'telefono', 'activo',
            'descuento_fijo', 'descuento_temporal', 'descuento_temporal_inicio',
            'descuento_temporal_fin', 'descuento_fidelidad', 'umbral_fidelidad',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:text-white'}),
            'documento': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:text-white'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:text-white'}),
            'telefono': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:text-white'}),
            'descuento_fijo': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:text-white', 'min': 0, 'max': 100, 'step': '0.01'}),
            'descuento_temporal': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:text-white', 'min': 0, 'max': 100, 'step': '0.01'}),
            'descuento_temporal_inicio': forms.DateInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:text-white', 'type': 'date'}),
            'descuento_temporal_fin': forms.DateInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:text-white', 'type': 'date'}),
            'descuento_fidelidad': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:text-white', 'min': 0, 'max': 100, 'step': '0.01'}),
            'umbral_fidelidad': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:text-white', 'min': 1}),
            'activo': forms.CheckboxInput(attrs={'class': 'h-4 w-4'}),
        }


class OrdenCompraForm(forms.ModelForm):
    class Meta:
        model = OrdenCompra
        fields = ['proveedor', 'fecha_entrega_esperada', 'estado', 'notas']
        widgets = {
            'proveedor': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 dark:bg-gray-700 dark:text-white'}),
            'fecha_entrega_esperada': forms.DateInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 dark:bg-gray-700 dark:text-white', 'type': 'date'}),
            'estado': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 dark:bg-gray-700 dark:text-white'}),
            'notas': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 dark:bg-gray-700 dark:text-white', 'rows': 3}),
        }


class DetalleCompraForm(forms.ModelForm):
    class Meta:
        model = DetalleCompra
        fields = ['producto', 'cantidad_solicitada', 'precio_unitario']
        widgets = {
            'producto': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 dark:bg-gray-700 dark:text-white'}),
            'cantidad_solicitada': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 dark:bg-gray-700 dark:text-white', 'min': '1'}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 dark:bg-gray-700 dark:text-white', 'step': '0.01'}),
        }


class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ['cliente', 'cliente_nombre', 'forma_pago', 'estado', 'notas']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 dark:bg-gray-700 dark:text-white'}),
            'cliente_nombre': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 dark:bg-gray-700 dark:text-white', 'placeholder': 'Nombre del cliente'}),
            'forma_pago': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 dark:bg-gray-700 dark:text-white'}),
            'estado': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 dark:bg-gray-700 dark:text-white'}),
            'notas': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 dark:bg-gray-700 dark:text-white', 'rows': 3}),
        }


class DetalleVentaForm(forms.ModelForm):
    class Meta:
        model = DetalleVenta
        fields = ['producto', 'cantidad', 'precio_unitario', 'descuento_porcentaje']
        widgets = {
            'producto': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 dark:bg-gray-700 dark:text-white'}),
            'cantidad': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 dark:bg-gray-700 dark:text-white', 'min': '1'}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 dark:bg-gray-700 dark:text-white', 'step': '0.01'}),
            'descuento_porcentaje': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 dark:bg-gray-700 dark:text-white', 'step': '0.01', 'min': '0'}),
        }
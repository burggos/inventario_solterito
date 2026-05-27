from django import forms
from django.contrib.auth.models import User, Group
from django.db.models import Q
from .models import Movimiento, Producto, Categoria, Proveedor

INPUT_CLS = 'mt-1 block w-full rounded-md border-gray-100 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 dark:placeholder-gray-400'

ROLES = [
    ('Administrador', 'Administrador'),
    ('Vendedor', 'Vendedor'),
    ('Bodeguero', 'Bodeguero'),
]

# Módulos configurables por rol (codename, etiqueta)
MODULOS = [
    ('ver_productos',   'Productos'),
    ('ver_clientes',    'Clientes'),
    ('ver_proveedores', 'Proveedores'),
    ('ver_ventas',      'Ventas'),
    ('ver_compras',     'Compras'),
    ('ver_movimientos', 'Movimientos / Ajuste de inventario'),
    ('ver_reportes',    'Reportes'),
]


class RolForm(forms.Form):
    nombre = forms.CharField(
        label='Nombre del rol',
        max_length=80,
        widget=forms.TextInput(attrs={'class': INPUT_CLS, 'placeholder': 'Ej: Supervisor, Cajero...', 'autocomplete': 'off'}),
    )
    modulos = forms.MultipleChoiceField(
        label='Módulos visibles',
        choices=MODULOS,
        required=False,
        widget=forms.CheckboxSelectMultiple(),
    )

    def __init__(self, *args, group_instance=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._group_instance = group_instance

    def clean_nombre(self):
        from django.contrib.auth.models import Group
        nombre = self.cleaned_data['nombre'].strip()
        qs = Group.objects.filter(name__iexact=nombre)
        if self._group_instance:
            qs = qs.exclude(pk=self._group_instance.pk)
        if qs.exists():
            raise forms.ValidationError('Ya existe un rol con ese nombre.')
        return nombre


class CrearUsuarioForm(forms.Form):
    username = forms.CharField(
        label='Nombre de usuario',
        widget=forms.TextInput(attrs={'class': INPUT_CLS, 'placeholder': 'ej. maria.lopez', 'autocomplete': 'off'}),
    )
    first_name = forms.CharField(
        label='Nombre', required=False,
        widget=forms.TextInput(attrs={'class': INPUT_CLS, 'placeholder': 'Nombre'}),
    )
    last_name = forms.CharField(
        label='Apellido', required=False,
        widget=forms.TextInput(attrs={'class': INPUT_CLS, 'placeholder': 'Apellido'}),
    )
    rol = forms.ChoiceField(
        label='Rol',
        choices=ROLES,
        widget=forms.Select(attrs={'class': INPUT_CLS}),
    )
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'class': INPUT_CLS, 'autocomplete': 'new-password'}),
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={'class': INPUT_CLS, 'autocomplete': 'new-password'}),
    )

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Ya existe un usuario con ese nombre.')
        return username

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        return cleaned_data


class EditarUsuarioForm(forms.Form):
    first_name = forms.CharField(
        label='Nombre', required=False,
        widget=forms.TextInput(attrs={'class': INPUT_CLS}),
    )
    last_name = forms.CharField(
        label='Apellido', required=False,
        widget=forms.TextInput(attrs={'class': INPUT_CLS}),
    )
    rol = forms.ChoiceField(
        label='Rol',
        choices=ROLES,
        widget=forms.Select(attrs={'class': INPUT_CLS}),
    )
    is_active = forms.BooleanField(
        label='Usuario activo', required=False,
        widget=forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-teal-600 focus:ring-teal-500'}),
    )
    password1 = forms.CharField(
        label='Nueva contraseña', required=False,
        help_text='Déjalo en blanco para no cambiarla.',
        widget=forms.PasswordInput(attrs={'class': INPUT_CLS, 'autocomplete': 'new-password', 'placeholder': 'Sin cambios'}),
    )
    password2 = forms.CharField(
        label='Confirmar nueva contraseña', required=False,
        widget=forms.PasswordInput(attrs={'class': INPUT_CLS, 'autocomplete': 'new-password', 'placeholder': 'Sin cambios'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        return cleaned_data


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': INPUT_CLS, 'placeholder': 'Ej: Lácteos, Bebidas...'}),
            'descripcion': forms.Textarea(attrs={'class': INPUT_CLS, 'rows': 3, 'placeholder': 'Descripción opcional...'}),
        }

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
        fields = ['nombre', 'descripcion', 'categoria', 'proveedor', 'precio_compra', 'precio_venta', 'stock_minimo']
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
            'proveedor': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-100 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200'
            }),
            'precio_compra': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-100 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 dark:placeholder-gray-400',
                'placeholder': 'Ej. 8000 (COP)',
                'step': '0.01',
            }),
            'precio_venta': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-100 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 dark:placeholder-gray-400',
                'placeholder': 'Ej. 12000 (COP)',
                'step': '0.01',
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
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['proveedor'].queryset = Proveedor.objects.filter(activo=True).order_by('nombre')
        self.fields['proveedor'].required = False
        self.similares_sugeridos = []

    def save(self, commit=True):
        producto = super().save(commit=False)
        # precio (campo requerido del modelo) se sincroniza con precio_venta o precio_compra
        producto.precio = producto.precio_venta or producto.precio_compra or producto.precio or 0
        if commit:
            producto.save()
        return producto

    def clean_nombre(self):
        nombre = (self.cleaned_data.get('nombre') or '').strip()
        if not nombre:
            return nombre

        exacto = Producto.objects.filter(nombre__iexact=nombre, activo=True).first()
        if exacto:
            raise forms.ValidationError(
                f'Ya existe un producto activo con el mismo nombre: "{exacto.nombre}". Revisa el catálogo antes de crear otro.'
            )

        filtros = Q(nombre__icontains=nombre)
        for token in [t for t in nombre.split() if len(t) >= 3]:
            filtros |= Q(nombre__icontains=token)

        similares = list(
            Producto.objects.filter(activo=True)
            .filter(filtros)
            .values_list('nombre', flat=True)
            .distinct()[:3]
        )
        self.similares_sugeridos = similares

        return nombre

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
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['descripcion'].required = True
        self.fields['descripcion'].help_text = 'Obligatorio: describe el motivo del ajuste'
        # Los bodegueros no pueden crear movimientos de tipo ajuste.
        if self.user and not self.user.is_superuser and not self.user.groups.filter(name='Administrador').exists():
            self.fields['tipo'].choices = [
                (value, label) for value, label in self.fields['tipo'].choices if value != 'ajuste'
            ]
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

        if (
            tipo == 'ajuste'
            and self.user
            and not self.user.is_superuser
            and not self.user.groups.filter(name='Administrador').exists()
        ):
            raise forms.ValidationError('No tienes permisos para registrar ajustes de inventario.')


class ProductoEditForm(forms.ModelForm):
    """Form for EDITING products. Stock is read-only (managed via movements)."""
    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'categoria', 'proveedor', 'precio', 'stock_minimo', 'imagen', 'codigo_barras']
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
            'proveedor': forms.Select(attrs={
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['proveedor'].queryset = Proveedor.objects.filter(activo=True).order_by('nombre')
        self.fields['proveedor'].required = False


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
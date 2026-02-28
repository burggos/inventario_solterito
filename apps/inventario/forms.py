from django import forms
from .models import Movimiento, Producto
from .models import Producto

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'categoria', 'precio', 'stock', 'stock_minimo', 'imagen', 'codigo_barras']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-100 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50',
                'placeholder': 'Ej. Leche Entera'
            }),
            'descripcion': forms.Textarea(attrs={
                'rows': 3,
                'class': 'mt-1 block w-full rounded-md border-gray-100 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50',
                'placeholder': 'Descripción del producto...'
            }),
            'categoria': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-100 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50'
            }),
            'precio': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-100 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50',
                'placeholder': '0.00'
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-100 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50',
                'placeholder': '0'
            }),
            'stock_minimo': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-100 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50',
                'placeholder': '5'
            }),
            'codigo_barras': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-100 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50',
                'placeholder': 'Ej. 7891234567890'
            }),
            'imagen': forms.FileInput(attrs={
                'class': 'mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary file:text-white hover:file:bg-teal-800'
            }),
        }

class MovimientoForm(forms.ModelForm):
    class Meta:
        model = Movimiento
        fields = ['producto', 'tipo', 'cantidad', 'descripcion']
    
    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        cantidad = cleaned_data.get('cantidad')
        producto = cleaned_data.get('producto')
        
        if tipo == 'salida' and producto and cantidad:
            if producto.stock < cantidad:
                raise forms.ValidationError(f'Stock insuficiente. Stock actual: {producto.stock}')
        return cleaned_data
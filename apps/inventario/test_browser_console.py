"""
Test para analizar errores en todas las páginas.
Ejecutar: python manage.py test apps.inventario.test_browser_console
"""

import re
import json
from django.test import TestCase, Client
from bs4 import BeautifulSoup


class BrowserConsoleErrorTest(TestCase):
    """Test que analiza errores y problemas en todas las páginas."""
    
    def setUp(self):
        """Iniciar cliente de test."""
        self.client = Client()
        
    def analyze_html_for_errors(self, html_content, url):
        """Analizar HTML en busca de errores comunes."""
        errors = []
        warnings = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Verificar etiquetas script sin cerrar correctamente
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    content = script.string
                    
                    # Buscar variables de template no interpoladas
                    if '{{' in content and '}}' in content:
                        matches = re.findall(r'{{.*?}}', content)
                        for match in matches:
                            warnings.append({
                                'type': 'Template Variable in JavaScript',
                                'content': match,
                                'severity': 'medium'
                            })
                    
                    # Buscar undefined variables
                    if 'undefined' in content:
                        warnings.append({
                            'type': 'Undefined reference',
                            'content': 'Posible referencia a variable undefined',
                            'severity': 'low'
                        })
                    
                    # Buscar console.error
                    if 'console.error' in content:
                        warnings.append({
                            'type': 'Console.error call',
                            'content': 'Código que hace console.error',
                            'severity': 'medium'
                        })
            
            # Verificar links rotos
            for link in soup.find_all('link'):
                href = link.get('href', '')
                if href and not href.startswith(('http', '/', 'data:')):
                    errors.append({
                        'type': 'Broken Link',
                        'content': href,
                        'severity': 'high'
                    })
            
            # Verificar imágenes rotas
            for img in soup.find_all('img'):
                src = img.get('src', '')
                if src and not src.startswith(('http', '/', 'data:')):
                    errors.append({
                        'type': 'Broken Image',
                        'content': src,
                        'severity': 'medium'
                    })
            
            # Verificar atributos data vacíos
            elements_with_data = soup.find_all(attrs={'data-': True})
            for elem in elements_with_data:
                for attr, value in elem.attrs.items():
                    if attr.startswith('data-') and not value:
                        warnings.append({
                            'type': 'Empty data attribute',
                            'content': attr,
                            'severity': 'low'
                        })
                        
        except Exception as e:
            errors.append({
                'type': 'Parse Error',
                'content': str(e),
                'severity': 'high'
            })
        
        return errors, warnings
    
    def test_login_page_analysis(self):
        """Test: Analizar errores en página de login."""
        response = self.client.get('/accounts/login/')
        errors, warnings = self.analyze_html_for_errors(response.content, 'Login')
        
        print("\n" + "="*80)
        print("LOGIN PAGE - Análisis de Errores")
        print("="*80)
        print(f"Status: {response.status_code}")
        
        if errors:
            print(f"\n❌ {len(errors)} ERRORES ENCONTRADOS:\n")
            for error in errors:
                print(f"  [{error['type']}] {error['content']}")
        else:
            print("\n✅ No se encontraron errores")
        
        if warnings:
            print(f"\n⚠️  {len(warnings)} ADVERTENCIAS:\n")
            for warning in warnings:
                print(f"  [{warning['type']}] {warning['content']}")
    
    def test_all_pages_analysis(self):
        """Test: Analizar errores en todas las páginas principales."""
        
        pages = [
            ('Login', '/accounts/login/', False),
            ('Crear Producto', '/producto/nuevo/', True),
            ('Reportes', '/reportes/', True),
            ('Home', '/', True),
            ('Lista Movimientos', '/movimientos/', True),
        ]
        
        all_errors = []
        all_warnings = []
        
        print("\n" + "="*80)
        print("ANÁLISIS DE ERRORES - TODAS LAS PÁGINAS")
        print("="*80 + "\n")
        
        for page_name, url, need_auth in pages:
            try:
                if need_auth:
                    self.client.force_login(self.get_or_create_user())
                
                response = self.client.get(url)
                
                if response.status_code == 200:
                    errors, warnings = self.analyze_html_for_errors(response.content, page_name)
                    
                    print(f"[{page_name}] Status: {response.status_code}")
                    
                    if errors:
                        print(f"  ❌ {len(errors)} errores")
                        all_errors.extend([(page_name, e) for e in errors])
                    else:
                        print(f"  ✅ Sin errores")
                    
                    if warnings:
                        print(f"  ⚠️  {len(warnings)} advertencias")
                        all_warnings.extend([(page_name, w) for w in warnings])
                    
                    print()
                else:
                    print(f"[{page_name}] Status: {response.status_code} ❌\n")
                    
            except Exception as e:
                print(f"[{page_name}] Error: {e}\n")
        
        # Resumen final
        print("="*80)
        print("RESUMEN FINAL")
        print("="*80)
        print(f"Total de errores encontrados: {len(all_errors)}")
        print(f"Total de advertencias: {len(all_warnings)}")
        
        if all_errors:
            print(f"\n❌ ERRORES:\n")
            for page_name, error in all_errors:
                print(f"  [{page_name}] {error['type']}: {error['content']}")
        
        if all_warnings:
            print(f"\n⚠️  ADVERTENCIAS:\n")
            for page_name, warning in all_warnings:
                print(f"  [{page_name}] {warning['type']}: {warning['content']}")
    
    def get_or_create_user(self):
        """Obtener o crear usuario de prueba con permisos."""
        from django.contrib.auth.models import User
        
        user, created = User.objects.get_or_create(username='testuser')
        
        # Hacer superuser para que tenga todo los permisos
        if created:
            user.set_password('testpass')
            user.is_staff = True
            user.is_superuser = True
            user.save()
        
        return user

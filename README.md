# MLC - Monitoreo Liderado por la Comunidad Guatemala

## Prueba de Concepto - Sitio Web Interactivo

Bienvenido a la prueba de concepto del sitio web para "Monitoreo Liderado por la Comunidad MLC" en Guatemala. Este proyecto propone una plataforma web integrada que combina información sobre el proyecto con dashboards dinámicos para dos actores clave: usuarios de servicios de salud y prestadores de servicios.

---

## 📁 Estructura del Proyecto

```
MLC POC/
├── index.html                    # Página de inicio/portada
├── metodologia.html              # Página de metodología del proyecto
├── blog.html                     # Página de blog y noticias
├── dashboard.html                # Panel de control (selector de rol)
├── dashboard-usuarios.html        # Dashboard dinámico para usuarios
├── dashboard-prestadores.html     # Dashboard dinámico para prestadores
├── css/
│   └── styles.css                # Estilos globales del proyecto
├── js/
│   └── script.js                 # Script JavaScript global
├── data/                         # Datos de las encuestas y catálogos
│   ├── kobo/                     # Exports originales de KoboToolbox (.csv / .xlsx)
│   ├── build_from_kobo.py        # Export de Kobo → JSON de los dashboards
│   ├── mock-usuarios.json        # Respuestas de usuarios (schema + responses)
│   ├── mock-prestadores.json     # Respuestas de prestadores
│   ├── indicators-*.json         # Ficha de indicadores por pilar
│   └── unidades-catalog.json     # Catálogo oficial de establecimientos
└── README.md                     # Este archivo
```

---

## 🎨 Paleta de Colores

El sitio utiliza una paleta de colores profesional y accesible:

- **Crimson Blaze**: #C111F (Acentos y llamadas a acción)
- **Blood Rust**: #790000 (Títulos y elementos principales)
- **Deep Oceanic**: #003049 (Fondo y elementos secundarios)
- **Mystic Blue**: #669BBC (Acentos y hovers)
- **Vanilla Cream**: #FDF0D5 (Fondos claros)

---

## 📄 Páginas Principales

### 1. **Inicio (index.html)**
- Portada del proyecto MLC
- Sección "Acerca del Proyecto" con información general
- Características del sistema
- Botón directo al Panel de Control

### 2. **Metodología (metodologia.html)**
- Marco conceptual con 5 dimensiones clave
- Proceso de monitoreo en 4 pasos
- Tabla de indicadores por dimensión
- Información de actores participantes

### 3. **Blog/Noticias (blog.html)**
- Últimas actualizaciones del proyecto
- Artículos destacados
- Galería de eventos
- Formulario de suscripción al newsletter

### 4. **Panel de Control (dashboard.html)**
- Selector de rol (Usuarios vs Prestadores)
- Descripción de cada tipo de panel
- Características comunes

### 5. **Dashboard de Usuarios (dashboard-usuarios.html)**
- Indicadores clave por dimensión
- Gráficos comparativos y de tendencias
- Tabla de desempeño por unidad
- Detalle de indicadores
- Área de retroalimentación

### 6. **Dashboard de Prestadores (dashboard-prestadores.html)**
- Comparativa: Tu unidad vs promedio regional
- Retroalimentación comunitaria
- Plan de mejora sugerido
- Recursos y apoyo disponibles
- Contacto con equipo MLC

---

## 🚀 Cómo Usar el Sitio

### Opción 1: Abrir en Navegador Directamente
1. Descarga o clona todos los archivos
2. Abre `index.html` en tu navegador preferido
3. Navega usando el menú superior

### Opción 2: Usando un Servidor Local
Si quieres que los gráficos funcionen mejor, usa un servidor local:

```bash
# Usando Python 3
python -m http.server 8000

# Usando Node.js (con http-server)
npx http-server
```

Luego accede a `http://localhost:8000`

---

## 🔧 Características Técnicas

### Frontend
- **HTML5**: Estructura semántica
- **CSS3**: Diseño responsivo y moderno
- **JavaScript Vanilla**: Interactividad sin dependencias
- **Chart.js**: Visualización de datos (CDN)

### Responsividad
- Diseño mobile-first
- Grid y Flexbox para layouts
- Media queries para pantallas pequeñas

### Accesibilidad
- Colores con contraste adecuado
- Navegación clara
- Semántica HTML correcta

---

## 📊 Tipos de Indicadores

El proyecto utiliza 5 dimensiones de calidad:

1. **Disponibilidad**: ¿Existen los servicios?
2. **Accesibilidad**: ¿Pueden acceder a ellos?
3. **Aceptabilidad**: ¿Son culturalmente aceptados?
4. **Adecuación**: ¿Son de calidad técnica?
5. **Asegurabilidad**: ¿Hay capacidad de cobertura?

---

## 📱 Navegación Rápida

| Sección | Ruta | Descripción |
|---------|------|-------------|
| Inicio | `index.html` | Portada e información general |
| Metodología | `metodologia.html` | Marco conceptual |
| Blog | `blog.html` | Noticias y eventos |
| Panel Control | `dashboard.html` | Selector de rol |
| Panel Usuarios | `dashboard-usuarios.html` | Dashboard de usuarios |
| Panel Prestadores | `dashboard-prestadores.html` | Dashboard de prestadores |

---

## 🎯 Datos Utilizados

Los dashboards se alimentan de las **respuestas reales** de las dos encuestas MLC
levantadas en KoboToolbox (julio–agosto 2026):

| Formulario | Export original | JSON del dashboard |
|---|---|---|
| Prestadores de servicios de salud | `data/kobo/kobo-prestadores.csv` | `data/mock-prestadores.json` |
| Usuarios de servicios de salud | `data/kobo/kobo-usuarios.xlsx` | `data/mock-usuarios.json` |

### Cómo actualizar los datos

1. Exportar de KoboToolbox en formato **CSV · labels · separador `;`**, o dejar
   el libro **.xlsx** ya depurado con esas mismas columnas.
2. Reemplazar los archivos en `data/kobo/` conservando los nombres
   (`kobo-usuarios.*`, `kobo-prestadores.*`). Si existen ambos formatos para un
   formulario, el script usa el `.xlsx`.
3. Ejecutar:

   ```bash
   python data/build_from_kobo.py       # regenera los JSON de respuestas
   python data/generate_indicators.py   # re-mapea la ficha de indicadores
   ```

El script canoniza el nombre del establecimiento contra `data/unidades-catalog.json`
(para que los filtros en cascada lo encuentren), traduce las etiquetas del
formulario a los códigos que usa `js/dashboard-data.js`, descarta submisiones con
`_uuid` repetido y omite el *Código Construido* de la persona encuestada por
tratarse de un pseudoidentificador.

---

## 🔄 Interactividad

### Filtros Disponibles
- **Region**: Selecciona regiones específicas
- **Unidad de Atención**: Filtra por unidades
- **Período**: Selecciona rangos de tiempo
- **Comparación**: Compara con promedios o similares

### Gráficos Dinámicos
- Gráficos de barra
- Gráficos de línea
- Gráficos radar
- Tablas interactivas

---

## 📞 Contacto

Para más información sobre el proyecto MLC:
- **Email**: info@mlcguatemala.org
- **Teléfono**: +502 XXXX-XXXX
- **Ubicación**: Guatemala

---

## 📝 Notas para Desarrollo Futuro

### Mejoras Sugeridas
1. **Backend**: Conectar con API real para datos dinámicos
2. **Autenticación**: Sistema de login para usuarios y prestadores
3. **Base de Datos**: Almacenar datos de indicadores
4. **Exportación**: Reportes PDF y Excel
5. **Mapas**: Visualización geográfica de indicadores
6. **Movilidad**: Aplicación móvil complementaria
7. **Integración**: Conexión con sistemas existentes (SIGSA, etc.)

### Tecnologías Recomendadas
- **Frontend**: React, Vue.js o Angular
- **Backend**: Node.js, Django o Flask
- **Base de Datos**: PostgreSQL o MongoDB
- **Mapas**: Leaflet o Mapbox
- **Visualización Avanzada**: D3.js, Plotly

---

## 📄 Licencia

Este proyecto es una prueba de concepto para el Monitoreo Liderado por la Comunidad en Guatemala.

---

## ✅ Checklist de Funcionalidades

- ✓ Navegación principal funcional
- ✓ Diseño responsivo
- ✓ Paleta de colores integrada
- ✓ Página de inicio con información del proyecto
- ✓ Sección "Acerca del Proyecto"
- ✓ Página de Metodología
- ✓ Página de Blog/Noticias
- ✓ Panel de Control con opciones
- ✓ Dashboard para Usuarios
- ✓ Dashboard para Prestadores
- ✓ Gráficos interactivos
- ✓ Tablas dinámicas
- ✓ Filtros y controles
- ✓ Área de retroalimentación
- ✓ Footer consistente en todas las páginas

---

**Versión**: 1.0 - Prueba de Concepto  
**Fecha**: Abril 2024  
**Estado**: Listo para exploración y feedback

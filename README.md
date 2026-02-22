## Tyke: Username OSINT Tool

Esta herramienta rinde homenaje a Tyke, una elefanta de circo africana que, tras años de maltrato y encierro, protagonizó una trágica huida en Honolulu, Hawái, en 1994. [ 🐘Tyke:Wikipedia](https://en.wikipedia.org/wiki/Tyke_(elephant))

Descripción
Tyke es una herramienta de reconocimiento (OSINT) desarrollada en Python diseñada para buscar la presencia de nombres de usuario en 568 plataformas y redes sociales. A diferencia de otros scripts de búsqueda simple, Tyke implementa un sistema de puntuación inteligente (Scoring) para reducir falsos positivos y categoriza los resultados según la naturaleza del sitio (Seguridad, Dev, Social, etc.).
Comparativa: Tyke vs. Otros (Sherlock/Maigret)
| Característica | Sherlock | Maigret | Tyke |
|---|---|---|---|
| Enfoque | Rápido / Minimalista | Profundo / Recursivo | Equilibrado / Reporte visual |
| Detección | Status Code | Texto/Status | Markers + Scoring + Estructura |
| Portabilidad | Alta | Media (Pesado) | Alta (Optimizado para Termux) |
| Reportes | TXT/JSON/CSV | HTML/PDF/JSON | HTML Interactivo (Mobile Friendly) |
| Proxies | Manual | Soporta Tor | Tor + Rotación Geonode integrada |
Características Principales
 * Deduplicación Automática: Filtra sitios repetidos en la base de datos para ahorrar tiempo.
 * Sistema de Scoring: Clasifica los resultados en EXISTS_HIGH o EXISTS_WEAK basándose en marcadores de texto y códigos HTTP.
 * Perfiles de Búsqueda: Permite filtrar por categorías como --security, --dev, --gaming, o --core.
 * Evasión de Bloqueos: Implementa retardos aleatorios (MIN_DELAY, MAX_DELAY) y rotación de User-Agents.
 * Integración de Proxies: Soporte nativo para Tor y carga automática de proxies mediante la API de Geonode.
 * Optimizado para Termux: Incluye funciones para abrir reportes directamente en el navegador de Android mediante termux-open-url.
[ss1](/img/ss1.png)[ss2](/img/ss2.png)
Instalación
En Termux/Linux
# Clonar el repositorio
git clone https://github.com/git5loxosec/tyke.git
cd tyke

# Instalar dependencias
pip3 install requests

En Termux (Android)
pkg update && pkg upgrade
pkg install python python-pip tor termux-api
pip3 install requests

Uso
El uso básico requiere el nombre de usuario y, opcionalmente, un perfil de búsqueda o flags de red.
python3 tyke.py <username> [perfil] [--tor] [--geonode]

Ejemplos:
 * Búsqueda global simple:
   python3 tyke.py janesmith
 * Búsqueda enfocada en ciberseguridad y desarrollo:
   python3 tyke.py johndoe security
 * Búsqueda usando la red Tor (Privacidad):
   python3 tyke.py anonuser --tor
 * Búsqueda múltiple de usuarios:
   python3 tyke.py user1 user2 user3 core
Perfiles disponibles:
 * all: Ejecuta la búsqueda en los 568 sitios.
 * core: Sitios principales (X, FB, GitHub, LinkedIn, etc.).
 * security: Plataformas de CTF, Bug Bounty y hacking.
 * dev: Repositorios y comunidades de programación.
 * gaming: Steam, Twitch, Xbox, PSN.
 * creative: Behance, ArtStation, SoundCloud.
Reportes
Al finalizar, Tyke genera un archivo HTML en la carpeta ~/tyke_reports. Este reporte es responsivo y permite filtrar visualmente los hallazgos por relevancia. Si estás en Termux, el script te ofrecerá abrir el reporte automáticamente usando un servidor local temporal.
Requerimientos
 * Python 3.8+
 * Librería requests
 * (Opcional) Servicio Tor corriendo para la flag --tor
 * (Opcional) Paquete termux-api para visualización en Android

## NO USAR SIN AUTORIZACIÓN DE TERCEROS NI CON INTENCIÓN CRIMINAL. ESTA HERRAMIENTA NO ES PARA SER USADA EN ACTIVIDADES ILÍCITAS/ILEGALES.

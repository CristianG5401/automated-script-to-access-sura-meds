# EPS Sura Initial Screenshot PoC

Pequeno proyecto de aprendizaje en Python para abrir la URL publica de medicamentos de EPS Sura con Chrome del sistema en modo stealth, conectar Playwright sobre CDP, guardar una captura inicial y producir una segunda captura con el formulario pre-captcha diligenciado.

## Objetivo

Este repositorio muestra un flujo pequeno y directo:

- lanzar Chrome del sistema con SeleniumBase CDP en modo stealth
- conectar Playwright al navegador activo por CDP
- abrir la SPA publica de EPS Sura
- esperar a que aparezca la interfaz principal
- diligenciar los tres campos previos al captcha
- guardar dos screenshots locales

## Runtime actual

El script usa esta combinacion:

- `seleniumbase` para lanzar Chrome del sistema en modo stealth con `sb_cdp.Chrome(...)`
- `playwright` para conectarse a ese navegador con `chromium.connect_over_cdp(...)`

No se usa el navegador descargado por Playwright. Por eso no hace falta correr `playwright install` para este proyecto.

## Que hace el script

El archivo [`take_initial_screenshot.py`](./take_initial_screenshot.py) ejecuta este flujo:

1. crea la carpeta `screenshots/` si no existe
2. lanza Chrome del sistema en stealth con SeleniumBase CDP
3. obtiene el endpoint CDP del navegador activo
4. conecta Playwright sobre ese endpoint CDP
5. abre la URL publica de medicamentos de EPS Sura
6. espera el contenedor principal de la SPA
7. guarda un screenshot inicial
8. selecciona tipo de documento, llena numero de documento y fecha de nacimiento
9. verifica los valores diligenciados
10. guarda un segundo screenshot con el formulario diligenciado
11. cierra Playwright y detiene la sesion de SeleniumBase

## Requisitos

- Python 3.9+
- Google Chrome instalado en el sistema
- acceso a internet

## Instalacion

En macOS y en varios entornos modernos, instalar paquetes con el Python del sistema puede fallar por la politica de `externally-managed-environment`. Aqui conviene usar un entorno virtual.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

No necesitas ejecutar `playwright install` porque el script usa Chrome del sistema lanzado por SeleniumBase.

## Ejecucion

Con el entorno virtual activo:

```bash
python take_initial_screenshot.py
```

Salida esperada en consola:

```text
Opening URL: https://portaleps.epssura.com/ServiciosUnClick/#/solicitudes/medicamentos?App=tramitesExternos
Waiting for SPA shell...
Saving screenshot to: screenshots/epssura-medicamentos-inicial.png
Screenshot saved successfully.
Selecting document type: CC
Filling document number: 123456789
Filling birth date: 01/01/1990
Saving populated-form screenshot to: screenshots/epssura-medicamentos-diligenciado.png
Populated-form screenshot saved successfully.
```

## Valores editables

Dentro de `take_initial_screenshot.py` puedes cambiar facilmente:

- `URL`
- `DOCUMENT_TYPE_TEXT`
- `DOCUMENT_NUMBER`
- `BIRTH_DATE`
- `HEADLESS`
- `ELEMENT_TIMEOUT_MS`
- `POST_DETECTION_DELAY_MS`
- `OUTPUT_PATH`
- `FILLED_OUTPUT_PATH`

`HEADLESS = True` mantiene el comportamiento actual en segundo plano. Si necesitas observar la pagina para depurar, puedes cambiarlo temporalmente a `False`.

## Screenshots generados

- `screenshots/epssura-medicamentos-inicial.png`
- `screenshots/epssura-medicamentos-diligenciado.png`

## Alcance actual

Este proyecto llena unicamente los tres campos previos al captcha:

- tipo de documento
- numero de documento
- fecha de nacimiento

No intenta resolver, hacer click ni automatizar el captcha. Tampoco envia el formulario despues de diligenciarlo.

## Camino futuro para captcha

La estructura actual deja abierto el camino para una iteracion futura con `sb.solve_captcha()`.

El punto natural para agregarlo seria despues de diligenciar y verificar los tres campos previos al captcha, manteniendo la misma sesion activa de SeleniumBase y la misma pagina conectada por Playwright.

## Estructura del proyecto

```text
.
├── README.md
├── requirements.txt
├── screenshots/
│   ├── epssura-medicamentos-diligenciado.png
│   └── epssura-medicamentos-inicial.png
├── take_initial_screenshot.py
└── tests/
    └── test_take_initial_screenshot.py
```

## Problemas comunes

### `python: command not found`

Usa `python3` para crear el entorno virtual:

```bash
python3 -m venv .venv
```

Despues de activar `.venv`, normalmente ya puedes usar `python`.

### `externally-managed-environment`

Eso pasa cuando intentas instalar dependencias en el Python del sistema. La solucion es usar `.venv`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### Fallo al abrir el navegador

Revisa:

- que Google Chrome este instalado
- que Chrome abra normalmente en tu maquina
- que no haya restricciones del entorno donde corres el script

### Screenshot en blanco o incompleto

Prueba primero aumentando:

- `ELEMENT_TIMEOUT_MS`
- `POST_DETECTION_DELAY_MS`

Si sigue fallando, cambia `HEADLESS` a `False` temporalmente para observar el comportamiento real del sitio.

## Dependencias usadas

[`requirements.txt`](./requirements.txt):

```text
seleniumbase
playwright
```

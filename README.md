# EPS Sura Initial Screenshot PoC

Pequeño proyecto de aprendizaje en Python usando `pydoll-python` para abrir la URL pública de medicamentos de EPS Sura en modo headless, guardar una captura inicial y producir una segunda captura con el formulario pre-captcha diligenciado.

## Objetivo

La idea de este proyecto es aprender una automatización web mínima:

- lanzar Chrome desde Python
- navegar a una SPA
- esperar a que aparezca una parte básica de la interfaz
- llenar los tres campos previos al captcha
- tomar screenshots y guardarlos localmente

## Qué hace el script

El archivo [`take_initial_screenshot.py`](./take_initial_screenshot.py) hace este flujo:

1. crea la carpeta `screenshots/` si no existe
2. inicia Chrome en modo headless
3. abre la URL pública de EPS Sura
4. espera el contenedor principal de la SPA
5. guarda un screenshot inicial
6. llena tipo de documento, número de documento y fecha de nacimiento
7. deja el captcha intacto
8. guarda un segundo screenshot con el formulario diligenciado

## Requisitos

- Python 3
- Google Chrome instalado
- acceso a internet

## Instalación

En macOS y en varios entornos modernos, instalar paquetes con el Python del sistema puede fallar por la política de `externally-managed-environment`. Por eso aquí conviene usar un entorno virtual.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Ejecución

Con el entorno virtual activo:

```bash
python take_initial_screenshot.py
```

Salida esperada en consola:

```text
Opening URL: https://portaleps.epssura.com/ServiciosUnClick/#/solicitudes/medicamentos?App=tramitesExternos
Waiting for SPA shell...
Container detected. Waiting a bit longer for route content to settle.
Saving screenshot to: screenshots/epssura-medicamentos-inicial.png
Screenshot saved successfully.
Selecting document type: CC
Filling document number: 123456789
Filling birth date: 01/01/1990
Verifying populated fields...
Saving populated-form screenshot to: screenshots/epssura-medicamentos-diligenciado.png
Populated-form screenshot saved successfully.
```

## Valores demo editables

Dentro de `take_initial_screenshot.py` puedes cambiar fácilmente:

- `DOCUMENT_TYPE_TEXT`
- `DOCUMENT_NUMBER`
- `BIRTH_DATE`

## Screenshots generados

- `screenshots/epssura-medicamentos-inicial.png`
- `screenshots/epssura-medicamentos-diligenciado.png`

## Alcance actual

Este proyecto llena únicamente los tres campos previos al captcha.
No intenta resolver, hacer click ni automatizar el captcha.

## Resultado

Los archivos generados quedan en:

```text
screenshots/epssura-medicamentos-inicial.png
screenshots/epssura-medicamentos-diligenciado.png
```

## Estructura del proyecto

```text
.
├── README.md
├── requirements.txt
├── screenshots/
│   ├── epssura-medicamentos-diligenciado.png
│   └── epssura-medicamentos-inicial.png
└── take_initial_screenshot.py
```

## Explicación rápida del código

### `asyncio`

Se usa porque `pydoll` trabaja con una API asíncrona. Por eso la función principal es `async def main()` y al final se ejecuta con:

```python
asyncio.run(main())
```

### `Path`

`Path` de `pathlib` hace más claro el manejo de rutas:

```python
OUTPUT_PATH = Path("screenshots/epssura-medicamentos-inicial.png")
```

### `ChromiumOptions`

Permite configurar el navegador. En este proyecto solo se activa:

```python
options.headless = True
```

Eso hace que Chrome corra en segundo plano, sin abrir una ventana visible.

### Espera del contenido

La página es una SPA. Eso significa que abrir la URL no garantiza que el contenido visible ya esté listo. Por eso el script primero intenta encontrar este contenedor:

```python
app_container = await tab.find(
    class_name="content-app",
    timeout=ELEMENT_TIMEOUT_SECONDS,
    raise_exc=False,
)
```

Si no aparece, el script hace una espera fija con `asyncio.sleep(...)` como respaldo.

## Problemas comunes

### `python: command not found`

Usa `python3` para crear el entorno virtual:

```bash
python3 -m venv .venv
```

Después de activar `.venv`, normalmente ya puedes usar `python`.

### `externally-managed-environment`

Eso pasa cuando intentas instalar dependencias en el Python del sistema. La solución es usar `.venv`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### `Failed to start the browser`

Revisa:

- que Google Chrome esté instalado
- que puedas abrir Chrome normalmente en tu máquina
- que no haya restricciones del entorno donde corres el script

### Screenshot en blanco o incompleto

Prueba primero aumentando:

- `FALLBACK_DELAY_SECONDS` de `5` a `8`
- `POST_DETECTION_DELAY_SECONDS` de `2` a un valor un poco mayor

Si sigue fallando, el siguiente paso lógico es esperar un selector más específico de la ruta o correr Chrome en modo visible para observar qué pasa.

## Dependencia usada

[`requirements.txt`](./requirements.txt):

```text
pydoll-python
```

## Ideas para seguir aprendiendo

- agregar argumentos CLI como `--url` y `--output`
- ejecutar el navegador en modo visible temporalmente
- esperar un selector más específico del formulario
- capturar errores de red o timeout con mensajes más claros
- guardar screenshots con timestamp para no sobrescribir resultados

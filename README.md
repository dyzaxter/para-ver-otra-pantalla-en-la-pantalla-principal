# Visor de Monitor

Pequeña app en Python para ver otra pantalla del PC dentro de una ventana.

La hice porque necesitaba tener el monitor secundario a la vista sin estar
cambiando de ventana todo el rato. Captura la pantalla con `mss`, la muestra
con PySide6 y le dibuja el cursor encima para que se vea dónde está el ratón.

Solo funciona en Windows (usa la API de Win32 para leer la posición del cursor).

## Qué hace

- Captura cualquier monitor en tiempo real dentro de una ventana.
- Puedes cambiar entre monitores con las teclas 1-4.
- Sube o baja los FPS con `+` y `-`.
- La ventana puede quedarse siempre encima (`T`).
- Muestra u oculta el cursor dibujado (`C`).
- Pantalla completa con `F`.
- `Esc` cierra (o sale de pantalla completa si estás en ella).

## Instalación

Necesitas Python 3.10 o superior. Luego:

```
pip install -r requirements.txt
```

O si lo prefieres a mano:

```
pip install mss PySide6
```

## Cómo usarlo

En Windows, lo más fácil es hacer doble clic en `visor_monitor.bat`. El script
busca Python, instala lo que falte y arranca la app.

Si prefieres lanzarlo a mano:

```
python visor_monitor.py
```

Por defecto intenta capturar el monitor 2 a 30 FPS. Si no encuentra ese
monitor, muestra el principal y avisa con un mensaje. Puedes cambiarlo
editando esta línea al final del archivo:

```python
viewer = MonitorViewer(monitor_index=2, fps=30)
```

## Atajos

| Tecla     | Qué hace                    |
|-----------|-----------------------------|
| 1 - 4     | Cambiar de monitor          |
| + / =     | Subir FPS                   |
| -         | Bajar FPS                   |
| T         | Siempre encima on/off       |
| C         | Cursor on/off               |
| F         | Pantalla completa           |
| Esc       | Cerrar / salir de fullscreen|

## Notas

- El archivo `error_log.txt` se genera solo cuando hay errores y no está en el
  repo (lo ignora el `.gitignore`). Cada vez que arrancas con el `.bat` se
  borra el anterior.
- Los FPS se guardan entre sesiones con `QSettings`, así que si los cambias
  con `+`/`-` se recuerdan la próxima vez.
- Probado en Windows 10 y 11 con Python 3.11-3.13. No lo he probado en otros
  sistemas porque el cursor usa la API de Windows.

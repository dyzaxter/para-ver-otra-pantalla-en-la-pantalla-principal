import sys
import traceback
import datetime
import ctypes
from ctypes import wintypes

LOG_FILE = "error_log.txt"


def log(msg):
    line = f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


# ---- Win32: obtener posicion del cursor en pixeles fisicos ----
class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


def get_cursor_screen_pos():
    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


# ---- imports protegidos ----
try:
    log("===== INICIO =====")
    import mss
    log("import mss OK")
except Exception as e:
    log(f"FALLO al importar mss: {e}")
    log(traceback.format_exc())
    input("Pulsa Enter para cerrar...")
    sys.exit(1)

try:
    from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
    from PySide6.QtGui import (
        QImage, QPixmap, QGuiApplication, QPainter, QColor, QPolygon, QPen
    )
    from PySide6.QtCore import QTimer, Qt, QSettings, QPoint
    log("import PySide6 OK")
except Exception as e:
    log(f"FALLO al importar PySide6: {e}")
    log(traceback.format_exc())
    input("Pulsa Enter para cerrar...")
    sys.exit(1)


def crear_mss():
    try:
        return mss.MSS()
    except AttributeError:
        return mss.mss()


class MonitorViewer(QWidget):
    def __init__(self, monitor_index=2, fps=30):
        super().__init__()
        self.settings = QSettings("MiVisor", "RaitonClone")
        self._frame_count = 0
        self.show_cursor = True  # toggle con la tecla C

        log("Inicializando captura...")
        self.sct = crear_mss()
        total = len(self.sct.monitors)
        log(f"Pantallas detectadas: {total - 1}")

        self.monitor_index = monitor_index
        self.aviso_monitor = None
        if self.monitor_index >= total:
            self.aviso_monitor = (
                f"Solo se detectan {total - 1} pantalla(s). "
                f"Mostrando la principal (monitor 1)."
            )
            log(f"AVISO: monitor {monitor_index} no existe, uso monitor 1.")
            self.monitor_index = 1 if total > 1 else 0

        self.fps = int(self.settings.value("fps", fps))
        self.always_on_top = True

        log(f"Monitor: {self.monitor_index}, FPS: {self.fps}")
        self.init_ui()
        self.start_capture()
        log("Visor listo.")

    def init_ui(self):
        self.setWindowTitle(f"Visor Monitor {self.monitor_index}  |  {self.fps} FPS")
        self.resize(960, 540)

        pantalla = QGuiApplication.primaryScreen().availableGeometry()
        x = pantalla.x() + (pantalla.width() - self.width()) // 2
        y = pantalla.y() + (pantalla.height() - self.height()) // 2
        self.move(x, y)

        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel("Capturando...")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("background-color: black; color: yellow;")
        layout.addWidget(self.label)
        self.setLayout(layout)

        if self.aviso_monitor:
            self.label.setText(self.aviso_monitor)

    def start_capture(self):
        if hasattr(self, "timer"):
            self.timer.stop()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(max(1, int(1000 / self.fps)))

    # ---------------------------------------------
    #  Dibuja una flecha de cursor en pixmap
    # ---------------------------------------------
    def _dibujar_cursor(self, pixmap, monitor):
        """Devuelve un nuevo pixmap con el cursor dibujado si esta dentro."""
        try:
            cx, cy = get_cursor_screen_pos()
        except Exception as e:
            log(f"No se pudo obtener posicion del cursor: {e}")
            return pixmap

        # Solo dibujar si el cursor esta dentro del monitor capturado
        if not (monitor["left"] <= cx < monitor["left"] + monitor["width"]
                and monitor["top"] <= cy < monitor["top"] + monitor["height"]):
            return pixmap

        # Posicion relativa dentro del monitor
        rel_x = cx - monitor["left"]
        rel_y = cy - monitor["top"]

        # El pixmap puede no tener el mismo tamano que el monitor fisico
        # (mss devuelve el tamano real, pero por si acaso escalamos la posicion)
        sx = pixmap.width() / monitor["width"]
        sy = pixmap.height() / monitor["height"]
        px = int(rel_x * sx)
        py = int(rel_y * sy)

        # Dibujar flecha clasica de Windows (blanca con borde negro)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Escalar el tamano del cursor segun el factor del pixmap
        escala = min(sx, sy) if (sx or sy) else 1.0
        k = max(0.6, min(1.5, escala))  # entre 0.6x y 1.5x

        # Polygon de la flecha en pixeles "base" (antes de escalar)
        puntos_base = [
            (0, 0), (0, 16), (4, 12), (7, 19),
            (10, 18), (7, 11), (12, 11)
        ]
        puntos = [QPoint(int(px + x * k), int(py + y * k)) for (x, y) in puntos_base]

        poligono = QPolygon(puntos)

        # Relleno blanco, borde negro (como el cursor real de Windows)
        painter.setBrush(QColor(255, 255, 255))
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.drawPolygon(poligono)
        painter.end()

        return pixmap

    def update_frame(self):
        try:
            monitor = self.sct.monitors[self.monitor_index]
            img = self.sct.grab(monitor)

            raw = bytes(img.bgra)
            q_img = QImage(
                raw, img.width, img.height, QImage.Format.Format_RGB32
            )
            pixmap = QPixmap.fromImage(q_img)

            # ---- NUEVO: dibujar cursor encima ----
            if self.show_cursor:
                pixmap = self._dibujar_cursor(pixmap, monitor)

            self.label.setPixmap(
                pixmap.scaled(
                    self.label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

            self._frame_count += 1
            if self._frame_count == 1:
                log(f"Primer frame OK ({img.width}x{img.height})")
            elif self._frame_count % 300 == 0:
                log(f"Frame {self._frame_count} - OK")
        except Exception as e:
            log(f"ERROR en update_frame: {e}")
            log(traceback.format_exc())
            self.timer.stop()

    def keyPressEvent(self, event):
        key = event.key()
        K = Qt.Key
        if K.Key_1 <= key <= K.Key_4:
            idx = key - K.Key_0
            if idx < len(self.sct.monitors):
                self.monitor_index = idx
                self.setWindowTitle(
                    f"Visor Monitor {self.monitor_index}  |  {self.fps} FPS"
                )
                log(f"Cambiado a monitor {self.monitor_index}")
        elif key in (K.Key_Plus, K.Key_Equal):
            self.fps = min(self.fps + 5, 120)
            self.start_capture()
            self.setWindowTitle(
                f"Visor Monitor {self.monitor_index}  |  {self.fps} FPS"
            )
        elif key == K.Key_Minus:
            self.fps = max(self.fps - 5, 5)
            self.start_capture()
            self.setWindowTitle(
                f"Visor Monitor {self.monitor_index}  |  {self.fps} FPS"
            )
        elif key == K.Key_T:
            self.always_on_top = not self.always_on_top
            self.setWindowFlag(
                Qt.WindowType.WindowStaysOnTopHint, self.always_on_top
            )
            self.show()
        elif key == K.Key_C:
            self.show_cursor = not self.show_cursor
            log(f"Mostrar cursor: {self.show_cursor}")
        elif key == K.Key_F:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
        elif key == K.Key_Escape:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.close()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        log("Cerrando visor.")
        if hasattr(self, "timer"):
            self.timer.stop()
        try:
            self.sct.close()
        except Exception:
            pass
        super().closeEvent(event)


if __name__ == "__main__":
    try:
        QApplication.setAttribute(
            Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True
        )
    except Exception:
        pass
    try:
        QApplication.setAttribute(
            Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True
        )
    except Exception:
        pass

    try:
        app = QApplication(sys.argv)
        viewer = MonitorViewer(monitor_index=2, fps=30)
        viewer.show()
        viewer.raise_()
        viewer.activateWindow()
        log("Ventana mostrada.")
        sys.exit(app.exec())
    except Exception as e:
        log(f"ERROR FATAL: {e}")
        log(traceback.format_exc())
        input("Pulsa Enter para cerrar...")
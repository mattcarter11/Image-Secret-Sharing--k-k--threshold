from functools import singledispatchmethod
from PySide6 import QtCore, QtGui, QtWidgets

VALID_FORMATS = ('.jpeg', '.jpg', '.png', '.pbm', '.pgm', '.ppm', '.xbm', '.xpm', '.bmp') # SVG and GIF also

class QPhotoViewer(QtWidgets.QGraphicsView):
    photoDropped = QtCore.Signal(list)

    def __init__(self, parent):
        super(QPhotoViewer, self).__init__(parent)
        self._zoom = 0
        self._empty = True
        self._photo = QtWidgets.QGraphicsPixmapItem()
        self._scene = QtWidgets.QGraphicsScene(self)
        self._scene.addItem(self._photo)
        self.setScene(self._scene)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(225, 225, 225)))
        self.setStyleSheet("QGraphicsView {border: 0.5px solid #adadad}")
        self.setToolTip(f'Drop Image ({" ".join(VALID_FORMATS)[:-1]})')

    def hasPhoto(self):
        return not self._empty

    def fitInView(self):
        rect = QtCore.QRectF(self._photo.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            if self.hasPhoto():
                unity = self.transform().mapRect(QtCore.QRectF(0, 0, 1, 1))
                self.scale(1 / unity.width(), 1 / unity.height())
                viewrect = self.viewport().rect()
                scenerect = self.transform().mapRect(rect)
                factor = min(viewrect.width() / scenerect.width(),
                             viewrect.height() / scenerect.height())
                self.scale(factor, factor)
            self._zoom = 0

    @singledispatchmethod
    def setPhoto(self, pixmap=None, fit=True):
        self._zoom = 0
        if pixmap and not pixmap.isNull():
            self._empty = False
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
            self._photo.setPixmap(pixmap)
        else:
            self._empty = True
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
            self._photo.setPixmap(QtGui.QPixmap())
        if fit:
            self.fitInView()
    
    @setPhoto.register(str)
    def _(self, path, fit=True):
        self.setPhoto(QtGui.QPixmap(path), fit)

    def wheelEvent(self, event):
        if self.hasPhoto():
            if event.angleDelta().y() > 0:
                factor = 1.25
                self._zoom += 1
            else:
                factor = 0.8
                self._zoom -= 1
            if self._zoom > 0:
                self.scale(factor, factor)
            elif self._zoom == 0:
                self.fitInView()
            else:
                self._zoom = 0
    
    def dragEnterEvent(self, event:QtGui.QDragEnterEvent) -> None:
        if event.mimeData().hasImage:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event:QtGui.QDragEnterEvent) -> None:
        if event.mimeData().hasImage:
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        if event.mimeData().hasImage:
            event.setDropAction(QtCore.Qt.CopyAction)
            paths = []
            invalid_paths = []
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if path.lower().endswith(VALID_FORMATS):
                    paths.append(path)
                else:
                    invalid_paths.append(path)

            if invalid_paths != []:
                msg = f"The following files are not valid images {VALID_FORMATS}\n"
                for path in invalid_paths:
                    msg += f'\n - {path}'
                QtWidgets.QMessageBox.warning(self, "Size Images Error", msg, QtWidgets.QMessageBox.Ok)
                
            self.setPhoto(paths[0])
            self.photoDropped.emit(paths)
            event.accept()
        else:
            event.ignore()

    def mouseDoubleClickEvent(self, _):
        self.fitInView() 


class Window(QtWidgets.QWidget):
    def __init__(self):
        super(Window, self).__init__()
        self.viewer = QPhotoViewer(self)
        self.viewer.photoDropped.connect(self.print_path)
        # 'Load image' button
        self.btnLoad = QtWidgets.QToolButton(self)
        self.btnLoad.setText('Load image')
        self.btnLoad.clicked.connect(self.loadImage)
        # Arrange layout
        VBlayout = QtWidgets.QVBoxLayout(self)
        VBlayout.addWidget(self.viewer)
        HBlayout = QtWidgets.QHBoxLayout()
        HBlayout.setAlignment(QtCore.Qt.AlignLeft)
        HBlayout.addWidget(self.btnLoad)
        VBlayout.addLayout(HBlayout)

    def print_path(self, path):
        print(path)

    def loadImage(self):
        self.viewer.setPhoto(QtGui.QPixmap('C:/Users/mattc/Desktop/Dungeons stuff/Datapacks flowchart maker/tests/test.svg'))


if __name__ == '__main__':
    app = QtWidgets.QApplication()
    window = Window()
    window.setGeometry(500, 300, 800, 600)
    window.show()
    app.exec()
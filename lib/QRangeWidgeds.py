from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QSizePolicy, QSlider,  QToolTip, QWidget, QApplication


class QRangeL(QLineEdit):
    newValue = Signal()

    def __init__(self, min=0, max=100, value = 0):
        super().__init__()
        self._min = min
        self._max = max
        self.value = value
        self.setValidator(QIntValidator(self._min, self._max))
        self.inputRejected.connect(self._updateValue)
        self.textEdited.connect(self._updateValue)
        self._updateTootlTip()
        
    def _updateTootlTip(self):
        self.setToolTip(f'{self._min}..{self._max}')

    def _updateValue(self):
        val = ''.join(filter(str.isdigit, self.text()))
        if not self.hasAcceptableInput():
            QToolTip.showText(self.mapToGlobal(QPoint(0, 10)), self.toolTip(), msecShowTime=2000)
            if val != '':
                self.value = int(val)
        else:
            if val != '':
                self.value = int(val)
    
    @property
    def value(self) -> int:
        val = ''.join(filter(str.isdigit, self.text()))
        if val != '':
            return int(val)
        return None 
    @value.setter
    def value(self, value:int = 0):
        if value > self.max:
            value = self.max
        elif value < self.min:
            value = self.min
        self.setText(str(value))
        self.newValue.emit()

    @property
    def min(self) -> int:
        return self._min
    @min.setter
    def min(self, min:int = 0):
        if min > self.value:
            self.value = min
        self._min = min
        self._updateTootlTip()
        self.setValidator(QIntValidator(self._min, self._max))

    @property
    def max(self) -> int:
        return self._max
    @max.setter
    def max(self, max:int = 100):
        if max < self.value:
            self.value = max
        self._max = max
        self._updateTootlTip()
        self.setValidator(QIntValidator(self._min, self._max))

class QRangeLS(QWidget):
    newValue = Signal()

    def __init__(self, min=0, max=100, value=0, lineStrech = 1, sliderStrech = 4):
        super().__init__()
        self.line = QRangeL()
        self.line.newValue.connect(self.line_new_value)
        policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        policy.setHorizontalStretch(lineStrech)
        self.line.setSizePolicy(policy)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.valueChanged.connect(self.slider_new_value)
        policy.setHorizontalStretch(sliderStrech)
        self.slider.setSizePolicy(policy)
        self.slider.setPageStep(1)

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.line)
        self.layout.addWidget(self.slider)
        self.setLayout(self.layout)

        self.min = min
        self.max = max
        self.value = value

    def line_new_value(self):
        self.slider.setValue(self.line.value)
        self.newValue.emit()

    def slider_new_value(self):
        self.line.value = self.slider.value()
        self.newValue.emit()

    @property
    def value(self) -> int:
        return self.line.value
    @value.setter
    def value(self, value:int = 0):
        self.line.value = value
        self.slider.setValue(self.line.value)
        
    @property
    def min(self) -> int:
        return self.line.min
    @min.setter
    def min(self, min:int = 0):
        self.line.min = min
        self.slider.setMinimum(self.line.min)
        
    @property
    def max(self) -> int:
        return self.line.max
    @max.setter
    def max(self, max:int = 100):
        self.line.max = max
        self.slider.setMaximum(self.line.max)


class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()
        layout = QHBoxLayout()
        ls = QRangeLS()
        layout.addWidget(ls)
        self.setLayout(layout)


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    app.exec()
"""QListWidget with fields selection."""

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
)
from qgis.core import QgsVectorLayer

__copyright__ = 'Copyright 2019, 3Liz'
__license__ = 'GPL version 3'
__email__ = 'info@3liz.org'
__revision__ = '$Format:%H$'


class ListFieldsSelection(QListWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionMode(QAbstractItemView.MultiSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.layer = None

    def set_layer(self, layer: QgsVectorLayer):
        self.layer = layer

        self.clear()

        for field in self.layer.fields():
            cell = QListWidgetItem()
            cell.setText(field.name())
            cell.setData(Qt.UserRole, field.name())
            index = layer.fields().indexFromName(field.name())
            if index >= 0:
                cell.setIcon(self.layer.fields().iconForField(index))
            self.addItem(cell)

    def set_selection(self, fields: tuple):
        for i in range(self.count()):
            item = self.item(i)
            item.setSelected(item.data(Qt.UserRole) in fields)

    def selection(self) -> list:
        selection = []
        for i in range(self.count()):
            item = self.item(i)
            if item.isSelected():
                selection.append(item.data(Qt.UserRole))
        return selection
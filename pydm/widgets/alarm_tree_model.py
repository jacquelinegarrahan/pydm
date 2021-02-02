from qtpy import QtCore
from qtpy.QtCore import QModelIndex, QVariant, Qt, Slot
from qtpy.QtGui import QBrush, QColor




class AlarmTreeModel(QtCore.QAbstractItemModel):
    def __init__(self, tree, parent=None):
        super(AlarmTreeModel, self).__init__(parent)
        self._tree = tree

    def columnCount(self, parent=QtCore.QModelIndex()):
        return self._tree.rootItem.columnCount()

    def data(self, index, role):
        if not index.isValid():
            return None

        item = self.getItem(index)
        
        if role in [QtCore.Qt.DisplayRole, QtCore.Qt.EditRole]:
            return item.data(0)

        if role == QtCore.Qt.TextColorRole:

            # no alarm
            if item._severity == 0:
                return QBrush(QtCore.Qt.green)

            # minor alarm
            elif item._severity == 1:
                return QBrush(QColor(250, 199, 0))

            # major alarm
            elif item._severity == 2: 
                return QBrush(QtCore.Qt.red)

            # invalid
            elif item._severity == 3:
                return QBrush(GtGui.QColor(102, 0, 255))

            # disconnected
            elif item._severity == 4:
                return QBrush(QtCore.Qt.black)

            # major/minor ack
            elif item._severity == 5:
                return QBrush(QColor(86, 86, 86))

            # major/minor ack
            elif item._severity == 6:
                return QBrush(QColor(86, 86, 86))



    def flags(self, index):
        if not index.isValid():
            return 0

        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def getItem(self, index):
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item

        else:
            return self._tree.rootItem

    def index(self, row, column, parent=QtCore.QModelIndex()):
        if parent.isValid() and parent.column() != 0:
            return QtCore.QModelIndex()

        parent = self.getItem(parent)
        childItem = parent.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()


    def insertRows(self, position, rows, parent=QtCore.QModelIndex()):
        parent_item = self.getItem(parent)
        self.beginInsertRows(parent, position, position + rows - 1)
        child = parent_item.addChild(position)
        child.data_changed.connect(self.update_values)

        self._tree.addNode(child)
        self.endInsertRows()

        return True

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        childItem = self.getItem(index)
        parent = childItem.parent()

        if not parent:
            return QtCore.QModelIndex()

        if parent == self._tree.rootItem:
            return QtCore.QModelIndex()

        return self.createIndex(parent.childNumber(), 0, parent)


    def removeRow(self, position, parent=QtCore.QModelIndex()):
        parent_item = self.getItem(parent)

        self.beginRemoveRows(parent, position, position)
        item = parent_item.removeChildren(position)
        self._tree.removeNode(item)

        # disconnect
        item.data_changed.disconnect(self.update_values)
        self.endRemoveRows()

        return True

    def rowCount(self, parent=QtCore.QModelIndex()):
        parent = self.getItem(parent)

        return parent.childCount()

    def setData(self, index, value=None, role=QtCore.Qt.EditRole, address=None):
        if role != QtCore.Qt.EditRole:
            return False

        item = self.getItem(index)

        if value: 
            result = item.set_label(value)

        if address:
            result = item.set_address(address) and result

        if result:
            self.dataChanged.emit(index, index)

        return result

    def set_address(self, index, value, role=QtCore.Qt.EditRole):
        if role != QtCore.Qt.EditRole:
            return False

        item = self.getItem(index)
        item.address = value

        self.dataChanged.emit(index, index)

        return True


    @Slot()
    def update_values(self):
        self.layoutChanged.emit()



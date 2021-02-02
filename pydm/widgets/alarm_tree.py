import json
from qtpy.QtWidgets import QTreeView, QFrame, QVBoxLayout, QAbstractItemView, QMenu
from qtpy.QtCore import Qt, Slot, QModelIndex, QItemSelection, QEvent, QRect, QObject, Signal
from qtpy.QtWidgets import QToolTip
from pydm.widgets.label import PyDMLabel
from qtpy.QtCore import Slot, Property
from functools import partial
from .channel import PyDMChannel
from .alarm_tree_model import AlarmTreeModel
from .base import PyDMWritableWidget, TextFormatter, str_types
from .. import utilities


class TreeItem(QObject):
    data_changed = Signal()
    send_value_signal = Signal(bool)

    def __init__(self, data, parent=None, address=""):
        super(TreeItem, self).__init__()
        self.parent_item = parent

        if not data:
            data=["NONE"]

        self.item_data = data
        self.children = []
        self.channel = None
        self.address = address
        self._channels = []
        self._severity = None

        if hasattr(self, "channels"):
            self.destroyed.connect(functools.partial(widget_destroyed,
                                                     self.channels))

    def child(self, row):
        return self.children[row]

    def childCount(self):
        return len(self.children)

    def childNumber(self):
        if self.parent_item != None:
            return self.parent_item.children.index(self)
        return 0

    def columnCount(self):
        return len(self.item_data)

    def data(self, column):
        return self.item_data[column]

    def addChild(self, position):
        child = TreeItem(None, parent=self)
        self.children.insert(position, child)
        return child

    def insertChild(self, position, child):
        self.children.insert(position, child)
        return child

    def parent(self):
        return self.parent_item

    def removeChildren(self, position):
        item = self.children.pop(position)

        return item

    def set_label(self, value):
        self.item_data = [value]
        return True

    def set_address(self, address):
        self.address = address
        return True
    
    @property
    def address(self):
        if self.channel is None:
            return None
        return self.channel.address

    @address.setter
    def address(self, new_address):
        self._address = new_address
        if new_address is None or len(str(new_address)) < 1:
            self.channel = None
            return

        self.channel = PyDMChannel(address=new_address,
                                   connection_slot=self.connectionStateChanged,
                                   value_slot=self.receiveNewValue,
                                   severity_slot=self.receiveNewSeverity,
                                   value_signal=self.send_value_signal,
                                   )


    def assignParent(self, parent):
        self.parent_item = parent

    def to_dict(self):
        return {"data": self.item_data, "address": self.address}

    @classmethod
    def from_dict(cls, data_map):
        data = data_map["data"]
        address = data_map["address"]
        return cls(data, address=address)

    @Slot(int)
    def receiveNewSeverity(self, new_severity):
        self._severity = new_severity
        self.data_changed.emit()

    @Slot(str)
    def receiveNewValue(self, new_value):
        self.data_changed.emit()

    @Slot(bool)
    def connectionStateChanged(self, connected):
        pass

    @Slot(bool)
    def acknowledge(self):
        self.send_value_signal.emit(True)

    @Slot(bool)
    def unacknowledge(self):
        self.send_value_signal.emit(False)




class PyDMAlarmTree(QTreeView, PyDMWritableWidget):

    def __init__(self, parent, init_channel=None):
        super(PyDMAlarmTree, self).__init__()

        QTreeView.__init__(self, parent)
        PyDMWritableWidget.__init__(self)
        
        self.setup_ui()

        self._nodes = []

        # Placeholder...
        rootData = ["Demo"]
        self.rootItem = TreeItem(rootData)
        self._nodes.append(self.rootItem)

        self.tree_model = AlarmTreeModel(self)
        self.setModel(self.tree_model)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._open_menu)


        if utilities.is_qt_designer():
            self.installEventFilter(self)

    def setup_ui(self):
        if not utilities.is_qt_designer():
            self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setDragDropOverwriteMode(False)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setHeaderHidden(True)
        self.setColumnWidth(0, 160)
        self.setColumnWidth(1, 160)
        self.setColumnWidth(2, 160)
        self.expandAll()



    def eventFilter(self, obj, event):
        ret = super(PyDMAlarmTree, self).eventFilter(obj, event)
        if utilities.is_qt_designer():
            if event.type() == QEvent.Enter:
                QToolTip.showText(
                    self.mapToGlobal(self.rect().center()),
                    'Edit table via Right-Click and select "Edit Table..."',
                    self,
                    QRect(0, 0, 200, 100),
                    4000)
        else:
            # Somehow super here is not invoking the PyDMPrimitiveWidget
            # eventFilter
            ret = PyDMWritableWidget.eventFilter(self, obj, event)

        return ret


    def clearNodes(self):
        self._nodes = []

    def addNode(self, item):
        self._nodes.append(item)
    
    def removeNode(self, node):
        self._nodes.remove(node)
        if len(self._nodes) < 1:
            # create root
            pass

    def removeNodeAtIndex(self, index):
        node_to_remove = self._nodes[index]
        self.removeNode(node_to_remove)

    def setNodeAtIndex(self, index, new_node):
        old_node = self._nodes[index]
        self._nodes[nodes] = new_node

    def nodeAtIndex(self, index):
        return self._nodes[index]

    def addChannel(self, node):
        self.addNode(node)

    def getNodes(self):
        hierarchy = self.get_hierarchy()
        return hierarchy

    def setNodes(self, new_hierarchy):
        try:
            new_hierarchy = json.loads(new_hierarchy)

        except ValueError as e:
            print("Error parsing node json data: {}".format(e))
            return

        # Reset
        self.clear()

        for i, node in enumerate(new_hierarchy):
            node_data = node[0]
            parent_idx = node[1]

            alarm_item = TreeItem.from_dict(node[0])
            self._nodes.append(alarm_item)

            if parent_idx is not None:
                alarm_item.assignParent(self._nodes[node[1]])
                self._nodes[node[1]].insertChild(-1, alarm_item)
            

            if i == 0:
                self.rootItem = alarm_item

        for node in self._nodes:
            node.data_changed.connect(self.tree_model.update_values)
            if node.channel is not None:
                node.channel.connect()
        

    # QProperty for getting/setting nodes
    nodes = Property("QString", getNodes, setNodes, designable=False)


    def get_hierarchy(self):
        hierarchy = []
        for i, node in enumerate(self._nodes):
            if node.parent_item is None:
                parent_idx = None
            else:
                parent_idx = self._nodes.index(node.parent_item)


            rep = [node.to_dict(), parent_idx]
            hierarchy.append(rep)

        return json.dumps(hierarchy)

    def clear(self):
        self._nodes = []

    def _open_menu(self, point):
        menu = QMenu()
        index = self.indexAt(point)
        menu.addAction("Acknowledge", partial(self._acknowledge_at_index, index))
        menu.addAction("Remove Acknowledge", partial(self._remove_acknowledge_at_index, index))

        menu.exec_(self.viewport().mapToGlobal(point))

    def _acknowledge_at_index(self, index):
        item = self.tree_model.getItem(index)
        item.acknowledge()

    def _remove_acknowledge_at_index(self, index):
        item = self.tree_model.getItem(index)
        item.unacknowledge()



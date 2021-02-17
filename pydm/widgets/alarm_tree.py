import json
from qtpy.QtWidgets import QTreeView, QFrame, QVBoxLayout, QAbstractItemView, QMenu, QAction
from qtpy.QtCore import Qt, Slot, QModelIndex, QItemSelectionModel, QEvent, QRect, QObject, Signal
from qtpy.QtWidgets import QToolTip
from pydm.widgets.label import PyDMLabel
from qtpy.QtCore import Slot, Property
from functools import partial
from .alarm_tree_model import AlarmTreeModel
from .base import PyDMWritableWidget, TextFormatter, str_types
from .. import utilities




class PyDMAlarmTree(QTreeView, PyDMWritableWidget):

    def __init__(self, parent, init_channel=None, config_name=None, edit_mode=False):
        super(PyDMAlarmTree, self).__init__()

        QTreeView.__init__(self, parent)
        PyDMWritableWidget.__init__(self)
        
        self.setup_ui()

        self._nodes = []

        self.config_name = config_name

        self.tree_model = AlarmTreeModel(self)
        self.setModel(self.tree_model)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        
        if not edit_mode:
            self.customContextMenuRequested.connect(self._open_menu)

        self.expandAll()

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

    def get_configuration_name(self):
        return self.config_name

    def set_configuration_name(self, config_name):
        self.config_name = config_name
        if not utilities.is_qt_designer():
            if self.config_name:
                self.tree_model.import_configuration_from_kafka(self.config_name)


    configuration_name = Property(str, get_configuration_name, set_configuration_name, designable=False)

    def _open_menu(self, point):
        menu = QMenu()
        index = self.indexAt(point)
        item = self.model().getItem(index)
        self.value_action = QAction(item.status, self)
        self.value_action.setEnabled(False)
        menu.addAction(self.value_action)

        self.acknowledge_action = QAction("Acknowledge", self)
        self.acknowledge_action.triggered.connect(partial(self._acknowledge_at_index, index))
        menu.addAction(self.acknowledge_action)

        self.remove_acknowledge_action = QAction("Remove Acknowledge", self)
        self.remove_acknowledge_action.triggered.connect(partial(self._remove_acknowledge_at_index, index))
    
        menu.addAction(self.remove_acknowledge_action)

        menu.exec_(self.viewport().mapToGlobal(point))

    def _acknowledge_at_index(self, index):
        item = self.tree_model.getItem(index)
        item.acknowledge()

    def _remove_acknowledge_at_index(self, index):
        item = self.tree_model.getItem(index)
        item.unacknowledge()

    def mousePressEvent(self, event):
        self.clearSelection()
        self.selectionModel().reset()
        QTreeView.mousePressEvent(self, event)


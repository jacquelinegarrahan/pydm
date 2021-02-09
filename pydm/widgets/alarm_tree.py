import json
from qtpy.QtWidgets import QTreeView, QFrame, QVBoxLayout, QAbstractItemView, QMenu
from qtpy.QtCore import Qt, Slot, QModelIndex, QItemSelection, QEvent, QRect, QObject, Signal
from qtpy.QtWidgets import QToolTip
from pydm.widgets.label import PyDMLabel
from qtpy.QtCore import Slot, Property
from functools import partial
from .alarm_tree_model import AlarmTreeModel
from .base import PyDMWritableWidget, TextFormatter, str_types
from .. import utilities




class PyDMAlarmTree(QTreeView, PyDMWritableWidget):

    def __init__(self, parent, init_channel=None, config_name=None):
        super(PyDMAlarmTree, self).__init__()

        QTreeView.__init__(self, parent)
        PyDMWritableWidget.__init__(self)
        
        self.setup_ui()

        self._nodes = []

        self.config_name = config_name

        self.tree_model = AlarmTreeModel(self)
        self.setModel(self.tree_model)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._open_menu)

        if utilities.is_qt_designer():
            self.installEventFilter(self)

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
        print(f"Getting config name {self.config_name}")
        return self.config_name

    def set_configuration_name(self, config_name):
        print(f"SETTING CONFIG NAME {config_name}")
        self.config_name = config_name
        if not utilities.is_qt_designer():
            if self.config_name:
                self.tree_model.import_configuration_from_kafka(self.config_name)


    configuration_name = Property(str, get_configuration_name, set_configuration_name, designable=False)


    def eventFilter(self, obj, event):
        ret = True
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
            ret = super(PyDMAlarmTree, self).eventFilter(obj, event)
            ret = PyDMWritableWidget.eventFilter(self, obj, event)
        return ret

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


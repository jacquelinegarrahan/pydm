import json
from qtpy.QtWidgets import QTreeView, QFrame, QVBoxLayout, QAbstractItemView, QMenu, QAction, QHeaderView, QLabel, QWidgetAction
from qtpy.QtCore import Qt, Slot, QModelIndex, QItemSelectionModel, QEvent, QRect, QObject, Signal
from qtpy.QtWidgets import QToolTip
from qtpy import QtGui
from pydm.widgets.label import PyDMLabel
from qtpy.QtCore import Slot, Property
from functools import partial
from .alarm_tree_model import AlarmTreeModel
from .base import PyDMWritableWidget, TextFormatter, str_types
from .. import utilities


class ValueAction(QAction):

    def __init__(self, *args, **kwargs):
        super(ValueAction, self).__init__(*args, **kwargs)

    def hovered(self): 
        return False



class PyDMAlarmTree(QTreeView, PyDMWritableWidget):

    def __init__(self, parent, init_channel=None, config_name=None, edit_mode=False):
        super(PyDMAlarmTree, self).__init__()

        QTreeView.__init__(self, parent)
        PyDMWritableWidget.__init__(self)
        
        self.setup_ui()

        self.setStyleSheet("background-color: rgb(179, 179, 179)")


        self._nodes = []

        self.config_name = config_name

        self.tree_model = AlarmTreeModel(self)
        self.setModel(self.tree_model)
        self.edit_mode = edit_mode

        self.setContextMenuPolicy(Qt.CustomContextMenu)

        if not edit_mode:
            self.customContextMenuRequested.connect(self._open_menu)


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
        if not utilities.is_qt_designer() and not self.edit_mode:
            if self.config_name:
                self.tree_model.import_configuration_from_kafka(self.config_name)


    configuration_name = Property(str, get_configuration_name, set_configuration_name, designable=False)

    def _open_menu(self, point):
        menu = QMenu()
        index = self.indexAt(point)
        item = self.model().getItem(index)


        # display trigger value
        self.value_action = QWidgetAction(menu)
        self.value_label = QLabel(item.value)
        self.value_label.setAlignment(Qt.AlignHCenter)
        self.value_action.setDefaultWidget(self.value_label)
        menu.addAction(self.value_action)

        # status 
        self.status_action = QWidgetAction(menu)
        self.status_label = QLabel(item.status)
        self.status_label.setAlignment(Qt.AlignHCenter)
        self.status_action.setDefaultWidget(self.status_label)
        menu.addAction(self.status_action)

        # severity
        self.severity_action = QWidgetAction(menu)
        print(item.last_state)
        self.severity_label = QLabel(item.last_state["severity"])

        self.severity_label.setAlignment(Qt.AlignHCenter)
        self.severity_action.setDefaultWidget(self.severity_label)
        menu.addAction(self.severity_action)

        # acknowledge
        self.acknowledge_action = QAction("Acknowledge", self)
        self.acknowledge_action.triggered.connect(partial(self._acknowledge_at_index, index))
        menu.addAction(self.acknowledge_action)

        # remove acknowledge
        self.remove_acknowledge_action = QAction("Remove Acknowledge", self)
        self.remove_acknowledge_action.triggered.connect(partial(self._remove_acknowledge_at_index, index))
        menu.addAction(self.remove_acknowledge_action)


        # enable
        self.enable_action = QAction("Enable", self)
        self.enable_action.triggered.connect(partial(self._enable_at_index, index))
        menu.addAction(self.enable_action)

        # disnable
        self.disable_action = QAction("Disable", self)
        self.disable_action.triggered.connect(partial(self._disable_at_index, index))
        menu.addAction(self.disable_action)


        # add ticket
        self.add_ticket = QAction("Add CATER", self)
        self.add_ticket.triggered.connect(partial(self._add_ticket_at_index, index))
        menu.addAction(self.add_ticket)
        self.add_ticket.setEnabled(False)

        if item.acknowledged:
            self.acknowledge_action.setEnabled(False)
            self.remove_acknowledge_action.setEnabled(True)
        
        else:
            self.remove_acknowledge_action.setEnabled(False)
            self.acknowledge_action.setEnabled(True)

        
        if item.enabled:
            self.enable_action.setEnabled(False)
            self.disable_action.setEnabled(True)
        
        else:
            self.enable_action.setEnabled(False)
            self.disable_action.setEnabled(True)

        menu.exec_(self.viewport().mapToGlobal(point))

    def _acknowledge_at_index(self, index):
        item = self.tree_model.getItem(index)
        item.acknowledge()

    def _remove_acknowledge_at_index(self, index):
        item = self.tree_model.getItem(index)
        item.unacknowledge()

    
    def _enable_at_index(self, index):
        item = self.tree_model.getItem(index)
        item.enable()

    def _disable_at_index(self, index):
        item = self.tree_model.getItem(index)
        item.disable()

    def mousePressEvent(self, event):
        self.clearSelection()
        self.selectionModel().reset()
        QTreeView.mousePressEvent(self, event)

    def _add_ticket_at_index(self, index):
        pass


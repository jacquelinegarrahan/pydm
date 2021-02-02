from qtpy.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTreeView, QTableWidgetItem,
                            QAbstractItemView, QSpacerItem, QSizePolicy,
                            QDialogButtonBox, QPushButton, QMenu, QGridLayout, QTableWidget)
from qtpy.QtCore import Qt, Slot, QModelIndex, QItemSelection
from qtpy import QtCore, QtGui
from qtpy.QtDesigner import QDesignerFormWindowInterface
from .alarm_tree_model import AlarmTreeModel
from collections import OrderedDict

#TODO: Switch naming from channel to address

class AlarmTreeEditorDialog(QDialog):

    TREE_MODEL_CLASS = AlarmTreeModel

    def __init__(self, tree, parent=None):
        super(AlarmTreeEditorDialog, self).__init__(parent)
        self.tree = tree

        # set up the ui
        self.setup_ui()

        # set model for the tree view
        self.tree_view.setModel(self.tree.tree_model)

        # allow add and remove row
        self.add_button.clicked.connect(self.insertChild)
        self.remove_button.clicked.connect(self.removeRow)
        self.remove_button.setEnabled(True)

        # connect save changes
        self.button_box.accepted.connect(self.saveChanges)

        # if exit without clicking save changes, reject
        self.button_box.rejected.connect(self.reject)

        # connect save changes
        self.config_button_box.accepted.connect(self.saveConfig)

        # if exit without clicking save changes, reject
        self.config_button_box.rejected.connect(self.reject)

        # upon tree view selection, change the item view
        self.tree_view.selectionModel().selectionChanged.connect(self.handle_selection)
        self.tree.tree_model.dataChanged.connect(self.item_change)


        # upon update of value in tree, update in table
        #self.tree_view.selectionModel().

        # default open size
        self.resize(800, 600)


    def setup_ui(self):

        self.layout = QGridLayout(self)

        # create the tree view layout and add/remove buttons
        self.tree_view_layout = QVBoxLayout()
        self.tree_view = QTreeView()
        self.tree_view.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.tree_view.setDragDropOverwriteMode(False)
        self.tree_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tree_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setColumnWidth(0, 160)
        self.tree_view.setColumnWidth(1, 160)
        self.tree_view.setColumnWidth(2, 160)

        self.tree_view_layout.addWidget(self.tree_view)

        # add/ remove buttons
        self.add_remove_layout = QHBoxLayout()
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding,
                             QSizePolicy.Minimum)
        self.add_remove_layout.addItem(spacer)
        self.add_button = QPushButton("New", self)
        self.add_remove_layout.addWidget(self.add_button)
        self.remove_button = QPushButton("Remove", self)
        self.add_remove_layout.addWidget(self.remove_button)
        self.tree_view_layout.addLayout(self.add_remove_layout)

        # add the tree view to the window
        self.layout.addLayout(self.tree_view_layout, 0, 0)

        # create a layout for the table
        self.table_view_layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table_view_layout.addWidget(self.table)
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding,
                             QSizePolicy.Minimum)

        self.table.setRowCount(2)
        self.table.setColumnCount(1)
        self.table.setVerticalHeaderItem(0, QTableWidgetItem("NAME")) 
        self.table.setVerticalHeaderItem(1, QTableWidgetItem("ADDRESS"))
        
        self._selected_name = QTableWidgetItem("")
        self._selected_channel = QTableWidgetItem("")

        self.table.setItem(0, 0, self._selected_name)
        self.table.setItem(0, 1, self._selected_channel)
        self.table.horizontalHeader().hide()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setStretchLastSection(False)
        self.table.resizeRowsToContents()
        self.table.setColumnWidth(0, 160)

        self._selected_channel.setFlags( QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled)
        self._selected_name.setFlags( QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled)

        self.table_view_layout.addItem(spacer)

        # create save button
        self.button_box = QDialogButtonBox(self)
        self.button_box.setOrientation(Qt.Horizontal)
        self.button_box.addButton("Save Changes", QDialogButtonBox.AcceptRole)
        self.table_view_layout.addWidget(self.button_box)


        # add table view to the window
        self.layout.addLayout(self.table_view_layout, 0, 1)


        # create save configuration
        self.config_button_box = QDialogButtonBox(self)
        self.config_button_box.setOrientation(Qt.Horizontal)
        self.config_button_box.addButton("Save Configuration", QDialogButtonBox.AcceptRole)
        self.layout.addWidget(self.config_button_box, 1,1)

        self.setWindowTitle("Alarm Table Editor")
        self.tree_view.expandAll()


    def insertChild(self):
        index = self.tree_view.selectionModel().currentIndex()
        model = self.tree_view.model()

        if model.columnCount(index) == 0:
            if not model.insertColumn(0, index):
                return

        if not model.insertRow(0, index):
            return

        for column in range(model.columnCount(index)):
            child = model.index(0, column, index)
            model.setData(child, value="NEW_PV",
                    role=QtCore.Qt.EditRole)

        self.tree_view.selectionModel().setCurrentIndex(model.index(0, 0, index),
                QtCore.QItemSelectionModel.ClearAndSelect)
                
    def removeRow(self):
        index = self.tree_view.selectionModel().currentIndex()
        self.tree_view.model().removeRow(index.row(), index.parent())

    @Slot()
    def saveChanges(self):
        index = self.tree_view.selectionModel().currentIndex()
        self.tree_view.model().setData(index, value=self._selected_name.text(), address=self._selected_channel.text())


    @Slot()
    def saveConfig(self):
        formWindow = QDesignerFormWindowInterface.findFormWindow(self.tree)
        if formWindow:
            formWindow.cursor().setProperty("nodes", self.tree.get_hierarchy())
        self.accept()
    

    @Slot()
    def handle_selection(self):
        self.remove_button.setEnabled(
        self.tree_view.selectionModel().hasSelection())

        self._selected_channel.setFlags( QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable)
        self._selected_name.setFlags( QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable)

        index = self.tree_view.selectionModel().currentIndex()
        item = self.tree_view.model().getItem(index)

        self.table.item(0, 0).setText(item.item_data[0])
        self.table.item(1, 0).setText(item.address)

    @Slot()
    def item_change(self):
        index = self.tree_view.selectionModel().currentIndex()
        item = self.tree_view.model().getItem(index)

        self.table.item(0, 0).setText(item.item_data[0])
        self.table.item(1, 0).setText(item.address)

    @Slot()
    def item_name_changed(self):
        index = self.tree_view.selectionModel().currentIndex()
        pass
            
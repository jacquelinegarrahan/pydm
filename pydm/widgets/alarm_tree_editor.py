from qtpy.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTreeView, QTableWidgetItem,
                            QAbstractItemView, QSpacerItem, QSizePolicy, QLineEdit,
                            QDialogButtonBox, QPushButton, QMenu, QGridLayout, QTableWidget)
from qtpy.QtCore import Qt, Slot, QModelIndex, QItemSelection
from qtpy import QtCore, QtGui
from qtpy.QtDesigner import QDesignerFormWindowInterface
from .alarm_tree_model import AlarmTreeModel
from collections import OrderedDict


class AlarmTreeConfigurationImportDialog(QDialog):

    def __init__(self, tree, parent=None):
        super(AlarmTreeConfigurationImportDialog, self).__init__(parent)
        self.tree = tree

        # set up the ui
        self.setup_ui()

        self.accept_button.clicked.connect(self.import_configuration)
        self.accept_button.setEnabled(True)

    def setup_ui(self):
        self.layout = QVBoxLayout(self)

        self.input = QLineEdit()
        self.accept_button = QPushButton("Accept Configuration", self)
        self.layout.addWidget(self.input)
        self.layout.addWidget(self.accept_button)


    @Slot()
    def import_configuration(self):
        configuration = self.input.text()
    #    self.tree.tree_model.import_configuration(configuration)
        formWindow = QDesignerFormWindowInterface.findFormWindow(self.tree)
        if formWindow:
            formWindow.cursor().setProperty("configuration_name", configuration)
        self.accept()
from qtpy import QtCore
from qtpy.QtCore import QModelIndex, QVariant, Qt, Slot, QObject, Signal
from qtpy.QtGui import QBrush, QColor
import os 
from kafka import KafkaConsumer
from .channel import PyDMChannel
import time
import json
from copy import deepcopy



class AlarmTreeItem(QObject):
    data_changed = Signal()
    send_value_signal = Signal(bool)

    def __init__(self, data, parent=None, address=""):
        super(AlarmTreeItem, self).__init__()
        self.parent_item = parent

        if not data:
            data=["NAN"]

        self.item_data = data
        self.children = []
        self.channel = None
        self.address = address
        self._channels = []
        self._severity = None



        self.description = ""
        self.enabled = True
        self.latching = False
        self.count = None
        self.delay = None

        if hasattr(self, "channels"):
            self.destroyed.connect(functools.partial(widget_destroyed,
                                                     self.channels))


    # For model logic
    def child(self, row):
        return self.children[row] if len(self.children) > row else []

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

    def createChild(self, position, child_data=None):
        child = AlarmTreeItem.from_dict(child_data, parent=self)
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
    
    def assignParent(self, parent):
        self.parent_item = parent


    # data
    def set_label(self, value):
        self.item_data = [value]
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

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, description):
        self._description = description

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, enabled):
        self._enabled = enabled
    
    @property
    def latching(self):
        return self._latching

    @latching.setter
    def latching(self, latching):
        self._latching = latching

    @property
    def annunciating(self):
        return self._annunciating

    @annunciating.setter
    def latching(self, annunciating):
        self._annunciating = annunciating

    @property
    def annunciating(self):
        return self._annunciating

    @annunciating.setter
    def latching(self, annunciating):
        self._annunciating = annunciating

    @property
    def delay(self):
        return self._delay

    @delay.setter
    def delay(self, delay):
        self._delay = delay

    @property
    def count(self):
        return self._count

    @count.setter
    def count(self, count):
        self._count = count



    @property
    def filter(self):
        return self._filter

    @annunciating.setter
    def filter(self, filter):
        self._filter = filter

    # command

    # automated action

    # Update functions
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


    # For recreation    
    def to_dict(self):
        return {"data": self.item_data, "address": self.address}

    @classmethod
    def from_dict(cls, data_map, parent=None):
        if data_map:
            data = data_map.get("data")
            address = data_map.get("address")

        else:
            data = None
            address = None

        return cls(data, parent=parent, address=address)



class AlarmTreeModel(QtCore.QAbstractItemModel):
    def __init__(self, tree, parent=None):
        super(AlarmTreeModel, self).__init__(parent)
        self._nodes = []
        self._tree = tree
        self._root_item = AlarmTreeItem([self._tree.config_name])
        self._nodes.append(self._root_item)

    def clear(self):
        self._nodes = []
        self._root_item = None

    def columnCount(self, parent=QtCore.QModelIndex()):
        return self._root_item.columnCount()

    def rowCount(self, parent=QtCore.QModelIndex()):
        parent = self.getItem(parent)

        return parent.childCount()


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
            
            # undefined
            elif item._severity == 7:
                return QBrush(QtCore.Qt.black)

            #undefined ack
            elif item._severity == 8:
                return QBrush(QColor(86, 86, 86))


    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled

        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled


    def getItem(self, index):
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item

        else:
            return self._root_item


    def index(self, row, column, parent=QtCore.QModelIndex()):
        if parent.isValid() and parent.column() != 0:
            return QtCore.QModelIndex()

        parent = self.getItem(parent)
        childItem = parent.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()


    def insertRow(self, position, parent=QtCore.QModelIndex(), child_data=None):
        if not parent:
            return False

        parent_item = self.getItem(parent)
        self.beginInsertRows(parent, position, position)
        child = parent_item.createChild(position, child_data=child_data)
        child.data_changed.connect(self.update_values)
        self.addNode(child)
        self.endInsertRows()

        return True

    

    def removeRow(self, position, parent=QtCore.QModelIndex()):
        parent_item = self.getItem(parent)

        self.beginRemoveRows(parent, position, position)
        item = parent_item.removeChildren(position)
        self.removeNode(item)

        # disconnect
        item.data_changed.disconnect(self.update_values)
        self.endRemoveRows()

        return True


    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        childItem = self.getItem(index)
        parent = childItem.parent()

        if not parent:
            return QtCore.QModelIndex()

        if parent == self._root_item:
            return QtCore.QModelIndex()

        return self.createIndex(parent.childNumber(), 0, parent)



    def set_data(self, index, label=None, role=QtCore.Qt.EditRole, address=None):
        if role != QtCore.Qt.EditRole:
            return False

        item = self.getItem(index)

        if value: 
            result = item.set_label(label)

        if address:
            item.address = address

        if result:
            self.dataChanged.emit(index, index)

        return result



    @Slot()
    def update_values(self):
        self.layoutChanged.emit()


    # drag/drop

    def supportedDropActions(self):
        return Qt.MoveAction

    def mimeTypes(self):
        return ['text/plain']

    def mimeData(self, indexes):
        mimedata = QtCore.QMimeData()
        item = self.getItem(indexes[0])

        if self.hasChildren(indexes[0]):
            print("HAS CHILDREN... HANDLE!")


        data = json.dumps(item.to_dict())
        mimedata.setText(data)
        return mimedata


    def dropMimeData(self, mimedata, action, row, column, parentIndex):

        if action == Qt.IgnoreAction: return True

        dropped_data = json.loads(mimedata.text())

        prior_index = self._tree.selectionModel().currentIndex()
        selected_parent = self.parent(prior_index)
        selected_row = prior_index.row()

        self.removeRow(selected_row, parent=selected_parent)
        self.insertRow(row, parent=parentIndex, child_data=dropped_data)

        return True


    def addNode(self, item):
        self._nodes.append(item)
    
    def removeNode(self, node):
        self._nodes.remove(node)
        if len(self._nodes) < 1:
            pass


    def getNodes(self):
        hierarchy = self._get_hierarchy()
        return hierarchy

    def _get_hierarchy(self):
        hierarchy = []
        for i, node in enumerate(self._nodes):
            if node.parent_item is None:
                parent_idx = None
            else:
                parent_idx = self._nodes.index(node.parent_item)


            rep = [node.to_dict(), parent_idx]
            hierarchy.append(rep)

        return json.dumps(hierarchy)

    def import_hierarchy(self, hierarchy):
        """
        Accepts a list of node representations in the list format [dictionary representation, parent]
        """
        for i, node in enumerate(hierarchy):
            node_data = node[0]
            parent_idx = node[1]

            alarm_item = AlarmTreeItem.from_dict(node[0])
            self._nodes.append(alarm_item)

            if parent_idx is not None:
                alarm_item.assignParent(self._nodes[node[1]])
                self._nodes[node[1]].insertChild(-1, alarm_item)
            

            if i == 0:
                self._root_item = alarm_item

        for node in self._nodes:
            node.data_changed.connect(self.update_values)
            if node.channel is not None:
                node.channel.connect()


    # configuration handling
    def import_configuration_from_kafka(self, alarm_configuration):

        # quick setup + parse of kafka compacted topic to construct tree....
        kafka_url = os.getenv("KAFKA_URL")

        consumer = KafkaConsumer(
            alarm_configuration,
            bootstrap_servers=[kafka_url],
            enable_auto_commit=True,
            key_deserializer=lambda x: x.decode('utf-8')
        )

        while not consumer._client.poll(): continue
        consumer.seek_to_beginning()

        key_paths = []
        keys = {}

        start = time.time() * 1000
        last_time = -100000
        while last_time < start:
            message = consumer.poll()
            for topic_partition in message:
                for record in message[topic_partition]:
                    last_time = record.timestamp
                    if last_time < start:
                        key_path = record.key.split(":/")[1]

                        # track key path
                        if key_path not in key_paths:

                            key_paths.append(key_path)
                            key_split = key_path.split("/")
                            
                            if len(key_split) not in keys:
                                keys[len(key_split)] = [{"key_path": key_path, "key_split": key_split}]

                            else:
                                keys[len(key_split)].append({"key_path": key_path, "key_split": key_split})


        nodes = []                    
        hierarchy = []

        max_depth = max(keys.keys())
        for depth in range(1, max_depth + 1):
            
            for key in keys[depth]:
                data = {"data": [key["key_split"][-1]], "address": f"alarm://{key['key_path']}"}

                nodes.append(key["key_path"])

                if depth > 1: 
                    parent = "/".join(key["key_split"][:-1])
                    parent_idx = nodes.index(parent)

                else:
                    parent_idx = None

                rep = [data, parent_idx]
                hierarchy.append(rep)

        # Reset
        self.clear()
        self.import_hierarchy(hierarchy)

        # trigger layout changed signal
        self.update_values()

# ----------------------------------------------------------------------------
#
# Copyright 2018 EMVA
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# ----------------------------------------------------------------------------


# Standard library imports
import sys

# Related third party imports
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QMainWindow, QApplication, QTreeView, \
    QAction, QComboBox, QLineEdit, QLabel, QShortcut

from genapi import EVisibility

# Local application/library specific imports
from core.thread_ import MutexLocker
from frontend.helper import compose_tooltip
from frontend.pyqt.action import Action
from frontend.pyqt.feature_tree import FeatureEditDelegate, FilterProxyModel, \
    FeatureTreeModel
from frontend.pyqt.helper import get_system_font
from frontend.pyqt.icon import Icon


"""

If you got into a trouble relate to model, the following tool could give
you a hint. ModelTest is a Python script and it tests your model and report
the result:

https://github.com/bgr/PyQt5_modeltest/tree/842904692a1d8286c6a87c9e6544f4abe553eb12

"""


class ActionExpandAll(Action):
    def __init__(self, parent_widget, icon, title):
        super().__init__(parent_widget, icon, title)

    def _execute(self):
        self._parent_widget.expand_all()

    def update(self):
        pass


class ActionCollapseAll(Action):
    def __init__(self, parent_widget, icon, title):
        #
        super().__init__(parent_widget, icon, title)

    def _execute(self):
        self._parent_widget.collapse_all()

    def update(self):
        pass


class AttributeController(QMainWindow):
    _visibility_dict = {
        'Beginner': EVisibility.Beginner,
        'Expert': EVisibility.Expert,
        'Guru': EVisibility.Guru,
        'All': EVisibility.Invisible,
    }

    def __init__(self, node_map, parent_widget=None):
        #
        super().__init__(parent_widget)

        #
        self._parent_widget = parent_widget

        #
        self.setWindowTitle('Attribute Controller')

        #
        self._view = QTreeView()
        self._view.setFont(get_system_font())

        #
        self._node_map = node_map
        self._model = FeatureTreeModel(
            self,
            self._node_map,
            self._parent_widget.harvester_core.thread_image_acquisition
        )

        #
        self._proxy = FilterProxyModel()
        self._proxy.setSourceModel(self._model)
        self._proxy.setDynamicSortFilter(True)

        #
        self._delegate = FeatureEditDelegate(proxy=self._proxy)
        self._view.setModel(self._proxy)
        self._view.setItemDelegate(self._delegate)
        self._view.setUniformRowHeights(True)

        #
        unit = 260
        for i in range(2):
            self._view.setColumnWidth(i, unit)

        w, h = 700, 600
        self._view.setGeometry(100, 100, w, h)

        self.setCentralWidget(self._view)
        self.setGeometry(100, 100, unit * 2, 640)

        self._combo_box_visibility = None
        self._line_edit_search_box = None

        #
        self._setup_toolbars()

    def _setup_toolbars(self):
        #
        group_filter = self.addToolBar('Node Visibility')
        group_manipulation = self.addToolBar('Node Tree Manipulation')

        #
        label_visibility = QLabel()
        label_visibility.setText('Visibility')
        label_visibility.setFont(get_system_font())

        #
        self._combo_box_visibility = QComboBox()
        self._combo_box_visibility.setSizeAdjustPolicy(
            QComboBox.AdjustToContents
        )

        items = ('Beginner', 'Expert', 'Guru', 'All')
        for item in items:
            self._combo_box_visibility.addItem(item)

        shortcut_key = 'Ctrl+v'
        shortcut = QShortcut(QKeySequence(shortcut_key), self)

        def show_popup():
            self._combo_box_visibility.showPopup()

        shortcut.activated.connect(show_popup)

        self._combo_box_visibility.setToolTip(
            compose_tooltip('Filter the nodes to show', shortcut_key)
        )
        self._combo_box_visibility.setFont(get_system_font())
        self._combo_box_visibility.currentIndexChanged.connect(
            self._invalidate_feature_tree_by_visibility
        )

        #
        button_expand_all = ActionExpandAll(
            self, Icon('expand.png'), 'Expand All'
        )
        shortcut_key = 'Ctrl+e'
        button_expand_all.setToolTip(
            compose_tooltip('Expand the node tree', shortcut_key)
        )
        button_expand_all.setShortcut(shortcut_key)
        button_expand_all.toggle()

        #
        button_collapse_all = ActionCollapseAll(
            self, Icon('collapse.png'), 'Collapse All'
        )
        shortcut_key = 'Ctrl+c'
        button_collapse_all.setToolTip(
            compose_tooltip('Collapse the node tree', shortcut_key)
        )
        button_collapse_all.setShortcut(shortcut_key)
        button_collapse_all.toggle()

        #
        label_search = QLabel()
        label_search.setText('RegEx Search')
        label_search.setFont(get_system_font())

        #
        self._line_edit_search_box = QLineEdit()
        self._line_edit_search_box.setFont(get_system_font())
        self._line_edit_search_box.textEdited.connect(
            self._invalidate_feature_tree_by_keyword
        )

        #
        group_filter.addWidget(label_visibility)
        group_filter.addWidget(self._combo_box_visibility)
        group_filter.addWidget(label_search)
        group_filter.addWidget(self._line_edit_search_box)
        group_filter.setStyleSheet('QToolBar{spacing:6px;}')

        #
        group_manipulation.addAction(button_expand_all)
        group_manipulation.addAction(button_collapse_all)

        #
        group_manipulation.actionTriggered[QAction].connect(
            self.on_button_clicked_action
        )

    def _invalidate_feature_tree_by_visibility(self):
        with MutexLocker(self._parent_widget.harvester_core.thread_image_acquisition):
            visibility = self._visibility_dict[
                self._combo_box_visibility.currentText()
            ]
            self._proxy.setVisibility(visibility)
            self._view.expandAll()

    @pyqtSlot('QString')
    def _invalidate_feature_tree_by_keyword(self, keyword):
        with MutexLocker(self._parent_widget.harvester_core.thread_image_acquisition):
            self._proxy.setKeyword(keyword)
            self._view.expandAll()

    @staticmethod
    def on_button_clicked_action(action):
        action.execute()

    def expand_all(self):
        self._view.expandAll()

    def collapse_all(self):
        self._view.collapseAll()

    def resize_column_width(self):
        for i in range(self._model.columnCount()):
            self._view.resizeColumnToContents(i)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    about = AttributeController()
    about.show()
    sys.exit(app.exec_())

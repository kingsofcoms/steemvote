
from PyQt4.QtGui import *
from PyQt4.QtCore import *

from steemvote.gui.util import floated_buttons

class MinutesWidget(QDoubleSpinBox):
    """Widget for setting a timespan in minutes."""
    def __init__(self, parent=None):
        super(MinutesWidget, self).__init__(parent)
        self.setRange(0.1, 1000.0)
        self.setDecimals(2)
        self.setSuffix(' minutes')

class SettingsModel(QAbstractTableModel):
    """Model for settings."""
    MIN_POST_AGE = 0
    MAX_POST_AGE = 1
    PRIORITY_HIGH = 2
    PRIORITY_NORMAL = 3
    PRIORITY_LOW = 4
    TOTAL_FIELDS = 5
    def __init__(self, config, parent=None):
        super(SettingsModel, self).__init__(parent)
        self.config = config

    def save(self):
        self.config.save()

    def columnCount(self, parent=QModelIndex()):
        return self.TOTAL_FIELDS

    def rowCount(self, parent=QModelIndex()):
        return 1

    def data(self, index, role = Qt.DisplayRole):
        if not index.isValid():
            return None

        data = None
        c = index.column()
        if c == self.MIN_POST_AGE:
            data = self.config.get_seconds('min_post_age') / 60.0
        elif c == self.MAX_POST_AGE:
            data = self.config.get_seconds('max_post_age') / 60.0
        elif c == self.PRIORITY_HIGH:
            data = self.config.get_decimal('priority_high') * 100.0
        elif c == self.PRIORITY_NORMAL:
            data = self.config.get_decimal('priority_normal') * 100.0
        elif c == self.PRIORITY_LOW:
            data = self.config.get_decimal('priority_low') * 100.0

        return data

    def setData(self, index, value, role = Qt.EditRole):
        if not index.isValid():
            return False
        if value is None:
            return False

        c = index.column()
        if c == self.MIN_POST_AGE:
            value = str(round(value, 2)) + ' minutes'
            self.config.set('min_post_age', value)
        elif c == self.MAX_POST_AGE:
            value = str(round(value, 2)) + ' minutes'
            self.config.set('max_post_age', value)
        elif c == self.PRIORITY_HIGH:
            value = str(round(value, 4)) + '%'
            self.config.set('priority_high', value)
        elif c == self.PRIORITY_NORMAL:
            value = str(round(value, 4)) + '%'
            self.config.set('priority_normal', value)
        elif c == self.PRIORITY_LOW:
            value = str(round(value, 4)) + '%'
            self.config.set('priority_low', value)
        else:
            return False

        self.dataChanged.emit(index, index)
        return True

class SettingsWidget(QWidget):
    settingsChanged = pyqtSignal()
    def __init__(self, config, parent=None):
        super(SettingsWidget, self).__init__(parent)
        self.model = SettingsModel(config)
        self.model.dataChanged.connect(self.check_conflicting_values)
        self.config = config

        self.min_post_age = MinutesWidget()
        self.max_post_age = MinutesWidget()

        self.priority_high = QDoubleSpinBox()
        self.priority_normal = QDoubleSpinBox()
        self.priority_low = QDoubleSpinBox()

        for widget in [self.priority_high, self.priority_normal, self.priority_low]:
            widget.setRange(1.0, 100.0)
            widget.setDecimals(4)
            widget.setSingleStep(0.1)
            widget.setSuffix('%')

        self.mapper = QDataWidgetMapper()
        self.mapper.setModel(self.model)
        self.mapper.addMapping(self.min_post_age, self.model.MIN_POST_AGE)
        self.mapper.addMapping(self.max_post_age, self.model.MAX_POST_AGE)
        self.mapper.addMapping(self.priority_high, self.model.PRIORITY_HIGH)
        self.mapper.addMapping(self.priority_normal, self.model.PRIORITY_NORMAL)
        self.mapper.addMapping(self.priority_low, self.model.PRIORITY_LOW)

        self.error_label = QLabel()
        self.error_label.setStyleSheet('QLabel {color: red;}')
        self.save_settings_button = QPushButton('Save Settings')
        self.save_settings_button.clicked.connect(self.save_settings)

        form = QFormLayout()
        form.addRow('Minimum post age:', self.min_post_age)
        form.addRow('Maximum post age:', self.max_post_age)
        form.addRow('Minimum voting power (high priority):', self.priority_high)
        form.addRow('Minimum voting power (normal priority):', self.priority_normal)
        form.addRow('Minimum voting power (low priority):', self.priority_low)
        form.addRow(floated_buttons([self.error_label, self.save_settings_button]))

        self.setLayout(form)

        self.mapper.setCurrentIndex(0)

    def save_settings(self):
        """Save config settings."""
        self.model.save()
        self.settingsChanged.emit()

    def disable_saving(self, reason):
        """Disable saving."""
        self.error_label.setText(reason)
        self.save_settings_button.setEnabled(False)

    def check_conflicting_values(self):
        """Check for settings which conflict with each other."""
        self.error_label.setText('')
        self.save_settings_button.setEnabled(True)
        # Check min/max post age.
        if self.min_post_age.value() > self.max_post_age.value():
            return self.disable_saving('Minimum post age cannot be more than maximum post age')
        # Check priority values.
        if not self.priority_low.value() >= self.priority_normal.value() >= self.priority_high.value():
            return self.disable_saving('Priority values must be as follows: low >= normal >= high')

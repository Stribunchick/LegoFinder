# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_mainwindow.ui'
##
## Created by: Qt User Interface Compiler version 6.10.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QMainWindow,
    QMenuBar, QPushButton, QSizePolicy, QSlider,
    QSpacerItem, QStatusBar, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1121, 782)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.frame = QFrame(self.centralwidget)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout = QVBoxLayout(self.frame)
        self.verticalLayout.setObjectName(u"verticalLayout")

        self.gridLayout.addWidget(self.frame, 0, 1, 5, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 4, 0, 1, 1)

        self.groupBox_2 = QGroupBox(self.centralwidget)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.verticalLayout_3 = QVBoxLayout(self.groupBox_2)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.static_select_part_label = QLabel(self.groupBox_2)
        self.static_select_part_label.setObjectName(u"static_select_part_label")

        self.horizontalLayout.addWidget(self.static_select_part_label)

        self.select_part_combo_box = QComboBox(self.groupBox_2)
        self.select_part_combo_box.setObjectName(u"select_part_combo_box")

        self.horizontalLayout.addWidget(self.select_part_combo_box)


        self.verticalLayout_3.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.static_conf_thres_label = QLabel(self.groupBox_2)
        self.static_conf_thres_label.setObjectName(u"static_conf_thres_label")

        self.horizontalLayout_2.addWidget(self.static_conf_thres_label)

        self.conf_thres_slider = QSlider(self.groupBox_2)
        self.conf_thres_slider.setObjectName(u"conf_thres_slider")
        self.conf_thres_slider.setOrientation(Qt.Orientation.Horizontal)

        self.horizontalLayout_2.addWidget(self.conf_thres_slider)


        self.verticalLayout_3.addLayout(self.horizontalLayout_2)


        self.gridLayout.addWidget(self.groupBox_2, 2, 0, 1, 1)

        self.groupBox = QGroupBox(self.centralwidget)
        self.groupBox.setObjectName(u"groupBox")
        self.verticalLayout_2 = QVBoxLayout(self.groupBox)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.add_part_button = QPushButton(self.groupBox)
        self.add_part_button.setObjectName(u"add_part_button")

        self.verticalLayout_2.addWidget(self.add_part_button)


        self.gridLayout.addWidget(self.groupBox, 0, 0, 1, 1)

        self.groupBox_3 = QGroupBox(self.centralwidget)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.horizontalLayout_3 = QHBoxLayout(self.groupBox_3)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.start_stop_acq_button = QPushButton(self.groupBox_3)
        self.start_stop_acq_button.setObjectName(u"start_stop_acq_button")
        self.start_stop_acq_button.setCheckable(True)

        self.horizontalLayout_3.addWidget(self.start_stop_acq_button)

        self.load_img_src_button = QPushButton(self.groupBox_3)
        self.load_img_src_button.setObjectName(u"load_img_src_button")

        self.horizontalLayout_3.addWidget(self.load_img_src_button)


        self.gridLayout.addWidget(self.groupBox_3, 3, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1121, 22))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("MainWindow", u"GroupBox", None))
        self.static_select_part_label.setText(QCoreApplication.translate("MainWindow", u"\u0412\u044b\u0431\u0440\u0430\u0442\u044c \u0434\u0435\u0442\u0430\u043b\u044c", None))
        self.static_conf_thres_label.setText(QCoreApplication.translate("MainWindow", u"\u041f\u043e\u0440\u043e\u0433 \u0443\u0432\u0435\u0440\u0435\u043d\u043d\u043e\u0441\u0442\u0438", None))
        self.groupBox.setTitle(QCoreApplication.translate("MainWindow", u"GroupBox", None))
        self.add_part_button.setText(QCoreApplication.translate("MainWindow", u"\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u0434\u0435\u0442\u0430\u043b\u044c", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("MainWindow", u"\u0423\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0435 \u043a\u0430\u043c\u0435\u0440\u043e\u0439", None))
        self.start_stop_acq_button.setText(QCoreApplication.translate("MainWindow", u"\u0421\u0442\u0430\u0440\u0442/\u0421\u0442\u043e\u043f", None))
#if QT_CONFIG(tooltip)
        self.load_img_src_button.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.load_img_src_button.setText(QCoreApplication.translate("MainWindow", u"\u0417\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u044c \u0438\u0437\u043e\u0431\u0440\u0430\u0436\u0435\u043d\u0438\u0435/\u0432\u0438\u0434\u0435\u043e", None))
    # retranslateUi


# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'add_part_window.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_AddPartWindow(object):
    def setupUi(self, AddPartWindow):
        if not AddPartWindow.objectName():
            AddPartWindow.setObjectName(u"AddPartWindow")
        AddPartWindow.resize(670, 491)
        self.gridLayout = QGridLayout(AddPartWindow)
        self.gridLayout.setObjectName(u"gridLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.videostream_frame = QFrame(AddPartWindow)
        self.videostream_frame.setObjectName(u"videostream_frame")
        self.videostream_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.videostream_frame.setFrameShadow(QFrame.Shadow.Raised)
        self.gridLayout_2 = QGridLayout(self.videostream_frame)
        self.gridLayout_2.setObjectName(u"gridLayout_2")

        self.horizontalLayout.addWidget(self.videostream_frame)

        self.static_frame = QFrame(AddPartWindow)
        self.static_frame.setObjectName(u"static_frame")
        self.static_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.static_frame.setFrameShadow(QFrame.Shadow.Raised)
        self.gridLayout_3 = QGridLayout(self.static_frame)
        self.gridLayout_3.setObjectName(u"gridLayout_3")

        self.horizontalLayout.addWidget(self.static_frame)


        self.gridLayout.addLayout(self.horizontalLayout, 0, 2, 3, 2)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.part_name_label = QLabel(AddPartWindow)
        self.part_name_label.setObjectName(u"part_name_label")

        self.horizontalLayout_2.addWidget(self.part_name_label)

        self.lineEdit = QLineEdit(AddPartWindow)
        self.lineEdit.setObjectName(u"lineEdit")

        self.horizontalLayout_2.addWidget(self.lineEdit)


        self.gridLayout.addLayout(self.horizontalLayout_2, 0, 0, 1, 1)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.snapshot_button = QPushButton(AddPartWindow)
        self.snapshot_button.setObjectName(u"snapshot_button")

        self.verticalLayout_3.addWidget(self.snapshot_button)

        self.load_image_button = QPushButton(AddPartWindow)
        self.load_image_button.setObjectName(u"load_image_button")

        self.verticalLayout_3.addWidget(self.load_image_button)


        self.gridLayout.addLayout(self.verticalLayout_3, 1, 0, 1, 1)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 0, 1, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 2, 0, 1, 1)


        self.retranslateUi(AddPartWindow)

        QMetaObject.connectSlotsByName(AddPartWindow)
    # setupUi

    def retranslateUi(self, AddPartWindow):
        AddPartWindow.setWindowTitle(QCoreApplication.translate("AddPartWindow", u"Form", None))
        self.part_name_label.setText(QCoreApplication.translate("AddPartWindow", u"\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u0434\u0435\u0442\u0430\u043b\u0438", None))
        self.snapshot_button.setText(QCoreApplication.translate("AddPartWindow", u"\u0421\u0434\u0435\u043b\u0430\u0442\u044c \u0441\u043d\u0438\u043c\u043e\u043a", None))
        self.load_image_button.setText(QCoreApplication.translate("AddPartWindow", u"\u0417\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u044c \u0438\u0437\u043e\u0431\u0440\u0430\u0436\u0435\u043d\u0438\u0435", None))
    # retranslateUi


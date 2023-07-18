
TEMPLATE = app

QT += widgets

SOURCES += example_new_api.cpp

SOURCES += mainwindow.cpp
HEADERS += mainwindow.h

HEADERS += mapping.h

INCLUDEPATH += ../../include/ ../../build
LIBS += -L../../build/ -lpsmoveapi -lpsmoveapi_tracker


cmake_minimum_required(VERSION 3.16)
project(GYROCUELaser VERSION 6.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)

find_package(Qt6 REQUIRED COMPONENTS Widgets)
qt_standard_project_setup()

set(SOURCES
    src/main.cpp
    src/lasercontroller.cpp
    src/overlaywindow.cpp
    src/panelwindow.cpp
)

set(HEADERS
    src/lasercontroller.h
    src/overlaywindow.h
    src/panelwindow.h
)

qt_add_executable(GYROCUELaser
    WIN32
    MACOSX_BUNDLE
    ${SOURCES}
    ${HEADERS}
    resources/resources.qrc
)

qt_add_resources(GYROCUELaser "appresources"
    PREFIX "/"
    FILES
        resources/logo_panel.png
)

target_link_libraries(GYROCUELaser PRIVATE Qt6::Widgets)

if(WIN32)
    target_link_libraries(GYROCUELaser PRIVATE user32)
    set_target_properties(GYROCUELaser PROPERTIES
        WIN32_EXECUTABLE TRUE
    )
    if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/resources/GYROCUELaser.ico")
        target_sources(GYROCUELaser PRIVATE resources/app.rc)
    endif()
endif()

if(APPLE)
    set_target_properties(GYROCUELaser PROPERTIES
        MACOSX_BUNDLE_GUI_IDENTIFIER "com.gyrocue.laser"
        MACOSX_BUNDLE_BUNDLE_VERSION ${PROJECT_VERSION}
        MACOSX_BUNDLE_SHORT_VERSION_STRING ${PROJECT_VERSION}
        MACOSX_BUNDLE_BUNDLE_NAME "GYROCUELaser"
    )
    find_library(CARBON_LIB Carbon)
    find_library(APPKIT_LIB AppKit)
    find_library(IOKIT_LIB IOKit)
    find_library(COREGRAPHICS_LIB CoreGraphics)
    target_link_libraries(GYROCUELaser PRIVATE
        ${CARBON_LIB} ${APPKIT_LIB} ${IOKIT_LIB} ${COREGRAPHICS_LIB})
endif()

install(TARGETS GYROCUELaser
    BUNDLE  DESTINATION .
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)

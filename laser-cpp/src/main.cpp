#include <QApplication>
#include <QIcon>
#include <QPixmap>

#include "lasercontroller.h"
#include "overlaywindow.h"
#include "panelwindow.h"

#ifdef Q_OS_WIN
#  include <windows.h>
#endif

int main(int argc, char *argv[])
{
#ifdef Q_OS_WIN
    // Enable HiDPI on Windows
    SetProcessDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2);
#endif

    QApplication app(argc, argv);
    app.setApplicationName("GYROCUELaser");
    app.setOrganizationName("Gyrocue Kft");
    app.setApplicationVersion("6.0");
    app.setQuitOnLastWindowClosed(false);

    // App icon
    QPixmap iconPix(":/logo_panel.png");
    if (!iconPix.isNull())
        app.setWindowIcon(QIcon(iconPix));

    // Init controller (loads config, enumerates monitors)
    LaserController *ctrl = LaserController::instance();
    Q_UNUSED(ctrl)

    // Overlay (transparent, click-through, always on top)
    OverlayWindow overlay;
    overlay.show();

    // Control panel
    PanelWindow panel;
    panel.show();

    return app.exec();
}

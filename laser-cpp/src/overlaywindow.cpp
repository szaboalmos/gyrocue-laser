#include "overlaywindow.h"
#include "lasercontroller.h"

#include <QPainter>
#include <QCursor>
#include <QGuiApplication>
#include <QScreen>
#include <QColor>

#ifdef Q_OS_WIN
#  include <windows.h>
#endif

#ifdef Q_OS_MACOS
#  include <ApplicationServices/ApplicationServices.h>
#endif

static const int WIN_SIZE = 100;

OverlayWindow::OverlayWindow(QWidget *parent)
    : QWidget(parent)
    , m_ctrl(LaserController::instance())
{
    setFixedSize(WIN_SIZE, WIN_SIZE);

    // Frameless, always-on-top, transparent background, no taskbar entry
    setWindowFlags(Qt::FramelessWindowHint
                   | Qt::WindowStaysOnTopHint
                   | Qt::Tool
                   | Qt::NoDropShadowWindowHint);
    setAttribute(Qt::WA_TranslucentBackground);
    setAttribute(Qt::WA_ShowWithoutActivating);
    setWindowOpacity(1.0);

    // Mouse follow
    m_followTimer = new QTimer(this);
    connect(m_followTimer, &QTimer::timeout, this, &OverlayWindow::followMouse);
    m_followTimer->start(8);

    // Hotkey polling
    m_hotkeyTimer = new QTimer(this);
    connect(m_hotkeyTimer, &QTimer::timeout, this, &OverlayWindow::pollHotkey);
    m_hotkeyTimer->start(16);

    connect(m_ctrl, &LaserController::stateChanged, this, [this]() { update(); });
}

OverlayWindow::~OverlayWindow()
{
    if (m_cursorHidden) showCursor();
}

void OverlayWindow::showEvent(QShowEvent *event)
{
    QWidget::showEvent(event);
    makeClickThrough();
}

void OverlayWindow::makeClickThrough()
{
#ifdef Q_OS_WIN
    HWND hwnd = (HWND)winId();
    LONG style = GetWindowLong(hwnd, GWL_EXSTYLE);
    SetWindowLong(hwnd, GWL_EXSTYLE,
                  style | WS_EX_TRANSPARENT | WS_EX_LAYERED | WS_EX_NOACTIVATE);
#endif
}

void OverlayWindow::followMouse()
{
    QPoint p = QCursor::pos();
    move(p.x() - WIN_SIZE / 2, p.y() - WIN_SIZE / 2);
}

void OverlayWindow::pollHotkey()
{
#ifdef Q_OS_WIN
    bool down = (GetAsyncKeyState(0x81) & 0x8000) != 0;  // VK_F18 = 0x81
#else
    bool down = false;  // macOS: CGEventTap in main.cpp sets visible directly
#endif

    if (down && !m_f18WasDown) {
        m_f18WasDown = true;
        onF18Press();
    } else if (!down && m_f18WasDown) {
        m_f18WasDown = false;
        onF18Release();
    }
}

void OverlayWindow::onF18Press()
{
    m_savedCursorPos = QCursor::pos();

    if (m_ctrl->centerNext) {
        QCursor::setPos(m_ctrl->screenCenter());
        m_ctrl->centerNext = false;
    } else if (m_ctrl->startMode == "center") {
        QCursor::setPos(m_ctrl->screenCenter());
    } else if (m_ctrl->startMode == "last" && !m_ctrl->lastPos.isNull()) {
        QCursor::setPos(m_ctrl->lastPos);
    }

    hideCursor();
    m_ctrl->visible = true;
    update();
}

void OverlayWindow::onF18Release()
{
    if (m_ctrl->startMode == "last") {
        m_ctrl->lastPos = QCursor::pos();
        m_ctrl->saveConfig();
    }

    m_ctrl->visible = false;
    update();

    // Restore cursor position before showing it
    QCursor::setPos(m_savedCursorPos);
    showCursor();
}

void OverlayWindow::hideCursor()
{
    if (m_cursorHidden) return;
#ifdef Q_OS_WIN
    while (ShowCursor(FALSE) >= 0) {}
#else
    // macOS: hide via CGDisplayHideCursor
    CGDisplayHideCursor(kCGDirectMainDisplay);
#endif
    m_cursorHidden = true;
}

void OverlayWindow::showCursor()
{
    if (!m_cursorHidden) return;
#ifdef Q_OS_WIN
    while (ShowCursor(TRUE) < 0) {}
#else
    CGDisplayShowCursor(kCGDirectMainDisplay);
#endif
    m_cursorHidden = false;
}

// ── Drawing ───────────────────────────────────────────────────────────────────

QColor OverlayWindow::darker(const QColor &c, int amt)
{
    return QColor(
        qMax(0, c.red()   - amt),
        qMax(0, c.green() - amt),
        qMax(0, c.blue()  - amt));
}

QColor OverlayWindow::lighter(const QColor &c, int amt)
{
    return QColor(
        qMin(255, c.red()   + amt),
        qMin(255, c.green() + amt),
        qMin(255, c.blue()  + amt));
}

void OverlayWindow::paintEvent(QPaintEvent *)
{
    QPainter p(this);
    p.setRenderHint(QPainter::Antialiasing);
    p.fillRect(rect(), Qt::transparent);

    if (!m_ctrl->visible) return;

    int cx  = WIN_SIZE / 2;
    int cy  = WIN_SIZE / 2;
    int r   = m_ctrl->size / 2;
    QColor col(m_ctrl->color);

    // Outer glow ring
    p.setPen(QPen(darker(col, 120), 2));
    p.setBrush(Qt::NoBrush);
    p.drawEllipse(QPointF(cx, cy), r + 3.0, r + 3.0);

    // Main dot
    p.setPen(QPen(darker(col, 60), 1));
    p.setBrush(QBrush(col));
    p.drawEllipse(QPointF(cx, cy), (double)r, (double)r);

    // Inner highlight
    int inner = qMax(1, r / 4);
    p.setPen(Qt::NoPen);
    p.setBrush(QBrush(lighter(col, 120)));
    p.drawEllipse(QPointF(cx, cy), (double)inner, (double)inner);
}

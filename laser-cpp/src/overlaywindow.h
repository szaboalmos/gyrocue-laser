#pragma once

#include <QWidget>
#include <QTimer>
#include <QPoint>

class LaserController;

class OverlayWindow : public QWidget
{
    Q_OBJECT

public:
    explicit OverlayWindow(QWidget *parent = nullptr);
    ~OverlayWindow();

protected:
    void paintEvent(QPaintEvent *event) override;
    void showEvent(QShowEvent *event) override;

private slots:
    void followMouse();
    void pollHotkey();

private:
    void onF18Press();
    void onF18Release();
    void hideCursor();
    void showCursor();
    void makeClickThrough();

    LaserController *m_ctrl;
    QTimer          *m_followTimer;
    QTimer          *m_hotkeyTimer;

    QPoint  m_savedCursorPos;
    bool    m_f18WasDown = false;
    bool    m_cursorHidden = false;

    static QColor darker(const QColor &c, int amt);
    static QColor lighter(const QColor &c, int amt);
};

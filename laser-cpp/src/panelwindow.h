#pragma once

#include <QWidget>
#include <QLabel>
#include <QLineEdit>
#include <QSlider>
#include <QPushButton>
#include <QButtonGroup>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QFrame>
#include <QTimer>

class LaserController;

// ── Color dot (custom painted circle) ────────────────────────────────────────
class ColorDot : public QWidget
{
    Q_OBJECT
public:
    explicit ColorDot(QWidget *parent = nullptr);
    void setColor(const QColor &c);
signals:
    void clicked();
protected:
    void paintEvent(QPaintEvent *) override;
    void mousePressEvent(QMouseEvent *) override;
private:
    QColor m_color;
};

// ── Preset swatch ─────────────────────────────────────────────────────────────
class Swatch : public QWidget
{
    Q_OBJECT
public:
    explicit Swatch(const QString &hex, QWidget *parent = nullptr);
signals:
    void clicked(const QString &hex);
protected:
    void paintEvent(QPaintEvent *) override;
    void enterEvent(QEnterEvent *) override;
    void leaveEvent(QEvent *) override;
    void mousePressEvent(QMouseEvent *) override;
private:
    QColor  m_color;
    QString m_hex;
    bool    m_hover = false;
};

// ── Panel window ──────────────────────────────────────────────────────────────
class PanelWindow : public QWidget
{
    Q_OBJECT
public:
    explicit PanelWindow(QWidget *parent = nullptr);

private slots:
    void applyColor(const QString &hex);
    void pickColorDialog();
    void onSizeChanged(int value);
    void setStartMode(const QString &mode);
    void centerNextPress();
    void onMonitorChanged(int id);
    void syncFromController();
    void onQuit();

private:
    QWidget* makeDivider();
    QWidget* makeSectionHeader(const QString &text);
    void     updateSegButtons();

    void keyPressEvent(QKeyEvent *e) override;

    LaserController *m_ctrl;

    ColorDot    *m_colorDot;
    QLineEdit   *m_hexEdit;
    QSlider     *m_sizeSlider;
    QLabel      *m_sizeLabel;
    QPushButton *m_btnCenter;
    QPushButton *m_btnLast;
    QButtonGroup *m_monitorGroup;

    QString m_currentColor;
};

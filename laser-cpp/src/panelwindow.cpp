#include "panelwindow.h"
#include "lasercontroller.h"

#include <QPainter>
#include <QPen>
#include <QBrush>
#include <QMouseEvent>
#include <QEnterEvent>
#include <QColorDialog>
#include <QRadioButton>
#include <QApplication>
#include <QPixmap>
#include <QIcon>

// ── Palette ───────────────────────────────────────────────────────────────────
static const QString BG   = "#f0f0f0";
static const QString HDR  = "#ffffff";
static const QString EL   = "#e0e0e0";
static const QString EL2  = "#d0d0d0";
static const QString DIV  = "#cccccc";
static const QString FG   = "#1a1a1a";
static const QString FG2  = "#555555";
static const QString ACC  = "#ff2020";
static const QString ACCD = "#cc1a1a";

// ── ColorDot ─────────────────────────────────────────────────────────────────
ColorDot::ColorDot(QWidget *parent) : QWidget(parent), m_color("#ff2020")
{
    setFixedSize(34, 34);
    setCursor(Qt::PointingHandCursor);
}

void ColorDot::setColor(const QColor &c) { m_color = c; update(); }

void ColorDot::paintEvent(QPaintEvent *)
{
    QPainter p(this);
    p.setRenderHint(QPainter::Antialiasing);
    p.setPen(Qt::NoPen);
    p.setBrush(m_color);
    p.drawEllipse(2, 2, 30, 30);
}

void ColorDot::mousePressEvent(QMouseEvent *) { emit clicked(); }

// ── Swatch ────────────────────────────────────────────────────────────────────
Swatch::Swatch(const QString &hex, QWidget *parent)
    : QWidget(parent), m_color(hex), m_hex(hex)
{
    setFixedSize(26, 26);
    setCursor(Qt::PointingHandCursor);
}

void Swatch::paintEvent(QPaintEvent *)
{
    QPainter p(this);
    p.setRenderHint(QPainter::Antialiasing);
    if (m_hover)
        p.setPen(QPen(QColor("#cccccc"), 2));
    else
        p.setPen(Qt::NoPen);
    p.setBrush(m_color);
    p.drawEllipse(2, 2, 22, 22);
}

void Swatch::enterEvent(QEnterEvent *) { m_hover = true;  update(); }
void Swatch::leaveEvent(QEvent *)      { m_hover = false; update(); }
void Swatch::mousePressEvent(QMouseEvent *) { emit clicked(m_hex); }

// ── PanelWindow ───────────────────────────────────────────────────────────────
PanelWindow::PanelWindow(QWidget *parent)
    : QWidget(parent)
    , m_ctrl(LaserController::instance())
{
    setWindowTitle("GYROCUE Laser");
    setFixedWidth(320);
    setWindowFlags(windowFlags() & ~Qt::WindowMaximizeButtonHint);

    // App icon
    QPixmap iconPix(":/logo_panel.png");
    if (!iconPix.isNull()) setWindowIcon(QIcon(iconPix));

    // Global stylesheet
    setStyleSheet(QString(
        "QWidget { background: %1; color: %2; font-family: 'Segoe UI'; font-size: 9pt; }"
        "QLineEdit { background: %3; color: %2; border: none; border-radius: 3px;"
        "            padding: 4px 6px; font-family: Consolas; font-size: 9pt; }"
        "QSlider::groove:horizontal { height: 4px; background: %3; border-radius: 2px; }"
        "QSlider::handle:horizontal { width: 14px; height: 14px; margin: -5px 0;"
        "                             background: %4; border-radius: 7px; }"
        "QSlider::sub-page:horizontal { background: %4; border-radius: 2px; }"
        "QRadioButton { spacing: 8px; }"
        "QRadioButton::indicator { width: 14px; height: 14px; }"
        "QPushButton { border: none; border-radius: 3px; padding: 7px 14px; }"
        "QPushButton:focus { outline: none; }"
    ).arg(BG, FG, EL, ACC));

    auto *rootLayout = new QVBoxLayout(this);
    rootLayout->setContentsMargins(0, 0, 0, 0);
    rootLayout->setSpacing(0);

    // ── HEADER ────────────────────────────────────────────────────────────────
    auto *hdr = new QWidget;
    hdr->setStyleSheet(QString("background: %1;").arg(HDR));
    auto *hdrL = new QHBoxLayout(hdr);
    hdrL->setContentsMargins(12, 7, 12, 7);
    hdrL->setSpacing(10);

    QPixmap logoPix(":/logo_panel.png");
    if (!logoPix.isNull()) {
        auto *logoLbl = new QLabel;
        logoLbl->setPixmap(logoPix);
        logoLbl->setStyleSheet(QString("background: %1;").arg(HDR));
        hdrL->addWidget(logoLbl);
    } else {
        auto *dot = new QLabel("⬤");
        dot->setStyleSheet(QString("color: %1; font-size: 12pt; background: %2;").arg(ACC, HDR));
        hdrL->addWidget(dot);
    }

    auto *vf = new QVBoxLayout;
    vf->setSpacing(1);
    auto *titleLbl = new QLabel("GYROCUE Laser");
    titleLbl->setStyleSheet(QString("color: %1; font-size: 11pt; font-weight: bold; background: %2;").arg(FG, HDR));
    auto *subLbl = new QLabel("gyrocue.com");
    subLbl->setStyleSheet(QString("color: %1; font-size: 7pt; background: %2;").arg(FG2, HDR));
    vf->addWidget(titleLbl);
    vf->addWidget(subLbl);
    hdrL->addLayout(vf);
    hdrL->addStretch();

    auto *verLbl = new QLabel("v6.0");
    verLbl->setStyleSheet(QString("color: %1; font-size: 7pt; background: %2;").arg(FG2, HDR));
    verLbl->setAlignment(Qt::AlignTop | Qt::AlignRight);
    hdrL->addWidget(verLbl);

    rootLayout->addWidget(hdr);
    rootLayout->addWidget(makeDivider());

    // ── COLOR ─────────────────────────────────────────────────────────────────
    rootLayout->addWidget(makeSectionHeader("Color"));

    auto *crowW = new QWidget;
    crowW->setStyleSheet(QString("background: %1;").arg(BG));
    auto *crowL = new QHBoxLayout(crowW);
    crowL->setContentsMargins(16, 0, 16, 8);
    crowL->setSpacing(10);

    m_colorDot = new ColorDot;
    m_colorDot->setColor(QColor(m_ctrl->color));
    crowL->addWidget(m_colorDot);

    m_hexEdit = new QLineEdit(m_ctrl->color);
    m_hexEdit->setFixedWidth(90);
    crowL->addWidget(m_hexEdit);

    auto *pickBtn = new QPushButton("🎨");
    pickBtn->setStyleSheet(QString(
        "QPushButton { background: %1; color: %2; padding: 6px 10px; }"
        "QPushButton:hover { background: %3; }").arg(EL, FG2, EL2));
    pickBtn->setCursor(Qt::PointingHandCursor);
    crowL->addWidget(pickBtn);
    crowL->addStretch();
    rootLayout->addWidget(crowW);

    // Preset swatches
    auto *prowW = new QWidget;
    prowW->setStyleSheet(QString("background: %1;").arg(BG));
    auto *prowL = new QHBoxLayout(prowW);
    prowL->setContentsMargins(16, 0, 16, 12);
    prowL->setSpacing(6);
    for (const QString &hc : PRESETS) {
        auto *sw = new Swatch(hc);
        prowL->addWidget(sw);
        connect(sw, &Swatch::clicked, this, &PanelWindow::applyColor);
    }
    prowL->addStretch();
    rootLayout->addWidget(prowW);

    connect(m_colorDot, &ColorDot::clicked, this, &PanelWindow::pickColorDialog);
    connect(pickBtn,    &QPushButton::clicked, this, &PanelWindow::pickColorDialog);
    connect(m_hexEdit,  &QLineEdit::returnPressed, this, [this]() {
        applyColor(m_hexEdit->text());
    });

    rootLayout->addWidget(makeDivider());

    // ── SIZE ──────────────────────────────────────────────────────────────────
    rootLayout->addWidget(makeSectionHeader("Dot Size"));

    auto *srowW = new QWidget;
    srowW->setStyleSheet(QString("background: %1;").arg(BG));
    auto *srowL = new QHBoxLayout(srowW);
    srowL->setContentsMargins(16, 0, 16, 14);
    srowL->setSpacing(10);

    m_sizeSlider = new QSlider(Qt::Horizontal);
    m_sizeSlider->setRange(6, 60);
    m_sizeSlider->setValue(m_ctrl->size);
    srowL->addWidget(m_sizeSlider);

    m_sizeLabel = new QLabel(QString("%1 px").arg(m_ctrl->size));
    m_sizeLabel->setFixedWidth(46);
    m_sizeLabel->setAlignment(Qt::AlignRight | Qt::AlignVCenter);
    m_sizeLabel->setStyleSheet(QString("color: %1; font-weight: bold; background: %2;").arg(ACC, BG));
    srowL->addWidget(m_sizeLabel);

    connect(m_sizeSlider, &QSlider::valueChanged, this, &PanelWindow::onSizeChanged);
    rootLayout->addWidget(srowW);
    rootLayout->addWidget(makeDivider());

    // ── START POSITION ────────────────────────────────────────────────────────
    rootLayout->addWidget(makeSectionHeader("Start Position"));

    auto *segW = new QWidget;
    segW->setStyleSheet(QString("background: %1; border-radius: 3px;").arg(EL));
    auto *segL = new QHBoxLayout(segW);
    segL->setContentsMargins(2, 2, 2, 2);
    segL->setSpacing(2);

    m_btnCenter = new QPushButton("Screen center");
    m_btnCenter->setCursor(Qt::PointingHandCursor);
    m_btnCenter->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Fixed);
    m_btnLast = new QPushButton("Last position");
    m_btnLast->setCursor(Qt::PointingHandCursor);
    m_btnLast->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Fixed);
    segL->addWidget(m_btnCenter);
    segL->addWidget(m_btnLast);

    auto *segWrap = new QWidget;
    segWrap->setStyleSheet(QString("background: %1;").arg(BG));
    auto *segWrapL = new QHBoxLayout(segWrap);
    segWrapL->setContentsMargins(16, 0, 16, 6);
    segWrapL->addWidget(segW);
    rootLayout->addWidget(segWrap);

    connect(m_btnCenter, &QPushButton::clicked, this, [this]() { setStartMode("center"); });
    connect(m_btnLast,   &QPushButton::clicked, this, [this]() { setStartMode("last"); });
    updateSegButtons();

    // Center next button
    auto *cnextBtn = new QPushButton("Center");
    cnextBtn->setCursor(Qt::PointingHandCursor);
    cnextBtn->setStyleSheet(QString(
        "QPushButton { background: %1; color: white; padding: 8px 16px; text-align: left; }"
        "QPushButton:hover { background: %2; }").arg(ACC, ACCD));
    connect(cnextBtn, &QPushButton::clicked, this, &PanelWindow::centerNextPress);

    auto *cnextWrap = new QWidget;
    cnextWrap->setStyleSheet(QString("background: %1;").arg(BG));
    auto *cnextL = new QHBoxLayout(cnextWrap);
    cnextL->setContentsMargins(16, 0, 16, 12);
    cnextL->addWidget(cnextBtn);
    rootLayout->addWidget(cnextWrap);
    rootLayout->addWidget(makeDivider());

    // ── MONITOR ───────────────────────────────────────────────────────────────
    rootLayout->addWidget(makeSectionHeader("Monitor"));

    m_monitorGroup = new QButtonGroup(this);
    m_monitorGroup->setExclusive(true);

    auto addMonRb = [&](const QString &text, int val) {
        auto *rb = new QRadioButton(text);
        rb->setStyleSheet(QString("QRadioButton { background: %1; padding: 2px 22px; }").arg(BG));
        rb->setChecked(m_ctrl->monitor == val);
        m_monitorGroup->addButton(rb, val);
        rootLayout->addWidget(rb);
    };

    addMonRb("All monitors", 0);
    for (int i = 0; i < m_ctrl->monitors.size(); ++i) {
        const QRect &m = m_ctrl->monitors.at(i);
        addMonRb(QString("Monitor %1  (%2×%3  @ %4,%5)")
                     .arg(i + 1).arg(m.width()).arg(m.height())
                     .arg(m.x()).arg(m.y()), i + 1);
    }

    connect(m_monitorGroup, &QButtonGroup::idClicked, this, &PanelWindow::onMonitorChanged);
    rootLayout->addWidget(makeDivider());

    // ── FOOTER ────────────────────────────────────────────────────────────────
    auto *footW = new QWidget;
    footW->setStyleSheet(QString("background: %1;").arg(BG));
    auto *footL = new QHBoxLayout(footW);
    footL->setContentsMargins(16, 10, 16, 10);

    footL->addStretch();

    auto *quitBtn = new QPushButton("✕  Quit");
    quitBtn->setCursor(Qt::PointingHandCursor);
    quitBtn->setStyleSheet(QString(
        "QPushButton { background: %1; color: white; font-weight: bold; padding: 7px 16px; }"
        "QPushButton:hover { background: %2; }").arg(ACC, ACCD));
    connect(quitBtn, &QPushButton::clicked, this, &PanelWindow::onQuit);
    footL->addWidget(quitBtn);
    rootLayout->addWidget(footW);

    adjustSize();
    move(120, 80);

    m_currentColor = m_ctrl->color;
}

// ── Helpers ───────────────────────────────────────────────────────────────────
QWidget* PanelWindow::makeDivider()
{
    auto *line = new QFrame;
    line->setFrameShape(QFrame::HLine);
    line->setFixedHeight(1);
    line->setStyleSheet(QString("background: %1; border: none;").arg(DIV));
    return line;
}

QWidget* PanelWindow::makeSectionHeader(const QString &text)
{
    auto *row = new QWidget;
    row->setStyleSheet(QString("background: %1;").arg(BG));
    auto *rl = new QHBoxLayout(row);
    rl->setContentsMargins(16, 14, 16, 6);
    rl->setSpacing(8);

    auto *bar = new QFrame;
    bar->setFixedSize(2, 12);
    bar->setStyleSheet(QString("background: %1; border: none;").arg(ACC));

    auto *lbl = new QLabel(text.toUpper());
    lbl->setStyleSheet(QString("color: %1; font-size: 7pt; font-weight: bold;").arg(FG2));

    rl->addWidget(bar);
    rl->addWidget(lbl);
    rl->addStretch();
    return row;
}

void PanelWindow::updateSegButtons()
{
    if (m_ctrl->startMode == "center") {
        m_btnCenter->setStyleSheet(QString(
            "QPushButton { background: %1; color: white; padding: 8px 10px; }"
            "QPushButton:hover { background: %2; }").arg(ACC, ACCD));
        m_btnLast->setStyleSheet(QString(
            "QPushButton { background: %1; color: %2; padding: 8px 10px; }"
            "QPushButton:hover { background: %3; }").arg(EL2, FG2, EL));
    } else {
        m_btnCenter->setStyleSheet(QString(
            "QPushButton { background: %1; color: %2; padding: 8px 10px; }"
            "QPushButton:hover { background: %3; }").arg(EL2, FG2, EL));
        m_btnLast->setStyleSheet(QString(
            "QPushButton { background: %1; color: white; padding: 8px 10px; }"
            "QPushButton:hover { background: %2; }").arg(ACC, ACCD));
    }
}

// ── Slots ─────────────────────────────────────────────────────────────────────
void PanelWindow::applyColor(const QString &hex)
{
    QColor c(hex);
    if (!c.isValid()) return;
    m_ctrl->color = hex;
    m_colorDot->setColor(c);
    m_hexEdit->setText(hex);
    m_ctrl->saveConfig();
    emit m_ctrl->stateChanged();
}

void PanelWindow::pickColorDialog()
{
    QColor c = QColorDialog::getColor(QColor(m_ctrl->color), this, "Laser color");
    if (c.isValid()) applyColor(c.name());
}

void PanelWindow::onSizeChanged(int value)
{
    m_ctrl->size = value;
    m_sizeLabel->setText(QString("%1 px").arg(value));
    m_ctrl->saveConfig();
    emit m_ctrl->stateChanged();
}

void PanelWindow::setStartMode(const QString &mode)
{
    m_ctrl->startMode = mode;
    updateSegButtons();
    m_ctrl->saveConfig();
}

void PanelWindow::centerNextPress()
{
    m_ctrl->centerNext = true;
}

void PanelWindow::onMonitorChanged(int id)
{
    m_ctrl->monitor = id;
    m_ctrl->saveConfig();
}

void PanelWindow::syncFromController()
{
    if (m_ctrl->color != m_currentColor) {
        m_currentColor = m_ctrl->color;
        m_colorDot->setColor(QColor(m_ctrl->color));
        m_hexEdit->setText(m_ctrl->color);
    }
    if (m_sizeSlider->value() != m_ctrl->size)
        m_sizeSlider->setValue(m_ctrl->size);
    updateSegButtons();
}

void PanelWindow::onQuit()
{
    m_ctrl->saveConfig();
    QApplication::quit();
}

void PanelWindow::keyPressEvent(QKeyEvent *e)
{
    if (e->key() == Qt::Key_Escape) onQuit();
    QWidget::keyPressEvent(e);
}

#pragma once

#include <QObject>
#include <QPoint>
#include <QString>
#include <QList>
#include <QRect>

static const QStringList PRESETS = {
    "#ff2020","#ff8800","#ffee00","#00e676",
    "#2979ff","#e040fb","#ffffff","#00e5ff"
};

class LaserController : public QObject
{
    Q_OBJECT

public:
    static LaserController* instance();

    // State
    QString color      = "#ff2020";
    int     size       = 18;
    bool    visible    = false;
    QString startMode  = "center";   // "center" | "last"
    QPoint  lastPos;
    int     monitor    = 0;          // 0=all, 1..N
    bool    centerNext = true;       // first press always centers

    // Monitors list (populated on start)
    QList<QRect> monitors;

    void loadConfig();
    void saveConfig();

    QPoint screenCenter() const;
    QRect  selectedMonitorRect() const;

signals:
    void stateChanged();

private:
    explicit LaserController(QObject *parent = nullptr);
    static LaserController *s_instance;

    QString configPath() const;
};

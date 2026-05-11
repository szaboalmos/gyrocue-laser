#include "lasercontroller.h"

#include <QStandardPaths>
#include <QDir>
#include <QFile>
#include <QJsonDocument>
#include <QJsonObject>
#include <QGuiApplication>
#include <QScreen>

LaserController *LaserController::s_instance = nullptr;

LaserController* LaserController::instance()
{
    if (!s_instance)
        s_instance = new LaserController();
    return s_instance;
}

LaserController::LaserController(QObject *parent) : QObject(parent)
{
    // Enumerate monitors
    for (QScreen *screen : QGuiApplication::screens())
        monitors.append(screen->geometry());

    loadConfig();
}

QString LaserController::configPath() const
{
    QString base = QStandardPaths::writableLocation(QStandardPaths::AppDataLocation);
    QDir().mkpath(base);
    return base + "/settings.json";
}

void LaserController::loadConfig()
{
    QFile f(configPath());
    if (!f.open(QIODevice::ReadOnly)) return;

    QJsonObject obj = QJsonDocument::fromJson(f.readAll()).object();

    color     = obj.value("color").toString(color);
    size      = obj.value("size").toInt(size);
    startMode = obj.value("start_mode").toString(startMode);
    monitor   = obj.value("monitor").toInt(monitor);

    if (obj.contains("last_pos")) {
        QJsonObject lp = obj.value("last_pos").toObject();
        lastPos = QPoint(lp["x"].toInt(), lp["y"].toInt());
    }
}

void LaserController::saveConfig()
{
    QJsonObject obj;
    obj["color"]      = color;
    obj["size"]       = size;
    obj["start_mode"] = startMode;
    obj["monitor"]    = monitor;

    if (!lastPos.isNull()) {
        QJsonObject lp;
        lp["x"] = lastPos.x();
        lp["y"] = lastPos.y();
        obj["last_pos"] = lp;
    }

    QFile f(configPath());
    if (f.open(QIODevice::WriteOnly))
        f.write(QJsonDocument(obj).toJson());
}

QPoint LaserController::screenCenter() const
{
    QRect r = selectedMonitorRect();
    return r.center();
}

QRect LaserController::selectedMonitorRect() const
{
    if (monitor > 0 && monitor <= monitors.size())
        return monitors.at(monitor - 1);

    // All monitors → bounding rect of primary screen
    if (!monitors.isEmpty())
        return monitors.first();

    return QRect(0, 0, 1920, 1080);
}

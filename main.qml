import QtQuick
import QtQuick.Window
import QtQuick.Controls.Material 2.12

Window {

    width: 360
    height: 600
    visible: true
    title: qsTr("Hello World")
    flags: Qt.WindowTitleHint

    property QtObject backend

    Material.theme: Material.Light
    Material.accent: Material.Purple


    MainView {

        //anchors.fill:
    }
}

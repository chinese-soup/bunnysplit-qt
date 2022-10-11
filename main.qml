import QtQuick
import QtQuick.Window
import QtQuick.Controls.Material 2.12

Window {

    width: 360
    height: 600
    visible: true
    title: qsTr("Bunnysplit-Linux")
    flags: Qt.WindowTitleHint

    property QtObject backend
    property QtObject backend2

    Material.theme: Material.Light
    Material.accent: Material.Purple


    MainView {

        //anchors.fill:
    }



}

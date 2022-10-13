import QtQuick
import QtQuick.Window
import QtQuick.Controls.Material 2.12

import QtQuick.Dialogs
ApplicationWindow {

    width: 360
    height: 600
    visible: true
    title: qsTr("Bunnysplit-Linux")
    flags: Qt.WindowTitleHint

    property QtObject backend
    property QtObject backend2
    property string selectedFileName

    Material.theme: Material.Light
    Material.accent: Material.Purple

    FileDialog {
        id: fileDialog
        currentFolder: StandardPaths.standardLocations(StandardPaths.PicturesLocation)[0]
        onAccepted: backend.json_filename = selectedFile
    }

    header: ToolBar {
        Button {
            text: qsTr("Choose Image...")
            onClicked: fileDialog.open()
        }
    }

    MainView {

        //anchors.fill:
    }



}

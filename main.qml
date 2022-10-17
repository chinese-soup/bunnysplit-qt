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

    /*header: ToolBar {
        Button {
            text: qsTr("Choose Image...")
            onClicked: menu.open() //fileDialog.open()

            Menu {
                id: menu
                y: fileButton.height

                MenuItem {
                    text: "New..."
                }
                MenuItem {
                    text: "Open..."
                    onClicked: fileDialog.open()
                }
                MenuItem {
                    text: "Save"
                }
            }
        }
    }*/

    MouseArea {
        z: 50000
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        onClicked: {
            if (mouse.button === Qt.RightButton)
                contextMenu.popup()
        }
        onPressAndHold: {
            if (mouse.source === Qt.MouseEventNotSynthesized)
                contextMenu.popup()
        }
        Menu {
            id: contextMenu
            MenuItem {
                onClicked: console.log("Edit splits")
                text: "Edit splits"
            }
            MenuItem {
                onClicked: fileDialog.open()
                text: "Open"
            }
            MenuItem {
                text: "Save"
            }
            MenuItem {
                text: "Save as..."
            }
        }
    }

    MainView {

        //anchors.fill:
    }



}

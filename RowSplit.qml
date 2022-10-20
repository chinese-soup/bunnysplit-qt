// RowSplit.qml
import QtQuick 2.0

import QtQuick.Controls 2.12
import QtQuick.Layouts 1
import QtQuick.Shapes 1.4

Rectangle {
    implicitWidth: layout.implicitWidth
    implicitHeight: layout.implicitHeight
    property bool is_current_split
    property string title: 'N/A'
    property string delta: '?'
    property string best_time: 'N/A BEST'

    RowLayout {
        id: layout
        anchors.fill: parent
        Label {
            id: split_name_text
            font.bold: is_current_split
            text: title
            color: current_split ? "red" : "black"
            wrapMode: Text.WordWrap
            font.pixelSize: 16

            Layout.fillHeight: true
            Layout.preferredWidth: 100
            /*background: Rectangle
            {
                color:  { if (title === "ba_maint") { return 'black' } else { return 'white' } }
            }*/

        }
        Label {
            id: curr_time_text
            font.bold: false
            color: delta > 0 ? "red" : "green"
            text: delta
            font.pixelSize: 16

            Layout.fillWidth: true
            Layout.fillHeight: true
        }
        Label {
            id: best_time_text
            font.bold: false
            text: best_time
            font.pixelSize: 16

            Layout.fillWidth: true
            Layout.fillHeight: true
        }

    }
}
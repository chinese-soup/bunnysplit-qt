import QtQuick

import QtQuick.Controls 2.12
import QtQuick.Layouts 1
import QtQuick.Shapes 1.4

RowLayout
{
    //spacing: 150
    anchors.fill: parent
    property string current_time: "0"
    property string model_name: "iPhone ??"
    property variant mrdka;
    property variant lockdownFailed;
    property variant ioregFailed;

    Connections {
        target: backend
        function onUpdated(msg) {
            current_time = msg["current_time"]
            console.log(current_time)
        }
    }

    Rectangle {
        //Layout.preferredWidth: parent.width / 2
        Layout.fillHeight: true
        id: leftSide

        //anchors.leftMargin: 50
        color: "blue"
        ColumnLayout {
            Text {
                id: timer_text
                Layout.alignment: Qt.AlignLeft
                text: "Time " + current_time
                font.pixelSize: 24
                color: gradient2
                palette: labelPal
            }
        }
    }
}

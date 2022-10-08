import QtQuick

import QtQuick.Controls 2.12
import QtQuick.Layouts 1
import QtQuick.Shapes 1.4


GridLayout
{
    //spacing: 150
    anchors.fill: parent

    Connections {
        target: backend

        function onUpdated(msg) {
            // current_time_property = msg["curr_time"]
            //console.log(msg["curr_time"])
            //console.log(msg["splits_data"][0])
            console.log(backend.get_splits.length)
            console.log(backend.get_splits)

            console.log(msg.get_splits)
            console.log(backend.timer_state_getter)

            /*for(var property in msg)
            {
                console.log(property)
            }*/

        }
    }
    Rectangle {
        //Layout.preferredWidth: parent.width / 2
        color: "blue"
        id: leftSide

        //anchors.leftMargin: 50
        ColumnLayout {
            Text {
                id: current_time
                Layout.alignment: Qt.AlignLeft
                text: backend.curr_time_getter
                font.pixelSize: 36
                color: backend.timer_state_getter ? 'green' : 'black'
            }
        }
    }
    GridLayout {
        columns: 1
        Row {
            spacing: 15
            Text {
                text: "SPlit name"
                font.bold: true
            }
            Text {
                font.bold: true
                text: "Delta"
            }
            Text {
                text: "Best time blabla"
                font.bold: true
            }
        }

        Repeater {
            id: repeater3
            model: backend.get_splits

            delegate: RowSplit {
                title: modelData.title
                delta: modelData.delta > 0 ? "+" + modelData.delta : modelData.delta
                best_time: modelData.time
                current_split: backend.curr_split_index_getter == index
           }
        }
    }

}



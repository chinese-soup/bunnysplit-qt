import QtQuick

import QtQuick.Controls 2.12
import QtQuick.Layouts 1.1
import QtQuick.Shapes 1.4

ColumnLayout {
    spacing: 0
    anchors.fill: parent
    Connections {
        target: backend

        function onUpdated(msg) {
            // current_time_property = msg["curr_time"]
            //console.log(msg["curr_time"])
            //console.log(msg["splits_data"][0])
            /*console.log(backend.get_splits.length)
            console.log(backend.get_splits)

            console.log(msg.get_splits)
            console.log(backend.timer_state_getter)*/


            /*for(var property in msg)
            {
                console.log(property)
            }*/
        }
    }

    RowLayout
    {
        id: layoutTopHeader
        Layout.fillWidth: true;
        Layout.preferredHeight: gamenameLabel.font.pixelSize + 8

        Label {
            id: gamenameLabel
            Layout.alignment: Qt.AlignCenter
            Layout.fillWidth: true;
            Layout.preferredWidth: 100

            text: backend.split_data.title + "(" + backend.split_data.category + ")"
            font.pixelSize: 13
            font.bold: true
            color: 'white'

            background: Rectangle {
                color: 'black'
                width: parent.width
                height: parent.height
            }
        }
        Label {
            Layout.alignment: Qt.AlignRight
            text: backend.split_data.attempt_count
            font.pixelSize: 13
            color: 'white'
            Layout.fillWidth: true;
            Layout.fillHeight: true

            background: Rectangle {
                color: 'black'
                width: parent.width
                height: parent.height
            }
        }
        Label {
            Layout.alignment: Qt.AlignRight
            text: backend.split_data.finished_count
            font.pixelSize: 13
            color: 'white'

            Layout.fillWidth: true;
            Layout.fillHeight: true

            background: Rectangle {
                color: 'black'
                width: parent.width
                height: parent.height
            }
        }
    }

    ScrollView
    {
       Layout.fillWidth: true
       Layout.fillHeight: true
       id: myScrollView
       clip: true
       ScrollBar.vertical.policy: ScrollBar.AlwaysOn

       ListView {
           highlightFollowsCurrentItem: true
           highlightRangeMode: ListView.ApplyRange
           preferredHighlightBegin: height / 2 - 24
           preferredHighlightEnd: height / 2 + 24

           id: kokot
           model: backend.get_splits
           currentIndex: backend.curr_split_index_getter

           delegate: RowSplit {
               title: modelData.title
               //delta: modelData.curr_split_index_getter >= index ? "nope" : modelData.delta
               delta: backend.curr_split_index_getter == index ? backend.curr_split_delta_getter : (modelData.delta > 0 ? "+" + modelData.delta : modelData.delta)
               best_time: modelData.time
               current_split: backend.curr_split_index_getter === index
           }
        }
    }
        //columns: 1
        /*RowLayout {
            Text {
                text: "Split name"
                font.bold: true
                Layout.preferredWidth: parent.width / 3
            }
            Text {
                font.bold: true
                text: "Delta"
                Layout.preferredWidth: parent.width / 3
            }
            Text {
                text: "BestTime"
                font.bold: true
                Layout.fillWidth: true
            }*/


    Rectangle {
        Layout.fillWidth: true;
        Layout.preferredHeight: 50
        Text {
            id: current_time
            text: backend.curr_time_getter
            font.pixelSize: 36
            color: backend.timer_state_getter ? 'green' : 'black'
            Layout.fillWidth: true
            //Layout.preferredWidth: 20
            }
        }
    }

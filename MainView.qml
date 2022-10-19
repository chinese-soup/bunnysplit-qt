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
        Layout.fillWidth: true
        Layout.topMargin: 0
        Layout.bottomMargin: 15
        Layout.preferredHeight: gamenameLabel.font.pixelSize + 8
        spacing: 0
        Label {
            id: gamenameLabel
            Layout.alignment: Qt.AlignLeft
            Layout.fillWidth: true;
            Layout.preferredWidth: 100

            text: backend.split_data.title + "  (" + backend.split_data.category + ")"
            font.pixelSize: 13
            font.bold: true
            color: 'white'

            background: Rectangle {
                color: 'black'
                width: parent.width + 10
                height: parent.height + 10
                y: -5
            }
        }
        Label {
            Layout.alignment: Qt.AlignRight
            text: backend.split_data.attempt_count
            font.pixelSize: 13
            color: 'white'
            Layout.fillWidth: true
            Layout.fillHeight: false

            background: Rectangle {
                color: 'black'
                width: parent.width + 10
                height: parent.height + 10
                y: -5
            }
        }
        Label {
            Layout.alignment: Qt.AlignRight
            text: backend.split_data.finished_count
            font.pixelSize: 13
            color: 'white'

            Layout.fillWidth: true;
            Layout.fillHeight: false

            background: Rectangle {
                color: 'black'
                width: parent.width + 10
                height: parent.height + 10
                y: -5
            }
        }
    }

    ScrollView
    {
       Layout.fillWidth: true
       Layout.fillHeight: true
       id: myScrollView
       clip: true
       ScrollBar.vertical.policy: ScrollBar.AsNeeded
       ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

       ListView {
           highlightFollowsCurrentItem: true
           highlightRangeMode: ListView.ApplyRange
           preferredHighlightBegin: height / 2 - 24
           preferredHighlightEnd: height / 2 + 24

           id: kokot
           model: backend.get_splits
           currentIndex: backend.curr_split_index_getter
           footerPositioning: ListView.OverlayFooter

           footer: RowSplit {
               property int fake_index: backend.get_splits.length - 1
               property var last_split_obj: backend.get_splits[fake_index]
               title: last_split_obj.title
               //title: backend.curr_split_index_getter
               // TODO: FIX
               //delta: backend.curr_split_index_getter == index ? backend.curr_split_delta_getter : (modelData.delta > 0 ? "+" + modelData.delta : modelData.delta)
               delta: last_split_obj.delta > 0 ? "+" + last_split_obj.delta : last_split_obj.delta
               best_time: last_split_obj.split_time
               is_current_split: backend.curr_split_index_getter === fake_index
               z: 20
           }
           delegate: RowSplit {
               title: modelData.title
               //delta: modelData.curr_split_index_getter >= index ? "nope" : modelData.delta
               delta: backend.curr_split_index_getter == index ? backend.curr_split_delta_getter : (modelData.delta > 0 ? "+" + modelData.delta : modelData.delta)
               best_time: modelData.split_time
               is_current_split: backend.curr_split_index_getter === index
           }
        }
    }

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

import QtQuick 2.15
import QtQuick.Controls 2.15
import PhoenixCreativePaintViewer 1.0

Rectangle {
    width: Constants.width
    height: Constants.height

    color: Constants.backgroundColor

    Text {
        text: qsTr("Hello PhoenixCreativePaintViewer")
        anchors.centerIn: parent
        font.family: Constants.font.family
    }
}

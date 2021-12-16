import sys
from PyQt5 import QtCore
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import *#QDialog, QApplication, QStackedWidget, QWidget
from PyQt5.QtCore import QEvent, Qt, QThread, QObject, pyqtSignal
import PyQt5.QtGui as QtGui
from PyODBCqueries import *
from decimal import Decimal
from ExtractFunction import *
from time import sleep

#global variable for outputting correct numbers
#dictionary keys are the index of the measurementSelector dropdown menu,
#they correspond to the correct multiplier for the unit of measure of pints
unitMultiplier = {5:1,4:1.5,3:2,2:4,1:6,0:8}
currentUnit = 5

class UploadDialog(QDialog):
    def __init__(self):
        super(UploadDialog,self).__init__()
        loadUi('src\\UploadDialog.ui',self)
    
    def closeEvent(self, event):
        # closes the dialog automatically when the upload thread finishes.
        # if the event's sender is anything other than a Worker object,
        # ie. a human, ignore the close request. (idiot-proofing)
        if not isinstance(self.sender(),Worker):
            event.ignore()

class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    fileName = pyqtSignal(str)
    files = ""

    def __init__(self, f):
        super(Worker,self).__init__()
        self.files = f
    def run(self):
        current = 0
        for f in self.files:
            print(f)
            current += 1
            if ".pdf" in f:

                self.fileName.emit(f)
                to_upload = extractPDF(f)
                addFormula(to_upload[0][2], to_upload[0][1], to_upload[0][0],str("Imported from: "+f.split("/")[-1]))
                old = to_upload[0]
                to_upload = to_upload[1:]
                for i in to_upload:
                    try:
                        addComponent( i[0], i[1])
                        addMakeupElement( old[2], old[1], i[0],i[2])
                    except(Exception):
                        print()
            self.progress.emit(current)
        sleep(2)
        self.finished.emit()
    
class MainScreen(QMainWindow):
    changed = QtCore.pyqtSignal(int)
    
    def __init__(self):
        super(MainScreen,self).__init__()
        loadUi('src\\Navigator.ui',self)
        self.NavPane.itemSelectionChanged.connect(self.selectPanel)

        home = HomeScreen()
        upload = UploadScreen()
        formula = FormulaScreen()
        component = ComponentScreen()
        self.MainViewStack.addWidget(home)
        self.MainViewStack.addWidget(upload)
        self.MainViewStack.addWidget(formula)
        self.MainViewStack.addWidget(component)

    def selectPanel(self):
        print("Navigating to page:",str(self.NavPane.currentRow()))
        self.MainViewStack.setCurrentIndex(self.NavPane.currentRow())
        if self.NavPane.currentRow() == 2:
            self.MainViewStack.currentWidget().populateFormulaList()
            self.MainViewStack.currentWidget().clear()
        if self.NavPane.currentRow() == 0:
            self.MainViewStack.currentWidget().refreshCounts()
        self.changed.emit(self.NavPane.currentRow())

class UploadScreen(QWidget):
    def __init__(self):
        super(UploadScreen,self).__init__()
        loadUi('src\\UploadWidget.ui',self)
        #self.login.clicked.connect(self.gotoLogin)

        self.uploadButton.clicked.connect(self.importFiles)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
            print("Ignoring")
    
    def dragMoveEvent(self, event: QtGui.QDragMoveEvent):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            event.ignore()
            print("Ignoring")

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            links = []

            for url in event.mimeData().urls():
                if url.isLocalFile():
                    links.append(str(url.toLocalFile()))
            
            newDialog = UploadDialog()
            newDialog.setFixedHeight(150)
            newDialog.setFixedWidth(300)
            newDialog.show()
            newDialog.currentFormula.setText("Demo Formula Name2")
            newDialog.progressBar.setRange(0, len(links))
            thread = QThread()
            worker = Worker(links)
            worker.moveToThread(thread)
            thread.started.connect(worker.run)
            worker.finished.connect(thread.quit)
            worker.finished.connect(worker.deleteLater)
            thread.finished.connect(thread.deleteLater)
            worker.progress.connect(newDialog.progressBar.setValue)
            worker.fileName.connect(newDialog.currentFormula.setText)
            worker.finished.connect(newDialog.close)

            thread.start()
            try:
                sys.exit(newDialog.exec())
            except:
                print("")
                    
    def importFiles(self):

        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        files, _ = QFileDialog.getOpenFileNames(self,"QFileDialog.getOpenFileNames()", "","PDF Files (*.pdf)", options=options)
        
        newDialog = UploadDialog()
        newDialog.setFixedHeight(150)
        newDialog.setFixedWidth(300)
        newDialog.show()
        newDialog.currentFormula.setText("Demo Formula Name2")
        newDialog.progressBar.setRange(0, len(files))

        thread = QThread()
        worker = Worker(files)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        worker.progress.connect(newDialog.progressBar.setValue)
        worker.fileName.connect(newDialog.currentFormula.setText)
        worker.finished.connect(newDialog.close)

        thread.start()
        try:
            sys.exit(newDialog.exec())
        except:
            print("Finished uploading")

class HomeScreen(QWidget):
    def __init__(self):
        super(HomeScreen,self).__init__()
        loadUi('src\\HomeWidget.ui',self)
        self.refreshCounts()
        
        #is there a better way to do this without this pointless loop?
    def refreshCounts(self):
        for row in componentCount():
            self.numComponents.setText(str(row.Count))
        
        for row in formulaCount():
            self.numFormulas.setText(str(row.Count))

class ComponentScreen(QWidget):
     def __init__(self):
        super(ComponentScreen, self).__init__()
        loadUi('src\\ComponentWidget.ui',self)

class FormulaScreen(QWidget):
    def __init__(self):
        super(FormulaScreen, self).__init__()
        loadUi('src\\FormulaWidget.ui',self)
        self.populateFormulaList()
        self.measurementSelector.setCurrentIndex(currentUnit)

        self.versionList.currentIndexChanged.connect(self.updateMakeup)

        self.formulaList.itemSelectionChanged.connect(self.updateSelection)

        self.notesBox.textChanged.connect(self.notesChanged)
        self.measurementSelector.currentIndexChanged.connect(self.updateMeasureUnits)
        self.deepSearchCheckbox.stateChanged.connect(self.searchFormulasResults)
        self.searchBox.textChanged.connect(self.searchFormulasResults)

    def clear(self):
        self.notesBox.clear()
        self.colorNumLarge.clear()
        self.colorNameLarge.clear()
        self.makeupTable.clearContents()
        self.displayWidget.hide()

    def searchFormulasResults(self):
        if self.searchBox.toPlainText().strip()=="":
            self.populateFormulaList()
        else:
            if self.deepSearchCheckbox.isChecked():
                r = deepFormulaSearch(self.searchBox.toPlainText())
            else:
                r = shallowFormulaSearch(self.searchBox.toPlainText())

            self.formulaList.clear()
            for row in r:
                self.formulaList.addItem(str(row.MPNum)+" - "+row.FormName.title())

    def updateMeasureUnits(self):
        global currentUnit
        currentUnit = self.measurementSelector.currentIndex()
        self.updateMakeup()

    def updateMakeup(self):
        if not self.colorNumLarge.text() == "" and not self.versionList.currentText() == "":
            self.makeupTable.setSortingEnabled(False)
            makeupElements = getMakeupElements(str(self.colorNumLarge.text()),self.versionList.currentText()).fetchall()
            self.makeupTable.setRowCount(len(makeupElements))
            self.makeupTable.clearContents()

            currentRow = 0

            factor = Decimal(unitMultiplier[currentUnit])

            for element in makeupElements:
                self.makeupTable.setItem(currentRow,0,QTableWidgetItem(element.CompCode))
                self.makeupTable.setItem(currentRow,1,QTableWidgetItem(element.IntDesc.title()))
                self.makeupTable.setItem(currentRow,2,QTableWidgetItem(str(factor*element.GramsPerPint)))
                if not currentRow == 0:
                    self.makeupTable.setItem(currentRow,3,QTableWidgetItem(str(factor*element.GramsPerPint+Decimal(self.makeupTable.item(currentRow-1,3).text()))))
                else:
                    self.makeupTable.setItem(currentRow,3,QTableWidgetItem(str(factor*element.GramsPerPint)))
                currentRow += 1
            
            self.makeupTable.setSortingEnabled(True)

    def updateVersion(self):
        selection = str(self.formulaList.currentItem().text()).split()[0]
        colorInfo = getFormula(selection,self.versionList.currentText())
        for color in colorInfo:
            self.colorNameLarge.setText(color.FormName.title())
        self.updateMakeup()


    def updateSelection(self):
        self.displayWidget.show()
        selection = str(self.formulaList.currentItem().text()).split()[0]
        print("User selected formula",selection)
        versions = getNumVersions(selection)
        self.versionList.clear()
        for v in versions:
            print(v)
            self.versionList.addItem(str(v.Version))

        colorInfo = getFormula(selection,self.versionList.currentText())
        print("Debugging, version selected is:",self.versionList.currentText())

        for color in colorInfo:
            self.colorNameLarge.setText(color.FormName.title())
            self.colorNumLarge.setText(str(color.MPNum))

        if color.Notes == None:
            self.notesBox.clear()
        else:
            self.notesBox.setPlainText(str(color.Notes))
        self.updateMakeup()

    def notesChanged(self):
        #the following line is a temporary workaround until I can make it so that the
        # interface for formulas is not displayed until a formula is actually selected
        if self.formulaList.currentItem():
            updateNotes(str(self.colorNumLarge.text()),self.versionList.currentText(),self.notesBox.toPlainText())

    def populateFormulaList(self):
        self.formulaList.clearSelection()
        print("Refreshing formula list!")
        r = (getAllFormulas())
        self.formulaList.clear()
        for row in r:
            self.formulaList.addItem(str(row.MPNum)+" - "+row.FormName.title())

    #def goBack(self):
        #widget.setCurrentIndex(widget.currentIndex()-1)

app = QApplication(sys.argv)
main = MainScreen()
main.setMinimumHeight(600)
main.setMinimumWidth(1000)
main.setWindowTitle("Phoenix Creative Database")
main.show()

# demoDialog = UploadDialog()
# demoDialog.setWindowFlag(Qt.FramelessWindowHint)
# demoDialog.show()

try:
    sys.exit(app.exec())
except:
    print("Exiting")
import sys
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import *#QDialog, QApplication, QStackedWidget, QWidget
from PyQt5.QtCore import Qt, QThread, QObject, pyqtSignal
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
                addFormula(to_upload[0][2], to_upload[0][1], to_upload[0][0],str("Originally imported from: "+f.split("/")[-1]))
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
        print("Current multiplier is:",currentUnit)
        print("Navigating to page:",str(self.NavPane.currentRow()))
        self.MainViewStack.setCurrentIndex(self.NavPane.currentRow())
        if self.NavPane.currentRow() == 2:
            self.MainViewStack.currentWidget().populateFormulaList()
            self.MainViewStack.currentWidget().clear(True)
        if self.NavPane.currentRow() == 3:
            self.MainViewStack.currentWidget().populateComponentList()
            self.MainViewStack.currentWidget().clear(True)
        if self.NavPane.currentRow() == 0:
            self.MainViewStack.currentWidget().refreshCounts()

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

        self.populateComponentList()
        self.measurementSelector.setCurrentIndex(currentUnit)
        self.componentList.itemSelectionChanged.connect(self.updateSelection)
        self.measurementSelector.currentIndexChanged.connect(self.updateMeasureUnits)
        self.searchBox.textChanged.connect(self.searchComponentsResults)

    def updateMeasureUnits(self):
        global currentUnit
        currentUnit = self.measurementSelector.currentIndex()
        self.updateFormulaTable()

    def clear(self,hide):
        self.compCodeLarge.clear()
        self.compDescLarge.clear()
        self.formulaTable.clearContents()
        if hide:
            self.displayWidget.hide()

    def updateSelection(self):
        self.displayWidget.show()
        self.measurementSelector.setCurrentIndex(currentUnit)
        selection = str(self.componentList.currentItem().text()).split()[0]
        print("User selected component",selection)

        compInfo = getComponent(selection)

        for c in compInfo:
            self.compCodeLarge.setText(c.IntCode)
            self.compDescLarge.setText(c.IntDesc.title())

        self.updateFormulaTable()
    
    def populateComponentList(self):
        self.componentList.clearSelection()
        print("Refreshing component list!")
        r = (getAllComponents())
        self.componentList.clear()
        for row in r:
            self.componentList.addItem(str(row.IntCode)+" - "+row.IntDesc.title())

    def searchComponentsResults(self):
        if self.searchBox.toPlainText().strip()=="":
            self.populateComponentList()
        else:
            r = componentSearch(self.searchBox.toPlainText())
            self.componentList.clear()
            for row in r:
                self.componentList.addItem(str(row.IntCode)+" - "+row.IntDesc.title())
        self.clear(False)
    def updateFormulaTable(self):
        if not self.compCodeLarge.text() == "":
            self.formulaTable.setSortingEnabled(False)
            formulasFound = getFormulasFromComponent(str(self.compCodeLarge.text())).fetchall()
            self.formulaTable.setRowCount(len(formulasFound))
            self.formulaTable.clearContents()

            currentRow = 0
            factor = Decimal(unitMultiplier[currentUnit])

            for f in formulasFound:
                self.formulaTable.setItem(currentRow,0,QTableWidgetItem(str(f.MPNum)))
                self.formulaTable.setItem(currentRow,1,QTableWidgetItem(f.FormName.title()))
                self.formulaTable.setItem(currentRow,2,QTableWidgetItem(str(f.Version)))
                self.formulaTable.setItem(currentRow,3,QTableWidgetItem(str(factor*f.GramsPerPint)))
                currentRow += 1
            
            self.formulaTable.resizeColumnsToContents()
            self.formulaTable.setSortingEnabled(True)   

class FormulaScreen(QWidget):
    def __init__(self):
        super(FormulaScreen, self).__init__()
        loadUi('src\\FormulaWidget.ui',self)
        self.populateFormulaList()
        self.measurementSelector.setCurrentIndex(currentUnit)
        self.versionList.currentIndexChanged.connect(self.updateVersion)
        self.formulaList.itemSelectionChanged.connect(self.updateSelection)
        self.notesBox.textChanged.connect(self.notesChanged)
        self.measurementSelector.currentIndexChanged.connect(self.updateMeasureUnits)
        self.deepSearchCheckbox.stateChanged.connect(self.searchFormulasResults)
        self.searchBox.textChanged.connect(self.searchFormulasResults)

    def clear(self, hide):
        self.versionList.clear()
        self.colorNumLarge.clear()
        self.colorNameLarge.clear()
        self.notesBox.clear()
        self.makeupTable.clearContents()
        if hide:
            self.displayWidget.hide()

    def searchFormulasResults(self):
        if self.searchBox.toPlainText().strip()=="":
            self.populateFormulaList()
        else:
            if self.deepSearchCheckbox.isChecked():
                r = deepFormulaSearch(self.searchBox.toPlainText().strip())
            else:
                r = shallowFormulaSearch(self.searchBox.toPlainText().strip())

            self.formulaList.clear()
            for row in r:
                self.formulaList.addItem(str(row.MPNum)+" - "+row.FormName.title())

        self.clear(False)

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
            self.makeupTable.resizeColumnsToContents()
            self.makeupTable.setSortingEnabled(True)

    def updateVersion(self):
        if self.formulaList.currentItem():
            print("Testing updateVersion()")
            selection = str(self.formulaList.currentItem().text()).split()[0]
            if(self.versionList.currentText() == ""):
                self.versionList.setCurrentIndex(0)
            colorInfo = getFormula(selection,self.versionList.currentText())

            color = colorInfo.fetchone()
            self.colorNameLarge.setText(color.FormName.title())
            self.notesBox.setText(color.Notes)
            
            self.updateMakeup()

    def updateSelection(self):
        self.measurementSelector.setCurrentIndex(currentUnit)
        self.displayWidget.show()
        
        selection = str(self.formulaList.currentItem().text()).split()[0]
        print("User selected formula",selection)
        versions = getNumVersions(selection).fetchall()
        newLen = len(versions)

        for i in range(0, len(versions)):
            if(i < self.versionList.count()):
                self.versionList.setItemText(i, str(versions.pop(0).Version))
            else:
                self.versionList.addItem(str(versions.pop(0).Version))
        
        while newLen < self.versionList.count():
            self.versionList.removeItem(self.versionList.count()-1)

        self.versionList.setCurrentIndex(0)
        colorInfo = getFormula(selection,self.versionList.currentText())
        # print("Debugging, version selected is:",self.versionList.currentText())

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
        r = getAllFormulas()
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
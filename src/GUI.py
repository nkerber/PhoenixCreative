import sys
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import *#QDialog, QApplication, QStackedWidget, QWidget
from PyQt5.QtCore import Qt, QThread, QObject, pyqtSignal
import PyQt5.QtGui as QtGui
from ConsoleApp import *
from decimal import Decimal
from ExtractFunction import *

#global variable for outputting correct numbers
#dictionary keys are the index of the measurementSelector dropdown menu,
#they correspond to the correct multiplier for the unit of measure of pints
unitMultiplier = {5:1,4:1.5,3:2,2:4,1:6,0:8}
currentUnit = 5

class UploadDialog(QDialog):
    def __init__(self):
        super(UploadDialog,self).__init__()
        loadUi('src\\UploadDialog.ui',self)

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
                addFormula(crsr, to_upload[0][2], to_upload[0][1], to_upload[0][0])
                old = to_upload[0]
                to_upload = to_upload[1:]
                for i in to_upload:
                    try:
                        addComponent(crsr, i[0], i[1])
                        addMakeupElement(crsr, old[2], old[1], i[0],i[2])
                    except(Exception):
                        print()
            self.progress.emit(current)
        self.finished.emit()
    

class MainScreen(QMainWindow):
    def __init__(self):
        super(MainScreen,self).__init__()
        loadUi('src\\Navigator.ui',self)
        self.NavPane.itemSelectionChanged.connect(self.selectPanel)

        home = HomeScreen()
        upload = UploadScreen()
        formula = FormulaScreen()
        self.MainViewStack.addWidget(home)
        self.MainViewStack.addWidget(upload)
        self.MainViewStack.addWidget(formula)

    def selectPanel(self):
        print("Navigating to page:",str(self.NavPane.currentRow()))
        self.MainViewStack.setCurrentIndex(self.NavPane.currentRow())

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

        thread.start()
        try:
            sys.exit(newDialog.exec())
        except:
            print("")

class HomeScreen(QWidget):
    def __init__(self):
        super(HomeScreen,self).__init__()
        loadUi('src\\HomeWidget.ui',self)

        #is there a better way to do this without this pointless loop?
        for row in componentCount(crsr):
            self.numComponents.setText(str(row.Count))
        
        for row in formulaCount(crsr):
            self.numFormulas.setText(str(row.Count))

class FormulaScreen(QWidget):
    def __init__(self):
        super(FormulaScreen, self).__init__()
        loadUi('src\\FormulaWidget.ui',self)
        self.populateFormulaList()
        self.measurementSelector.setCurrentIndex(currentUnit)

        #self.formulaList.setCurrentRow(0)
        #self.formulaList.setCurrentItem(self.formulaList.itemFromIndex(0))
        #neither of these seem to work. want to make it automatically
        #display the info from the first formula in the list
 
        #self.backButton.clicked.connect(self.goBack)
        self.formulaList.itemSelectionChanged.connect(self.updateSelection)
        #Note: right now I imagine this could have the potential to
        #cause tremendous lag. Need a way to make this only
        #update notes in the database every 10 seconds or something like that
        # could maybe call this only when the user changes their selection?
        # create an updateallinfo function that gets called every time the user switches
        # screens ??
        self.notesBox.textChanged.connect(self.notesChanged)
        self.measurementSelector.currentIndexChanged.connect(self.updateMeasureUnits)

        self.searchBox.textChanged.connect(self.searchFormulasResults)
        #QPlainTextEdit.plainte

    def searchFormulasResults(self):
        if self.searchBox.toPlainText=="":
            self.populateFormulaList(crsr)
        else:
            r = getSearchedFormulas(crsr,self.searchBox.toPlainText())
            self.formulaList.clear()
            for row in r:
                self.formulaList.addItem(row.FormName.title())

    def updateMeasureUnits(self):
        global currentUnit
        currentUnit = self.measurementSelector.currentIndex()
        self.updateMakeup()

    def updateMakeup(self):
        makeupElements = getMakeupElements(crsr,str(self.colorNumLarge.text())).fetchall()
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

    def updateSelection(self):
        selection = str(self.formulaList.currentItem().text())
        print("User selected formula",selection)
        colorInfo = getFormula(crsr,selection)

        # note the current temporary solution for versioning.
        # need to find a better way!

        for color in colorInfo:
            self.colorNameLarge.setText(color.FormName.title())
            self.colorNumLarge.setText(str(color.MPNum))
            self.colorVersionLarge.setText(str(color.Version))
        # THIS IS A STUPID WORKAROUND, NEED TO FIND A BETTER SOLUTION
        # otherwise the queries get stacked and the program breaks! ideas welcome
        #self.colorNameLarge = colorInfo.FormName

        if color.Notes == None:
            self.notesBox.clear()
        else:
            self.notesBox.setPlainText(str(color.Notes))
        self.updateMakeup()

    def notesChanged(self):
        #the following line is a temporary workaround until I can make it so that the
        # interface for formulas is not displayed until a formula is actually selected
        if self.formulaList.currentItem():
            updateNotes(crsr,str(self.colorNumLarge.text()),str(self.colorVersionLarge.text()),self.notesBox.toPlainText())
        crsr.commit()
    def populateFormulaList(self):
        r = (getAllFormulas(crsr))
        self.formulaList.clear()
        for row in r:
            self.formulaList.addItem(row.FormName.title())

    #def goBack(self):
        #widget.setCurrentIndex(widget.currentIndex()-1)

app = QApplication(sys.argv)
main = MainScreen()
main.setMinimumHeight(600)
main.setMinimumWidth(1000)
main.setWindowTitle("Phoenix Creative Database")
main.show()

try:
    sys.exit(app.exec())
except:
    print("Exiting")
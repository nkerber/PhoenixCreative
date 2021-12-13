import sys
from PyQt5.uic import loadUi
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *#QDialog, QApplication, QStackedWidget, QWidget
from ConsoleApp import *
from decimal import Decimal

#global variable for outputting correct numbers
#dictionary keys are the index of the measurementSelector dropdown menu,
#they correspond to the correct multiplier for the unit of measure of pints
unitMultiplier = {5:1,4:-1,3:-1,2:-1,1:-1,0:-1}
currentUnit = 5


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

class HomeScreen(QWidget):
    def __init__(self):
        super(HomeScreen,self).__init__()
        loadUi('src\\HomeWidget.ui',self)

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

        for element in makeupElements:
            self.makeupTable.setItem(currentRow,0,QTableWidgetItem(element.CompCode))
            self.makeupTable.setItem(currentRow,1,QTableWidgetItem(element.IntDesc.title()))
            self.makeupTable.setItem(currentRow,2,QTableWidgetItem(str(unitMultiplier[currentUnit]*element.GramsPerPint)))
            if not currentRow == 0:
                self.makeupTable.setItem(currentRow,3,QTableWidgetItem(str(unitMultiplier[currentUnit]*element.GramsPerPint+Decimal(self.makeupTable.item(currentRow-1,3).text()))))
            else:
                self.makeupTable.setItem(currentRow,3,QTableWidgetItem(str(unitMultiplier[currentUnit]*element.GramsPerPint)))
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
import sys
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QThread, QObject, pyqtSignal
import PyQt5.QtGui as QtGui
from PyODBCqueries import *
from decimal import Decimal
from ExtractFunction import *
from time import sleep

# Developed by Nate Kerber and Hunter Austin
# Database Final Project
# Client: Phoenix Creative

# Global variable for scaling quantities
# Dictionary keys are the index of the measurementSelector dropdown menu,
# they correspond to the correct multiplier for the unit of measure of pints
unitMultiplier = {5:1,4:1.5,3:2,2:4,1:6,0:8}
currentUnit = 5

# Popup menu displaying the upload progress of any set of files
class UploadDialog(QDialog):
    # See UploadDialog.ui
    def __init__(self):
        super(UploadDialog,self).__init__()
        loadUi('src\\UploadDialog.ui',self)
    
    # Closes the dialog automatically when the upload thread finishes.
    # If the event's sender is anything other than a Worker object,
    # ie. a human, ignore the event (idiot-proofing)
    def closeEvent(self, event):
        if not isinstance(self.sender(),Worker):
            event.ignore()

# Multithreadding application so user can continue to browse the app while upload does it's thing
# Worker handles all of the upload processing, emitting signals as it goes to update the UI
class Worker(QObject):
    # Signals to the main thread
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    fileName = pyqtSignal(str)
    files = ""

    def __init__(self, f):
        super(Worker,self).__init__()
        self.files = f

    # Execute the extraction and upload stuff
    def run(self):
        current = 0
        for f in self.files:
            print(f)
            current += 1

            # Parse all file locations, looking for ".pdf" in the filename
            if ".pdf" in f:
                try:
                    self.fileName.emit(f) # Send current filename to other thread
                    to_upload = extractPDF(f) # Grab our PDF from Adobe as a JSON object and parse it

                    # Begin uploading the PDF to the database
                    addFormula(to_upload[0][2], to_upload[0][1], to_upload[0][0])
                    old = to_upload[0] # Save formula information
                    to_upload = to_upload[1:] # Remove formula information from components
                    
                    # Going through each component
                    for i in to_upload:
                        try:
                            # Add the component to the database if it doesn't exist already and connect the component to the formula
                            addComponent( i[0], i[1])
                            addMakeupElement( old[2], old[1], i[0],i[2])
                        except(Exception):
                            print("Components/Makeup element were not added!")
                except:
                    print("Filename might not be a PDF! Remove any instance of \".pdf\" from the filename so this doesn't happen again!")

            # Tell the world what we have done
            self.progress.emit(current)
        
        # Wait a couple seconds on complete, then close
        sleep(2)
        self.finished.emit()

# Housing for user interface
class MainScreen(QMainWindow):
    def __init__(self):
        super(MainScreen,self).__init__()
        loadUi('src\\Navigator.ui',self)
        self.NavPane.itemSelectionChanged.connect(self.selectPanel)

        # Instantiate screens and add them to the list
        home = HomeScreen()
        upload = UploadScreen()
        formula = FormulaScreen()
        component = ComponentScreen()
        self.MainViewStack.addWidget(home)
        self.MainViewStack.addWidget(upload)
        self.MainViewStack.addWidget(formula)
        self.MainViewStack.addWidget(component)

    # Called to change screens in the UI
    def selectPanel(self):
        # Change current visual panel
        # print("Navigating to page:",str(self.NavPane.currentRow()))
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

# Housing for UI
class HomeScreen(QWidget):
    def __init__(self):
        super(HomeScreen,self).__init__()
        loadUi('src\\HomeWidget.ui',self)
        # TODO in HomeWidget.ui: Make logo transparent background, not white
        self.refreshCounts()
        
        # Is there a better way to do this without this pointless loop?
    def refreshCounts(self):
        for row in componentCount():
            self.numComponents.setText(str(row.Count))
        
        for row in formulaCount():
            self.numFormulas.setText(str(row.Count))

# UI for uploading PDFs to the Adobe algorithm + database
class UploadScreen(QWidget):
    def __init__(self):
        # Load our UI
        super(UploadScreen,self).__init__()
        loadUi('src\\UploadWidget.ui',self)

        # Connect the button to our import function
        self.uploadButton.clicked.connect(self.importFiles)

    # Start a multithreadded window for uploading/parsing the PDF to the database
    def startUploadDialog(self, links):
        # Instantiate our uploadDialog object for the user to track how far along the upload process is
        newDialog = UploadDialog()
        newDialog.setFixedHeight(150)
        newDialog.setFixedWidth(300)
        newDialog.show()
        newDialog.currentFormula.setText("No Formula")
        newDialog.progressBar.setRange(0, len(links))

        # Create our thread/worker and assign the worker to that thread
        thread = QThread()
        worker = Worker(links)
        worker.moveToThread(thread)

        # Connect worker and thread signals
        thread.started.connect(worker.run) # On start, worker runs
        worker.finished.connect(thread.quit) # On finish, thread closes
        worker.finished.connect(worker.deleteLater) # On finish, worker closes
        thread.finished.connect(thread.deleteLater) # On thread finish, thread closes
        worker.progress.connect(newDialog.progressBar.setValue) # When worker makes progress, set the progressBar value
        worker.fileName.connect(newDialog.currentFormula.setText) # When the worker changes filenames, set the formula display text

        # Begin processing
        thread.start()

        # Keep it open until things are done
        try:
            sys.exit(newDialog.exec())
        except:
            print("")
    
    # Visual display for drag and drop to go from the (/) to the []+ icon when hovering over the dropspace
    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        if event.mimeData().hasUrls(): # If we have files
            event.accept()              # Display the []+
        else:
            event.ignore()              # Otherwise display the (/)
    
    # Same thing as dragEnterEvent(), but for when the mouse moves pixels inside the dropspace
    def dragMoveEvent(self, event: QtGui.QDragMoveEvent):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            event.ignore()

    # When a user actually drops files into the dropspace
    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        # As long as we have files
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)

            # Accept the drop
            event.accept()
            links = []

            # If the item is a localFile, add it to our list
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    links.append(str(url.toLocalFile()))
            
            # Create and start the upload process
            self.startUploadDialog(links)
                    
    # Non-Drag and Drop UI for selecting pdfs. This is technically safer due to it only finding *.pdf files, but drag and drop is much friendlier
    def importFiles(self):
        # Set our options
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        # Open dialog for pdf files using the options specified
        files, _ = QFileDialog.getOpenFileNames(self,"QFileDialog.getOpenFileNames()", "","PDF Files (*.pdf)", options=options)
        
        # Open and start upload dialog for uploading PDFs
        self.startUploadDialog(files)

# Widget for showing all formulas that qualify for search, or all formulas in the database if there is no search text
class FormulaScreen(QWidget):
    def __init__(self):
        # Load our UI
        super(FormulaScreen, self).__init__()
        loadUi('src\\FormulaWidget.ui',self)

        # Fill our list with elements
        self.populateFormulaList()

        # Set our measurement dropdown to our default/current value
        self.measurementSelector.setCurrentIndex(currentUnit)
        # Connect our version list dropdown to our current formula by version function
        self.versionList.currentIndexChanged.connect(self.updateVersion)
        # Connect our formulaList to call our select formula function
        self.formulaList.itemSelectionChanged.connect(self.updateSelection)
        # Connect our notes box so that when we type, we call our function to update the database with the notes
        self.notesBox.textChanged.connect(self.notesChanged)
        # Connect our unit multiplier changing to call our update function for both the multiplier and the makeup quantities
        self.measurementSelector.currentIndexChanged.connect(self.updateMeasureUnits)
        # Connect our checkbox for deep search to re-call searchFormulasResults on either toggle
        self.deepSearchCheckbox.stateChanged.connect(self.searchFormulasResults)
        # Connect our search text so that when it changes, we call our searchResults function
        self.searchBox.textChanged.connect(self.searchFormulasResults)

    # Clear all data from the UI, leaving it visible if hide == false
    def clear(self, hide):
        self.versionList.clear()
        self.colorNumLarge.clear()
        self.colorNameLarge.clear()
        self.notesBox.clear()
        self.makeupTable.clearContents()
        if hide:
            self.displayWidget.hide()

    # Fill our formulaList with formulas that pass the search parameter
    def searchFormulasResults(self):
        # If we have no search text, just display all results
        if self.searchBox.toPlainText().strip()=="":
            self.populateFormulaList()
        else:
            # Search based on deepSearch box
            if self.deepSearchCheckbox.isChecked():
                r = deepFormulaSearch(self.searchBox.toPlainText().strip())
            else:
                r = shallowFormulaSearch(self.searchBox.toPlainText().strip())

            # Clear list
            self.formulaList.clear()

            # Re-fill list
            for row in r:
                self.formulaList.addItem(str(row.MPNum)+" - "+row.FormName.title())

        self.clear(False)

    # Change our current unit multiplier across the entire program
    def updateMeasureUnits(self):
        global currentUnit
        currentUnit = self.measurementSelector.currentIndex()

        # Re-calculate and display our makeup elements
        self.updateMakeup()

    # Grab all elements for the formula and display them in the makeupTable
    def updateMakeup(self):
        # As long as we have both an MPNum and a version
        if not self.colorNumLarge.text() == "" and not self.versionList.currentText() == "":
            
            # Disable sorting
            self.makeupTable.setSortingEnabled(False)

            # Grab all elements
            makeupElements = getMakeupElements(str(self.colorNumLarge.text()),self.versionList.currentText()).fetchall()
            
            # UI stuff
            self.makeupTable.setRowCount(len(makeupElements))
            self.makeupTable.clearContents()

            currentRow = 0
            factor = Decimal(unitMultiplier[currentUnit])

            # Load elements into our table
            for element in makeupElements:
                self.makeupTable.setItem(currentRow,0,QTableWidgetItem(element.CompCode))
                self.makeupTable.setItem(currentRow,1,QTableWidgetItem(element.IntDesc.title()))
                self.makeupTable.setItem(currentRow,2,QTableWidgetItem(str(factor*element.GramsPerPint)))
                if not currentRow == 0:
                    self.makeupTable.setItem(currentRow,3,QTableWidgetItem(str(factor*element.GramsPerPint+Decimal(self.makeupTable.item(currentRow-1,3).text()))))
                else:
                    self.makeupTable.setItem(currentRow,3,QTableWidgetItem(str(factor*element.GramsPerPint)))
                currentRow += 1
            
            # Make things fit across the table and re-enable sorting
            self.makeupTable.resizeColumnsToContents()
            self.makeupTable.setSortingEnabled(True)

    # Grab the current formula with the selected version
    def updateVersion(self):
        # As long as we have an item selected
        if self.formulaList.currentItem():
            selection = str(self.formulaList.currentItem().text()).split()[0]
            
            # Reset our version selection if need be
            if(self.versionList.currentText() == ""):
                self.versionList.setCurrentIndex(0)
            
            # Grab the formula information
            formula = getFormula(selection,self.versionList.currentText()).fetchone()

            # Set our UI text to display information
            self.colorNameLarge.setText(formula.FormName.title())
            self.notesBox.setText(formula.Notes)
            
            # Update our table with accurate information
            self.updateMakeup()

    # Change our selection on press
    def updateSelection(self):
        self.measurementSelector.setCurrentIndex(currentUnit)
        self.displayWidget.show()
        
        selection = str(self.formulaList.currentItem().text()).split()[0]
        print("User selected formula",selection)

        # Store our versions in an array and the length of it. Can't use len(versions) down the line. Explained later
        versions = getNumVersions(selection).fetchall()
        newLen = len(versions)

        # For all current version numbers
        for i in range(0, len(versions)):
            # If we are trying to insert a version and we have an open slot for it
            if(i < self.versionList.count()):
                # Pop it off the array [hence, no len(versions)] and set the current item index text to our current text
                self.versionList.setItemText(i, str(versions.pop(0).Version))
            else:
                # Otherwise add it to the list
                self.versionList.addItem(str(versions.pop(0).Version))
        
        # If we had fewer new items than old items, we will have extras from the previous formula
        while newLen < self.versionList.count():
            # So remove them
            self.versionList.removeItem(self.versionList.count()-1)

        # Reset our selection to the latest version
        self.versionList.setCurrentIndex(0)

        # Refresh our formula based on version
        colorInfo = getFormula(selection,self.versionList.currentText())

        # This should only ever have one element, but whatever
        for color in colorInfo:
            self.colorNameLarge.setText(color.FormName.title())
            self.colorNumLarge.setText(str(color.MPNum))

        # This needs to be outside of the for loop for some reason. It breaks otherwise.
        if color.Notes == None:
            self.notesBox.clear()
        else:
            self.notesBox.setPlainText(str(color.Notes))

        # Grab elements for the table
        self.updateMakeup()

    # Call our database update function whenever notes are changed
    def notesChanged(self):
        # Only if we have a valid selection
        if self.formulaList.currentItem():
            updateNotes(str(self.colorNumLarge.text()),self.versionList.currentText(),self.notesBox.toPlainText())

    # Grab all formulas, disregarding search term
    def populateFormulaList(self):
        # Clear list and selection
        self.formulaList.clearSelection()
        self.formulaList.clear()
        
        # Place all results in the list
        r = getAllFormulas()
        for row in r:
            self.formulaList.addItem(str(row.MPNum)+" - "+row.FormName.title())

# Widget for showing all components that qualify for search, or all components in the database if there is no search text
# Very similar to FormulaScreen, but with fewer connections and different components in the UI
class ComponentScreen(QWidget):
    def __init__(self):
        super(ComponentScreen, self).__init__()
        loadUi('src\\ComponentWidget.ui',self)

        self.populateComponentList()
        self.measurementSelector.setCurrentIndex(currentUnit)
        self.componentList.itemSelectionChanged.connect(self.updateSelection)
        self.measurementSelector.currentIndexChanged.connect(self.updateMeasureUnits)
        self.searchBox.textChanged.connect(self.searchComponentsResults)

    # Change our current unit multiplier across the entire program
    def updateMeasureUnits(self):
        global currentUnit
        currentUnit = self.measurementSelector.currentIndex()
        self.updateFormulaTable()

    # Clear all data from the UI, leaving it visible if hide == false
    def clear(self,hide):
        self.compCodeLarge.clear()
        self.compDescLarge.clear()
        self.formulaTable.clearContents()
        if hide:
            self.displayWidget.hide()

    # Change our selection on press
    def updateSelection(self):
        self.displayWidget.show()
        self.measurementSelector.setCurrentIndex(currentUnit)
        selection = str(self.componentList.currentItem().text()).split()[0]

        compInfo = getComponent(selection)

        for c in compInfo:
            self.compCodeLarge.setText(c.IntCode)
            self.compDescLarge.setText(c.IntDesc.title())

        self.updateFormulaTable()
    
    # Grab all components, disregarding search term
    def populateComponentList(self):
        self.componentList.clearSelection()
        r = (getAllComponents())
        self.componentList.clear()
        for row in r:
            self.componentList.addItem(str(row.IntCode)+" - "+row.IntDesc.title())

    # Fill our componentList with components that pass the search parameter
    def searchComponentsResults(self):
        if self.searchBox.toPlainText().strip()=="":
            self.populateComponentList()
        else:
            r = componentSearch(self.searchBox.toPlainText())
            self.componentList.clear()
            for row in r:
                self.componentList.addItem(str(row.IntCode)+" - "+row.IntDesc.title())
        self.clear(False)
    
    # Clear and reset our table with valid information based on selection
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

app = QApplication(sys.argv)
main = MainScreen()
main.setMinimumHeight(600)
main.setMinimumWidth(1000)
main.setWindowTitle("Phoenix Creative Database")
# TODO set window image
main.show()

# TODO log to file

try:
    sys.exit(app.exec())
except:
    print("Exiting")
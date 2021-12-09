from ConsoleApp import *
from ExtractFunction import *
# from GUI import *
 
while True:
    print()
    cmd = int(input("Options: Display all components (1), Display all formulas (2), Find a specific component (3), Find a specific formula (4), Search formulas (5), Search components (6), Add component (7), Add makeup element (8), Add formula (9), Update formula notes (10), Extract and upload information from PDF (11), Exit (0) "))
    if cmd == 0:
        print("Closing...")
        break
    elif cmd == 1:
        displayAllComponents(crsr)
    elif cmd == 2:
        displayAllFormulas(crsr)
    elif cmd == 3:
        findComponent(crsr)
    elif cmd == 4:
        findFormula(crsr)
    elif cmd == 5:
        searchFormulas(crsr)
    elif cmd == 6:
        searchComponents(crsr)
    elif cmd == 7:
        addComponentAsk(crsr)
    elif cmd == 8:
        addMakeupElementAsk(crsr)
    elif cmd == 9:
        addFormulaAsk(crsr)
    elif cmd == 10:
        updateNotes(crsr,2112,2.0,"Note added from python!")
    elif cmd == 11:
        to_upload = []
        path = str(input("Please enter the absolute path to the file you want to upload"))
        to_upload = extractPDF(path)
        addFormula(crsr, to_upload[0][2], to_upload[0][1], to_upload[0][0])
        old = to_upload[0]
        to_upload = to_upload[1:]
        for i in to_upload:
            try:
                addComponent(crsr, i[0], i[1])
                addMakeupElement(crsr, old[2], old[1], i[0],i[2])
            except(Exception):
                print()
    else:
        print("Invalid command!")
    cnxn.commit() #Save changes to the database after each command
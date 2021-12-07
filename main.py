from ConsoleApp import *
from GUI import *
from ReadPDF import *

while True:
    print()
    cmd = int(input("Options: Display all components (1), Display all formulas (2), Find a specific component (3), Find a specific formula (4), Search formulas (5), Search components (6), Add component (7), Add makeup element (8), Add formula (9), Update formula notes (10), Exit (0) "))
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
    else:
        print("Invalid command!")
    cnxn.commit() #Save changes to the database after each command
# This code operated the application from the command line
# and with the introduction of the GUI has been deprecated.

# from ConsoleApp import *
# from ExtractFunction import *
# from GUI import *

# def addMakeupElementAsk(crsr):
#     formNum = input("What is the formula number? ")
#     version = input("What is the formula version? ")
#     compCode = input("What is the intermediate code for the component? ")
#     GpP = input("What is the GpP for the component? ")
#     addMakeupElement(crsr,formNum,version,compCode,GpP)

# def addFormulaAsk(crsr):
#     formNum = input("What is the formula number? ")
#     version = input("What is the formula version? ")
#     formName = input("What is the formula name? ")
#     addFormula(crsr,formNum,version,formName)

# def outputComponent(crsr,sql):
#     rows = crsr.execute(sql)
#     for row in rows:
#         printer = "Component: " + row.IntCode 
#         if row.IntDesc is not None:
#             printer += "Description: " + row.IntDesc
#         print(printer)

# def displayAllComponents(crsr):
#     sql = "SELECT * "
#     sql+= "FROM Component"
#     outputComponent(crsr,sql)

# def findComponent(crsr):
#     intCode = input("What component would you like to display? ")
#     sql = "SELECT * "
#     sql+= "FROM Component "
#     sql+= "WHERE IntCode = '"+intCode+"'"
#     outputComponent(crsr,sql)

# def searchComponents(crsr):
#     param = input("Search components by code or description: ")
#     sql =  "SELECT * "
#     sql += "FROM Component "
#     sql += "WHERE IntCode LIKE '%"+str(param)+"%' OR IntDesc LIKE '%"+str(param)+"%'"
#     outputComponent(crsr,sql)

# def searchFormulas(crsr):
#     param = input("Search formulas by name, number, version, or notes: ")
#     sql =  "SELECT * "
#     sql += "FROM Formula "
#     sql += "WHERE FormName LIKE '%"+str(param)+"%' OR MPNum LIKE '%"+str(param)+"%' OR Version LIKE '%"+str(param)+"%' OR Notes LIKE '%"+str(param)+"%'"
#     outputFormula(crsr,sql)

# def addComponentAsk(crsr):
#     code = input("What is the intermediate code for the component? ")
#     desc = input("What is the description for the component? ")
#     addComponent(crsr,code,desc)

# def outputMakeup(crsr,formCode):
#     sql =  "SELECT M.CompCode,C.IntDesc,M.GramsPerPint " 
#     sql += "FROM Makeup M, Component C "
#     sql += "WHERE FormNum = " + str(formCode) + " AND M.CompCode = C.IntCode "
#     sql += "ORDER BY GramsPerPint DESC"
#     rows = crsr.execute(sql)
#     for row in rows:
#         printer = "Component: " + row.CompCode 
#         if row.IntDesc is not None:
#             printer += "Description: " + row.IntDesc
#         printer += "Grams per pint: "+str(row.GramsPerPint)
#         print(printer)

# def outputFormula(crsr,sql):
#     rows = crsr.execute(sql)
#     if not crsr.rowcount == 0:
#         for row in rows:
#             printer = "Formula: " + str(row.MPNum) + " Version: " + str(row.Version) + " Formula Name: " + row.FormName
#             if row.Notes is not None:
#                 printer += "Notes: " + row.Notes
#             print(printer)
#     else:
#         print("No formulas found with that query!")

# def findFormula(crsr):
#     formCode = input("What formula would you like to display? ")
#     sql = "SELECT * "
#     sql+= "FROM Formula "
#     sql+= "WHERE MPNum = "+str(formCode)
#     outputFormula(crsr,sql)
#     outputMakeup(crsr,formCode)


# while True:
#     print()
#     cmd = int(input("Options: Display all components (1), Display all formulas (2), Find a specific component (3), Find a specific formula (4), Search formulas (5), Search components (6), Add component (7), Add makeup element (8), Add formula (9), Update formula notes (10), Extract and upload information from PDF (11), Exit (0) "))
#     if cmd == 0:
#         print("Closing...")
#         break
#     elif cmd == 1:
#         displayAllComponents(crsr)
#     elif cmd == 2:
#         displayAllFormulas(crsr)
#     elif cmd == 3:
#         findComponent(crsr)
#     elif cmd == 4:
#         findFormula(crsr)
#     elif cmd == 5:
#         searchFormulas(crsr)
#     elif cmd == 6:
#         searchComponents(crsr)
#     elif cmd == 7:
#         addComponentAsk(crsr)
#     elif cmd == 8:
#         addMakeupElementAsk(crsr)
#     elif cmd == 9:
#         addFormulaAsk(crsr)
#     elif cmd == 10:
#         updateNotes(crsr,2112,2.0,"Note added from python!")
#     elif cmd == 11:
#         to_upload = []
#         path = str(input("Please enter the absolute path to the file you want to upload"))
#         #to_upload = extractPDF(path)
#         addFormula(crsr, to_upload[0][2], to_upload[0][1], to_upload[0][0])
#         old = to_upload[0]
#         to_upload = to_upload[1:]
#         for i in to_upload:
#             try:
#                 addComponent(crsr, i[0], i[1])
#                 addMakeupElement(crsr, old[2], old[1], i[0],i[2])
#             except(Exception):
#                 print()
#     else:
#         print("Invalid command!")
#     cnxn.commit() #Save changes to the database after each command
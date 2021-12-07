import pyodbc

# Define Global Connection
try:
    conn_str = (r'DRIVER={SQL Server};Server=CS1;Database=PhoenixCreative;Trusted_Connection=YES;')
    cnxn = pyodbc.connect(conn_str)
    crsr = cnxn.cursor()
except pyodbc.Error:
    print("Database connection failed!")

# Define Lookup Commands
def outputMakeup(crsr,formCode):
    pass
    sql =  "SELECT M.CompCode,C.IntDesc,M.GramsPerPint " 
    sql += "FROM Makeup M, Component C "
    sql += "WHERE FormNum = " + str(formCode) + " AND M.CompCode = C.IntCode "
    sql += "ORDER BY GramsPerPint DESC"
    rows = crsr.execute(sql)
    for row in rows:
        printer = "Component: " + row.CompCode 
        if row.IntDesc is not None:
            printer += "Description: " + row.IntDesc
        printer += "Grams per pint: "+str(row.GramsPerPint)
        print(printer)

def outputFormula(crsr,sql):
    rows = crsr.execute(sql)
    if not crsr.rowcount == 0:
        for row in rows:
            printer = "Formula: " + str(row.MPNum) + " Version: " + str(row.Version) + " Formula Name: " + row.FormName
            if row.Notes is not None:
                printer += "Notes: " + row.Notes
            print(printer)
    else:
        print("No formulas found with that query!")

def findFormula(crsr):
    formCode = input("What formula would you like to display? ")
    sql = "SELECT * "
    sql+= "FROM Formula "
    sql+= "WHERE MPNum = "+str(formCode)
    outputFormula(crsr,sql)
    outputMakeup(crsr,formCode)

def displayAllFormulas(crsr):
    sql = "SELECT * "
    sql+= "FROM Formula"
    outputFormula(crsr,sql)

def outputComponent(crsr,sql):
    rows = crsr.execute(sql)
    for row in rows:
        printer = "Component: " + row.IntCode 
        if row.IntDesc is not None:
            printer += "Description: " + row.IntDesc
        print(printer)

def displayAllComponents(crsr):
    sql = "SELECT * "
    sql+= "FROM Component"
    outputComponent(crsr,sql)

def findComponent(crsr):
    intCode = input("What component would you like to display? ")
    sql = "SELECT * "
    sql+= "FROM Component "
    sql+= "WHERE IntCode = '"+intCode+"'"
    outputComponent(crsr,sql)

def searchComponents(crsr):
    param = input("Search components by code or description: ")
    sql =  "SELECT * "
    sql += "FROM Component "
    sql += "WHERE IntCode LIKE '%"+str(param)+"%' OR IntDesc LIKE '%"+str(param)+"%'"
    outputComponent(crsr,sql)

def searchFormulas(crsr):
    param = input("Search formulas by name, number, version, or notes: ")
    sql =  "SELECT * "
    sql += "FROM Formula "
    sql += "WHERE FormName LIKE '%"+str(param)+"%' OR MPNum LIKE '%"+str(param)+"%' OR Version LIKE '%"+str(param)+"%' OR Notes LIKE '%"+str(param)+"%'"
    outputFormula(crsr,sql)

# Insert commands

def addComponentAsk(crsr):
    code = input("What is the intermediate code for the component? ")
    desc = input("What is the description for the component? ")
    addComponent(crsr,code,desc)

def addComponent(crsr,code,desc):
    sql =  "IF EXISTS (SELECT IntCode FROM Component WHERE IntCode = '"+code+"')"
    sql += "UPDATE Component SET IntDesc = '"+desc+"' WHERE IntCode = '"+code+"'"
    sql += "ELSE INSERT INTO Component VALUES ('"+code+"','"+desc+"')"
    crsr.execute(sql)
    print("Updated",code,"successfully.")

def addMakeupElementAsk(crsr):
    formNum = input("What is the formula number? ")
    version = input("What is the formula version? ")
    compCode = input("What is the intermediate code for the component? ")
    GpP = input("What is the GpP for the component? ")
    addMakeupElement(crsr,formNum,version,compCode,GpP)

def addMakeupElement(crsr,formNum,Version,compCode,GpP):
    sql =  "IF EXISTS (SELECT FormNum,FormVersion,CompCode FROM Makeup WHERE FormNum = '"+str(formNum)+"' AND FormVersion = '"+str(Version)+"' AND CompCode = '"+compCode+"')"
    sql += "UPDATE Makeup SET GramsPerPint = '"+str(GpP)+"' WHERE FormNum = '"+compCode+"' AND FormVersion = '"+str(Version)+"' AND CompCode = '"+compCode+"'"
    sql += "ELSE INSERT INTO Makeup VALUES ('"+str(formNum)+"','"+str(Version)+"','"+compCode+"','"+str(GpP)+"')"
    crsr.execute(sql)
    print("Updated makeup for",str(formNum),str(Version),"and component",compCode,"successfully.")

def addFormulaAsk(crsr):
    formNum = input("What is the formula number? ")
    version = input("What is the formula version? ")
    formName = input("What is the formula name? ")
    addFormula(crsr,formNum,version,formName)

def addFormula(crsr, formNum,formVersion,formName):
    sql =  "IF EXISTS (SELECT MPNum FROM Formula WHERE MPNum = '"+str(formNum)+"' AND Version = '"+str(formVersion)+"')"
    sql += "UPDATE Formula SET FormName = '"+formName+"' WHERE MPNum = '"+str(formNum)+"' AND Version = '"+str(formVersion)+"'"
    sql += "ELSE INSERT INTO Formula VALUES ('"+str(formNum)+"','"+str(formVersion)+"','"+formName+"',NULL)"
    crsr.execute(sql)
    print("Updated formula",str(formNum),str(formVersion),"successfully.")

# Other

def updateNotes(crsr,formNum,formVersion,notes):
    sql = "UPDATE Formula SET Notes = '"+notes+"' WHERE MPNum = '"+str(formNum)+"' AND Version = '"+str(formVersion)+"'"
    crsr.execute(sql)
    print("Updated notes for formula",str(formNum),str(formVersion),"successfully.")
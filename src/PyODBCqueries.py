import pyodbc

# Define Global Connection
try:
    connectA = pyodbc.connect(r'DRIVER={SQL Server};Server=CS1;Database=PhoenixCreative;Uid=haustin23x;Pwd=2256017;').cursor() # For non-upload queries
    connectB = pyodbc.connect(r'DRIVER={SQL Server};Server=CS1;Database=PhoenixCreative;Uid=haustin23x;Pwd=2256017;').cursor() # For upload queries

except pyodbc.Error:
    print("Database connection failed!")
 
# Define Queries

def getNumVersions(formNum):
    sql =  "SELECT Version "
    sql += "FROM Formula "
    sql += "WHERE MPNum = "+str(formNum)+" "
    sql+= "ORDER BY Version DESC"
    # print("Trying to get version numbers for a formula: ", sql)
    return connectB.execute(sql)

def getMakeupElements(formCode,version):
    sql =  "SELECT M.CompCode,C.IntDesc,M.GramsPerPint " 
    sql += "FROM Makeup M, Component C "
    sql += "WHERE FormNum = " + str(formCode) + " AND FormVersion = " + str(version) +" AND M.CompCode = C.IntCode "
    sql += "ORDER BY GramsPerPint DESC"
    # print("Trying to get components for a formula: ", sql)
    return connectA.execute(sql)

def getAllFormulas():
    sql = "SELECT F1.FormName, F2.Version, F2.MPNum "
    sql +="FROM Formula as F1, (SELECT MAX(F.Version) as Version, F3.MPNum as MPNum FROM Formula F, (SELECT DISTINCT MPNum From Formula) as F3 WHERE F.MPNum = F3.MPNum GROUP BY F3.MPNum) as F2 "
    sql +="WHERE F1.MPNum = F2.MPNum and F1.Version = F2.Version"
    # print("Trying to get all formulas: ", sql)
    return connectA.execute(sql)

def componentCount():
    sql = "SELECT COUNT(*) AS Count "
    sql += "FROM Component"
    # print("Trying to count components: ", sql)
    return connectA.execute(sql)

def formulaCount():
    sql = "SELECT COUNT(*) AS Count "
    sql += "FROM Formula"
    # print("Trying to count formulas: ", sql)
    return connectA.execute(sql)

def getFormula(formNum,version):
    sql = "SELECT * "
    sql += "FROM Formula "
    sql += "WHERE MPNum = "+formNum+" AND Version = "+version+""
    # print("Trying to get a specific formula: ", sql)
    return connectA.execute(sql)

def getComponent(compCode):
    sql = "SELECT * "
    sql += "FROM Component "
    sql += "WHERE IntCode = '"+compCode+"'"
    # print("Trying to get a specific component: ", sql)
    return connectA.execute(sql)

def getAllComponents():
    sql =  "SELECT * "
    sql += "FROM Component "
    # print("Trying to get all components: ", sql)
    return connectA.execute(sql)

def componentSearch(param):
    sql =  "SELECT * "
    sql += "FROM Component "
    sql += "WHERE IntCode LIKE '%"+str(param)+"%' or IntDesc like '%"+str(param)+"%'"
    # print("Trying to search for components: ", sql)
    return connectA.execute(sql)

def getFormulasFromComponent(compCode):
    sql =  "SELECT F.MPNum,F.FormName,F.Version, M.GramsPerPint "
    sql += "FROM Component C, Formula F, Makeup M "
    sql += "WHERE C.IntCode = M.CompCode AND F.MPNum = M.FormNum AND C.IntCode = '"+str(compCode)+"'"
    # print("Trying to get all formulas that use a specific component: ", sql)
    return connectA.execute(sql)

def deepFormulaSearch(param):
    sql =  "SELECT DISTINCT Formula.MPNum, Formula.Version, CAST(Formula.FormName AS VARCHAR(MAX)) as FormName, CAST(Formula.Notes AS VARCHAR(MAX)) as Notes "
    sql += "FROM Formula, Makeup, Component,(SELECT MAX(F.Version) as Version, F3.MPNum as MPNum FROM Formula F, (SELECT DISTINCT MPNum From Formula) as F3 WHERE F.MPNum = F3.MPNum GROUP BY F3.MPNum) as F2 "
    sql += "WHERE Formula.MPNum = Makeup.FormNum AND Makeup.CompCode = Component.IntCode AND Formula.Version = F2.Version AND Formula.MPNum = F2.MPNum AND "
    sql += "(Component.IntDesc LIKE '%"+str(param) +"%' OR Formula.FormName LIKE '%"+str(param)+"%' OR Formula.MPNum LIKE '%"+str(param)+"%' OR Formula.Version LIKE '%"+str(param)+"%' OR Formula.Notes LIKE '%"+str(param)+"%' OR Component.IntCode LIKE '%"+str(param)+"%')"
    # print("Trying to search all formulas, notes, and components that have param: {", param, "}", sql)
    return connectA.execute(sql)

def shallowFormulaSearch(param):
    sql =  "SELECT DISTINCT Formula.MPNum, Formula.Version, CAST(Formula.FormName AS VARCHAR(MAX)) as FormName, CAST(Formula.Notes AS VARCHAR(MAX)) as Notes "
    sql += "FROM Formula,(SELECT MAX(F.Version) as Version, F3.MPNum as MPNum FROM Formula F, (SELECT DISTINCT MPNum From Formula) as F3 WHERE F.MPNum = F3.MPNum GROUP BY F3.MPNum) as F2 "
    sql += "WHERE Formula.Version = F2.Version AND Formula.MPNum = F2.MPNum AND "
    sql += "(Formula.FormName LIKE '%"+str(param)+"%' OR Formula.MPNum LIKE '%"+str(param)+"%' OR Formula.Version LIKE '%"+str(param)+"%' OR Formula.Notes LIKE '%"+str(param)+"%')"
    # print("Trying to search all formulas and notes that have param: {", param, "}", sql)
    return connectA.execute(sql)

def addComponent(code,desc):
    sql =  "IF EXISTS (SELECT IntCode FROM Component WHERE IntCode = '"+code+"')"
    sql += "UPDATE Component SET IntDesc = '"+desc+"' WHERE IntCode = '"+code+"'"
    sql += "ELSE INSERT INTO Component VALUES ('"+code+"','"+desc+"')"
    # print("Trying to add a component to the database: {", code, "}", sql)
    try:
        connectA.execute(sql)
        connectA.commit()
    except:
        print("Updated",code,"unsuccessfully.")

def addMakeupElement(formNum,Version,compCode,GpP):
    sql =  "IF EXISTS (SELECT FormNum,FormVersion,CompCode FROM Makeup WHERE FormNum = '"+str(formNum)+"' AND FormVersion = '"+str(Version)+"' AND CompCode = '"+compCode+"')"
    sql += "UPDATE Makeup SET GramsPerPint = '"+str(GpP)+"' WHERE FormNum = '"+compCode+"' AND FormVersion = '"+str(Version)+"' AND CompCode = '"+compCode+"'"
    sql += "ELSE INSERT INTO Makeup VALUES ('"+str(formNum)+"','"+str(Version)+"','"+compCode+"','"+str(GpP)+"')"
    # print("Trying to add a connection between a formula and a component: ", sql)
    try:
        connectA.execute(sql)
        connectA.commit()
    except:
        print("Updated makeup for",str(formNum),str(Version),"and component",compCode,"unsuccessfully.")

def addFormula( formNum,formVersion,formName,fileName):
    sql =  "IF EXISTS (SELECT MPNum FROM Formula WHERE MPNum = '"+str(formNum)+"' AND Version = '"+str(formVersion)+"')"
    sql += "UPDATE Formula SET FormName = '"+formName+"' WHERE MPNum = '"+str(formNum)+"' AND Version = '"+str(formVersion)+"'"
    sql += "ELSE INSERT INTO Formula VALUES ('"+str(formNum)+"','"+str(formVersion)+"','"+formName+"','"+fileName+"')"
    # print("Trying to add a formula to the database: ", sql)
    try:
        connectA.execute(sql)
        connectA.commit()
    except:
        print("Updated formula",str(formNum),str(formVersion),"unsuccessfully.")

def updateNotes(formNum,formVersion,notes):
    if notes == "":
        sql = "UPDATE Formula SET Notes = NULL WHERE MPNum = '"+str(formNum)+"' AND Version = '"+str(formVersion)+"'"
    else:
        sql = "UPDATE Formula SET Notes = '"+notes+"' WHERE MPNum = '"+str(formNum)+"' AND Version = '"+str(formVersion)+"'"
    # print("Trying to update notes in the database: ", sql)
    try:
        connectA.execute(sql)
        connectA.commit()
    except:
        print("Updated notes for formula",str(formNum),str(formVersion),"unsuccessfully.")
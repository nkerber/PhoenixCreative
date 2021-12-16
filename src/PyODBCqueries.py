import pyodbc

# Define Global Connection
try:
    connectA = pyodbc.connect(r'DRIVER={SQL Server};Server=CS1;Database=PhoenixCreative;Uid=haustin23x;Pwd=2256017;').cursor()
    connectB = pyodbc.connect(r'DRIVER={SQL Server};Server=CS1;Database=PhoenixCreative;Uid=haustin23x;Pwd=2256017;').cursor()

except pyodbc.Error:
    print("Database connection failed!")
 
# Define Queries

def getNumVersions(formNum):
    
    sql =  "SELECT Version "
    sql += "FROM Formula "
    sql += "WHERE MPNum = "+str(formNum)+" "
    sql+= "ORDER BY Version DESC"
    print("Trying sql: ",sql)
    return connectB.execute(sql)

def getMakeupElements(formCode,version):
    sql =  "SELECT M.CompCode,C.IntDesc,M.GramsPerPint " 
    sql += "FROM Makeup M, Component C "
    sql += "WHERE FormNum = " + str(formCode) + " AND FormVersion = " + str(version) +" AND M.CompCode = C.IntCode "
    sql += "ORDER BY GramsPerPint DESC"
    #print("trying sql:",sql)
    return connectA.execute(sql)

def getAllFormulas():
    sql = "SELECT F1.FormName, F2.Version, F2.MPNum "
    sql +="FROM Formula as F1, (SELECT MAX(F.Version) as Version, F3.MPNum as MPNum FROM Formula F, (SELECT DISTINCT MPNum From Formula) as F3 WHERE F.MPNum = F3.MPNum GROUP BY F3.MPNum) as F2 "
    sql +="WHERE F1.MPNum = F2.MPNum and F1.Version = F2.Version"
    return connectA.execute(sql)

def componentCount():
    sql = "SELECT COUNT(*) AS Count "
    sql += "FROM Component"
    rows = connectA.execute(sql)
    return rows

def formulaCount():
    sql = "SELECT COUNT(*) AS Count "
    sql += "FROM Formula"
    rows = connectA.execute(sql)
    return rows

def getFormula(formNum,version):
    sql = "SELECT * "
    sql += "FROM Formula "
    sql += "WHERE MPNum = "+formNum+" AND Version = "+version+""
    print("Grabbing formulas via SQL: " + sql)
    return connectA.execute(sql)

def getComponent(compCode):
    sql = "SELECT * "
    sql += "FROM Component "
    sql += "WHERE IntCode = '"+compCode+"'"
    return connectA.execute(sql)

def getAllComponents():
    sql =  "SELECT * "
    sql += "FROM Component "
    return connectA.execute(sql)

def componentSearch(param):
    sql =  "SELECT * "
    sql += "FROM Component "
    sql += "WHERE IntCode LIKE '%"+str(param)+"%' or IntDesc like '%"+str(param)+"%'"
    return connectA.execute(sql)

def getFormulasFromComponent(compCode):
    sql =  "SELECT F.MPNum,F.FormName,F.Version, M.GramsPerPint "
    sql += "FROM Component C, Formula F, Makeup M "
    sql += "WHERE C.IntCode = M.CompCode AND F.MPNum = M.FormNum AND C.IntCode = '"+str(compCode)+"'"
    return connectA.execute(sql)

def deepFormulaSearch(param):
    sql =  "SELECT DISTINCT Formula.MPNum, Formula.Version, CAST(Formula.FormName AS VARCHAR(MAX)) as FormName, CAST(Formula.Notes AS VARCHAR(MAX)) as Notes "
    sql += "FROM Formula, Makeup, Component,(SELECT MAX(F.Version) as Version, F3.MPNum as MPNum FROM Formula F, (SELECT DISTINCT MPNum From Formula) as F3 WHERE F.MPNum = F3.MPNum GROUP BY F3.MPNum) as F2 "
    sql += "WHERE Formula.MPNum = Makeup.FormNum AND Makeup.CompCode = Component.IntCode AND Formula.Version = F2.Version AND Formula.MPNum = F2.MPNum AND "
    sql += "(Component.IntDesc LIKE '%"+str(param) +"%' OR Formula.FormName LIKE '%"+str(param)+"%' OR Formula.MPNum LIKE '%"+str(param)+"%' OR Formula.Version LIKE '%"+str(param)+"%' OR Formula.Notes LIKE '%"+str(param)+"%' OR Component.IntCode LIKE '%"+str(param)+"%')"
    return connectA.execute(sql)

def shallowFormulaSearch(param):
    sql =  "SELECT DISTINCT Formula.MPNum, Formula.Version, CAST(Formula.FormName AS VARCHAR(MAX)) as FormName, CAST(Formula.Notes AS VARCHAR(MAX)) as Notes "
    sql += "FROM Formula,(SELECT MAX(F.Version) as Version, F3.MPNum as MPNum FROM Formula F, (SELECT DISTINCT MPNum From Formula) as F3 WHERE F.MPNum = F3.MPNum GROUP BY F3.MPNum) as F2 "
    sql += "WHERE Formula.Version = F2.Version AND Formula.MPNum = F2.MPNum AND "
    sql += "(Formula.FormName LIKE '%"+str(param)+"%' OR Formula.MPNum LIKE '%"+str(param)+"%' OR Formula.Version LIKE '%"+str(param)+"%' OR Formula.Notes LIKE '%"+str(param)+"%')"
    print("Shallow searching\n\n")
    return connectA.execute(sql)

def addComponent(code,desc):
    sql =  "IF EXISTS (SELECT IntCode FROM Component WHERE IntCode = '"+code+"')"
    sql += "UPDATE Component SET IntDesc = '"+desc+"' WHERE IntCode = '"+code+"'"
    sql += "ELSE INSERT INTO Component VALUES ('"+code+"','"+desc+"')"
    connectA.execute(sql)
    connectA.commit()

    print("Updated",code,"successfully.")

def addMakeupElement(formNum,Version,compCode,GpP):
    sql =  "IF EXISTS (SELECT FormNum,FormVersion,CompCode FROM Makeup WHERE FormNum = '"+str(formNum)+"' AND FormVersion = '"+str(Version)+"' AND CompCode = '"+compCode+"')"
    sql += "UPDATE Makeup SET GramsPerPint = '"+str(GpP)+"' WHERE FormNum = '"+compCode+"' AND FormVersion = '"+str(Version)+"' AND CompCode = '"+compCode+"'"
    sql += "ELSE INSERT INTO Makeup VALUES ('"+str(formNum)+"','"+str(Version)+"','"+compCode+"','"+str(GpP)+"')"
    connectA.execute(sql)
    connectA.commit()

    print("Updated makeup for",str(formNum),str(Version),"and component",compCode,"successfully.")

def addFormula( formNum,formVersion,formName,fileName):
    sql =  "IF EXISTS (SELECT MPNum FROM Formula WHERE MPNum = '"+str(formNum)+"' AND Version = '"+str(formVersion)+"')"
    sql += "UPDATE Formula SET FormName = '"+formName+"' WHERE MPNum = '"+str(formNum)+"' AND Version = '"+str(formVersion)+"'"
    sql += "ELSE INSERT INTO Formula VALUES ('"+str(formNum)+"','"+str(formVersion)+"','"+formName+"','"+fileName+"')"
    print("Attemping to execute query: ",sql)
    connectA.execute(sql)
    connectA.commit()
    print("Updated formula",str(formNum),str(formVersion),"successfully.")

def updateNotes(formNum,formVersion,notes):
    if notes == "":
        sql = "UPDATE Formula SET Notes = NULL WHERE MPNum = '"+str(formNum)+"' AND Version = '"+str(formVersion)+"'"
    else:
        sql = "UPDATE Formula SET Notes = '"+notes+"' WHERE MPNum = '"+str(formNum)+"' AND Version = '"+str(formVersion)+"'"
    connectA.execute(sql)
    print("Updated notes for formula",str(formNum),str(formVersion),"successfully.")
    connectA.commit()
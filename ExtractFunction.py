import logging
import os.path
import json

from adobe.pdfservices.operation.auth.credentials import Credentials
from adobe.pdfservices.operation.exception.exceptions import ServiceApiException, ServiceUsageException, SdkException
from adobe.pdfservices.operation.pdfops.options.extractpdf.extract_pdf_options import ExtractPDFOptions
from adobe.pdfservices.operation.pdfops.options.extractpdf.extract_element_type import ExtractElementType
from adobe.pdfservices.operation.execution_context import ExecutionContext
from adobe.pdfservices.operation.io.file_ref import FileRef
from adobe.pdfservices.operation.pdfops.extract_pdf_operation import ExtractPDFOperation

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

nextColorName = False
nextMPNum = False
nextVersionNum = False
MPNum = -1
colorName = ""
versionNum = -1
preIC = 0
codeIndex = 0
descIndex = 1
gppIndex = 6
index = 0
begin = False
components = [[]]

def isNum(e):
    for i in e:
        if(not str.isdigit(i) and i != '.'):
            return False
    return True

def checkForElements(e):
    global nextColorName
    global colorName
    global nextMPNum
    global MPNum
    global nextVersionNum
    global versionNum
    global preIC

    e['Text'] = str.removesuffix(e['Text'], ' ')
    e['Text'] = str.removeprefix(e['Text'], ' ')

    if(nextMPNum):
        if(str.isdigit(e['Text'])):
            if(' ' in e['Text']):
                MPNum = json.dumps(e['Text']).split(' ')[0]
            else:
                MPNum = e['Text']
            nextMPNum = False
    
    if(nextColorName):
        colorName = e['Text']
        nextColorName = False
    
    if(nextVersionNum):
        if(not str.isdigit(e['Text']) and isNum(e['Text'])):
            if(' ' in e['Text']):
                versionNum = json.dumps(e['Text']).split(' ')[0]
            else:
                versionNum = e['Text']
            nextVersionNum = False

    if("MP Number" in e['Text']):
        nextMPNum = True
        if(len(json.dumps(e['Text'])) > len("MP Number A")): # " A" is used to give an extra space at the end plus a couple other characters, because MPNum should be 5+ numbers.
            nextMPNum = False
            s = json.dumps(e['Text']).split(' ')
            MPNum = s[2]
    
    if("Name" in e['Text']):
        if(e['Text'].endswith('Name')):
            nextColorName = True
        elif(len(e['Text']) > len("Color Name ")):
            colorName = json.dumps(e['Text']).split(' ')[2]
    
    if("Version" in e['Text']):
        if(e['Text'].endswith('Version')):
            nextVersionNum = True
        elif(len(e['Text']) > len("Version ")):
            t = json.dumps(e['Text']).split(' ')
            if(not isNum(t[1])):
                nextVersionNum = True
            else:
                versionNum = t[1]
        else:
            nextVersionNum = True
    
    if("Intermediate Code" in e['Text']):
        preIC = 1

def postICElements(e):
    global components # Lists
    global preIC, codeIndex, descIndex, gppIndex, index # Ints
    global begin # bools

    if(preIC == 2):
        print(e['Text'])
        if('/TD/' in e['Path'] and begin):
            index = 0
            components.append([])
        elif(begin):
            index+=1

        if(index == codeIndex):
            components[-1].append(e['Text'])
        elif(index == descIndex):
            components[-1].append(e['Text'])
        elif(index == gppIndex):
            components[-1].append(e['Text'])

        if('Grams per Pint' in e['Text']):
            begin = True
        
        if('Total:' in e['Text']):
            preIC == 3
    elif(str.startswith(e['Text'], "Intermediate Code")):
        preIC = 2

def printCurrents():
    global colorName, versionNum, MPNum
    global components
    print('\nColor Name: ' + colorName)
    print('Version: ' + versionNum)
    print('MPNum: ' + MPNum)

    for i in components:
        print('Componet Code: ' + i[0])
        print('Componet Name: ' + i[1])
        print('Grams per Pint: ' + i[2])
    
    print('---------')

try:
    # get base path.
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # Initial setup, create credentials instance.
    credentials = Credentials.service_account_credentials_builder() \
        .from_file(base_path + "/pdfservices-api-credentials.json") \
        .build()

    # Create an ExecutionContext using credentials and create a new operation instance.
    execution_context = ExecutionContext.create(credentials)
    extract_pdf_operation = ExtractPDFOperation.create_new()

    # Set operation input from a source file.
    extract_pdf_operation.set_input(FileRef.create_from_local_file("C:/Users/bobhu/Desktop/Coca Cola-Silver.pdf")) # Hardcode local file for testing purposes

    # Build ExtractPDF options and set them into the operation
    extract_pdf_options: ExtractPDFOptions = ExtractPDFOptions.builder() \
        .with_element_to_extract(ExtractElementType.TEXT) \
        .build()
    extract_pdf_operation.set_options(extract_pdf_options)
    try:
        # Execute the operation.
        result: FileRef = extract_pdf_operation.execute(execution_context)

        # Save the result to the specified location.
        result.save_as(base_path + "/output/ExtractTextInfoFromPDF.json")

        f = open(base_path + "/output/ExtractTextInfoFromPDF.json", "r+", encoding="cp437") # Encoding lets us replace stupid characters
        
        fixed = f.readline()
        while(fixed[0] != '{'):
            while(fixed[0] != '{'):
                if(fixed[0] == '\n'):
                    fixed = f.readline()
                else: 
                    fixed = fixed[1:]
        
        while(not fixed.endswith('}')):
            fixed = fixed[:len(fixed)-1]
        f.close()

        f = open(base_path + "/output/ExtractTextInfoFromPDF.json", "w", encoding="cp437") # Close and reopen file for writing over current stuff. Then we can use it for parsing in the program.
        f.write(fixed)
        f.close()
    except (Exception):
        print('')

    f = open(base_path + "/output/ExtractTextInfoFromPDF.json")
    data = json.load(f)

    for i in data['elements']:
        if('Text' in i):
            if(preIC == 0):
                checkForElements(i)
            elif(preIC == 1 or preIC == 2):
                postICElements(i)
    
    components[0][0] = colorName
    components[0][1] = versionNum
    components[0][2] = MPNum
    printCurrents()
    # return components

except (ServiceApiException, ServiceUsageException, SdkException):
    logging.exception("Exception encountered while executing operation")

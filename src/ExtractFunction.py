import logging
import os
import json
import zipfile

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
versionNum = "NA"
preIC = 0
codeIndex = 0
descIndex = 1
gppIndex = 6
index = 0
begin = False
components = [[]]

# Reset all variables to their default. Otherwise, between extractions, these variables would remain as they were.
def reset():
    global nextColorName, nextMPNum, nextVersionNum, MPNum, colorName, versionNum, preIC, codeIndex, descIndex,gppIndex, index, begin, components
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

# Check for decimal number because Python doesn't have the capability to include '.' in their isDigit()
def isNum(e):
    for i in e:
        if(not str.isdigit(i) and i != '.'):
            return False
    return True

# Check to see if we find any of our variable names, and override the global variables if we find any
def checkForElements(e):
    global nextColorName
    global colorName
    global nextMPNum
    global MPNum
    global nextVersionNum
    global versionNum
    global preIC

    # Get rid of any extra spaces at either end
    e['Text'] = str.rstrip(e['Text'], ' ')
    e['Text'] = str.lstrip(e['Text'], ' ')

    # If the next value is supposed to be an MPNum
    if(nextMPNum):
        if(str.isdigit(e['Text'])):
            if(' ' in e['Text']):
                MPNum = json.dumps(e['Text']).split(' ')[0]
            else:
                MPNum = e['Text']
            nextMPNum = False
    
    # If the next value is supposed to be a colorName
    if(nextColorName):
        colorName = e['Text']
        nextColorName = False
    
    # If the next value is supposed to be a Version number
    if(nextVersionNum):
        if(not str.isdigit(e['Text']) and isNum(e['Text'])):
            if(' ' in e['Text']):
                versionNum = json.dumps(e['Text']).split(' ')[0]
            else:
                versionNum = e['Text']
            nextVersionNum = False

    # If we find "MP Number" in our current text
    if("MP Number" in e['Text']):
        nextMPNum = True

        # If we find a string that is longer than a basic "MP Number ", indicating that MP Number is potentially in this element
        if(len(json.dumps(e['Text'])) > len("MP Number A")): # " A" is used to give an extra space at the end plus a couple other characters, because MPNum should be 5+ numbers.
            nextMPNum = False
            s = json.dumps(e['Text']).split(' ')
            MPNum = s[2]
    
    # If we find "Name" in the current text
    if("Name" in e['Text']):
        # With nothing else at the end
        if(e['Text'].endswith('Name')):
            nextColorName = True
        elif(len(e['Text']) > len("Color Name ")): # Otherwise if the text potentially has a name after "Color Name"
            colorName = json.dumps(e['Text']).split(' ')[2]
    
    # If we find "Version" in the current text
    if("Version" in e['Text']):
        # And it ends with "Version"
        if(e['Text'].endswith("Version")):
            nextVersionNum = True
        elif(len(e['Text']) > len("Version ")): # Otherwise if it is longer than "Version ", indicating the version number might be in this element
            t = json.dumps(e['Text']).split(' ')

            # But we don't find a version number after the space
            if(not isNum(t[1])):
                nextVersionNum = True
            else:
                versionNum = t[1]
        else:
            nextVersionNum = True
    
    # If we find "Intermediate Code", we can move onto postICEElements()
    if("Intermediate Code" in e['Text']):
        preIC = 1

# Data grabber
def postICElements(e):
    global components # Lists
    global preIC, codeIndex, descIndex, gppIndex, index # Ints
    global begin # bools

    # If we care about our data (i.e. if we have found two instances of "Intermediate Code")
    if(preIC == 2):

        # If this is an end table element and we have begun grabbing data
        if("/TD/" in e['Path'] and begin):
            # Reset our position and add a new component
            index = 0
            components.append([])
        elif(begin):
            # Otherwise iterate
            index+=1

        # If we are at a known index
            # Append the current table element to that position
        if(index == codeIndex):
            components[-1].append(e['Text'])
        elif(index == descIndex):
            components[-1].append(e['Text'])
        elif(index == gppIndex):
            components[-1].append(e['Text'])

        # Once we find our GPP index, we can start grabbing data
        if('Grams per Pint' in e['Text']):
            begin = True
        
        # Once we find our end marker, we can stop looking for data
        if('Total:' in e['Text']):
            preIC == 3
    
    # Otherwise if we find our second intermediate code, we can start looking for data/indexes
    elif(str.startswith(e['Text'], "Intermediate Code")):
        preIC = 2

# A way to print stuff formatted nicely
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

# Send the file to Adobe and parse it
def extractPDF(path):
    reset()

    try:
        # get base path.
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) +"/PHOENIXCREATIVE"

        # Initial setup, create credentials instance.
        credentials = Credentials.service_account_credentials_builder() \
            .from_file("./pdfservices-api-credentials.json") \
            .build()

        # Create an ExecutionContext using credentials and create a new operation instance.
        execution_context = ExecutionContext.create(credentials)
        extract_pdf_operation = ExtractPDFOperation.create_new()

        # Set operation input from a source file.
        extract_pdf_operation.set_input(FileRef.create_from_local_file(path))

        # Build ExtractPDF options and set them into the operation
        extract_pdf_options: ExtractPDFOptions = ExtractPDFOptions.builder() \
            .with_element_to_extract(ExtractElementType.TEXT) \
            .build()
        extract_pdf_operation.set_options(extract_pdf_options)
        try:
            # Execute the operation.
            result: FileRef = extract_pdf_operation.execute(execution_context)

            # Remove previous file
            if os.path.exists("./output/structuredData.json"):
                os.remove("./output/structuredData.json")

            # Save the result to the specified location.
            result.save_as("./output/ExtractTextInfoFromPDF.zip")

            # Unzip file
            with zipfile.ZipFile("./output/ExtractTextInfoFromPDF.zip", 'r') as zipRef:
                zipRef.extractall("./output")

            # Remove old zip file
            if os.path.exists("./output/ExtractTextInfoFromPDF.zip"):
                os.remove("./output/ExtractTextInfoFromPDF.zip")

            # Open JSON file
            f = open("./output/structuredData.json", "r+", encoding="cp437") # Encoding lets us replace stupid characters
            
            # Make sure the file isn't weirdly encoded and have other garbage in it outside of the JSON
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

            # Overwrite the current file because we don't ever delete it
            f = open("./output/structuredData.json", "w", encoding="cp437") # Close and reopen file for writing over current stuff. Then we can use it for parsing in the program.
            f.write(fixed)
            f.close()
        except (Exception):
            print('Extraction process failed!')

        # Open and load the file as a JSON object so we can parse it
        f = open("./output/structuredData.json")
        data = json.load(f)

        # Start looking for things
        for i in data['elements']:
            if('Text' in i):
                if(preIC == 0):
                    checkForElements(i)
                elif(preIC == 1 or preIC == 2):
                    postICElements(i)

        # Set our initial elements to the formula information
        components[0][0] = colorName
        components[0][1] = versionNum
        components[0][2] = MPNum
        return components

    except (ServiceApiException, ServiceUsageException, SdkException):
        logging.exception("Exception encountered while executing operation")
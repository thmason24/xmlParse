#!/usr/bin/env python

import sys
import codecs
from splitFunctions import getCDATA 
from splitFunctions import reqObject
from splitFunctions import table2Lists
from splitFunctions import generateXMLReq
from bs4 import BeautifulSoup

#always print in unicode
#sys.stdout = codecs.getwriter('utf-8')(sys.stdout)

inRequirement=False
inFind=False
inReplace=False

def specParse(curBlock):
    descBlock=[]
    toDelete = []
    # determine requirement type
    reqType="I"
    for index, curLine in enumerate(curBlock):
        if "<requirement-type>" in curLine:
            if "Software Requirement" in curLine:
                reqType="R"        
                
    #execute find replace if of desired type        
    if reqType == "R":
        # import find block
        inDesc=False

        #extract description block
        for index, curLine in enumerate(curBlock):
            if "<description" in curLine:
                inDesc=True                
            if inDesc:
                descBlock.append(curLine)
                toDelete.append(index)
            if "</description" in curLine:
                inDesc=False
                        
        descBlock =  "".join(descBlock)
        # use LXML to extract CDATA from parse.
        CDATA = getCDATA(descBlock,"//description")[0]
        #parse with beautifulSoup
        soup = BeautifulSoup(CDATA, 'html.parser')

# here we must determine if the use case is in the form of a table or a list      
        if soup.table != None: #if table
            #break up requirement flows into info, main flow, alt flow, and specials
            reqType = "info"
            curObject = reqObject()
            curObject.reqType = "info"        
            scenario = []
            report = False
            appendOld = False
            #get table tag
            tableTag = soup.table
            tableTag.clear()
            tableHead = soup.table.prettify()
            #reread soup
            soup = BeautifulSoup(CDATA, 'html.parser')        
            #parse table formatted specs
            for row in soup.find_all('tr'):
                key = row.td.text  #grab key from first column
                #check if this is a report
                if "GENERAL" in key.upper() and "REPORT" in key.upper() and "HEADER" in key.upper():
                    report = True
                    inBody = False
                #assign key
                #for report
                if report:
                    #assign category
                    if ("BODY" in key.upper()  and "REPORT" in key.upper()) or "CONTENTS" in key.upper():
                        reqType = "report"
                        inBody = True
                        appendOld = True
                    elif "SPECIAL" in key.upper() and  "REQUIREMENT" in key.upper():
                        reqType = "special"
                        inBody = False
                        appendOld = True
                    elif inBody and (len(row.find_all("td")) != 3 or \
                    ("LAST" in key.upper() and "PAGE" in key.upper() and "REPORT" in key.upper())):
                        reqType = "reportTable"
                    #close old object and start a new one if keyed
                    if appendOld:
                        appendOld = False
                        scenario.append(curObject) #append last object to list
                        curObject = reqObject()   #start new object
                        curObject.reqType = reqType 
                        curObject.content.append(row)
                    else:
                        curObject.content.append(row)   #add this row to current object                
                    #assign espec to legacy tag
                    if "ESPEC" in key:
                        for word in key.split():
                            if "REN:ESPEC" in word:
                                curObject.legacyTag = word 
                #for use case
                else:
                    if "REN:ESPEC" in key:                 
                        #assign category
                        #try to see if there is a problem with the table
                        try:
                            if "SPECIAL" in key.upper():
                                reqType = "special"
                            elif "A" in row.find_all('td')[1].text:
                                reqType = "altflow"
                            else:
                                reqType = "mainflow"
                        except:
                            sys.stderr.write("\n\nfailed to read row \n\n")
                            sys.stderr.write(row.prettify())                            
                    elif "SPECIAL" in key.upper(): # case for no special requirements
                        reqType = "special"
                    
                    #close old object and start a new one if keyed
                    if "ESPEC" in key or "Special" in key:
                        scenario.append(curObject) #append last object to list
                        curObject = reqObject()   #start new object
                        #assign espec to legacy tag
                        for word in key.split():
                            if "REN:ESPEC" in word:
                                curObject.legacyTag = word 
                        curObject.reqType = reqType 
                        curObject.content.append(row)
                    else:
                        curObject.content.append(row)   #add this row to current object
            #append final object
            curObject.reqType = reqType
            scenario.append(curObject)  
            splitReqs =  table2Lists(scenario,tableHead)        

                
        else: # if formatted as list
            curObject = reqObject()
            curObject.reqType = "mainflow"        
            scenario = []
            report = False
            appendOld = False
#            for row in soup.find_all('p'):
            for row in soup.contents:
                try:
                    key = row.prettify()  
                except: 
                    key = row
                #chek for EPEC tag and assign it to legacy tag
                for word in key.split():
                    if "REN:ESPEC" in word:
                        curObject.legacyTag = word
                #check for PRD tag and assign it to parent tag
                for word in key.split():
                    if "REN:PRD" in word:
                        curObject.parentTag = word                        
                #check for words to transition to alt flows or special requirements
                if ("ALT" in key.upper() and "FLOW" in key.upper()) or \
                ("SPECIAL" in key.upper() and "REQUIREMENT" in key.upper()):
                    
                    #assign reqtype (later converted to category)
                    if "ALT" in key.upper() and "FLOW" in key.upper():
                        reqType = "altflow"
                    else:
                        reqType = "special"
                        
                    scenario.append(curObject) #append last object to list
                    curObject = reqObject()   #start new object
                    curObject.content.append(row)
                else:
                    curObject.content.append(row)   #add this row to current object
            #append final object
            scenario.append(curObject)
            for i in scenario:
                i.TTreqType = "Use Case"  # set all thes to use case
                i.cdata = ''
                for j in i.content:
                    try:
                        i.cdata = i.cdata + j.prettify()
                    except: 
                        i.cdata = i.cdata + j
            splitReqs =  scenario                                     
        #for each requirement that was split out we now
        # must generate a complete testtrack requirement      
        xmlRequirements = []
        curBlockOut=[]
        for i in splitReqs:
            xmlRequirements = generateXMLReq(i,''.join(curBlock))
            for j in xmlRequirements:
                curBlockOut.append(j)
        return curBlockOut
    else:
        #if not required type,  just return the block
        return curBlock
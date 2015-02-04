#!/usr/bin/env python

import sys
import codecs
from splitFunctions import getCDATA 
from splitFunctions import reqObject
from splitFunctions import table2Lists
from splitFunctions import generateXMLReq
from bs4 import BeautifulSoup
from lxml import etree

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
                
    #if it's a requirement,  then parse it      
    if reqType == "R":

        #extract title
        parser = etree.XMLParser(strip_cdata=False)
        root = etree.fromstring("".join(curBlock),parser)
        title=root.find("summary").text

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
        soup = BeautifulSoup(CDATA, 'lxml')
        
        #determine if formatting is table: just look for primary actor row.
        table = False
        for cell in soup.find_all('td'):
            if "PRIMARY" in cell.text.upper() and "ACTOR" in cell.text.upper():
                table = True
                

# here we must determine if the use case is in the form of a table or a list      
#        if soup.table != None: #if table
        if table:
            #break up requirement flows into info, main flow, alt flow, and specials
            reqType = "info"
            curObject = reqObject()
            curObject.reqType = "info"     
            curObject.title = title
            altTitle=''
            scenario = []
            report = False
            appendOld = False
            specialStarted = False
            #get table tag
            tableTag = soup.table
            tableTag.clear()
            tableHead = soup.table.prettify()
            #reread soup
            soup = BeautifulSoup(CDATA, 'lxml')        
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
                            if "SPECIAL" in key.upper() or specialStarted:
                                reqType = "special"
                                specialStarted = True # we now know we're in special requirements section
                            elif "A" in row.find_all('td')[1].text:
                                reqType = "altflow"
                                #extract title from key for alt flow and special titles
                                for word in key.split():
                                    if "REN:ESPEC" in word:
                                        tag = word
                                altTitle = key.split(tag)[1].replace('\n','')
                            else:
                                reqType = "mainflow"
                        except:
                            sys.stderr.write("\n\nfailed to read row \n\n")
                            sys.stderr.write(row.prettify().encode('utf'))                            
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
                        curObject.altTitle = altTitle                       
                        curObject.content.append(row)
                    else:
                        curObject.content.append(row)   #add this row to current object
            #append final object
            curObject.reqType = reqType
            curObject.altTitle = altTitle 
            scenario.append(curObject)
            splitReqs =  table2Lists(scenario,tableHead)        

                
        else: # if formatted as list
 
            #first generate info requirement
            scenario = []
            curObject = reqObject()
            reqType = "info"
            curObject.reqType = "info"
            curObject.title = title
            altEnable = False
            specEnable = False
            
            for row in soup.html.body.contents:
                #skip if no text attribue.
                try:
                    row.text 
                except:
                    continue
                try:
                    key = row.find('strong').text # find tags in bold faces
                except:
                    key = ""
                    
                #check for words to transition to alt flows or special requirements
                #if key is not None:
                if ("MAIN" in key.upper() and "FLOW" in key.upper()) or \
                ("ALTERNATE" in key.upper() and "FLOW" in key.upper()) or \
                ("SPECIAL" in key.upper() and "REQUIREMENT" in key.upper()) or \
                (reqType == "altflow" and "REN:ESPEC" in row.text.upper() and altEnable) or \
                (reqType == "special" and "REN:ESPEC" in row.text.upper() and specEnable ):
                    #before appending to the scenario we have to check
                    # if especs are in an ol list in which case we have to
                    #break them up for altflows and special reqs
                    #determine if "ol" is contained in curObject.content
                    foundOL = False
                    for item in curObject.content:
                        if item.find("ol") != None:
                            foundOL = True
                    if (reqType == "altflow" or reqType == "special") and foundOL:
                        splitObject = reqObject()
                        splitContent = BeautifulSoup("<div></div").body.contents[0]
                        firstItem = True
                        for item in curObject.content:
                            if item.name == "ol":
                                olTag = BeautifulSoup("<ol></ol").body.contents[0]
                                for listItem in item:  #iterate through list items
                                    try:
                                        listItem.text
                                    except:
                                        continue # navigable string
                                    if "REN:ESPEC" in listItem.text:
                                        if firstItem:                                                
                                            firstItem = False
                                            #for first espec just add this tag to the ol.  if it's the only one
                                            # it will be appended on the last append
                                            addListItem = BeautifulSoup(listItem.prettify())
                                            for k in addListItem.body.contents:
                                                olTag.append(k)                                            
                                        else:
                                            #wrap up the old ESPEC in it's own ordered list, add to scenario 
                                            #and start new one
                                            addListItem = BeautifulSoup(olTag.prettify())
                                            for k in addListItem.body.contents:
                                                splitContent.append(k)
                                            splitObject.content = splitContent.prettify()
                                            splitObject.reqType = reqType
                                                                                   
                                            scenario.append(splitObject)
                                            #start new
                                            splitObject = reqObject()
                                            splitContent = BeautifulSoup("<div></div").body.contents[0]
                                            olTag = BeautifulSoup("<ol></ol").body.contents[0]
                                            addListItem = BeautifulSoup(listItem.prettify())
                                            for k in addListItem.body.contents:
                                                olTag.append(k)
                                    else: # add to previous tag
                                        addListItem = BeautifulSoup(listItem.prettify())
                                        for k in addListItem.body.contents:
                                            olTag.append(k) 
                                        
                                #add final tag
                                addListItem = BeautifulSoup(olTag.prettify())
                                for k in addListItem.body.contents:
                                    splitContent.append(k)                                                
                            else:
                                addItem = BeautifulSoup(item.prettify())
                                for k in addItem.body.contents:
                                    splitContent.append(k)   
                                
                        splitObject.content = splitContent.prettify()
                        splitObject.reqType = reqType                                                                                                                                  
                        scenario.append(splitObject)
                    else:
                        curObject.reqType = reqType   

                        scenario.append(curObject) #append last object to list
                    curObject = reqObject() #start new object
                                                                                                              
                    #assign reqtype (later converted to category)
                    if "MAIN" in key.upper() and "FLOW" in key.upper():
                        reqType = "mainflow"

                    elif "ALTERNATE" in key.upper() and "FLOW" in key.upper() or\
                    (reqType == "altflow" and "REN:ESPEC" in row.text.upper() and altEnable):
                        reqType = "altflow"
                    else:
                        reqType = "special"
                                
                #check for EPEC tag to set enables
                for word in row.text.split():
                    if "REN:ESPEC" in word:
                        if reqType == "altflow":                            
                            altEnable = True;
                        if reqType == "special":
                            specEnable = True;
        
                curObject.content.append(row)   #add this row to current object
            #append final object
            curObject.reqType = reqType                    
            scenario.append(curObject)
            for i in scenario:
                if i.reqType == "info":
                    i.TTreqType = "Information"  # set all except info to use case
                else:
                    i.TTreqType = "Use Case" 
                i.cdata = ''
                for j in i.content:
                    try:
                        i.cdata = i.cdata + j.prettify()
                    except: 
                        i.cdata = i.cdata + j
                #move tags from info section to mainflow
                if i.reqType == "mainflow":
                    i.legacyTag = scenario[0].legacyTag
                    scenario[0].legacyTag = ''
                    i.parentTag = scenario[0].parentTag
                    scenario[0].parentTag = []
                else:
                    for j in i.content: # add espec and parent tags
                        try:
                            for word in j.text.split():
                                if "REN:ESPEC" in word:
                                    i.legacyTag = word
                                if "REN:PRD" in word:
                                    i.parentTag.append(word)   
                        except:
                            for word in j.split():
                                if "REN:ESPEC" in word:
                                    i.legacyTag = word
                                if "REN:PRD" in word:
                                    i.parentTag.append(word)

            splitReqs =  scenario                                     
        #for each requirement that was split out we now
        # must generate a complete testtrack requirement      
        xmlRequirements = []
        curBlockOut=[]
        altCount = 0
        specialCount = 0
        for i in splitReqs:
            #pass counts to enumerate flows
            if i.reqType == "altflow":
                altCount += 1
            if i.reqType == "special":
                specialCount += 1
            xmlRequirements = generateXMLReq(i,''.join(curBlock),altCount,specialCount)
            for j in xmlRequirements:
                curBlockOut.append(j)
        return curBlockOut
    else:
        #if not required type,  just return the block
        return curBlock
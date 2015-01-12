#!/usr/bin/env python

import sys
import codecs
from lxml import etree
from splitFunctions import getCDATA 
from splitFunctions import reqObject
from splitFunctions import table2Lists
from splitFunctions import generateXMLReq
from bs4 import BeautifulSoup

#always print in unicode
sys.stdout = codecs.getwriter('utf-8')(sys.stdout)

inRequirement=False
inFind=False
inReplace=False

def FindReplace(curBlock):
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
                descIndex = index # grab index for when description starts
                
            if inDesc:
                descBlock.append(curLine)
                toDelete.append(index)

            if "</description" in curLine:
                inDesc=False
                        
        #remove existing description block 
        #curBlockOut = [i for j, i in enumerate(curBlock) if j not in toDelete]
        descBlock =  "".join(descBlock)
        # use LXML to extract CDATA from parse.
        CDATA = getCDATA(descBlock,"//description")[0]
        #parse with beautifulSoup
        soup = BeautifulSoup(CDATA, 'html.parser')
        #get table tag
        tableTag = soup.table
        tableTag.clear()
        tableHead = soup.table.prettify()
        #reread soup
        soup = BeautifulSoup(CDATA, 'html.parser')
        #sys.exit()
        
        #break up requirement flows into info, main flow, alt flow, and specials
        reqType = "info"
        curObject = reqObject()
        curObject.reqType = "info"        
        scenario = []
        report = False
        appendOld = False
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
                elif "SPECIAL REQUIREMENTS" in key.upper():
                    reqType = "special"
                    inBody = False
                    appendOld = True
                elif inBody and (len(row.find_all("td")) != 3 or "LAST PAGE OF REPORT" in key.upper()):
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
                    if "A" in row.find_all('td')[1].text:
                        reqType = "altflow"
                    elif "Special" in key:
                        reqType = "special"
                    else:
                        reqType = "mainflow"
                elif "Special" in key: # case for no special requirements
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
        #sys.exit()
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
        
curBlock = []
with open(sys.argv[1], 'r') as my_file:  
    reqNum = 0
    DictID = {}
    header = []
    reqsOut = []
    newNodeList = []

    #parse the rest
    for line in my_file:
       #check to see if we are in a requirement box.
        line = line.decode('utf-8')
        if "<requirement>" in line:
            inRequirement=True
            curBlock = []
            curBlock.append(line)
        elif inRequirement:
            curBlock.append(line)
        else:
            pass            
            #reqsOut.append(line)
                    
        if "</requirement>" in line:
            inRequirement=False      
            curBlockOut = FindReplace(curBlock) 
            #add serpate requiement IDs
            first = True
            for i in curBlockOut:
              #  sys.stderr.write(str(type(i)) + "\n")
                if "record-id" in i:
                    reqNum += 1
                    #store old ID and append to dict
                    oldID = (etree.fromstring(i)).text
                    DictID[oldID] = reqNum
                    reqsOut.append(("\t<record-id>" + str(reqNum) + "</record-id>\n").decode('utf-8'))
                    #generate new node link
                    if first:
                        parentID = reqNum
                        nodeOrder = 1
                        first = False
                    else:
                        #generate node from old ID to new ID
                        newNode=etree.Element("document-tree-node")
                        etree.SubElement(newNode,"node-id").text = str(reqNum)  #use reqNum for node-ID also                    
                        etree.SubElement(newNode,"parent-node-id").text = str(parentID)                         
                        etree.SubElement(newNode,"node-order").text = str(nodeOrder)                        
                        etree.SubElement(newNode,"node-requirement-id").text = str(reqNum)                         
                        newNodeList.append(newNode)
                        nodeOrder += 1
                else:
                    reqsOut.append(i)
 
#remove blank space so that pretty print works
parser = etree.XMLParser(remove_blank_text=True)
docTree = etree.parse(sys.argv[1],parser).xpath("//requirement-document")[0]
#replace IDs in old document with new IDs
#also set teh node-ID to parent ID since that's what was set in the new nodes for 
#parent-node-ID
for i in docTree.xpath("//document-tree-node"):  
    i.find("node-requirement-id").text = str(DictID[i.find("node-requirement-id").text])
    i.find("node-id").text = i.find("node-requirement-id").text

#add new nodes
for i in newNodeList:
    docTree.append(i)
    
 
#get header and testtrack opener
with open(sys.argv[1], 'r') as my_file:   
    for index,i in enumerate(my_file):
        if index < 3:
            header.append(i.decode('utf-8'))
#print header
for i in header:
    sys.stdout.write(i)
#print requirements
for i in reqsOut:
    sys.stdout.write(i)
#print docTree
print(etree.tostring(docTree,pretty_print=True)),
#print test track ojects close
print "</TestTrackData>",
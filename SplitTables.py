#!/usr/bin/env python

import sys
import codecs
from lxml import etree
from specParse import specParse

#always print in unicode
sys.stdout = codecs.getwriter('utf-8')(sys.stdout)

inRequirement=False
inFind=False
inReplace=False

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
            #spec parse turns requirements into scenario objects
            curBlockOut = specParse(curBlock) 
            #add serpate requiement IDs
            first = True #first requirement keeps it's parent node
            for i in curBlockOut:
                if "record-id" in i:
                    reqNum += 1
                    reqsOut.append(("\t<record-id>" + str(reqNum) + "</record-id>\n").decode('utf-8'))
                    #generate new node link
                    if first:
                        #store old ID and append to dict
                        oldID = (etree.fromstring(i)).text
                        DictID[oldID] = reqNum   #create dictionary of new requirements to old so that we can make the doc tree later                     
                        parentID = reqNum #remaining are assigned this parent
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
                elif "requirement-number" in i:
                    reqsOut.append(("\t<requirement-number>" + str(reqNum) + "</requirement-number>\n").decode('utf-8'))
                else:
                    reqsOut.append(i)
 
#remove blank space so that pretty print works
parser = etree.XMLParser(remove_blank_text=True)
docTree = etree.parse(sys.argv[1],parser).xpath("//requirement-document")[0]
#replace IDs in old document with new IDs
#also set teh node-ID to parent ID since that's what was set in the new nodes for 
#parent-node-ID

#first generate dictionary to translate between requirement number and record-id in the original document
# to reassign parent nodes,  we have to go from original node-ID to original requirement-ID  and then to the new node ID
node2rec = {}
for i in docTree.xpath("//document-tree-node"): 
    node2rec[i.find("node-id").text] = i.find("node-requirement-id").text

for i in docTree.xpath("//document-tree-node"):  
    i.find("node-requirement-id").text = str(DictID[i.find("node-requirement-id").text])
    if not i.find("parent-node-id").text == '0':
        i.find("parent-node-id").text = str(DictID[node2rec[i.find("parent-node-id").text]])
    #sys.stderr.write(i.find("parent-node-id").text + "\n")
    i.find("node-id").text = i.find("node-requirement-id").text
#add new nodes
for i in newNodeList:
    docTree.append(i)

#insert new nodes after their parents
for i in newNodeList:
    parentNode = i.find("parent-node-id").text
    #search string
    string = '//node-id[text()="' + str(parentNode) + '"]'

#change record ID to highest number
reqNum += 1
docTree.find("record-id").text=str(reqNum)
 
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
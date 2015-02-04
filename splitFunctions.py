# -*- coding: utf-8 -*-
"""
Created on Tue Jan 06 08:54:20 2015

@author: 10016928
"""
import sys 
import codecs
import re
from lxml import etree
#from bs4 import BeautifulSoup, CData
from bs4 import BeautifulSoup
#always print in unicode
#if sys.stdout.encoding != 'UTF-8':
#    sys.stdout = codecs.getwriter('utf-8')(sys.stdout, 'strict')
#if sys.stderr.encoding != 'UTF-8':
#    sys.stderr = codecs.getwriter('utf-8')(sys.stderr, 'strict')


def getCDATA(block,tag):
    parseOut=[]
    root = etree.fromstring(block)
    for log in root.xpath(tag):
        parseOut.append(log.text.encode('utf-8'))
    return parseOut
    
class reqObject(object):
    def __init__(self,content=[],cdata='',title='',altTitle='',titleClear=False,reqType='',category='',TTreqType='',legacyTag='',parentTag=[]):
        self.content = []
        self.cdata = ''
        self.title = ''
        self.altTitle = '' # sub title for altflows
        self.titleClear = False
        self.reqType = ''
        self.category = ''
        self.TTreqType = ''
        self.legacyTag = ''
        self.parentTag = []
        
def table2Lists(scenario,tableHead):
    objects=[]
    for i in scenario:
        tableRows=[]
        newReq = reqObject()
        #set requirement type,  opening should be info section
        if i.reqType == "info":
            newReq.TTreqType = "Information"
        else:
            newReq.TTreqType = "Use Case"
            newReq.category  = i.reqType                                 
            newReq.titleClear = True
        newReq.reqType = i.reqType
        newReq.altTitle = i.altTitle
        #set legacyTag
        #collect mainflow tag
        #save mainflow to set to alt flow if necessary
        if i.reqType == "mainflow":
            mainFlowLegacyTag = i.legacyTag
        #save info lg ID to set to report ID
        if i.reqType == "info":
            infoLegacyTag = i.legacyTag
        #set legacy tag if it exists, otherwise set to mainflow tag
        if i.reqType == "altflow" and i.legacyTag == '':
            newReq.legacyTag = mainFlowLegacyTag       
        elif i.reqType == "report" and i.legacyTag == '':
            newReq.legacyTag = infoLegacyTag
        else:
            newReq.legacyTag = i.legacyTag
        #set parent tags
        for j in i.content:
            for word in j.text.split():
                if "REN:PRD" in word:
                    newReq.parentTag.append(word)
        #set parent tag is empy, if it is,  set to mainflow tag
        if i.reqType == "mainflow":
            mainFlowParentTag = newReq.parentTag
        if i.reqType == "altflow" and newReq.parentTag == []:
            newReq.parentTag = mainFlowParentTag

        #parse opening info section and turn into text.
        #data at this point is one html row per item     
        if i.reqType == "info":
            newReq.reqType=i.reqType
            #extract info attributes
            for row in i.content:
                key = row.td.text  #grab key from first column
                content = row.find_all('td')[1]
                #sys.stderr.write((key.lower()).encode('utf-8') + '\n')   
                #sys.stderr.write((content).encode('utf-8') + '\n\n')
                #set title to name
                if "name" in key.lower():
                    newReq.title = content.text
                #add primary actor
                elif "primary" in key.lower() and "actor" in key.lower():
                    newReq.cdata += ("<p> <strong>Primary Actor: </strong>" + content.text + "</p>\n" )
                    newReq.cdata += ("<BR>\n")
                #add secondary actor
                elif "second" in key.lower() and "actor" in key.lower():
                    newReq.cdata += ("<p> <strong>Secondary Actor: </strong>" + content.text + "</p>\n" )
                    newReq.cdata += ("<BR>\n")
                elif "goal" in key.lower():
                    newReq.cdata += ("<p> <strong>Goal: </strong>" + content.text + "</p>\n" )
                    newReq.cdata += ("<BR>\n")
                elif "preconditions" in key.lower():
                    if content.ul is None:
                        newReq.cdata += ("<p> <strong>Preconditions: </strong>" + content.text + "</p>\n" )
                    else:
                        newReq.cdata += ("<p> <strong>Preconditions: </strong> </p>\n" )
                        newReq.cdata +=  content.ul.prettify()
                    newReq.cdata += ("<BR>\n")
                elif "postconditions" in key.lower():
                    if content.ul is None:
                        newReq.cdata += ("<p> <strong>Postconditions: </strong>" + content.text + "</p>\n" )
                    else:
                        newReq.cdata += ("<p> <strong>Postconditions: </strong> </p>\n" )
                        newReq.cdata +=  content.ul.prettify()
                    newReq.cdata += ("<BR>\n")
                elif "assumptions" in key.lower():
                    if content.ul is None:
                        newReq.cdata += ("<p> <strong>Assumptions: </strong>" + content.text + "</p>\n" )
                    else:
                        newReq.cdata += ("<p> <strong>Assumptions: </strong> </p>\n" )
                        newReq.cdata +=  content.ul.prettify()
                    newReq.cdata += ("<BR>\n")
                elif "trigger" in key.lower():
                    newReq.cdata += ("<p> <strong>Trigger: </strong>" + content.text + "</p>\n" )
                    newReq.cdata += ("<BR>\n")
            #exit()
        #parse tables and turn them into numbered lists
        #if use case
        elif i.reqType == "mainflow" or i.reqType == "altflow" or i.reqType == "report":
            newReq.reqType=i.reqType
            #replace each step with an HTML bullet
            # each reqtype at this point is formatted such that each 
            #row is a use case step
            
            #create new tag
            soup = BeautifulSoup("<div></div>")
            numberedList=soup.div
            listOrder=1
            beginOrderedList=False
            beginUnorderedList=False
            inSubList = False
            for row in i.content:
                if len(row.find_all("td")) == 3:  #check if this is a use case row
                    #here we have to check if this is second order flow
                    #we check the second column to see if it has a number, if it does
                    #it's first order, otherwise it's second order
                    #we also have to keep track of which order we were in so we can start
                    # and end new nested lists
                    
                    key = row.find_all("td")[1].text 
                    

                    
                    #get content, parse out nagivable strings
                    content = []
                    for j in row.find_all("td")[2].contents:                    
                        try:
                            j.text                            
                            content.append(j)
                        except:
                            continue
                    #print key
                    #for j in content:
                    #        print j.text
                    
                    #use case
                    if i.reqType == "mainflow" or i.reqType == "altflow":
                        # content in second column indicates beginning of a new first order step
                        # and start new tag if it doesn't exist
                        if len(key) > 1:
                            if not beginOrderedList:
                                mainList=soup.new_tag("ol") # start the sublist
                                numberedList.append(mainList)
                                beginOrderedList=True
                            #start new list item
                            #curItem = soup.new_tag("li")
                            #mainList.append(curItem)

                        #if no ordered list has been started, add pre-steps to an unordered list
                        if not beginOrderedList:
                            if not beginUnorderedList:
                                mainList = soup.new_tag("ul")
                                mainList['style']='padding-left: 20pt'
                                mainList['type']='none'
                                #numberedList.append(mainList)
                                beginUnorderedList=True

                        #parsing for unorderedlist
                        if not beginOrderedList:
                            #add things to unordered list
                            for j in content:
                                #newTag = soup.new_tag("li")
                                newTag = soup.new_tag("span")
                                newTag.append(j)
                                newTag['class'] = 'preList'
                                newTag['style'] = 'padding-left: 30pt'
                                #mainList.append(newTag)
                                numberedList.append(newTag)

                        #parsing for ordered List
                        else:                        
                            for j in content:
                                # if Alternate flow, then stuck indent it        
                                #start new lists if first element is a number
                                if len(j.text.split(None,1)) > 1:
                                    #this case is for if it IS a number header
                                    if not re.search(r'[^A0-9.]',j.text.split(None,1)[0]):
                                        if not inSubList:
                                            subList=soup.new_tag("ol") # start the sublist
                                            subList['type']='a'
                                        inSubList = True
                                        newTag = soup.new_tag("li")
                                        #to keep formatting parse the first string and omit the first word
                                        for k in j.strings:
                                            k.replace_with(k.split(None,1)[1])
                                            break
                                        newTag.append(j)
                                        subList.append(newTag)
                                    #if not a number header
                                    else:
                                        if inSubList:  # need to wrap up old ordered list
                                            mainList.append(subList)
                                        inSubList = False
                                        
                                        if ("ALTERNATE" in j.text.upper() and "FLOW" in j.text.upper()) or \
                                        "RULE:" in j.text.upper():  
                                            breakTag = soup.new_tag("br")                                   
                                            #replace paraphraph threads with div to stop from reordering everything
                                            mainList.append(breakTag)
                                            if j.name == "p":
                                                j.name = "span"
                                            mainList.append(j)    
                                            
                                            #replace paraphraph threads with div to stop from reordering everything
                                            
                                            
#                                            if mainList.find_all(True,recursive=False)[-1].name == "ol":
#                                                mainList.find_all(True,recursive=False)[-1].find_all(True,recursive=False)[-1].append(breakTag)
#                                                mainList.find_all(True,recursive=False)[-1].find_all(True,recursive=False)[-1].append(newTag)
#                                            else:
#                                                mainList.append(newTag)
                                            
                                        else:
                                            newTag = soup.new_tag("li")
                                            newTag.append(j)
                                            mainList.append(newTag)

                    #report
                    else:
                        if len(row.find_all("td")[1].text) > 1:  #section header                     
                            newTag = soup.new_tag("li")
                            for j in row.find_all("td")[2].contents:
                                newTag.append(j)
                                numberedList.append(newTag)
                            listOrder=1
                        else: #second order
                            if listOrder == 1: #if we just started a second oreder list
                                subList=soup.new_tag("ol") # start the sublist
                                numberedList.append(subList)
                            #now add things to the sublist
                            for j in row.find_all("td")[2].strings:
                                newTag = soup.new_tag("li")
                                # if string starts with a number, get rid of it and use the html numbering
                                #check if string
                                jSplit = j.split(None,1)                              
                                if len(jSplit) > 1 :
                                    if not re.search(r'[^0-9.]',jSplit[0]):
                                        newTag.string = jSplit[1]
                                        #append to the last sublist
                                        numberedList.find_all("ol")[-1].append(newTag)                                      
                                    else:
                                        newTag.string = j
                                        #append to the last sublist
                                        numberedList.find_all("ol")[-1].append(newTag)                               
                            listOrder=2
  
                elif i.reqType == "report":
                   # add the rest to a table
                    tableRows.append(row)                    
                else:
                    break #end parse if encounter a row that's not 3 columns 
            #add list to requirement objects   
            if i.reqType == "report":
                style = """<style>
ol li {display:block;} /* hide original list counter */
ol > li:first-child {counter-reset: item;} /* reset counter */
ol > li {counter-increment: item; position: relative;} /* increment counter */
ol > li:before {content:counters(item, ".") ". "; position: absolute; margin-right: 100%; right: 10px;} /* print counter *
</style>\n"""     
            else:
                style = """<style>
ol {
    counter-reset: item;
}
ol li {
    display: block;
    position: relative;
}
ol li:before {
    content: counters(item, ".")".";
    counter-increment: item;
    position: absolute;
    margin-right: 100%;
    right: 10px; /* space between number and text */
}

</style>\n"""                 
            newReq.cdata = style + numberedList.prettify()   
            #print("\nend")
            #exit()                             
        else:
            #keep as table using the imported header string
            table = BeautifulSoup(tableHead)
            for row in i.content:
                table.table.append(row)
            #create styles table and add it in front 
            newReq.cdata=table.table.prettify()
            
        objects.append(newReq)
       
    return objects
                        
def generateXMLReq(ReqObj,block,altCount,specialCount):  
    # we want to replace Cdata in the description with the requirement objects CDATA
    parser = etree.XMLParser(strip_cdata=False)
    root = etree.fromstring(block,parser)
    #replace with our CDATA
    root.find("description").text = etree.CDATA(ReqObj.cdata)
    #set requirement Type
    root.find("requirement-type").text = ReqObj.TTreqType                    
    #set legacy tag to title
    #root.xpath("//custom-field-value[@field-name='Target']/multi-line-text")[0].text = ReqObj.legacyTag
    #root.find("summary").text = ReqObj.legacyTag
    #set ESPEC to legacy tag 
    root.xpath("//custom-field-value[@field-name='Release']")[0].set('field-value', ReqObj.legacyTag) 
    #set parent Tag
    root.xpath("//custom-field-value[@field-name='External Traceability']/multi-line-text")[0].text = \
    "\n".join(ReqObj.parentTag)
    #set category
    root.xpath("//custom-field-value[@field-name='Category']")[0].set('field-value', ReqObj.category)    
    #clear title if not info and set to ESPEC.
    if ReqObj.reqType == "info":
        root.find("summary").text = ReqObj.title
    elif ReqObj.reqType == "mainflow":
        root.find("summary").text = "Main Flow"
    elif ReqObj.reqType == "altflow":
        root.find("summary").text = "Alternative Flow " + str(altCount) + " " + ReqObj.altTitle
        sys.stderr.write(root.find("summary").text.encode('utf-8') + "\n")
    elif ReqObj.reqType == "special":
        root.find("summary").text = "Special Requirements " + str(specialCount)
    outString = etree.tostring(root)
    # set espec tag to 

    outStringSplit=[]
    for i, line in  enumerate(outString.split('\n')):
        outStringSplit.append(line + '\n')
    return outStringSplit
     
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 06 08:54:20 2015

@author: 10016928
"""
import sys 
import re
from lxml import etree
#from bs4 import BeautifulSoup, CData
from bs4 import BeautifulSoup


def getCDATA(block,tag):
    parseOut=[]
    root = etree.fromstring(block)
    for log in root.xpath(tag):
        parseOut.append(log.text.encode('utf-8'))
    return parseOut
    
class reqObject(object):
    def __init__(self,content=[],cdata='',titleClear=False,reqType='',category='',TTreqType='',legacyTag='',parentTag=[]):
        self.content = []
        self.cdata = ''
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
        
        #parse tables and turn them into numbered lists
        #if use case
        if i.reqType == "mainflow" or i.reqType == "altflow" or i.reqType == "report":
            newReq.reqType=i.reqType
            #replace each step with an HTML bullet
            # each reqtype at this point is formatted such that each 
            #row is a use case step
            
            #create new tag
            soup = BeautifulSoup("<ol></ol>")
            numberedList=soup.ol
            listOrder=1
            for row in i.content:
                if len(row.find_all("td")) == 3:  #check if this is a use case row
                    #here we have to check if this is second order flow
                    #we check the second column to see if it has a number, if it does
                    #it's first order, otherwise it's second order
                    #we also have to keep track of which order we were in so we can start
                    # and end new nested lists

                    #use case
                    if i.reqType == "mainflow" or i.reqType == "altflow":
                        if len(row.find_all("td")[1].text) > 1:  #first order                     
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
                            newTag = soup.new_tag("li")
                            for j in row.find_all("td")[2].contents:
                                newTag.append(j)
                            #append to the last sublist
                            numberedList.find_all("ol")[-1].append(newTag)
                            listOrder=2
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
                                    if re.search(r'[0-9.]',jSplit[0]):
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
                                    
        else:
            #keep as table using the imported header string
            table = BeautifulSoup(tableHead)
            for row in i.content:
                table.table.append(row)
            #create styles table and add it in front 
            newReq.cdata=table.table.prettify()
            
        objects.append(newReq)
    return objects
                        
def generateXMLReq(ReqObj,block):  
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
    #set parent Tag
    root.xpath("//custom-field-value[@field-name='External Traceability']/multi-line-text")[0].text = \
    "\n".join(ReqObj.parentTag)
    #set category
    root.xpath("//custom-field-value[@field-name='Category']")[0].set('field-value', ReqObj.category)    
    #clear title if not info and set to ESPEC.
    if ReqObj.titleClear:
        root.find("summary").text = ReqObj.legacyTag
    
    outString = etree.tostring(root)

    outStringSplit=[]
    for i, line in  enumerate(outString.split('\n')):
        outStringSplit.append(line + '\n')
    return outStringSplit
        
     
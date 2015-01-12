# -*- coding: utf-8 -*-
"""
Created on Tue Jan 06 08:54:20 2015

@author: 10016928
"""
import sys 
from lxml import etree
#from bs4 import BeautifulSoup, CData
from bs4 import BeautifulSoup
#always print in unicode
#sys.stdout = codecs.getwriter('utf-8')(sys.stdout) 

def getCDATA(block,tag):
    parseOut=[]
    root = etree.fromstring(block)
    for log in root.xpath(tag):
        parseOut.append(log.text.encode('utf-8'))
    return parseOut
    
class reqObject(object):
    def __init__(self,content=[],cdata='',reqType='',category='',TTreqType='',legacyTag='',parentTag=[]):
        self.content = []
        self.cdata = ''
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
            newReq.TTreqType = "information"
        else:
            newReq.TTreqType = "Use Case"
            newReq.category  = i.reqType
        #set legacyTag
        newReq.legacyTag = i.legacyTag
        #set parent tags
        for j in i.content:
            for word in j.text.split():
                if "REN:PRD" in word:
                    newReq.parentTag.append(word)
        #parse tables and turn them into numbered lists
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
                elif i.reqType == "report":
                   # add the rest to a table
                    tableRows.append(row)                    
                else:
                    break #end parse if encounter a row that's not 3 columns 
            #add list to requirement objects   
            style = """<style>
    ol { counter-reset: item }
    li { display: block }
    li:before { content: counters(item, ".") " "; counter-increment: item }
</style>\n"""                      
            newReq.cdata = style + numberedList.prettify()   
            #sys.stderr.write(newReq.cdata)
            #sys.exit()
                                    
        else:
            #keep as table using the imported header string
            table = BeautifulSoup(tableHead)
            for row in i.content:
                table.table.append(row)
            #create styles table and add it in front 
            #print(table.table.prettify())
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
    #set legacy tag
    root.xpath("//custom-field-value[@field-name='Target']/multi-line-text")[0].text = ReqObj.legacyTag
    #set parent Tag
    root.xpath("//custom-field-value[@field-name='External Traceability']/multi-line-text")[0].text = \
    "\n".join(ReqObj.parentTag)
    #set category
    root.xpath("//custom-field-value[@field-name='Category']")[0].set('field-value', ReqObj.category)    
   
    outString = etree.tostring(root)

    outStringSplit=[]
    for i, line in  enumerate(outString.split('\n')):
        outStringSplit.append(line + '\n')
    return outStringSplit
        
     
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 11 09:26:23 2015

@author: Tim
Tests the output of SplitTables by putting cdata results in webpages

"""
import sys
import os
import webbrowser
from lxml import etree

with open(sys.argv[1], 'r') as my_file:
	parser = etree.XMLParser(remove_blank_text=True)
	docTree = etree.parse(sys.argv[1],parser).xpath("//TestTrackData")[0]

HTML_block = []
for i in docTree:
    if i.tag == "requirement":
        if (i.find("description"))  != None:
           # print i.find("description").text
            HTML_block.append(i.find("description").text)

new = 2

for index, i in enumerate(HTML_block):
    
    path = os.path.abspath('temp.html')
    url = 'file://' + path        
    with open(path, 'w') as f:
        f.write(i.encode('UTF-8'))        

    webbrowser.get('safari').open_new_tab(url) 
    raw_input('next?')
    #webbrowser.open_new_tab(url) 
   
    #webbrowser.open(url)

 
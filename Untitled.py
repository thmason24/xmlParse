#!/usr/bin/python

import sys
import xml.sax

class tableHandler( xml.sax.ContentHandler ):
   def __init__(self):
      self.CurrentData = ""
      self.row = ""
      self.rows = []


   # Call when an element starts
   def startElement(self, tag, attributes):
      self.CurrentData = tag
      if tag == "table":
         print "*****started table*****"
      elif tag == "td":
         print "*****started ROW*****"

   # Call when an elements ends
   def endElement(self, tag):
      if self.CurrentData == "table":
         print "Type:", self.type
      elif self.CurrentData == "tr":
         print "ROWS", self.row
      self.CurrentData = ""

   # Call when a character is read
   def characters(self, content):
      #print content
      #print self.CurrentData
      if self.CurrentData == "tr":
         print "you fool at tr!"
         self.row = content

if ( __name__ == "__main__"):
   # create an XMLReader
   parser = xml.sax.make_parser()
   # turn off namepsaces
   parser.setFeature(xml.sax.handler.feature_namespaces, 0)

   # override the default ContextHandler
   Handler = tableHandler()
   parser.setContentHandler( Handler )

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
        curBlockOut = [i for j, i in enumerate(curBlock) if j not in toDelete]
        #Remove open and end XML tags
        #for i in descBlock:       
        #    sys.stdout.write(str(i))        
        #parser.parse(str("descBlock.xml"))
        #parser.parse(str("movies.xml"))
        print "TEST"
        sys.exit()
        #Replace content

        
        # remove requirement end tag and tack it on at the end
        #curBlockOut.pop()
        #curBlockOut = curBlockOut[:CFindex] + replaceBlock + curBlockOut[CFindex:]
        #curBlockOut.append("\n</requirement>\n")

        return curBlockOut
    else:
        #if not required type,  just return the block
        return curBlock
        
curBlock = []
with open(sys.argv[1], 'r') as my_file:  
    count = 0
    for line in my_file:
 
       #check to see if we are in a requirement box
        if "<requirement>" in line:
            inRequirement=True
            curBlock = []
            curBlock.append(line)
        elif inRequirement:
            curBlock.append(line)
        else:
            print line,
                    
        if "</requirement>" in line:
            inRequirement=False
            count = count + 1 
            sys.stderr.write(str(count))
            sys.stderr.write('\n')
            # execute find replace and print         
            curBlockOut = FindReplace(curBlock)  
            #for i in curBlockOut:
            #    sys.stdout.write(i)
#            print("\n".join(CurBlock))
            #if count == 3:
                #sys.exit()
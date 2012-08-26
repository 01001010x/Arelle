'''
Created on Aug 26, 2012

@author: Mark V Systems Limited
(c) Copyright 2012 Mark V Systems Limited, All rights reserved.
'''
import os, time, io, ast

def entityEncode(arg):  # be sure it's a string, vs int, etc, and encode &, <, ".
    return str(arg).replace("&","&amp;").replace("<","&lt;").replace('"','&quot;')

if __name__ == "__main__":
    startedAt = time.time()
    
    idMsg = []
    numArelleSrcFiles = 0

    arelleSrcPath = (os.path.dirname(__file__) or os.curdir) + os.sep + "arelle"
    for arelleSrcDir in (arelleSrcPath, arelleSrcPath + os.sep + "examples" + os.sep + "plugin"):
        for moduleFilename in os.listdir(arelleSrcDir):
            if moduleFilename.endswith(".py"):
                numArelleSrcFiles += 1
                with open(arelleSrcDir + os.sep + moduleFilename) as f:
                    tree = ast.parse(f.read(), filename=moduleFilename)
                    for item in ast.walk(tree):
                        try:
                            if (isinstance(item, ast.Call) and
                                item.func.attr in ("info","warning","log","error","exception")):
                                    funcName = item.func.attr
                                    iArgOffset = 0
                                    if funcName == "info":
                                        level = "info"
                                    elif funcName == "warning":
                                        level = "warning"
                                    elif funcName == "error":
                                        level = "error"
                                    elif funcName == "exception":
                                        level = "exception"
                                    elif funcName == "log":
                                        level = item.args[0].s.lower()
                                        iArgOffset = 1
                                    errCodeArg = item.args[0 + iArgOffset]  # str or tuple
                                    if isinstance(errCodeArg,ast.Str):
                                        errCodes = (errCodeArg.s,)
                                    else:
                                        if any(isinstance(elt, ast.Call)
                                               for elt in ast.walk(errCodeArg)):
                                            errCodes = ("(dynamic)",)
                                        else:
                                            errCodes = [elt.s 
                                                        for elt in ast.walk(errCodeArg)
                                                        if isinstance(elt, ast.Str)]
                                    msgArg = item.args[1 + iArgOffset]
                                    if isinstance(msgArg, ast.Str):
                                        msg = msgArg.s
                                    elif isinstance(msgArg, ast.Call) and msgArg.func.id == '_':
                                        msg = msgArg.args[0].s
                                    elif any(isinstance(elt, ast.Call)
                                             for elt in ast.walk(msgArg)):
                                        msg = "(dynamic)"
                                    else:
                                        continue # not sure what to report
                                    keywords = [keyword.arg 
                                                for keyword in item.keywords
                                                if keyword.arg != 'modelObject']
                                    for errCode in errCodes:
                                        idMsg.append((errCode, msg, level, keywords, moduleFilename, item.lineno))                                        
                        except (AttributeError, IndexError):
                            pass
                    

    lines = []
    for id,msg,level,args,module,line in idMsg:
        try:
            lines.append("<message code=\"{0}\"\n         level=\"{3}\"\n         module=\"{4}\" line=\"{5}\"\n         args=\"{2}\">\n{1}\n</message>"
                      .format(id, 
                              entityEncode(msg),
                              entityEncode(" ".join(args)),
                              level,
                              module,
                              line))
        except Exception as ex:
            print(ex)

    os.makedirs(arelleSrcPath + os.sep + "doc", exist_ok=True)
    with io.open(arelleSrcPath + os.sep + "doc" + os.sep + "messagesCatalog.xml", 'wt', encoding='utf-8') as f:
        f.write(
'''<?xml version="1.0" encoding="utf-8"?>
<messages xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"  xsi:noNamespaceSchemaLocation="messagesCatalog.xsd" >
<!-- 

This file contains Arelle messages text.   Each message has a code 
that corresponds to the message code in the log file, level (severity), 
args (available through log file), and message replacement text.

(Messages with dynamically composed error codes or text content 
(such as ValidateXbrlDTS.py line 158 or lxml parser messages) 
are reported as "(dynamic)".)

-->

''')
        f.write("\n\n".join(sorted(lines)))
        f.write("\n\n</messages>")
        
    with io.open(arelleSrcPath + os.sep + "doc" + os.sep + "messagesCatalog.xsd", 'wt', encoding='utf-8') as f:
        f.write(
'''<?xml version="1.0" encoding="UTF-8"?>
<schema xmlns="http://www.w3.org/2001/XMLSchema" elementFormDefault="unqualified"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <element name="messages">
    <complexType>
      <sequence>
        <element maxOccurs="unbounded" ref="message"/>
      </sequence>
    </complexType>
  </element>
  <element name="message">
    <complexType>
        <complexContent>
          <restriction base="string">
              <attribute name="code" use="required" type="normalizedString"/>
              <attribute name="level" use="required" type="token"/>
              <attribute name="module" type="normalizedString"/>
              <attribute name="line" type="integer"/>
              <attribute name="args" type="NMTOKENS"/>
          </restriction>
        </complexContent>
    </complexType>
  </element>
</schema>
''')
    
    print("Arelle messages catalog {0:.2f} secs, {1} formula files, {2} messages".format( time.time() - startedAt, numArelleSrcFiles, len(idMsg) ))
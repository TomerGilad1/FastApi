from fastapi import Request,FastAPI,Response,Query
import logging
import datetime
import os
from typing import Union
arguments_stack = []
app = FastAPI()
twoArgsOperations = {'plus','minus','times','divide','pow'}
oneArgsOperations = {'abs','fact'}
if not os.path.exists('logs'):
 os.mkdir('logs')
#stack logger
stack_logger = logging.getLogger('stack-logger')
stack_logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s.%(msecs)03d %(levelname)s: %(message)s', datefmt='%d-%m-%Y %H:%M:%S')
stackHandler= logging.FileHandler('logs/stack.log','w+')
stackHandler.mode='w'
stackHandler.setLevel(logging.INFO)
stackHandler.setFormatter(formatter)
stack_logger.addHandler(stackHandler)

#independent logger
independent_logger = logging.getLogger('independent-logger')
independent_logger.setLevel(logging.DEBUG)
independentHandler = logging.FileHandler('logs/independent.log','w+')
independentHandler.mode='w'
independentHandler.setLevel(logging.DEBUG)
independentHandler.setFormatter(formatter)
independent_logger.addHandler(independentHandler)

#request logger
request_logger = logging.getLogger('request-logger')
request_logger.setLevel(logging.INFO)
requestHandler = logging.FileHandler('logs/requests.log','w+')
requestHandler.mode='w'
requestHandler.setLevel(logging.INFO)
requestHandler.setFormatter(formatter)
request_logger.addHandler(requestHandler)

operationResult = 0
global request_num
request_num=0
def requestInfoMsg(resource,verb):
    global request_num
    request_num+=1
    return f'Incoming request | #{request_num} | resource: {resource} | HTTP Verb {verb} | request #{request_num}'
def requestDebugMsg(duration):
    return f'request #{request_num} duration: {int(duration)}ms | request #{request_num}'

def timeInterval(start):
   time=datetime.datetime.now()-start
   return time.total_seconds()*1000

@app.post("/independent/calculate")
async def independentCalculate(request:Request,response: Response):
    request_logger.info(requestInfoMsg('/independent/calculate','POST')) 
    start=datetime.datetime.now()
    body = await request.json()
    if (len(body)==0 | ( not 'operation' in body) | (not 'arguments' in body)):
        result=res("",response,"",409)
        independent_logger.error(msgWithRequestNum(ErrorLoggerMsg('')))
        request_logger.debug(requestDebugMsg(timeInterval(start))) #request debug TIME
        return result
    arguments = body["arguments"]
    operation = body["operation"]
    if not isTwoArgOperation(operation.lower()) and not isOneArgOperation(operation.lower()):
       errorMsg=(f"Error: unknown operation: {operation}")
       result=res("",response,errorMsg,409)
       independent_logger.error(msgWithRequestNum(ErrorLoggerMsg(errorMsg)))
       request_logger.debug(requestDebugMsg(timeInterval(start))) #request debug TIME
       return result

    if isTwoArgOperation(operation.lower()):
        if len(arguments)==2:
          result=twoArgOperation(arguments[0],arguments[1],operation,response)
          #
          if response.status_code != 200:
            independent_logger.error(msgWithRequestNum(ErrorLoggerMsg(operationResult)))
          else:
            independent_logger.info(msgWithRequestNum(f"Performing operation {operation}. Result is {operationResult}"))
            independent_logger.debug(msgWithRequestNum(f"Performing operation: {operation}({arguments[0]},{arguments[1]}) = {operationResult}"))
            request_logger.debug(requestDebugMsg(timeInterval(start))) #request debug TIME
          return result
        elif len(arguments)>2:
            errorMsg=(f"Error: Too many arguments to perform the operation {operation}")
            result=res("",response,errorMsg,409)
            independent_logger.error(msgWithRequestNum(ErrorLoggerMsg(errorMsg)))
            request_logger.debug(requestDebugMsg(timeInterval(start))) #request debug TIME
            return result
        elif len(arguments)<2:
            errorMsg=(f"Error: Not enough arguments to perform the operation {operation}")
            result=res("",response,errorMsg,409)
            independent_logger.error(msgWithRequestNum(ErrorLoggerMsg(errorMsg)))
            request_logger.debug(requestDebugMsg(timeInterval(start))) #request debug TIME
            return result
    elif isOneArgOperation(operation.lower()):
        if len(arguments)==1:
            result= oneArgOperation(arguments[0],operation,response)
            if response.status_code==200:
             independent_logger.info(msgWithRequestNum(f"Performing operation {operation}. Result is {operationResult}"))
             independent_logger.debug(msgWithRequestNum(f"Performing operation: {operation}({arguments[0]}) = {operationResult}"))
            else:
              independent_logger.error(msgWithRequestNum(ErrorLoggerMsg(operationResult)))
            request_logger.debug(requestDebugMsg(timeInterval(start))) #request debug TIME
            return result
        elif len(arguments)>1:
            errorMsg=(f"Error: Too many arguments to perform the operation {operation}")
            result=res("",response,errorMsg,409)
            independent_logger.error(msgWithRequestNum(ErrorLoggerMsg(errorMsg)))
            request_logger.debug(requestDebugMsg(timeInterval(start))) #request debug TIME
            return result
        elif len(arguments)<1:
            errorMsg(f"Error: Not enough arguments to perform the operation {operation}")
            result=res("",response,errorMsg,409)
            independent_logger.error(msgWithRequestNum(ErrorLoggerMsg(errorMsg)))
            request_logger.debug(requestDebugMsg(timeInterval(start))) #request debug TIME
            return result

@app.get("/stack/size")
async def getStackSize(request:Request,response: Response):
    request_logger.info(requestInfoMsg('/stack/size','GET'))
    start=datetime.datetime.now()
    stack_logger.info(msgWithRequestNum(f"Stack size is {len(arguments_stack)}"))
    result=res(len(arguments_stack),response)
    stackVariables=[]
    i=0
    msg= "Stack content (first == top): ["
    while len(arguments_stack)!= 0:
      curNum=arguments_stack.pop()
      stackVariables.append(curNum)
      if i==0:
        i+=1
        msg+=str(curNum)
      else:
       msg+=(f",{curNum}")
    msg+="]"
    while len(stackVariables)!= 0:
      arguments_stack.append(stackVariables.pop())
    stack_logger.debug(msgWithRequestNum(msg))
    request_logger.debug(requestDebugMsg(timeInterval(start))) #request debug TIME
    return result


@app.put("/stack/arguments") #3
async def pushToStack(response: Response,request:Request):
    request_logger.info(requestInfoMsg('/stack/arguments','PUT'))
    global operationResult
    start=datetime.datetime.now()
    body = await request.json()
    if (len(body)!=1 |(not 'arguments' in body)):
        result=res("",response,"",409)
        stack_logger.error(msgWithRequestNum(ErrorLoggerMsg('')))
        request_logger.debug(requestDebugMsg(timeInterval(start))) #request debug TIME
        return result
    arguments = body["arguments"]
    if(not validNumList(arguments)):
        result=res("",response,"",409)
        stack_logger.error(msgWithRequestNum(ErrorLoggerMsg('')))
        request_logger.debug(requestDebugMsg(timeInterval(start))) #request debug TIME
        return result
    stackSizeBefore=len(arguments_stack)
    stack_logger.info(msgWithRequestNum(f'Adding total of {len(arguments)} argument(s) to the stack | Stack size: {len(arguments)+len(arguments_stack)}'))
    msg="Adding arguments: "
    for num in range(len(arguments)):
      if num==0:
       msg+=f"{arguments[num]}"
      else:
        msg+=f",{arguments[num]}"
      arguments_stack.append(arguments[num])
    msg+=f" | Stack size before {stackSizeBefore} | stack size after {len(arguments_stack)}" 

    result=res("",response)
    stack_logger.debug(msgWithRequestNum(msg))
    request_logger.debug(requestDebugMsg(timeInterval(start))) #request debug TIME
    return result

def validNumList(arguments):
     return all(isinstance(x, int) for x in arguments)

@app.get("/stack/operate") #4
async def performOperation(operation,response: Response):
    request_logger.info(requestInfoMsg('/stack/operate','GET'))
    global operationResult
    start=datetime.datetime.now()
    if operation==None:
        result=res("",response,"",409)
        stack_logger.error(msgWithRequestNum(ErrorLoggerMsg(res)))
        request_logger.debug(requestDebugMsg(timeInterval(start))) #request debug TIME
        return result
    if len(operation)!=0:
      i_operation = operation.lower()
      if not isTwoArgOperation(operation) and not isOneArgOperation(operation):
        result=res("",response,(f"Error: unknown operation: {operation}"),409)
        stack_logger.error(msgWithRequestNum(ErrorLoggerMsg('')))                                           # error logger!
        request_logger.debug(requestDebugMsg(timeInterval(start))) #request debug TIME
        return result
      if isTwoArgOperation(i_operation):
           if len(arguments_stack)>=2:
              arg1=arguments_stack.pop()
              arg2=arguments_stack.pop()
              result=twoArgOperation(arg1,arg2,i_operation,response)
              if response.status_code!= 200:
                stack_logger.error(msgWithRequestNum(ErrorLoggerMsg(operationResult)))
              else:
                stack_logger.info(msgWithRequestNum(f"Performing operation {i_operation}. Result is {operationResult} | stack size: {len(arguments_stack)}"))
                stack_logger.debug(msgWithRequestNum(f"Performing operation: {i_operation}({arg1},{arg2}) = {operationResult}"))
              request_logger.debug(requestDebugMsg(timeInterval(start))) #request debug TIME
              return result
           else:
            errorMsg=f"Error: cannot implement operation {operation}. It requires {2} arguments and the stack has only {len(arguments_stack)} arguments"
            result=res("",response,errorMsg,409)
            stack_logger.error(msgWithRequestNum(ErrorLoggerMsg(errorMsg)))   # error logger!
            request_logger.debug(requestDebugMsg(timeInterval(start))) #request debug TIME
            return result 
      elif isOneArgOperation(i_operation):
           if len(arguments_stack)>=1:
              argument=arguments_stack.pop()
              result=oneArgOperation(argument,operation,response,True)
              stack_logger.info(msgWithRequestNum(f"Performing operation {i_operation}. Result is {operationResult} | stack size: {len(arguments_stack)}"))
              stack_logger.debug(msgWithRequestNum(f"Performing operation: {i_operation}({argument}) = {operationResult}"))
              request_logger.debug(requestDebugMsg(timeInterval(start))) #request debug TIME
              return result
           else:
            errorMsg=f"Error: cannot implement operation {operation}. It requires {1} arguments and the stack has only {len(arguments_stack)} arguments"
            result=res("",response,errorMsg,409)
            stack_logger.error(msgWithRequestNum(ErrorLoggerMsg(errorMsg)))   # error logger!
            request_logger.debug(requestDebugMsg(timeInterval(start))) #request debug TIME
            return result
    errorMsg=(f"Error: unknown operation: {operation}")
    result=res("",errorMsg,409)
    stack_logger.error(msgWithRequestNum(ErrorLoggerMsg(errorMsg)))   # error logger!
    request_logger.debug(requestDebugMsg(timeInterval(start))) #request debug TIME
    return result

@app.delete("/stack/arguments") #5
async def deleteStack(count,response: Response):
    request_logger.info(requestInfoMsg('/stack/arguments','DELETE'))
    start=datetime.datetime.now()
    if (count==None):
        result=res("",response,"",409)
        stack_logger.error(msgWithRequestNum(ErrorLoggerMsg('')))
        request_logger.debug(requestDebugMsg(timeInterval(start))) #request debug TIME
        return result
    popCount =  int(count)

    stackCount=len(arguments_stack)
    if popCount > stackCount:
        errorMsg=(f"Error: cannot remove {count} from the stack. It has only {stackCount} arguments")
        result=res("",response,errorMsg,409)
        stack_logger.error(msgWithRequestNum(ErrorLoggerMsg(errorMsg)))
        request_logger.debug(requestDebugMsg(timeInterval(start))) #request debug TIME
        return result
    stack_logger.info(msgWithRequestNum(f"Removing total {popCount} argument(s) from the stack | Stack size: {len(arguments_stack)-popCount}"))
    for x in range(popCount):
        arguments_stack.pop()
    request_logger.debug(requestDebugMsg(timeInterval(start))) #request debug TIME
    return res(len(arguments_stack),response)
      
def twoArgOperation(argument_x, argument_y, operation,response):
    global operationResult
    i_operation = operation.lower()
    if i_operation == "plus":
        operationResult=to_integer_if_whole(argument_x + argument_y)
        return res(argument_x + argument_y,response)
    elif i_operation == "minus":
        operationResult=to_integer_if_whole(argument_x - argument_y)
        return res(argument_x - argument_y,response)
    elif i_operation == "times":
         operationResult=to_integer_if_whole(argument_x * argument_y)
         return res(argument_x * argument_y,response)
    elif i_operation == "divide":
        if(argument_y==0):
            operationResult="Error while performing operation Divide: division by 0"
            return res("",response,operationResult,409)
        else:
         operationResult=to_integer_if_whole(argument_x / argument_y)
         return res(argument_x / argument_y,response)
    elif i_operation == "pow":
        operationResult=to_integer_if_whole(argument_x * argument_y)
        return res(operationResult,response)


def  isTwoArgOperation(operation):
  if operation in twoArgsOperations:
     return True
  return False

def isOneArgOperation(operation):
  if operation in oneArgsOperations:
    return True
  return False 

def oneArgOperation(argument_x, operation,response,isStack=False):
    i_operation=operation.lower()
    global operationResult
    if i_operation == "abs":
        result = argument_x
        if argument_x<0:
           result*=-1
        operationResult=to_integer_if_whole(result)
        return res(result,response)
    elif i_operation == "fact":
        result=argument_x
        if argument_x>=0:
            for i in range (1,argument_x):
                result*=i
            operationResult=to_integer_if_whole(result)
            return res(result,response)
        elif argument_x<0:
            for i in range (1,-argument_x):
                result*=-i
            operationResult=to_integer_if_whole(result)
            return res(result,response)
        else:
          if(isStack):
            arguments_stack.append(argument_x)
          operationResult="Error while performing operation Factorial: not supported for the negative number"
          return res("",response,operationResult,409)

@app.get("/logs/level")
async def getLoggerLevel(logger_name: str =Query(None, alias="logger-name")):
 start=datetime.datetime.now()
 request_logger.info(requestInfoMsg('/logs/level','GET'))
 if logger_name=="request-logger":
    request_logger.debug(requestDebugMsg(timeInterval(start))) #request debug TIME
    return "INFO"
 elif logger_name=="stack-logger":
    request_logger.debug(requestDebugMsg(timeInterval(start))) #request debug TIME
    return "INFO"
 elif logger_name=="independent-logger":
    request_logger.debug(requestDebugMsg(timeInterval(start))) #request debug TIME
    return "DEBUG"
 else:
    request_logger.debug(requestDebugMsg(timeInterval(start))) #request debug TIME
    return "no logger found with that name"


@app.put("/logs/level")
async def setLoggerLevel(logger_name: str =Query(None, alias="logger-name") ,logger_level: str = Query(None, alias="logger-level")):
 request_logger.info(requestInfoMsg('/logs/level','PUT'))
 
 start=datetime.datetime.now()
 if logger_level =="ERROR":
   level=logging.ERROR
 elif logger_level =="INFO" :
   level=logging.INFO
 elif  logger_level =="DEBUG":
   level=logging.DEBUG  
 else:
    request_logger.debug(requestDebugMsg(timeInterval(start))) #request debug TIME
    return "The level sent isn't one of these : ERROR, INFO, DEBUG"
 if logger_name=="request-logger":
    request_logger.setLevel(level)
    requestHandler.setLevel(level)
    request_logger.debug(requestDebugMsg(timeInterval(start))) #request debug TIME
    return loggerLevel(level)
 elif logger_name=="stack-logger":
    stack_logger.setLevel(level)
    stackHandler.setLevel(level)
    request_logger.debug(requestDebugMsg(timeInterval(start))) #request debug TIME
    return loggerLevel(level)
 elif logger_name=="independent-logger":
    independent_logger.setLevel(level)
    independentHandler.setLevel(level)
    request_logger.debug(requestDebugMsg(timeInterval(start))) #request debug TIME
    return loggerLevel(level)
 else:
    request_logger.debug(requestDebugMsg(timeInterval(start))) #request debug TIME
    return "no logger found the sent name"


def loggerLevel(level):
  if level==10:
    return "DEBUG"
  elif level==20:
    return "INFO"
  elif level==40:
    return "ERROR"
  else:
    return 0

def to_integer_if_whole(num: float) -> Union[float, int]:
    if num == round(num):
        return int(num)
    return num

def ErrorLoggerMsg(msg):
  return f"Server encountered an error ! message: {msg}"

def msgWithRequestNum(msg):
  global request_num
  return msg+(f' | request #{request_num}')

def res(res,response,errorMsg="",responseCode=200):
 resp = dict()
 resp["result"]=res
 resp["error-message"]=errorMsg
 response.status_code=responseCode
 return str(resp)



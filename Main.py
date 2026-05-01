#Sari Abdalghani - 1220982
#Khaled Abu Lebdeh - 1220187

import threading
from time import *
import copy
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

#global vairables
graph = {}
lock_readyQueue = threading.Lock()
lock_waitingQueue = threading.Lock()
lock_priorityLists = threading.Lock()
lock_count= threading.Lock()
lock_IOQueue= threading.Lock()
TarminatingProcess=[]
TIME=0
QUANTUM=5
S=QUANTUM
MyProcess=-1
COUNT=0 # when counter equals QUANTUM -> context switch

RESOURCES={
    #False: resource is not assigned (allocated)
    "[1]": False,
    "[2]": False,
    "[3]": False,
    "[4]": False,
    "[5]": False,
    "[6]": False,
    "[7]": False,
    "[8]": False,
    "[9]": False,
    "[10]": False
}

def addProcess (processInfo:str, processesList:list,copy_processesList:list): 
    #line format: PID, Arrival Time, Priority - [Sequence of CPU and IO bursts]

    parts= processInfo.split("|")
    numbers= parts[0].strip().split(" ") #parts[0]: PID, Arrival Time, Priority
    sequence= parts[1].strip().split("-") #parts[1]: the sequence
    sequence= [s.strip() for s in sequence]

    process = {# Create a dictionary for the process
          "PID": int (numbers[0]) ,
          "arrival time": int (numbers[1]),
          "priority": int (numbers[2]) , 
          "sequence": sequence ,
          "start time":0,
           "end time":0,
          "execution time":0,
          "start blocking":0,#time when blocked to witing queue until resource is available
          "end blocking":0,#time when blocked to witing queue until resource is available
          "blocking time":0,
          "IO time":0,
          "started":False,
          "finished":False
        }
    T_process = {}
    
    T_process = copy.deepcopy(process)
    processesList.append(process)
    copy_processesList.append(T_process)


def loadFile (processesList:list,copy_processesList:list)->None: #read file, add each line separately to the list
    f=open ("input.txt", "r")
    for line in f:
        addProcess(line,processesList,copy_processesList)

def findInProcessesList (PID:int, processesList:list)->dict:
    for process in processesList:
        if process["PID"]==PID:
            return process

def isResourceAllocated (resourceName:str)->bool:
    global RESOURCES
    return RESOURCES[resourceName]

def timer ()-> None:
    global TIME
    while True:
        sleep(1)
        TIME+=1

def manageQuantums (priorityLists:list, readyQueue:list) -> None:
    global COUNT
    global QUANTUM
    global lock_count

    while True:
        with lock_count:
            if COUNT==QUANTUM:#preemption
                priorityLists[0].append(priorityLists[0].pop(0))#preempte process to the end of queue
                COUNT=0
            else:
                COUNT+=1

def findPriorityLists (readyQueue:list)->list:
    priorityLists=[]
    i=0 #don't use for i in range,, i can't be modified directly
    numOfReadyProcesses=len(readyQueue)
    while i < numOfReadyProcesses:
        counter=0
        tempList =[]
        for j in range (i, numOfReadyProcesses):
            if readyQueue[j]["priority"]==readyQueue[i]["priority"]:
                counter+=1
                tempList.append(readyQueue[j])
        i+= counter
        priorityLists.append(tempList)
    return priorityLists
def isInPriorityLists(process:dict, priorityLists:list)->bool:
    for LIST in priorityLists:
        for PROCESS in LIST:
            if process["PID"]==PROCESS["PID"]:
                return True
    return False
def updatePriorityLists (priorityLists:list, readyQueue:list)->None:
    
    copy_prioritLists= priorityLists.copy()
    for LIST in priorityLists:
        for process in LIST:
            if process not in readyQueue:
                index1=copy_prioritLists.index(LIST)
                copy_prioritLists[index1].remove(process)
    with lock_priorityLists:
        priorityLists.clear()
        priorityLists.extend(copy_prioritLists)
    

    for process in readyQueue:
        if isInPriorityLists(process,priorityLists):
            continue
        for LIST in priorityLists:
            if LIST[0]["priority"]==process["priority"]:
                with lock_priorityLists:
                    LIST.append(process)
            elif LIST[0]["priority"]>process["priority"]:
                #no other processes with this priority, and it is not the least priority
                    newList=[]
                    newList.append(process)
                    with lock_priorityLists:
                        priorityLists.insert(priorityLists.index(LIST), newList)  
        else:#no other processes with this priority
            newList=[]
            newList.append(process)
            with lock_priorityLists:
                priorityLists.append(newList)
    
def addToReadyQueue (readyQueue:list,priorityLists:list, processesList:list)->None:
    global TIME

    for process in processesList:
        while process["arrival time"] > TIME: #wait until we reach the appropriate time to add process to ready queue
            pass
        with lock_readyQueue:
            readyQueue.append(process)
            readyQueue.sort(key=lambda x: x['priority']) 

        new_priority_lists = findPriorityLists(readyQueue)
        with lock_priorityLists:
            priorityLists.clear()
            priorityLists.extend(new_priority_lists)#to ensure editing values in the refernce passed, not new refernce
            print(process["PID"], " JOINED")
def deleteFromMainQueue (processToDelete:dict, readyQueue:list)->None:
    copy_readyQueue= readyQueue.copy()
    for process in readyQueue:
        if process["PID"]==processToDelete["PID"]:
            copy_readyQueue.remove(processToDelete)
            break
    with lock_readyQueue:
        readyQueue.clear()
        readyQueue.extend(copy_readyQueue)

def addToWaitingQueue (process:dict,waitsFor:str,waitingQueue:list)->None:
    waitingProcess={
        "process":process,
        "waitsFor": waitsFor
    }
    with lock_waitingQueue:
        waitingQueue.append(waitingProcess)

def wakeUpBlockedProcesses (waitingQueue:list, readyQueue:list, priorityLists:list)->None:#waits for resource
    global TIME
    copy_waitingQueue= waitingQueue.copy()
    for waitingProcess in waitingQueue:
        if not isResourceAllocated(waitingProcess["waitsFor"]):
            print("\nwaked up ",waitingProcess["process"]["PID"]  )

            waitingProcess["process"]["end blocking"]=TIME
            waitingProcess["process"]["blocking time"]+= (int(waitingProcess["process"]["end blocking"])-int(waitingProcess["process"]["start blocking"]))
            with lock_readyQueue:
                readyQueue.append(waitingProcess["process"])
                readyQueue.sort(key=lambda x: x['priority']) 
            for LIST in priorityLists:
                if LIST[0]["priority"]==waitingProcess["process"]["priority"]:
                    with lock_priorityLists:
                        LIST.append(waitingProcess["process"])
                    break
                elif LIST[0]["priority"]>waitingProcess["process"]["priority"]:
                    #no other processes with this priority, and it is not the least priority
                    newList=[]
                    newList.append(waitingProcess["process"])
                    with lock_priorityLists:
                        priorityLists.insert(priorityLists.index(LIST), newList)  
                    break
            else:#no other processes with this priority
                newList=[]
                newList.append(waitingProcess["process"])
                with lock_priorityLists:
                    priorityLists.append(newList)
            copy_waitingQueue.remove(waitingProcess)
    waitingQueue.clear()
    waitingQueue.extend(copy_waitingQueue)

def addToIOQueue (process:dict,IOPeriod:str,IOStartTime:str,IOQueue:list)->None:
    IOProcess={
        "process":process,
        "IOPeriod": str(IOPeriod),
        "IOStartTime": str(IOStartTime)
    }
    with lock_IOQueue:
        IOQueue.append(IOProcess)

def returnIOProcesses (IOQueue:list, readyQueue:list, priorityLists:list)->None:#push processes that finished IO
    global TIME
    copy_IOQueue=IOQueue.copy()
    for IOProcess in IOQueue:
        if int (IOProcess["IOStartTime"].strip())+ int(IOProcess["IOPeriod"].strip()) <= TIME:
            
            #if process has other bursts to exexute #imposssible, process always starts/ends with CPU
            if len(IOProcess["process"]["sequence"])<1:
                        process=findInProcessesList(IOProcess["process"]["PID"],processesList)
                        process["finished"]=True
                        process["IO time"]+= int(IOProcess["IOPeriod"].strip())
            else:
                with lock_IOQueue:
                    IOProcess["process"]["IO time"]+=int(IOProcess["IOPeriod"])
                with lock_readyQueue:
                    readyQueue.append(IOProcess["process"])
                    readyQueue.sort(key=lambda x: x['priority']) 
                for LIST in priorityLists:#add to the end of its priority list
                    if LIST[0]["priority"]==IOProcess["process"]["priority"]:
                        with lock_priorityLists:
                            LIST.append(IOProcess["process"])
                        break                         
                    elif LIST[0]["priority"]>IOProcess["process"]["priority"]:
                    #no other processes with this priority, and it is not the least priority
                        newList=[]
                        newList.append(IOProcess["process"])
                        with lock_priorityLists:
                            priorityLists.insert(priorityLists.index(LIST), newList)  
                        break
                else:
                    #no other processes with this priority, and it is the least priority
                    newList=[]
                    newList.append(IOProcess["process"])
                    with lock_priorityLists:
                        priorityLists.append(newList)
            copy_IOQueue.remove(IOProcess)

            print("finished IO ",IOProcess["process"]["PID"] )
    with lock_IOQueue:
        IOQueue.clear()
        IOQueue.extend(copy_IOQueue)

def constructEditedBurst (edited_burstOperations:list,type:str)->str:
    if len(edited_burstOperations)<1:
        return ""
    
    result=f"{type}"
    result+="{"
    for operation in edited_burstOperations:
        result+=(f"{operation}"+ ", ")
    
    result= result[:-2].strip()+"}"
    return result
 
def addToGanttChart (PID:int, startTime:int, endTime:int, GanttChart:list)->None:
    processInGantt={
        "PID":PID,
        "start time":startTime,
        "end time":endTime
    }
    GanttChart.append(processInGantt)
def drawGanttChart(GanttChart):
    fig, ax = plt.subplots(figsize=(10, 5))

    colors = {}  
    color_map = plt.cm.get_cmap("tab20")

    for entry in GanttChart:
        pid = entry["PID"]
        start_time = entry["start time"]
        end_time = entry["end time"]

        # Assign a color to each PID
        if pid not in colors:
            colors[pid] = color_map(len(colors) / 20)

        # Draw a bar for the process on the same y-coordinate
        ax.barh(
            "Processes",  # Single y-label for all processes
            width=end_time - start_time,
            left=start_time,
            height=0.1,
            color=colors[pid],
            edgecolor="black",
        )

    # Add gridlines for clarity
    ax.grid(axis="x", linestyle="--", alpha=0.7)

    # Set axis labels and title
    ax.set_xlabel("Time")
    ax.set_ylabel("Processes")
    ax.set_title("Gantt Chart")

    # Add a legend for the PIDs
    legend_patches = [
        mpatches.Patch(color=color, label=f"PID {pid}")
        for pid, color in colors.items()
    ]
    ax.legend(handles=legend_patches, bbox_to_anchor=(1.05, 1), loc="upper left")

    # Adjust layout
    plt.tight_layout()
    plt.show()
#Deadlock functions
    
def add_vertex(vertex:str): # add vertex to the main graph
    if vertex not in graph:
        graph[vertex]=[]

def add_edge(vertex1:str, vertex2:str): # add edge to the main graph
    if vertex1 in graph :#removed "and vertex2 in graph"
        graph[vertex1].append(vertex2)
 
def remove_edge(vertex1:str, vertex2:str): # remove edge from the main graph
    if vertex1 in graph :
        if vertex2 in graph[vertex1]:  # removed "and vertex2 in graph[vertex1]"
            graph[vertex1].remove(vertex2)
def return_resources (process:dict, readyQueue:list)->None:
    numOfBursts=len(process["sequence"])
    i=0
    while i<numOfBursts:#has bursts

        currentBurst=process["sequence"][i]
        if str(currentBurst).startswith("CPU"):
            burstOperations= str(currentBurst)[4:-1].strip().split(",")
            burstOperations= [s.strip() for s in burstOperations]
            for operation in burstOperations:
                if str(operation).startswith("F"):
                    resourceName=operation[1:].strip()
                    RESOURCES[resourceName]=False #free resouce 
                    remove_edge(str(resourceName), str(process["PID"]))
                    #error occurred

        #if IO, no resources to return back
        i+=1

    
def dfs(R_or_P:str,color:dict, parent:dict): #check if the graph has a cycle or not
    color[R_or_P] = 'G'
    for v in graph[R_or_P]:
        if color[v] == 'w':
            check = dfs(v,color,parent)
            if check == True:
                return True
        elif color[v] == 'G': #check if the graph has a cycle
            return True #if the graph has a cycle return True
    
    color[R_or_P] = 'B'
    return False #if the graph hasn't cycle return False

def deadlockDetector ()->bool:
    color = {}
    parent= {}
    for R_or_P in graph.keys(): #initialize the graph colors for each vertex to be white
        color[R_or_P] = 'w'
    for R_or_P in graph.keys():
        if color[R_or_P] == 'w':
            
            temp =dfs(R_or_P, color, parent)
            if temp:
                return True
    return False

processesList = [] #holds all processes
copy_processesList=[]
loadFile (processesList,copy_processesList)
numOfProcesses= len (processesList) # number of processes in the system

processesList.sort(key=lambda x: x['arrival time']) #to determine when the process should enter Ready Queue

readyQueue=[]
priorityLists=[] #all processes with priority x are in one list, all lists of different priorities are in priorityLists (sorted by priority)

timeThread = threading.Thread(target=timer)#separate thread increases the time spent
queueThread = threading.Thread(target=addToReadyQueue, args=(readyQueue,priorityLists,processesList))

#Deadlock initializaton



# Start the thread
timeThread.start()
queueThread.start()

#if a list has many processes -> Round Robin

waitingQueue=[]
IOQueue=[]
GanttChart=[]

J=0
#Starting Processes' Execution
sleep(0.001)
while J<numOfProcesses:
    if len(priorityLists)>0:#there are processes to execute
        #always execute priorityLists[0], since it has the highest priority
        myList=priorityLists[0]
        print("A list with priority = ",priorityLists[0][0]["priority"] )
        while True:
            try:
                process=priorityLists[0][0]
                print("\nPROCESS PID= ", process["PID"])
            except:
                break #####update lists

            if process["finished"]==False:

                #set start time
                if process["started"]==False:
                    process["started"]=True
                    process["start time"]=TIME

                currentBurst=process["sequence"][0]
                print("burst: ",currentBurst)
                 #Case 1: IO burst
                if str(currentBurst).startswith("IO"):
                    IOPeriod=str(currentBurst)[3:-1].strip()
                    del process["sequence"][0]
                    addToIOQueue(process,IOPeriod,process["end time"],IOQueue)
                    deleteFromMainQueue(process,readyQueue)#uses mutex lock
                    updatePriorityLists(priorityLists,readyQueue)

                    with lock_priorityLists:
                        priorityLists=findPriorityLists(readyQueue)#update lists
                #Case 2: CPU burst
                elif str(currentBurst).startswith("CPU"):
                    burstOperations= str(currentBurst)[4:-1].strip().split(",")
                    burstOperations= [s.strip() for s in burstOperations]
                    #opeartion is either request or free or execute

                    edited_burstOperations=burstOperations.copy()#to delete executed opeartions, and keep others
                    for operation in burstOperations:

                        #Case 1-A: Request
                        if str(operation).startswith("R"):
                            resourceName=operation[1:].strip()
                            if  isResourceAllocated(resourceName):#resource is allocated by another process
                                process["start blocking"]=TIME

                                add_vertex(str(process["PID"]))
                                add_edge(str(process["PID"]),str(resourceName))#request edge
                                if deadlockDetector():
                                    deleteFromMainQueue(process,readyQueue)
                                    print("DEADLOCK was detected!!")
                                    print(f"Process[{process["PID"]}] has beem terminated, at time : ",TIME)
                                    return_resources(process,readyQueue)
                                    wakeUpBlockedProcesses(waitingQueue,readyQueue,priorityLists)
                                    for T_process in copy_processesList:
                                        if T_process["PID"]==process["PID"]:
                                            break
                                    process["sequence"]= T_process["sequence"]
                                    readyQueue.append(process)
                                    with lock_priorityLists:
                                        priorityLists=findPriorityLists(readyQueue)
                                    J+=1
                                    break
                                else:#no deadlock


                                    addToWaitingQueue(process,resourceName, waitingQueue)#uses mutex lock
                                    deleteFromMainQueue(process,readyQueue)#uses mutex lock
                                    #updatePriorityLists(priorityLists,readyQueue)
                                    with lock_priorityLists:
                                        priorityLists=findPriorityLists(readyQueue)#update lists
                                    break

                            else:#resource is available -> allocate
                                RESOURCES[resourceName]=True #allocate resouce
                                remove_edge(str(process["PID"]),resourceName)
                                add_vertex(str(resourceName))
                                add_vertex(str(process["PID"]))

                                add_edge(str(resourceName),str(process["PID"]))#assignment edge
                                if deadlockDetector():
                                    deleteFromMainQueue(process,readyQueue)

                                    print(f"Process[{process["PID"]}] has beem terminated, at time : ",TIME)
                                    #free resources,, and delete edges
                                    return_resources(process,readyQueue)
                                    wakeUpBlockedProcesses(waitingQueue,readyQueue,priorityLists)
                                    for T_process in copy_processesList:
                                        if T_process["PID"]==process["PID"]:
                                            break
                                    readyQueue.append(process)
                                    process["sequence"]= T_process["sequence"]
                                    
                                    with lock_priorityLists:
                                        priorityLists=findPriorityLists(readyQueue)
                                    J+=1
                                    #break #?
                                else:
                                    edited_burstOperations.remove(operation)
                        
                        #case 1-B: Free
                        elif str(operation).startswith("F"):
                            resourceName=operation[1:].strip()
                            RESOURCES[resourceName]=False #free resouce 
                            remove_edge(str(resourceName), str(process["PID"]))
                            edited_burstOperations.remove(operation)
                            wakeUpBlockedProcesses(waitingQueue,readyQueue,priorityLists)
                        


                        #case 1-c: execute within an interval
                        elif str(operation).strip().isdecimal() :
                            if MyProcess==process["PID"]:
                                startTime=TIME#to add in Gantt Chart
                                process["execution time"]+= (min (QUANTUM,int((operation).strip()),S))
                                for i in range((min (QUANTUM,int((operation).strip()),S))):
                                    sleep(1)#edited from 0.5 to 1

                                endTime=TIME
                                process["end time"]=TIME
                            else:
                                S=QUANTUM
                                startTime=TIME#to add in Gantt Chart
                                process["execution time"]+= (min (QUANTUM,int((operation).strip())))
                                for i in range((min (QUANTUM,int((operation).strip())))):
                                    sleep(1)#edited from 0.5 to 1

                                endTime=TIME
                                process["end time"]=TIME

                            addToGanttChart(process["PID"],startTime,endTime,GanttChart)

                            if int((operation).strip()) < QUANTUM:#finished this execution
                                S=QUANTUM-int((operation).strip())
                                MyProcess=process["PID"]
                                edited_burstOperations.remove(operation)
                                
                            else:#preempted, hasn't finished
                                if S!=QUANTUM and MyProcess==process["PID"]:
                                    index=edited_burstOperations.index(operation)
                                    edited_burstOperations[index]= int((operation).strip()) - S
                                    S=QUANTUM
                                    MyProcess=-1
                                elif int((operation).strip()) == QUANTUM:
                                    edited_burstOperations.remove(operation)
                                else:
                                    index=edited_burstOperations.index(operation)
                                    edited_burstOperations[index]= int((operation).strip()) - QUANTUM
                                #preemption to apply round robin
                                with lock_priorityLists:
                                    if priorityLists:
                                        priorityLists[0].append(priorityLists[0].pop(0))#preempte process to the end of queue
                                process["sequence"][0]=constructEditedBurst(edited_burstOperations,"CPU")
                                # break

                        process["sequence"][0]=constructEditedBurst(edited_burstOperations,"CPU")
                        #if process has executed all its bursts -> delete process ->update lists
                        if process["sequence"][0]=="":
                            del process["sequence"][0]
                        if len(process["sequence"])<1:
                            process["finished"]=True
                            deleteFromMainQueue(process,readyQueue)
                            # updatePriorityLists(priorityLists,readyQueue)

                            with lock_priorityLists:
                                priorityLists=findPriorityLists(readyQueue)
                            J+=1
                        break

                else:
                    deleteFromMainQueue(process,readyQueue)#uses mutex lock
                    updatePriorityLists(priorityLists,readyQueue)
                    with lock_priorityLists:
                        priorityLists=findPriorityLists(readyQueue)#update lists
                    J+=1
          
                #wakeUpBlockedProcesses(waitingQueue,readyQueue,priorityLists)
                returnIOProcesses(IOQueue,readyQueue,priorityLists)
                #process also added to priorityLists
        
        for process in myList:
            deleteFromMainQueue(process,readyQueue)
            updatePriorityLists(priorityLists,readyQueue)
            with lock_priorityLists:
                priorityLists=findPriorityLists(readyQueue)
    else:
        #wakeUpBlockedProcesses(waitingQueue,readyQueue,priorityLists)
        returnIOProcesses(IOQueue,readyQueue,priorityLists)
        with lock_priorityLists:
            priorityLists=findPriorityLists(readyQueue)
        updatePriorityLists(priorityLists,readyQueue)

J=0
totalWaitingTime=0
totalTurnaroundTime=0


for process in processesList:
    turnaround= int(process["end time"])-int(process["arrival time"])
    waiting= turnaround-int(process["execution time"])-int(process["IO time"])- int(process["blocking time"])
    totalWaitingTime+=waiting 
    totalTurnaroundTime+=turnaround
    
    print(f"\n[{process["PID"]}] - start={process["start time"]} - end={process["end time"]}")  
    print(f"wait={waiting} - turnaround={turnaround}")

avgWaitingTime=totalWaitingTime/numOfProcesses
avgTurnaroundTime=totalTurnaroundTime/numOfProcesses

print("waiting= ", avgWaitingTime)
print("turnaround= ", avgTurnaroundTime)
for processInGantt in GanttChart:
    print (f"[PID={processInGantt["PID"]}] : start={processInGantt["start time"]} - end={processInGantt["end time"]}")

drawGanttChart(GanttChart)        
    
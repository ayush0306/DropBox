from __future__ import print_function
import socket
import os
import threading
import copy
import time
import sys
import md5

m=md5.new()
m2=md5.new()

port1 = 60000
s = socket.socket()  #client
host1 = ""

port2 = 60001
s2 = socket.socket()    #server
host2 = ""


s2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s2.bind((host2, port2))
s2.listen(5)

s.connect((host1, port1))
print(s.recv(1024))
print("Connection established")

conn, addr = s2.accept()
conn.send("Connection established")

def fileDetails(eachFile):
    modTime = time.ctime(os.path.getmtime(eachFile))
    size = os.path.getsize(eachFile)
    tmpCommand = 'file '+ str(eachFile)
    filetype = str(os.popen(tmpCommand).read())
    withoutNewLine = filetype[0:len(filetype)-1]
    toret = str(withoutNewLine)+" "+str(modTime)+" "+str(size)+"\n"
    return toret

def calculateHash(filename):
    tmpCommand = 'cksum '+ filename
    toret = str(os.popen(tmpCommand).read()).split()
    return toret[0]

def downloadTCP(filename):
    f = open(filename,'rb')
    l = f.read(1024)
    while(l):
        conn.send(l)
        l=f.read(1024)
    f.close()

def checkArgLength(argLength,verifyLength):
    if(argLength==verifyLength):
        return True
    conn.send('wrong command')
    return False

def recieveFile(eachFile):
    s.send("download "+eachFile)
    out = ""
    while True:
        tmp = s.recv(1024)
        out += tmp
        # print(out)
        if(out[-3:]=="EOF"):
            print("writing to file")
            f=open(eachFile,'wb')
            f.write(out[0:len(out)-3])
            f.close()
            s.send("next")
            outa=""
            while True:
                tmpa = s.recv(1024)
                outa +=tmpa
                if(outa[-3:]=="EOF"):
                    perm = outa[len(outa)-6:len(outa)-3]
                    # print(perm)
                    changePerm = "chmod "+perm+" "+eachFile
                    os.popen(changePerm)
                    break
            break

class senderThread (threading.Thread):

    def __init__(self,threadID,name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name

    def run(self):
        while True:
            print("EnterYourCommand>>>",end='')
            a = raw_input()
            s.send(a)
            if(a=='quit'):
                break
            print('receiving data...')
            out = ""
            while True:
                tmp = s.recv(1024)
                out += tmp
                # print(out)
                if(out[0:2]=='no'):
                    print("File does not exist")
                    break
                elif(out[-3:]=="EOF"):
                    command = a.split()
                    if(command[0]=='download'):
                        if(command[1]=="TCP" or command[1]=="UDP"):
                            if(len(command)==3):
                                print("writing to file")
                                f=open(command[2],'wb')
                                f.write(out[0:len(out)-3])
                                f.close()
                                s.send("next")
                                outa=""
                                while True:
                                    tmpa = s.recv(1024)
                                    outa += tmpa
                                    if(outa[-3:]=="EOF"):
                                        perm = outa[len(outa)-6:len(outa)-3]
                                        # print(perm)
                                        changePerm = "chmod "+perm+" "+command[2]
                                        os.popen(changePerm)
                                        print(outa[0:len(outa)-7])
                                        break
                        else:
                            print("wrong command")
                    else:
                        print(out[0:len(out)-4])
                    break
            print('data recieved.')

class recieverThread (threading.Thread):

    def __init__(self,threadID,name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name

    def run(self):
        while True:
            # print("new loop")
            data = conn.recv(1024)
            # print("input is ",data)
            args = data.split()

            if ( args[0] == 'quit' ):
                break

            elif(len(args)<2):
                conn.send("wrong command")

            elif(args[0]=='index'):
                files=os.listdir(os.curdir)
                if(args[1]=='shortlist'):
                    if(checkArgLength(len(args),4)):
                        for eachFile in files:
                            tmp1=os.stat(eachFile)
                            modTime=int(tmp1.st_mtime)
                            if modTime>=(int)(args[2]) and modTime<=(int)(args[3]):
                                toret = fileDetails(eachFile)
                                conn.send(str(toret))
                elif(args[1]=='longlist'):
                    if(checkArgLength(len(args),2)):
                        for filename in files:
                            toret = fileDetails(filename)
                            conn.send(str(toret))
                elif(args[1]=='regex'):
                    if(checkArgLength(len(args),3)):
                        regex = "ls | grep " + '"' + args[2] + '"'
                        files = str(os.popen(regex).read()).split("\n")
                        for eachFile in files[0:len(files)-1]:
                            toret = fileDetails(eachFile)
                            conn.send(str(toret))
                else:
                    conn.send("wrong command")

            elif(args[0]=='hash'):
                if(args[1]=='verify'):
                    if(checkArgLength(len(args),3)):
                        if(os.path.isfile(args[2])):
                            hashval = calculateHash(args[2])
                            modTime = time.ctime(os.path.getmtime(args[2]))
                            toret = str(args[2])+" : "+str(hashval)+" "+str(modTime)+"\n"
                            conn.send(str(toret))
                        else:
                            conn.send("no such file\n")
                elif(args[1]=='checkall'):
                    if(checkArgLength(len(args),2)):
                        files=os.listdir(os.curdir)
                        for eachFile in files:
                            if(os.path.isdir(eachFile) == False):
                                hashval = calculateHash(eachFile)
                                modTime = time.ctime(os.path.getmtime(eachFile))
                                toret = str(eachFile)+" : "+str(hashval)+" "+str(modTime)+"\n"
                                conn.send(str(toret))
            elif(args[0]=='download'):
                if(checkArgLength(len(args),3)):
                    if(args[1]=="TCP"):
                        if(os.path.isfile(args[2])):
                            downloadTCP(args[2])
                            conn.send('EOF')
                            conn.recv(1024)
                            tmp1 = fileDetails(args[2])
                            m.update(open(args[2],'rb').read())
                            hashval = m.hexdigest()
                            tmp2 = "MD5 Hash : "+str(hashval)
                            tmp3 = oct(os.stat(args[2])[0])[-3:]
                            toret = str(tmp1)+str(tmp2)+"\n"+str(tmp3)
                            conn.send(str(toret))
                        else:
                            conn.send("no")
            else:
                conn.send("wrong command")
            conn.send('EOF')
            # print("finished on server side")

class recieverSync (threading.Thread):

    def __init__(self,threadID,name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name

    def run(self):
        while True:
            inp = conn.recv(1024)
            args = inp.split()
            # print(args)
            if(args[0]=='delete'):
                    if(os.path.isfile(args[1])):
                        deleteFile = "rm -rf "+str(args[1])
                        os.popen(deleteFile)
            elif(args[0]=='index'):
                files=os.listdir(os.curdir)
                for each in files:
                    if(os.path.isdir(each)):
                        files.remove(each)
                for eachFile in files:
                    tmp1=os.stat(eachFile)
                    modTime=int(tmp1.st_mtime)
                    # m.update(open(eachFile,'rb').read())
                    # hashval = m.hexdigest()
                    command = 'cksum '+eachFile
                    twoVals = os.popen(command).read()
                    oneVal = twoVals.split()
                    hashval = oneVal[0]
                    toret=str(eachFile)+":"+str(modTime)+":"+str(hashval)+" "
                    conn.send(str(toret))
                conn.send('EOF')
            elif(args[0]=='download'):
                downloadTCP(args[1])
                conn.send('EOF')
                tmp3 = oct(os.stat(args[1])[0])[-3:]
                conn.recv(1024)
                conn.send(str(tmp3))
                conn.send('EOF')

            elif(args[0]=='quit'):
                break

class sendSync (threading.Thread):

    def __init__(self,threadID,name,files):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.prev = copy.deepcopy(files)

    def run(self):
        cnt = 400000
        while(cnt>0):
            new = os.listdir(os.curdir)
            for each in new:
                if(os.path.isdir(each)):
                    new.remove(each)
            for eachFile in self.prev:
                if eachFile not in new:
                    deleteFile = "delete "+str(eachFile)
                    s.send(deleteFile)
            self.prev = copy.deepcopy(new)
            s.send("index")
            out = ""
            while True:
                out+=s.recv(1024)
                if(out[-3:]=="EOF"):
                    tmp1 = out[0:len(out)-3]
                    filelist = tmp1.split()
                    break
            # print(filelist)
            for entries in filelist:
                tmp2 = entries.split(':')
                # print(entries)
                eachFile = tmp2[0]
                if eachFile not in new:
                    print(eachFile," not in this directory")
                    recieveFile(eachFile)
                elif eachFile in new:
                    # m2.update(open(eachFile,'rb').read())
                    # hashval = m2.hexdigest()
                    command = 'cksum '+eachFile
                    twoVals = os.popen(command).read()
                    oneVal = twoVals.split()
                    hashval = oneVal[0]
                    if(str(hashval)!=tmp2[2]):
                        tmp1=os.stat(eachFile)
                        modTime=int(tmp1.st_mtime)
                        if(int(tmp2[1])>modTime):
                            print(eachFile," not updated")
                            recieveFile(eachFile)
            cnt-=1
            time.sleep(3)
        s.send('quit')


if(len(sys.argv)!=2):
    print("invalid input")

else:
    if(sys.argv[1]=='1'):
        thread1 = recieverThread(1, "reciever")
        thread1.start()

        thread2 = senderThread(2,"sender")
        thread2.start()

        thread1.join()
        thread2.join()

    elif(sys.argv[1]=='2'):
        thread1 = recieverSync(1, "reciever")
        thread1.start()

        listing = os.listdir(os.curdir)
        # print(listing)
        for each in listing:
            if(os.path.isdir(each)):
                listing.remove(each)
        # print(listing)
        thread2 = sendSync(2,"sender",listing)
        thread2.start()

        thread1.join()
        thread2.join()

s.close()
s2.close()
print("connection closed")

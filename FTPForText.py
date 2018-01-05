'''
The final activity for the Advanced Python section is a drive-wide FTP-like
tool. You should be able to receive multiple connections, each on their
own thread. You should take several commands:
DRIVESEARCH <filename>
    DRIVESEARCH looks for the given filename across the entire drive. If
    it finds the file, it sends back the drive location.
DIRSEARCH <directory> <filename>
    DIRSEARCH looks for the file in the given directory or its
    subdirectories. If it finds the file, it sends back the location.
DOWNLOAD <filename>
    DOWNLOAD requires the full file path, or at least the relative path,
    of the file. It sends the contents of the file across the network.
UPLOAD <filename>
    UPLOAD requires the full file path, or at least the relative path,
    where the user wants to locate the file. It reads the file contents
    from across the network connection.
CLOSE
    CLOSE ends the connection

This activity will require you to use multithreading, ctypes, regular
expressions, and some libraries with which you're unfamiliar. ENJOY!
'''

import os, re, socket, threading, struct
from ctypes import *

def read_file(filename): #ctypes
    file_handle=windll.Kernel32.CreateFileA(filename,0x10000000,0,0,3,0x80,0) #Open file only if it exists
    if file_handle==-1: #Invalid Handle value
        return -1
    data=create_string_buffer(4096)
    read_data=c_int(0)
    if (windll.Kernel32.ReadFile(file_handle,byref(data),4096,byref(read_data),None)==0):
        return -1
    windll.Kernel32.CloseHandle(file_handle)
    print data.value
    return data.value

def create_file(filename, data): #ctypes
    file_handle=windll.Kernel32.CreateFileA(filename,0x10000000,0,0,4,0x80,0)
    if file_handle==-1: #Invalid Handle value
        return -1
    data_written=c_int(0)
    if(windll.Kernel32.WriteFile(file_handle,data,len(data),byref(data_written),None)==0):
        return -1
    windll.Kernel32.CloseHandle(file_handle)
    return

def recv_data(sock): #Implement a networking protocol
    data_length,=struct.unpack("!I",sock.recv(4)) #As struct.unpack returns a tuple
    data_received=sock.recv(data_length)
    return data_received

def send_data(sock,data): #Implement a networking protocol
    #Before we send data we need to notify the client the length of the data being sent
    data_length=len(data)
    sock.send(struct.pack("!I",data_length))  #This is used to send the data length in an unsigned int format in network byte order
    sock.send(data)
    return

def search_drive(file_name): #DRIVESEARCH
    file_regex=re.compile(file_name)
    for root,dirs,files in os.walk("C:\\"):
        for the_file in files:
            if (re.search(file_regex,the_file)):
                return os.path.join(root,the_file) #Returns the first file found
    return -1  # Consistently returning -1 for all sorts of errors. Returns -1 if it doesn't find a file

def search_directory(file_name): #DIRSEARCH
    file_regex=re.compile(file_name)
    for root,dirs,files in os.walk(os.getcwd()):   #getcwd() returns the current working directory
        for the_file in files:
            if (re.search(file_regex,the_file)):
                return os.path.join(root,the_file)
    return -1  # Consistently returning -1 for all sorts of errors

def send_file_contents(file_name,usersock,userinfo): #DOWNLOAD
    the_file=read_file(file_name)
    if the_file==-1:
        send_data(usersock,"File download failed")
    else:
        send_data(usersock,the_file)
    return

def receive_file_contents(file_name,usersock):#UPLOAD
    data=recv_data(usersock)
    if(create_file(file_name,data)==-1):
        send_data(usersock,"File upload failed")
    else:
        send_data(usersock,"Successful!!")
    return

def handle_connection(usersock,userinfo):
    bool_continue=True
    while bool_continue:
        send_data(usersock,"Enter a command:")
        command=recv_data(usersock).upper() #Receiving command from the client socket
        commands_list=["DRIVESEARCH","DIRSEARCH","DOWNLOAD","UPLOAD","CLOSE"] #List of commands we need to implement

        if (command=="DRIVESEARCH"):
            send_data(usersock,"Filename:")  #Prompt for client to enter the file name he is looking for
            file_name=recv_data(usersock)
            search_result=search_drive(file_name)
            if search_result==-1:
                send_data(usersock,"File Not Found")
            else:
                send_data(usersock,search_result)

        elif (command=="DIRSEARCH"):
            send_data(usersock,"Filename:")
            file_name=recv_data(usersock)
            search_result=search_directory(file_name)
            if search_result==-1:
                    send_data(usersock,"File Not Found")
            else:
                send_data(usersock,search_result)

        elif (command=="DOWNLOAD"):
            send_data(usersock,"Filename:")
            file_name=recv_data(usersock)
            send_file_contents(file_name,usersock,userinfo)

        elif (command=="UPLOAD"):
            send_data(usersock,"Filename:")
            file_name=recv_data(usersock)
            receive_file_contents(file_name,usersock)

        elif (command=="CLOSE"):
            bool_continue=False

        else:
            send_data(usersock,"INVALID COMMAND!!")

    return

def main():
    while True:
        sock_server=socket.socket(socket.AF_INET,socket.SOCK_STREAM) #socket object for our server
        HOST=''
        PORT=55555
        sock_server.bind((HOST,PORT))
        sock_server.listen(8) #Listens for connections
        usersock,userinfo=sock_server.accept()
        connection_thread_list=threading.Thread(None,handle_connection,None,(usersock,userinfo))
        connection_thread_list.start()
    return



main()

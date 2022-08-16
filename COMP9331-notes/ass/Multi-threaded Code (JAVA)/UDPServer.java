/*
 * Threaded UDPServer
 * Compile: javac UDPServer.java
 * Run: java UDPServer PortNo
 */

import java.io.*;
import java.net.*;
import java.util.*;
import java.text.SimpleDateFormat;
import java.util.concurrent.locks.*;

public class UDPServer extends Thread{

    static List<SocketAddress> clients=new ArrayList<SocketAddress>();
    static byte[] sendData = new byte[1024];
    static DatagramSocket serverSocket;
    static int UPDATE_INTERVAL = 1000;//milliseconds
    static ReentrantLock syncLock = new ReentrantLock();
    
	public static void main(String[] args)throws Exception {
        //Assign Port no
        int serverPort = Integer.parseInt(args[0]);
		serverSocket = new DatagramSocket(serverPort);
        System.out.println("Server is ready :");
        
        String sentence = null;
        //prepare buffers
        byte[] receiveData = null;
        String serverMessage = null;
        SocketAddress sAddr;
        //Start the other sending thread
        UDPServer us=new UDPServer();
        us.start();
        
        while (true){
            //receive UDP datagram
            receiveData = new byte[1024];
            DatagramPacket receivePacket = new DatagramPacket(receiveData, receiveData.length);
            serverSocket.receive(receivePacket);
            
            //get data
            sentence = new String(receivePacket.getData());
            //Need only the data received not the spaces till size of buffer
            sentence=sentence.trim();
            System.out.println("RECEIVED: " + sentence);
            //get lock
            syncLock.lock();
            sAddr = receivePacket.getSocketAddress();
            if(sentence.equals("Subscribe")){
                clients.add(sAddr);
                serverMessage="Subscription successfull";
            }
            else if(sentence.equals("Unsubscribe")){
                    if (clients.contains(sAddr)){
                        clients.remove(sAddr);
                        serverMessage="Subscription removed";
                    }
                    else{
                    serverMessage="You are not currently subscribed";
                    }
            }
            else{
                serverMessage="Unknown command, send Subscribe or Unsubscribe only";
            }
            
            //prepare to send reply back
            sendData = serverMessage.getBytes();
            
            //send it back to client on SocktAddress sAddr
            DatagramPacket sendPacket = new DatagramPacket(sendData, sendData.length, sAddr);
            serverSocket.send(sendPacket);
            //This should be the main
            //System.out.println(Thread.currentThread().getName());
            syncLock.unlock();
        } // end of while (true)
        
	} // end of main()
// We will send from this thread
    public void run(){
        while(true){
            //get lock
            syncLock.lock();
            for (int j=0; j < clients.size();j++){
                long millis = System.currentTimeMillis();
                Date date_time = new Date(millis);
                String message= "Current time is " + date_time;
                sendData = message.getBytes();
                DatagramPacket sendPacket = new DatagramPacket(sendData, sendData.length, clients.get(j));
                try{
                serverSocket.send(sendPacket);
                } catch (IOException e){ }
                String clientInfo =clients.get(j).toString();
                //Not printing the leading /
                System.out.println("Sending time to " + clientInfo.substring(1) + " at time " + date_time);
            }
            //release lock
            syncLock.unlock();
        //sleep for UPDATE_INTERVAL
        try{
            Thread.sleep(UPDATE_INTERVAL);//in milliseconds
        } catch (InterruptedException e){
            System.out.println(e);
        }
       // System.out.println(Thread.currentThread().getName());
    }// while ends
    } //run ends
} // end of class UDPServer

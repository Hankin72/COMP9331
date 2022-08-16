/*
 *
 *  UDPClient
 *  * Compile: java UDPClient.java
 *  * Run: java UDPClient localhost PortNo
 */
import java.io.*;
import java.net.*;

public class UDPClient {

	public static void main(String[] args) throws Exception {
        if(args.length != 2){
            System.out.println("Usage: java UDPClinet localhost PortNo");
            System.exit(1);
        }
		// Define socket parameters, address and Port No
        InetAddress IPAddress = InetAddress.getByName(args[0]);
        int serverPort = Integer.parseInt(args[1]);
		//change above port number if required
		
		// create socket which connects to server
		DatagramSocket clientSocket = new DatagramSocket();
/*This line creates the client’s socket, called clientSocket. DatagramSocket indicates that we are using UDP*/
        
		// get input from keyboard
        System.out.println("Please type Subscribe");
		String sentence;
		BufferedReader inFromUser =
			new BufferedReader(new InputStreamReader(System.in));
		sentence = inFromUser.readLine();
        //prepare for sending
        byte[] sendData=new byte[1024];
        sendData=sentence.getBytes();
		// write to server, need to create DatagramPAcket with server address and port No
        DatagramPacket sendPacket=new DatagramPacket(sendData,sendData.length,IPAddress,serverPort);
        //actual send call
        clientSocket.send(sendPacket);
        
        //prepare buffer to receive reply
        byte[] receiveData=new byte[1024];
		// receive from server
        DatagramPacket receivePacket = new DatagramPacket(receiveData,receiveData.length);
        clientSocket.receive(receivePacket);
        
        String reply = new String(receivePacket.getData());
        System.out.println("FROM SERVER:" + reply);
        reply=reply.trim();
        if(reply.equals("Subscription successfull")){
            //Expect 10 messages telling us about the current time
            for(int i=0;i<10;i++){
                clientSocket.receive(receivePacket);
                reply = new String(receivePacket.getData());
                System.out.println(reply);
            }
        }// if ends
        
        sentence="Unsubscribe";
        sendData=sentence.getBytes();
        sendPacket=new DatagramPacket(sendData,sendData.length,IPAddress,serverPort);
        //actual send call
        clientSocket.send(sendPacket);
        //close the scoket
        clientSocket.close();
		
	} // end of main
    
} // end of class UDPClient

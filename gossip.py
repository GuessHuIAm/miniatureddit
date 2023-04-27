import socket
import threading
import json
from config import *


class GossipProtocol:
    def __init__(self):
        pass
        # # Sets up a UDP socket listener on a specified port
        # self.peers = []
        # self.stop_flag = False

        # # Start the listener thread for incoming messages
        # self.listener_thread = threading.Thread(target=self.listener)
        # self.listener_thread.start()

    def listener(self):
        pass
        # sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # sock.bind((HOST, PORT))

        # while not self.stop_flag:
        #     data, addr = sock.recvfrom(1024)
        #     self.handle_received_data(data, addr)

        # sock.close()

    def handle_received_data(self, data, addr):
        pass
        # try:
        #     message = json.loads(data)
        #     # Handle incoming messages, e.g., update local data, propagate messages
        # except json.JSONDecodeError:
        #     pass

    def broadcast(self, data):
        pass
        # json_data = json.dumps(data)
        # for peer in self.peers:
        #     sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #     sock.sendto(json_data.encode('utf-8'), peer)
        #     sock.close()

    def add_peer(self, ip_address, port):
        pass
        # addr = (ip_address, port)
        # self.peers.append(addr)

    def remove_peer(self, addr):
        pass
        # self.peers.remove(addr)

    def stop(self):
        pass
        # self.stop_flag = True
        # self.listener_thread.join()

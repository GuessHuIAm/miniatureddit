import threading
from config import *
from models import db
from os import path
from sqlalchemy import text

import p2psync_pb2 as pb2
import p2psync_pb2_grpc as pb2_grpc
import grpc

class GossipProtocol:
    def __init__(self, self_ip, self_port, other_ip, other_port, session, context):
        self.COMMIT_LOG_FILE = f'commit_{self_ip}_{self_port}.txt'

        # Sets up a UDP socket listener on a specified port
        global peers
        peers = \
            [pb2.Peer(host=other_ip, port=other_port)] \
            if not (other_ip is None or other_port is None) \
            else []

        # Stop flag
        self.stop_flag = False

        # Start listener threads for incoming peers
        if peers:
            self.listener_threads = [threading.Thread(target=self.listen_peers, args=(peers[0],))]
            self.listener_threads[0].start()

        # Get the last commit number
        if path.exists(self.COMMIT_LOG_FILE):
            with open(self.COMMIT_LOG_FILE, "r") as f:
                self.commit_counter = int(f.readlines()[-1].split("|")[0])
        else:
            self.commit_counter = 0

        if peers:
            # Constantly update current commit log with any of the other peers' commit logs
            self.commit_listener_thread = threading.Thread(target=self.listen_commits, args=(session, context))
            self.commit_listener_thread.start()


    def listen_commits(self, session, context):
        global peers
        while True:
            for peer in peers:
                try:
                    new_logs = self.receive_commit_log(peer)
                except:
                    continue

                # Update database with commit log
                if new_logs:
                    self.update_database(new_logs, session, context)

                # Exit loop if we get new logs successfully
                break

            else:
                # If the loop completes without finding any updates, raise an exception
                raise Exception("Not able to update database. Please check your connection and try again.")


    def receive_commit_log(self, peer):
        # Receive commit log from peer
        try:
            host, port = peer.host, peer.port
            stub = pb2_grpc.P2PSyncStub(grpc.insecure_channel(f'{host}:{port}'))
            response_iterator = stub.ListenCommands(pb2.Peer(host=host, port=port))

            new_logs = []
            counter = self.commit_counter

            for res in response_iterator:
                timestamp, command = res.timestamp, res.command

                if int(timestamp) > counter:
                    # Add the commit to the list of new commits
                    new_logs.append(f'{timestamp}|{command[:-1]}')

                    # Update the counter variable
                    counter = int(timestamp)

            return new_logs

        except Exception:
            print("Could not receive file.")
            return None


    def update_database(self, new_logs, session, context):
        '''Get the database up to date with the commit log,
        starting from the last commit number, self.commit_counter'''
        for line in new_logs:
            commit_num, commit = line.split("|")
            if int(commit_num) > self.commit_counter:
                # Execute the commit
                with context:
                    session.execute(text(commit))
                    session.commit()
                # Update the counter
                with open(self.COMMIT_LOG_FILE, "a") as f:
                    f.write(f"{str(commit_num)}|{commit}\n")
                self.commit_counter = int(commit_num)


    def listen_peers(self, peer):
        '''Updates peers constantly '''
        host, port = peer.host, peer.port
        stub = pb2_grpc.P2PSyncStub(grpc.insecure_channel(f'{host}:{port}'))
        peers_stream = stub.GetPeerList(pb2.Empty())
        for p in peers_stream:
            if self.stop_flag:
                break
            global peers
            peers = p.peers  # TODO: Verify that this works as intended


    def broadcast(self, command):
        '''Broadcasts a command to all peers in the network, and updates the commit log'''
        with open(self.COMMIT_LOG_FILE, "a") as f:
            f.write(f"{str(self.commit_counter + 1)}|{command}\n")
        self.commit_counter += 1


    def stop(self):
        self.stop_flag = True
        for t in self.listener_threads:
            t.join()
        self.commit_listener_thread.join()


class P2PSyncServer(pb2_grpc.P2PSyncServicer):
    def __init__(self):
        self.peers_edited = True


    def GetPeerList(self, request, context):
        """Send stream of peer lists to client"""
        while True:
            if self.peers_edited:
                self.peers_edited = False
                global peers
                yield pb2.PeerList(peers=peers)


    def ListenCommands(self, request, context):
        """Continually send stream of items from commit log to client"""
        host, port = request.host, request.port
        commit_log_file = f'commit_{host}_{port}.txt'
        with open(commit_log_file, 'r') as commit_log:
            for line in commit_log.readlines():
                timestamp, command = line.split('|')
                yield pb2.DatabaseCommand(timestamp=int(timestamp), command=command)


    def Connect(self, request, context):
        '''Receive connection from other P2PNode'''
        addr = (request.host, request.port)
        global peers
        peers.append(pb2.Peer(host=addr[0], port=addr[1]))
        self.peers_edited = True

        # Start continuous heartbeat with new peer node
        threading.Thread(target=self.heartbeat_peer, args=(*addr,)).start()

        return pb2.Empty()

    def Heartbeat(self, request, context):
        '''Heartbeat'''
        return pb2.Empty()

    def heartbeat_peer(self, host, port):
        '''Continuous heartbeat to peer at (host, port)'''
        stub = pb2_grpc.P2PSyncStub(grpc.insecure_channel(f'{host}:{port}'))
        while True:
            try:
                stub.Heartbeat(pb2.Empty())
            except grpc._channel._InactiveRpcError:
                break

        # Remove peer if heartbeat fails
        global peers
        peers.remove((host, port))
        peers_edited = True




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
        global SESSION
        SESSION = session
        global CONTEXT
        CONTEXT = context

        global COMMIT_LOG_FILE
        COMMIT_LOG_FILE = f'commit_{self_ip}_{self_port}.txt'

        # Sets up a UDP socket listener on a specified port
        global peers
        peers = \
            [pb2.Peer(host=other_ip, port=other_port)] \
            if not (other_ip is None or other_port is None) \
            else []

        # Stop flag
        self.stop_flag = False

        # Get the last commit number
        global commit_counter
        commit_counter = 0
        if path.exists(COMMIT_LOG_FILE):
            with open(COMMIT_LOG_FILE, "r") as f:
                commit_counter = int(f.readlines()[-1].split("|")[0])
        else:
            open(COMMIT_LOG_FILE, 'w').close()

        # Update current commit log with any of the other peers' commit logs
        if peers:
            self.load_commits()


    def load_commits(self):
        global peers
        for peer in peers:
            try:
                new_logs = self.receive_commit_log(peer)
            except grpc._channel._InactiveRpcError:
                continue

            # Update database with commit log
            if new_logs:
                self.update_database(new_logs)

            # Exit loop if we get new logs successfully
            break

        else:
            # If the loop completes without finding any updates, raise an exception
            raise Exception("Not able to update database. Please check your connection and try again.")


    def receive_commit_log(self, peer):
        # Receive commit log from peer
        global commit_counter
        try:
            host, port = peer.host, peer.port
            stub = pb2_grpc.P2PSyncStub(grpc.insecure_channel(f'{host}:{port}'))
            response_iterator = stub.ListenCommands(pb2.Peer(host=host, port=port))

            new_logs = []
            counter = commit_counter
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


    def update_database(self, new_logs):
        '''Get the database up to date with the commit log,
        starting from the last commit number, commit_counter'''
        global commit_counter
        for line in new_logs:
            commit_num, commit = line.split("|")
            if int(commit_num) > commit_counter:
                # Execute the commit
                with CONTEXT:
                    SESSION.execute(text(commit))
                    SESSION.commit()
                # Update the counter
                with open(COMMIT_LOG_FILE, "a") as f:
                    f.write(f"{str(commit_num)}|{commit}\n")
                commit_counter = int(commit_num)


    def broadcast(self, command):
        '''Broadcasts a command to all peers in the network, and updates the commit log'''
        global commit_counter
        commit_counter += 1
        with open(COMMIT_LOG_FILE, "a") as f:
            f.write(f"{commit_counter}|{command}\n")

        # Broadcast to all peers
        for p in peers:
            host, port = p.host, p.port
            stub = pb2_grpc.P2PSyncStub(grpc.insecure_channel(f'{host}:{port}'))
            stub.SendCommand(pb2.DatabaseCommand(timestamp=int(commit_counter), command=command))


    def stop(self):
        self.stop_flag = True


class P2PSyncServer(pb2_grpc.P2PSyncServicer):
    def PeerListUpdate(self, request, context):
        """Send stream of peer lists to client"""
        peer, add = request.peer, request.add
        global peers
        if add:
            peers.append(peer)
        else:
            peers.remove(peer)


    def ListenCommands(self, request, context):
        """Continually send stream of items from commit log to client"""
        global COMMIT_LOG_FILE
        with open(COMMIT_LOG_FILE, 'r') as commit_log:
            for line in commit_log.readlines():
                timestamp, command = line.split('|')
                yield pb2.DatabaseCommand(timestamp=int(timestamp), command=command)


    def Connect(self, request, context):
        '''Receive connection from other P2PNode'''
        host, port = request.host, request.port
        peer = pb2.Peer(host=host, port=port)
        stub = pb2_grpc.P2PSyncStub(grpc.insecure_channel(f'{host}:{port}'))
        global peers
        stub.SetPeerList(peers)
        self.broadcast_peer_update(peers, peer, True)
        peers.append(peer)

        # Start continuous heartbeat with new peer node
        threading.Thread(target=self.heartbeat_peer, args=(host, port,)).start()

        return pb2.Empty()


    def Heartbeat(self, request, context):
        '''Heartbeat'''
        return pb2.Empty()


    def SendCommand(self, request, context):
        '''Register a command in the commit log and database if is greater than own commit counter'''
        timestamp, command = request.timestamp, request.command

        # If timestamp is greater than own commit counter, update commit log
        global commit_counter
        if timestamp > commit_counter:
            # Execute the command
            global CONTEXT
            global SESSION
            with CONTEXT:
                SESSION.execute(text(command))
                SESSION.commit()

            # Update the counter
            with open(COMMIT_LOG_FILE, "a") as f:
                f.write(f"{timestamp}|{command}\n")
            commit_counter = timestamp

        return pb2.Empty()


    def SetPeerList(self, request, context):
        '''Initialize peer list of this node to that given in the input'''
        global peers
        peers = request.peers
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
        peer = pb2.Peer(host=host, port=port)
        peers.remove(peer)
        self.broadcast_peer_update(peers, peer, False)


    def broadcast_peer_update(self, peers, peer, add):
        '''Broadcast peer update for Peer peer depending on
           whether or not it was added (add=True) or removed (add=False)'''
        for p in peers:
            host, port = p.host, p.port
            stub = pb2_grpc.P2PSyncStub(grpc.insecure_channel(f'{host}:{port}'))
            stub.PeerListUpdate(pb2.PeerUpdate(peer=peer, add=add))
# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: p2psync.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\rp2psync.proto\"\x07\n\x05\x45mpty\".\n\nPeerUpdate\x12\x13\n\x04peer\x18\x01 \x01(\x0b\x32\x05.Peer\x12\x0b\n\x03\x61\x64\x64\x18\x02 \x01(\x08\" \n\x08PeerList\x12\x14\n\x05peers\x18\x01 \x03(\x0b\x32\x05.Peer\"\"\n\x04Peer\x12\x0c\n\x04host\x18\x01 \x01(\t\x12\x0c\n\x04port\x18\x02 \x01(\t\"5\n\x0f\x44\x61tabaseCommand\x12\x11\n\ttimestamp\x18\x01 \x01(\x05\x12\x0f\n\x07\x63ommand\x18\x02 \x01(\t2\xef\x01\n\x07P2PSync\x12\'\n\x0ePeerListUpdate\x12\x0b.PeerUpdate\x1a\x06.Empty\"\x00\x12.\n\x0eListenCommands\x12\x06.Empty\x1a\x10.DatabaseCommand\"\x00\x30\x01\x12\x1a\n\x07\x43onnect\x12\x05.Peer\x1a\x06.Empty\"\x00\x12\x1d\n\tHeartbeat\x12\x06.Empty\x1a\x06.Empty\"\x00\x12)\n\x0bSendCommand\x12\x10.DatabaseCommand\x1a\x06.Empty\"\x00\x12%\n\x0fRequestPeerList\x12\x05.Peer\x1a\t.PeerList\"\x00\x62\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'p2psync_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _EMPTY._serialized_start=17
  _EMPTY._serialized_end=24
  _PEERUPDATE._serialized_start=26
  _PEERUPDATE._serialized_end=72
  _PEERLIST._serialized_start=74
  _PEERLIST._serialized_end=106
  _PEER._serialized_start=108
  _PEER._serialized_end=142
  _DATABASECOMMAND._serialized_start=144
  _DATABASECOMMAND._serialized_end=197
  _P2PSYNC._serialized_start=200
  _P2PSYNC._serialized_end=439
# @@protoc_insertion_point(module_scope)

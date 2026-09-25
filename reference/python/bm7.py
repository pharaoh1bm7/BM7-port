#!/usr/bin/env python3
"""BM7 v0.1 reference implementation. Standard library only."""
from __future__ import annotations
import argparse, hashlib, hmac, secrets, socket, struct, time
from dataclasses import dataclass, field
from enum import IntEnum

MAGIC=b"B7"; VERSION=1; AUTH_LEN=32
HEADER_FMT="!2sBBHHHQQQ16sI32s"  # magic,ver,type,flags,hlen,plen,session,epoch,seq,sender,lease,tag
HEADER_LEN=struct.calcsize(HEADER_FMT)
PAYLOAD_FMT="!16sIIB3s"; PAYLOAD_LEN=struct.calcsize(PAYLOAD_FMT)

class Msg(IntEnum): HELLO=1; ADVERTISE=2; CLAIM=3; ACK=4; RELEASE=5; ERROR=6
class State(IntEnum): INIT=0; DISCOVERING=1; STANDBY=2; ACTIVE=3; FAILOVER=4; RECOVERY=5
ACTIVE=1; STANDBY=2; RECOVERING=4; PREEMPT=8; QUORUM=16

@dataclass(order=True, frozen=True)
class Rank:
    priority:int
    cost:int
    node_id:bytes
    def key(self): return (-self.priority, self.cost, self.node_id)

@dataclass
class Peer:
    node_id:bytes; priority:int; cost:int=0; last_seen:float=0; epoch:int=0; seq:int=0; state:State=State.INIT; lease_until:float=0

@dataclass
class BM7Node:
    node_id:bytes
    service_id:bytes
    priority:int
    cost:int
    peers:set[bytes]
    key:bytes
    hello_interval:float=2.0
    failure_threshold:int=3
    lease_seconds:float=10.0
    hold_down:float=10.0
    preemption_delay:float=5.0
    session_id:int=field(default_factory=lambda: secrets.randbits(64))
    epoch:int=0; seq:int=0; state:State=State.INIT; peers_state:dict[bytes,Peer]=field(default_factory=dict)
    active_owner:bytes|None=None; last_change:float=field(default_factory=time.monotonic)

    def __post_init__(self):
        self.peers.add(self.node_id)
        self.peers_state[self.node_id]=Peer(self.node_id,self.priority,self.cost,last_seen=time.monotonic(),state=self.state)

    def rank(self, node_id:bytes)->Rank:
        p=self.peers_state[node_id]
        return Rank(p.priority,p.cost,node_id)

    def quorum(self)->int: return len(self.peers)//2+1
    def live_voters(self, now=None)->set[bytes]:
        now=time.monotonic() if now is None else now
        out=set()
        for nid,p in self.peers_state.items():
            if nid==self.node_id or now-p.last_seen <= self.hello_interval*self.failure_threshold: out.add(nid)
        return out

    def has_quorum(self, now=None)->bool: return len(self.live_voters(now))>=self.quorum()

    def observe(self, packet:bytes, now=None)->bool:
        now=time.monotonic() if now is None else now
        msg=Packet.decode(packet)
        if not hmac.compare_digest(msg.tag, msg.compute_tag(self.key)): raise ValueError("bad authentication tag")
        if msg.sender_id not in self.peers: raise ValueError("unknown peer")
        p=self.peers_state.setdefault(msg.sender_id,Peer(msg.sender_id,0))
        if msg.epoch < self.epoch: return False
        if msg.epoch==p.epoch and msg.sequence<=p.seq: return False
        p.epoch=msg.epoch; p.seq=msg.sequence; p.last_seen=now; p.state=msg.state; p.lease_until=now+msg.lease_ms/1000 if msg.lease_ms else 0
        if msg.epoch>self.epoch: self.epoch=msg.epoch
        if msg.message_type==Msg.CLAIM:
            if not self.has_quorum(now): return False
            self.active_owner=msg.sender_id
            self.state=State.STANDBY if msg.sender_id!=self.node_id else State.ACTIVE
        elif msg.message_type==Msg.RELEASE and self.active_owner==msg.sender_id:
            self.active_owner=None
        return True

    def packet(self,msg_type:Msg,state:State|None=None,lease_ms:int=0,flags:int=0)->bytes:
        self.seq+=1
        st=self.state if state is None else state
        if self.has_quorum(): flags|=QUORUM
        p=struct.pack(PAYLOAD_FMT,self.service_id,self.priority,self.cost,int(st),b"\0\0\0")
        return Packet(msg_type,flags,self.session_id,self.epoch,self.seq,self.node_id,lease_ms,p,b"").encode(self.key)

    def hello(self)->bytes: return self.packet(Msg.HELLO,self.state,0)
    def advertise(self)->bytes: return self.packet(Msg.ADVERTISE,self.state,0)
    def claim(self,now=None)->bytes:
        now=time.monotonic() if now is None else now
        if not self.has_quorum(now): raise RuntimeError("cannot claim without quorum")
        self.epoch=max(self.epoch,max((p.epoch for p in self.peers_state.values()),default=0))+1
        self.state=State.ACTIVE; self.active_owner=self.node_id; self.last_change=now
        return self.packet(Msg.CLAIM,State.ACTIVE,int(self.lease_seconds*1000),ACTIVE|QUORUM)

    def should_claim(self,now=None)->bool:
        now=time.monotonic() if now is None else now
        if not self.has_quorum(now): return False
        live=self.live_voters(now)
        candidates=[self.node_id]+[nid for nid in live if nid in self.peers_state]
        winner=min(candidates,key=lambda nid:self.rank(nid).key())
        if winner!=self.node_id: return False
        if self.active_owner and self.active_owner!=self.node_id:
            p=self.peers_state.get(self.active_owner)
            if p and p.lease_until>now: return False
        return now-self.last_change>=self.preemption_delay or self.active_owner is None

@dataclass
class Packet:
    message_type:Msg; flags:int; session_id:int; epoch:int; sequence:int; sender_id:bytes; lease_ms:int; payload:bytes; tag:bytes
    def __post_init__(self):
        if len(self.sender_id)!=16: raise ValueError("sender_id must be 16 bytes")
        if len(self.payload)>65535: raise ValueError("payload too large")
    def header_without_tag(self)->bytes:
        return struct.pack(HEADER_FMT,MAGIC,VERSION,int(self.message_type),self.flags,HEADER_LEN,len(self.payload),self.session_id,self.epoch,self.sequence,self.sender_id,self.lease_ms,b"\0"*AUTH_LEN)
    @property
    def state(self)->State:
        if len(self.payload) >= PAYLOAD_LEN:
            try: return State(self.payload[24])
            except ValueError: return State.INIT
        return State.INIT
    def compute_tag(self,key:bytes)->bytes: return hmac.new(key,self.header_without_tag()+self.payload,hashlib.sha256).digest()
    def encode(self,key:bytes)->bytes:
        tag=self.compute_tag(key)
        return struct.pack(HEADER_FMT,MAGIC,VERSION,int(self.message_type),self.flags,HEADER_LEN,len(self.payload),self.session_id,self.epoch,self.sequence,self.sender_id,self.lease_ms,tag)+self.payload
    @classmethod
    def decode(cls,data:bytes)->"Packet":
        if len(data)<HEADER_LEN: raise ValueError("short packet")
        vals=struct.unpack(HEADER_FMT,data[:HEADER_LEN]); magic,ver,mt,flags,hlen,plen,sid,epoch,seq,sender,lease,tag=vals
        if magic!=MAGIC or ver!=VERSION or hlen!=HEADER_LEN or plen!=len(data)-HEADER_LEN: raise ValueError("invalid header")
        try: typ=Msg(mt)
        except ValueError: raise ValueError("unknown message type")
        return cls(typ,flags,sid,epoch,seq,sender,lease,data[HEADER_LEN:],tag)

def make_node(name:str, priority:int)->BM7Node:
    nid=hashlib.sha256(name.encode()).digest()[:16]
    peers={nid}
    return BM7Node(nid,hashlib.sha256(b"demo-service").digest()[:16],priority,0,peers,b"demo-secret")

def demo():
    a=make_node("A",100); b=make_node("B",200); c=make_node("C",150)
    ids={a.node_id,b.node_id,c.node_id}
    for n in (a,b,c):
        n.peers=set(ids); n.peers_state={x:Peer(x, {a.node_id:100,b.node_id:200,c.node_id:150}[x], last_seen=time.monotonic()) for x in ids}
    # B is preferred. Simulate B failure; A and C form quorum and C wins.
    now=time.monotonic()+7
    b.peers_state[a.node_id].last_seen=now-20; b.peers_state[c.node_id].last_seen=now-20
    c.peers_state[b.node_id].last_seen=now-20; a.peers_state[b.node_id].last_seen=now-20; c.peers_state[a.node_id].last_seen=now; a.peers_state[c.node_id].last_seen=now
    c.last_change=now-10
    assert c.should_claim(now)
    print("BM7 demo: C is eligible to claim after B failure and quorum remains available.")
    pkt=c.claim(now)
    assert a.observe(pkt,now) and a.active_owner==c.node_id
    print("BM7 demo: Python packet encode/decode/authentication/state transition succeeded.")

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--demo",action="store_true")
    args=ap.parse_args()
    if args.demo: demo()

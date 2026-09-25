import sys, os, unittest, hashlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'reference', 'python'))
from bm7 import *

class TestWire(unittest.TestCase):
 def setUp(self):
  self.key=b'test-key'; self.node=b'0123456789abcdef'; self.service=b'fedcba9876543210'
 def test_roundtrip(self):
  p=Packet(Msg.HELLO,QUORUM,1,4,10,self.node,2000,b'x'*32,b'')
  q=Packet.decode(p.encode(self.key)); self.assertEqual(q.sequence,10); self.assertEqual(q.epoch,4); self.assertEqual(q.sender_id,self.node)
  self.assertTrue(hmac.compare_digest(q.tag,q.compute_tag(self.key)))
 def test_tamper_rejected(self):
  p=Packet(Msg.CLAIM,0,1,1,1,self.node,1000,b'x'*32,b''); d=bytearray(p.encode(self.key)); d[-1]^=1
  q=Packet.decode(bytes(d));
  with self.assertRaises(ValueError):
   if not hmac.compare_digest(q.tag,q.compute_tag(self.key)): raise ValueError('bad authentication')
 def test_replay_rejected(self):
  n=BM7Node(self.node,self.service,100,0,{self.node,b'aaaaaaaaaaaaaaaa'},self.key)
  p=Packet(Msg.HELLO,0,1,0,5,b'aaaaaaaaaaaaaaaa',0,b'x'*32,b'').encode(self.key)
  self.assertTrue(n.observe(p)); self.assertFalse(n.observe(p))
 def test_malformed(self):
  with self.assertRaises(ValueError): Packet.decode(b'bad')

class TestElection(unittest.TestCase):
 def test_c_wins_after_b_failure(self):
  ids=[bytes(x,'ascii') for x in ('AAAAAAAAAAAAAAAA','BBBBBBBBBBBBBBBB','CCCCCCCCCCCCCCCC')]
  now=100.0; key=b'k'; service=b'S'*16
  n=BM7Node(ids[2],service,150,0,set(ids),key)
  n.peers_state={ids[0]:Peer(ids[0],100,last_seen=now),ids[1]:Peer(ids[1],200,last_seen=now-20),ids[2]:Peer(ids[2],150,last_seen=now)}
  n.last_change=now-20
  self.assertTrue(n.should_claim(now))
  pkt=n.claim(now); self.assertEqual(n.state,State.ACTIVE); self.assertEqual(n.active_owner,ids[2])

if __name__=='__main__': unittest.main()

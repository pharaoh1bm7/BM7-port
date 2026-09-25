package bm7
import "testing"
func TestRoundTrip(t *testing.T){var p Packet;p.Type=MsgHello;p.Session=7;p.Epoch=3;p.Sequence=9;p.Lease=1000;p.Payload[0]=1;copy(p.Sender[:],[]byte("0123456789abcdef"));key:=[]byte("secret");d:=Encode(p,key);q,e:=Decode(d,key);if e!=nil{t.Fatal(e)};if q.Type!=p.Type||q.Sequence!=p.Sequence||q.Epoch!=p.Epoch{t.Fatal("round trip mismatch")}}
func TestTamper(t *testing.T){var p Packet;p.Type=MsgClaim;key:=[]byte("secret");d:=Encode(p,key);d[100]^=1;if _,e:=Decode(d,key);e==nil{t.Fatal("tampered packet accepted")}}

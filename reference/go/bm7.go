package bm7

import (
 "crypto/hmac"
 "crypto/sha256"
 "encoding/binary"
 "errors"
)

const (
 Magic0='B'; Magic1='7'; Version=1; HeaderLen=86; AuthLen=32; PayloadLen=32
 MsgHello=1; MsgAdvertise=2; MsgClaim=3; MsgAck=4; MsgRelease=5; MsgError=6
)

type Packet struct { Type uint8; Flags uint16; Session,Epoch,Sequence uint64; Sender [16]byte; Lease uint32; Payload [32]byte; Tag [32]byte }

func put64(b []byte,v uint64){binary.BigEndian.PutUint64(b,v)}
func Encode(p Packet,key []byte) []byte {
 out:=make([]byte,HeaderLen+PayloadLen); out[0]=Magic0; out[1]=Magic1; out[2]=Version; out[3]=p.Type; binary.BigEndian.PutUint16(out[4:6],p.Flags); binary.BigEndian.PutUint16(out[6:8],HeaderLen); binary.BigEndian.PutUint16(out[8:10],PayloadLen); put64(out[10:18],p.Session); put64(out[18:26],p.Epoch); put64(out[26:34],p.Sequence); copy(out[34:50],p.Sender[:]); binary.BigEndian.PutUint32(out[50:54],p.Lease); copy(out[86:118],p.Payload[:]);
 mac:=hmac.New(sha256.New,key); mac.Write(out[:86]); mac.Write(out[86:]); copy(out[54:86],mac.Sum(nil)); return out
}
func Decode(data,key []byte)(Packet,error){
 var p Packet; if len(data)!=HeaderLen+PayloadLen{return p,errors.New("invalid length")}; if data[0]!=Magic0||data[1]!=Magic1||data[2]!=Version{return p,errors.New("invalid magic/version")}; p.Type=data[3]; if p.Type<MsgHello||p.Type>MsgError{return p,errors.New("unknown type")}; p.Flags=binary.BigEndian.Uint16(data[4:6]); if binary.BigEndian.Uint16(data[6:8])!=HeaderLen||binary.BigEndian.Uint16(data[8:10])!=PayloadLen{return p,errors.New("invalid lengths")}; p.Session=binary.BigEndian.Uint64(data[10:18]); p.Epoch=binary.BigEndian.Uint64(data[18:26]); p.Sequence=binary.BigEndian.Uint64(data[26:34]); copy(p.Sender[:],data[34:50]); p.Lease=binary.BigEndian.Uint32(data[50:54]); copy(p.Tag[:],data[54:86]); copy(p.Payload[:],data[86:118]);
 tmp:=make([]byte,len(data)); copy(tmp,data); for i:=54;i<86;i++{tmp[i]=0}; mac:=hmac.New(sha256.New,key); mac.Write(tmp[:86]); mac.Write(tmp[86:]); if !hmac.Equal(p.Tag[:],mac.Sum(nil)){return p,errors.New("authentication failed")}; return p,nil
}

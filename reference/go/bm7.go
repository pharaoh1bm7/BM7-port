package bm7

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/binary"
	"errors"
)

const (
	Magic0    = 'B'
	Magic1    = '7'
	Version   = 1
	HeaderLen = 86
	AuthLen   = 32
	PayloadLen = 32
	PacketLen = HeaderLen + PayloadLen
)

const (
	MsgHello     = 1
	MsgAdvertise = 2
	MsgClaim     = 3
	MsgACK       = 4
	MsgRelease   = 5
	MsgError     = 6
)

const (
	FlagActive     uint16 = 0x0001
	FlagStandby    uint16 = 0x0002
	FlagRecovering uint16 = 0x0004
	FlagPreempt    uint16 = 0x0008
	FlagQuorum     uint16 = 0x0010
)

type State uint8

const (
	StateInit State = iota
	StateDiscovering
	StateStandby
	StateActive
	StateFailover
	StateRecovery
)

type Packet struct {
	Type     uint8
	Flags    uint16
	Session  uint64
	Epoch    uint64
	Sequence uint64
	Sender   [16]byte
	Lease    uint32
	Payload  [PayloadLen]byte
	Tag      [AuthLen]byte
}

func Encode(p Packet, key []byte) []byte {
	out := make([]byte, PacketLen)

	out[0] = Magic0
	out[1] = Magic1
	out[2] = Version
	out[3] = p.Type

	binary.BigEndian.PutUint16(out[4:6], p.Flags)
	binary.BigEndian.PutUint16(out[6:8], HeaderLen)
	binary.BigEndian.PutUint16(out[8:10], PayloadLen)

	binary.BigEndian.PutUint64(out[10:18], p.Session)
	binary.BigEndian.PutUint64(out[18:26], p.Epoch)
	binary.BigEndian.PutUint64(out[26:34], p.Sequence)

	copy(out[34:50], p.Sender[:])

	binary.BigEndian.PutUint32(out[50:54], p.Lease)

	copy(out[86:118], p.Payload[:])

	mac := hmac.New(sha256.New, key)

	// Authentication tag field is zero while calculating HMAC.
	mac.Write(out[:86])
	mac.Write(out[86:118])

	copy(out[54:86], mac.Sum(nil))

	return out
}

func Decode(
	data []byte,
	key []byte,
) (Packet, error) {

	var p Packet

	if len(data) != PacketLen {
		return p, errors.New("invalid packet length")
	}

	if data[0] != Magic0 ||
		data[1] != Magic1 {
		return p, errors.New("invalid BM7 magic")
	}

	if data[2] != Version {
		return p, errors.New("unsupported BM7 version")
	}

	p.Type = data[3]

	if p.Type < MsgHello ||
		p.Type > MsgError {
		return p, errors.New("unknown message type")
	}

	if binary.BigEndian.Uint16(
		data[6:8],
	) != HeaderLen {
		return p, errors.New("invalid header length")
	}

	if binary.BigEndian.Uint16(
		data[8:10],
	) != PayloadLen {
		return p, errors.New("invalid payload length")
	}

	p.Flags = binary.BigEndian.Uint16(
		data[4:6],
	)

	p.Session = binary.BigEndian.Uint64(
		data[10:18],
	)

	p.Epoch = binary.BigEndian.Uint64(
		data[18:26],
	)

	p.Sequence = binary.BigEndian.Uint64(
		data[26:34],
	)

	copy(
		p.Sender[:],
		data[34:50],
	)

	p.Lease = binary.BigEndian.Uint32(
		data[50:54],
	)

	copy(
		p.Tag[:],
		data[54:86],
	)

	copy(
		p.Payload[:],
		data[86:118],
	)

	// Validate state.
	state := State(p.Payload[24])

	if state > StateRecovery {
		return p, errors.New("invalid state")
	}

	// Validate HMAC.
	tmp := make([]byte, len(data))
	copy(tmp, data)

	for i := 54; i < 86; i++ {
		tmp[i] = 0
	}

	mac := hmac.New(
		sha256.New,
		key,
	)

	mac.Write(tmp[:86])
	mac.Write(tmp[86:118])

	if !hmac.Equal(
		p.Tag[:],
		mac.Sum(nil),
	) {
		return p, errors.New(
			"authentication failed",
		)
	}

	return p, nil
}

// ServiceID returns the 128-bit logical service ID.
func (p Packet) ServiceID() [16]byte {
	var id [16]byte
	copy(id[:], p.Payload[:16])
	return id
}

// Priority returns the node priority.
func (p Packet) Priority() uint32 {
	return binary.BigEndian.Uint32(
		p.Payload[16:20],
	)
}

// Cost returns the network cost.
func (p Packet) Cost() uint32 {
	return binary.BigEndian.Uint32(
		p.Payload[20:24],
	)

// State returns the BM7 node state.
func (p Packet) State() State {
	return State(p.Payload[24])
}

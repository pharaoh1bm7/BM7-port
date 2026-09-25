package main

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/binary"
	"errors"
	"fmt"
	"log"
	"net"
	"time"
)

const (
	Version     = 0x01
	MsgHello    = 0x01
	HeaderLen   = 24
)

type BM7Packet struct {
	Version     byte
	MsgType     byte
	Flags       byte
	HeaderLen   byte
	SessionID   uint32
	SeqNum      uint32
	SenderID    uint32
	Epoch       uint32
	PayloadLen  uint32
	Payload     []byte
	AuthTag     []byte
}

func PackPacket(msgType, flags byte, sessionID, seqNum, senderID, epoch uint32, payload []byte, secretKey []byte) ([]byte, error) {
	payloadLen := uint32(len(payload))
	totalLen := HeaderLen + int(payloadLen) + 32 // 32 bytes for HMAC-SHA256
	buf := make([]byte, totalLen)

	buf[0] = Version
	buf[1] = msgType
	buf[2] = flags
	buf[3] = HeaderLen

	binary.BigEndian.PutUint32(buf[4:8], sessionID)
	binary.BigEndian.PutUint32(buf[8:12], seqNum)
	binary.BigEndian.PutUint32(buf[12:16], senderID)
	binary.BigEndian.PutUint32(buf[16:20], epoch)
	binary.BigEndian.PutUint32(buf[20:24], payloadLen)

	copy(buf[24:24+payloadLen], payload)

	// Compute HMAC-SHA256 over header + payload
	mac := hmac.New(sha256.New, secretKey)
	mac.Write(buf[:24+payloadLen])
	authTag := mac.Sum(nil)

	copy(buf[24+payloadLen:], authTag)
	return buf, nil
}

func UnpackPacket(data []byte, secretKey []byte) (*BM7Packet, error) {
	if len(data) < HeaderLen+32 {
		return nil, errors.New("packet too short")
	}

	payloadLen := binary.BigEndian.Uint32(data[20:24])
	expectedTotalLen := HeaderLen + int(payloadLen) + 32
	if len(data) != expectedTotalLen {
		return nil, errors.New("malformed packet length")
	}

	packetBody := data[:HeaderLen+payloadLen]
	receivedTag := data[HeaderLen+payloadLen:]

	// Verify HMAC
	mac := hmac.New(sha256.New, secretKey)
	mac.Write(packetBody)
	expectedTag := mac.Sum(nil)

	if !hmac.Equal(receivedTag, expectedTag) {
		return nil, errors.New("HMAC verification failed")
	}

	p := &BM7Packet{
		Version:    data[0],
		MsgType:    data[1],
		Flags:      data[2],
		HeaderLen:  data[3],
		SessionID:  binary.BigEndian.Uint32(data[4:8]),
		SeqNum:     binary.BigEndian.Uint32(data[8:12]),
		SenderID:   binary.BigEndian.Uint32(data[12:16]),
		Epoch:      binary.BigEndian.Uint32(data[16:20]),
		PayloadLen: payloadLen,
		Payload:    data[24 : 24+payloadLen],
		AuthTag:    receivedTag,
	}

	return p, nil
}

func main() {
	secret := []byte("bm7-secure-shared-key")
	payload := []byte("PRIORITY:200")

	pkt, err := PackPacket(MsgHello, 0x01, 9999, 1, 102, 1, payload, secret)
	if err != nil {
		log.Fatalf("Packing failed: %v", err)
	}

	fmt.Printf("Go successfully packed %d bytes\n", len(pkt))

	// Test unpacking
	unpacked, err := UnpackPacket(pkt, secret)
	if err != nil {
		log.Fatalf("Unpacking failed: %v", err)
	}

	fmt.Printf("Go unpacked packet from Sender ID: %d, Payload: %s\n", unpacked.SenderID, string(unpacked.Payload))
    _ = time.Now()
}
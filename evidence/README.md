# Evidence



------------------------------------------------------------------------------------------------------------------------------------------
BM7 demo OK
HEADER_LEN=86
PAYLOAD_LEN=32
PACKET_LEN=118
quorum=OK
deterministic-election=OK
epoch=OK
lease=OK
HMAC=OK
replay-protection=OK
active-lease-advertisement=OK
stable-election=OK
preferred-return-preemption=OK
------------------------------------------------------------------------------------------------------------------------------------------

┌──(root㉿pharaohBM7)-[~/BM7-port]
└─# python3 lab/udp_node.py --node A
[START] Node A priority=100 UDP/55001
BM7 node listening on UDP/55001
Packet size: 118 bytes
[RX] ('::1', 55002, 0, 0) HELLO epoch=0 seq=1
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=0 seq=2
[RX] ('::1', 55003, 0, 0) HELLO epoch=0 seq=1
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=0 seq=2
[RX] ('::1', 55002, 0, 0) HELLO epoch=0 seq=3
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=0 seq=4
[RX] ('::1', 55003, 0, 0) HELLO epoch=0 seq=3
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=0 seq=4
[RX] ('::1', 55002, 0, 0) HELLO epoch=0 seq=5
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=0 seq=6
[RX] ('::1', 55003, 0, 0) HELLO epoch=0 seq=5
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=0 seq=6
[RX] ('::1', 55002, 0, 0) CLAIM epoch=1 seq=7
[RX] ('::1', 55002, 0, 0) HELLO epoch=1 seq=8
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=1 seq=9
[RX] ('::1', 55003, 0, 0) HELLO epoch=1 seq=7
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=1 seq=8
[RX] ('::1', 55002, 0, 0) HELLO epoch=1 seq=10
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=1 seq=11
[RX] ('::1', 55003, 0, 0) HELLO epoch=1 seq=9
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=1 seq=10
[RX] ('::1', 55002, 0, 0) HELLO epoch=1 seq=12
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=1 seq=13
[RX] ('::1', 55003, 0, 0) HELLO epoch=1 seq=11
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=1 seq=12
[RX] ('::1', 55002, 0, 0) HELLO epoch=1 seq=14
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=1 seq=15
[RX] ('::1', 55003, 0, 0) HELLO epoch=1 seq=13
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=1 seq=14
[RX] ('::1', 55002, 0, 0) HELLO epoch=1 seq=16
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=1 seq=17
[RX] ('::1', 55003, 0, 0) HELLO epoch=1 seq=15
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=1 seq=16
[RX] ('::1', 55002, 0, 0) HELLO epoch=1 seq=18
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=1 seq=19
[RX] ('::1', 55003, 0, 0) HELLO epoch=1 seq=17
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=1 seq=18
[RX] ('::1', 55003, 0, 0) HELLO epoch=1 seq=19
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=1 seq=20
[RX] ('::1', 55003, 0, 0) HELLO epoch=1 seq=21
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=1 seq=22
[RX] ('::1', 55003, 0, 0) HELLO epoch=1 seq=23
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=1 seq=24
[RX] ('::1', 55003, 0, 0) HELLO epoch=1 seq=25
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=1 seq=26
[RX] ('::1', 55003, 0, 0) HELLO epoch=1 seq=27
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=1 seq=28
[RX] ('::1', 55003, 0, 0) HELLO epoch=1 seq=29
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=1 seq=30
[RX] ('::1', 55003, 0, 0) HELLO epoch=1 seq=31
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=1 seq=32
[RX] ('::1', 55003, 0, 0) CLAIM epoch=2 seq=33
[RX] ('::1', 55003, 0, 0) HELLO epoch=2 seq=34
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=2 seq=35
[RX] ('::1', 55003, 0, 0) HELLO epoch=2 seq=36
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=2 seq=37
[RX] ('::1', 55003, 0, 0) HELLO epoch=2 seq=38
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=2 seq=39
[RX] ('::1', 55003, 0, 0) HELLO epoch=2 seq=40
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=2 seq=41
[RX] ('::1', 55003, 0, 0) HELLO epoch=2 seq=42
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=2 seq=43
[RX] ('::1', 55003, 0, 0) HELLO epoch=2 seq=44
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=2 seq=45
[RX] ('::1', 55002, 0, 0) HELLO epoch=2 seq=3
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=2 seq=4
[RX] ('::1', 55003, 0, 0) HELLO epoch=2 seq=46
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=2 seq=47
[RX] ('::1', 55002, 0, 0) HELLO epoch=2 seq=5
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=2 seq=6
[RX] ('::1', 55003, 0, 0) HELLO epoch=2 seq=48
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=2 seq=49
[RX] ('::1', 55002, 0, 0) HELLO epoch=2 seq=7
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=2 seq=8
[RX] ('::1', 55002, 0, 0) CLAIM epoch=3 seq=9
[RX] ('::1', 55003, 0, 0) HELLO epoch=3 seq=50
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=3 seq=51
[RX] ('::1', 55002, 0, 0) HELLO epoch=3 seq=10
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=3 seq=11
[RX] ('::1', 55003, 0, 0) HELLO epoch=3 seq=52
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=3 seq=53
[RX] ('::1', 55002, 0, 0) HELLO epoch=3 seq=12
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=3 seq=13
[RX] ('::1', 55003, 0, 0) HELLO epoch=3 seq=54
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=3 seq=55
[RX] ('::1', 55002, 0, 0) HELLO epoch=3 seq=14
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=3 seq=15
[RX] ('::1', 55003, 0, 0) HELLO epoch=3 seq=56
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=3 seq=57
[RX] ('::1', 55002, 0, 0) HELLO epoch=3 seq=16
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=3 seq=17
[RX] ('::1', 55003, 0, 0) HELLO epoch=3 seq=58
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=3 seq=59
[RX] ('::1', 55002, 0, 0) HELLO epoch=3 seq=18
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=3 seq=19
[RX] ('::1', 55003, 0, 0) HELLO epoch=3 seq=60
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=3 seq=61
[RX] ('::1', 55002, 0, 0) HELLO epoch=3 seq=20
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=3 seq=21
[RX] ('::1', 55003, 0, 0) HELLO epoch=3 seq=62
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=3 seq=63
[RX] ('::1', 55002, 0, 0) HELLO epoch=3 seq=22
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=3 seq=23
[RX] ('::1', 55003, 0, 0) HELLO epoch=3 seq=64
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=3 seq=65

 ----------------------------------------------------------------------------------------------------------------------------------------                                                                                                                                                                                                                                             
┌──(root㉿pharaohBM7)-[~/BM7-port]
└─# python3 lab/udp_node.py --node B
[START] Node B priority=200 UDP/55002
BM7 node listening on UDP/55002
Packet size: 118 bytes
[RX] ('::1', 55003, 0, 0) HELLO epoch=0 seq=1
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=0 seq=2
[RX] ('::1', 55001, 0, 0) HELLO epoch=0 seq=3
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=0 seq=4
[RX] ('::1', 55003, 0, 0) HELLO epoch=0 seq=3
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=0 seq=4
[RX] ('::1', 55001, 0, 0) HELLO epoch=0 seq=5
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=0 seq=6
[RX] ('::1', 55003, 0, 0) HELLO epoch=0 seq=5
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=0 seq=6
[STATE] local node became ACTIVE epoch=1
[RX] ('::1', 55001, 0, 0) HELLO epoch=1 seq=7
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=1 seq=8
[RX] ('::1', 55003, 0, 0) HELLO epoch=1 seq=7
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=1 seq=8
[RX] ('::1', 55001, 0, 0) HELLO epoch=1 seq=9
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=1 seq=10
[RX] ('::1', 55003, 0, 0) HELLO epoch=1 seq=9
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=1 seq=10
[RX] ('::1', 55001, 0, 0) HELLO epoch=1 seq=11
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=1 seq=12
[RX] ('::1', 55003, 0, 0) HELLO epoch=1 seq=11
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=1 seq=12
[RX] ('::1', 55001, 0, 0) HELLO epoch=1 seq=13
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=1 seq=14
[RX] ('::1', 55003, 0, 0) HELLO epoch=1 seq=13
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=1 seq=14
[RX] ('::1', 55001, 0, 0) HELLO epoch=1 seq=15
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=1 seq=16
[RX] ('::1', 55003, 0, 0) HELLO epoch=1 seq=15
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=1 seq=16
[RX] ('::1', 55001, 0, 0) HELLO epoch=1 seq=17
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=1 seq=18
[RX] ('::1', 55003, 0, 0) HELLO epoch=1 seq=17
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=1 seq=18


-----------------------------------------------------------------------------------------------------------------------------------------                                                                                                
┌──(root㉿pharaohBM7)-[~/BM7-port]
└─# python3 lab/udp_node.py --node B
[START] Node B priority=200 UDP/55002
BM7 node listening on UDP/55002
Packet size: 118 bytes
[RX] ('::1', 55001, 0, 0) HELLO epoch=2 seq=43
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=2 seq=44
[RX] ('::1', 55003, 0, 0) HELLO epoch=2 seq=44
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=2 seq=45
[RX] ('::1', 55001, 0, 0) HELLO epoch=2 seq=45
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=2 seq=46
[RX] ('::1', 55003, 0, 0) HELLO epoch=2 seq=46
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=2 seq=47
[RX] ('::1', 55001, 0, 0) HELLO epoch=2 seq=47
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=2 seq=48
[RX] ('::1', 55003, 0, 0) HELLO epoch=2 seq=48
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=2 seq=49
[STATE] local node PREEMPTED owner epoch=3
[RX] ('::1', 55001, 0, 0) HELLO epoch=3 seq=49
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=3 seq=50
[RX] ('::1', 55003, 0, 0) HELLO epoch=3 seq=50
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=3 seq=51
[RX] ('::1', 55001, 0, 0) HELLO epoch=3 seq=51
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=3 seq=52
[RX] ('::1', 55003, 0, 0) HELLO epoch=3 seq=52
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=3 seq=53
[RX] ('::1', 55001, 0, 0) HELLO epoch=3 seq=53
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=3 seq=54
[RX] ('::1', 55003, 0, 0) HELLO epoch=3 seq=54
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=3 seq=55
[RX] ('::1', 55001, 0, 0) HELLO epoch=3 seq=55
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=3 seq=56
[RX] ('::1', 55003, 0, 0) HELLO epoch=3 seq=56
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=3 seq=57
[RX] ('::1', 55001, 0, 0) HELLO epoch=3 seq=57
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=3 seq=58
[RX] ('::1', 55003, 0, 0) HELLO epoch=3 seq=58
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=3 seq=59
[RX] ('::1', 55001, 0, 0) HELLO epoch=3 seq=59
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=3 seq=60
[RX] ('::1', 55003, 0, 0) HELLO epoch=3 seq=60
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=3 seq=61
[RX] ('::1', 55001, 0, 0) HELLO epoch=3 seq=61
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=3 seq=62
[RX] ('::1', 55003, 0, 0) HELLO epoch=3 seq=62
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=3 seq=63
[RX] ('::1', 55001, 0, 0) HELLO epoch=3 seq=63
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=3 seq=64

-----------------------------------------------------------------------------------------------------------------------------------------                                                                                                                       
┌──(root㉿pharaohBM7)-[~/BM7-port]
└─# python3 lab/udp_node.py --node C 
[START] Node C priority=150 UDP/55003
BM7 node listening on UDP/55003
Packet size: 118 bytes
[RX] ('::1', 55001, 0, 0) HELLO epoch=0 seq=3
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=0 seq=4
[RX] ('::1', 55002, 0, 0) HELLO epoch=0 seq=3
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=0 seq=4
[RX] ('::1', 55001, 0, 0) HELLO epoch=0 seq=5
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=0 seq=6
[RX] ('::1', 55002, 0, 0) HELLO epoch=0 seq=5
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=0 seq=6
[RX] ('::1', 55002, 0, 0) CLAIM epoch=1 seq=7
[RX] ('::1', 55001, 0, 0) HELLO epoch=1 seq=7
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=1 seq=8
[RX] ('::1', 55002, 0, 0) HELLO epoch=1 seq=8
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=1 seq=9
[RX] ('::1', 55001, 0, 0) HELLO epoch=1 seq=9
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=1 seq=10
[RX] ('::1', 55002, 0, 0) HELLO epoch=1 seq=10
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=1 seq=11
[RX] ('::1', 55001, 0, 0) HELLO epoch=1 seq=11
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=1 seq=12
[RX] ('::1', 55002, 0, 0) HELLO epoch=1 seq=12
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=1 seq=13
[RX] ('::1', 55001, 0, 0) HELLO epoch=1 seq=13
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=1 seq=14
[RX] ('::1', 55002, 0, 0) HELLO epoch=1 seq=14
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=1 seq=15
[RX] ('::1', 55001, 0, 0) HELLO epoch=1 seq=15
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=1 seq=16
[RX] ('::1', 55002, 0, 0) HELLO epoch=1 seq=16
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=1 seq=17
[RX] ('::1', 55001, 0, 0) HELLO epoch=1 seq=17
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=1 seq=18
[RX] ('::1', 55002, 0, 0) HELLO epoch=1 seq=18
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=1 seq=19
[RX] ('::1', 55001, 0, 0) HELLO epoch=1 seq=19
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=1 seq=20
[RX] ('::1', 55001, 0, 0) HELLO epoch=1 seq=21
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=1 seq=22
[RX] ('::1', 55001, 0, 0) HELLO epoch=1 seq=23
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=1 seq=24
[RX] ('::1', 55001, 0, 0) HELLO epoch=1 seq=25
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=1 seq=26
[RX] ('::1', 55001, 0, 0) HELLO epoch=1 seq=27
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=1 seq=28
[RX] ('::1', 55001, 0, 0) HELLO epoch=1 seq=29
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=1 seq=30
[RX] ('::1', 55001, 0, 0) HELLO epoch=1 seq=31
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=1 seq=32
[STATE] local node became ACTIVE epoch=2
[RX] ('::1', 55001, 0, 0) HELLO epoch=2 seq=33
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=2 seq=34
[RX] ('::1', 55001, 0, 0) HELLO epoch=2 seq=35
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=2 seq=36
[RX] ('::1', 55001, 0, 0) HELLO epoch=2 seq=37
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=2 seq=38
[RX] ('::1', 55001, 0, 0) HELLO epoch=2 seq=39
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=2 seq=40
[RX] ('::1', 55001, 0, 0) HELLO epoch=2 seq=41
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=2 seq=42
[RX] ('::1', 55001, 0, 0) HELLO epoch=2 seq=43
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=2 seq=44
[RX] ('::1', 55002, 0, 0) HELLO epoch=2 seq=3
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=2 seq=4
[RX] ('::1', 55001, 0, 0) HELLO epoch=2 seq=45
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=2 seq=46
[RX] ('::1', 55002, 0, 0) HELLO epoch=2 seq=5
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=2 seq=6
[RX] ('::1', 55001, 0, 0) HELLO epoch=2 seq=47
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=2 seq=48
[RX] ('::1', 55002, 0, 0) HELLO epoch=2 seq=7
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=2 seq=8
[RX] ('::1', 55002, 0, 0) CLAIM epoch=3 seq=9
[RX] ('::1', 55001, 0, 0) HELLO epoch=3 seq=49
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=3 seq=50
[RX] ('::1', 55002, 0, 0) HELLO epoch=3 seq=10
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=3 seq=11
[RX] ('::1', 55001, 0, 0) HELLO epoch=3 seq=51
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=3 seq=52
[RX] ('::1', 55002, 0, 0) HELLO epoch=3 seq=12
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=3 seq=13
[RX] ('::1', 55001, 0, 0) HELLO epoch=3 seq=53
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=3 seq=54
[RX] ('::1', 55002, 0, 0) HELLO epoch=3 seq=14
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=3 seq=15
[RX] ('::1', 55001, 0, 0) HELLO epoch=3 seq=55
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=3 seq=56
[RX] ('::1', 55002, 0, 0) HELLO epoch=3 seq=16
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=3 seq=17
[RX] ('::1', 55001, 0, 0) HELLO epoch=3 seq=57
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=3 seq=58
[RX] ('::1', 55002, 0, 0) HELLO epoch=3 seq=18
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=3 seq=19
[RX] ('::1', 55001, 0, 0) HELLO epoch=3 seq=59
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=3 seq=60
[RX] ('::1', 55002, 0, 0) HELLO epoch=3 seq=20
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=3 seq=21
[RX] ('::1', 55001, 0, 0) HELLO epoch=3 seq=61
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=3 seq=62
[RX] ('::1', 55002, 0, 0) HELLO epoch=3 seq=22
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=3 seq=23
[RX] ('::1', 55001, 0, 0) HELLO epoch=3 seq=63
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=3 seq=64





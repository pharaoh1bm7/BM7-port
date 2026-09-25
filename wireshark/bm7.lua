-- Minimal BM7 v1 Wireshark dissector.
local bm7 = Proto("bm7", "BM7 Branch Mobility and Failover Protocol")
local f_magic=ProtoField.string("bm7.magic","Magic")
local f_version=ProtoField.uint8("bm7.version","Version",base.DEC)
local f_type=ProtoField.uint8("bm7.type","Message Type",base.DEC)
local f_flags=ProtoField.uint16("bm7.flags","Flags",base.HEX)
local f_epoch=ProtoField.uint64("bm7.epoch","Epoch",base.DEC)
local f_seq=ProtoField.uint64("bm7.sequence","Sequence",base.DEC)
bm7.fields={f_magic,f_version,f_type,f_flags,f_epoch,f_seq}
function bm7.dissector(buf,pinfo,tree)
 if buf:len()<86 or buf(0,2):string()~="B7" then return 0 end
 pinfo.cols.protocol="BM7"; local t=tree:add(bm7,buf(),"BM7")
 t:add(f_magic,buf(0,2)); t:add(f_version,buf(2,1)); t:add(f_type,buf(3,1)); t:add(f_flags,buf(4,2)); t:add(f_epoch,buf(18,8)); t:add(f_seq,buf(26,8)); return buf:len()
end
DissectorTable.get("udp.port"):add(55000,bm7)

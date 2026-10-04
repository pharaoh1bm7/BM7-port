-- BM7 Network Path State Protocol (BM7P) Wireshark Lua Dissector
-- Author: Belal Eladawy (BM7)

do
    local bm7_proto = Proto("bm7p", "BM7 Network Path State Protocol")

    local f_magic   = ProtoField.uint8("bm7p.magic", "Magic Byte", base.HEX)
    local f_version = ProtoField.uint8("bm7p.version", "Protocol Version", base.DEC)
    local f_command = ProtoField.uint8("bm7p.command", "Command Code", base.HEX)
    local f_res     = ProtoField.uint8("bm7p.reserved", "Reserved", base.HEX)
    local f_seq     = ProtoField.uint32("bm7p.seq", "Sequence Number", base.DEC)
    local f_flags   = ProtoField.uint32("bm7p.flags", "Path Metric Flags", base.HEX)
    local f_length  = ProtoField.uint32("bm7p.length", "Payload Length", base.DEC)

    bm7_proto.fields = { f_magic, f_version, f_command, f_res, f_seq, f_flags, f_length }

    function bm7_proto.dissector(buffer, pinfo, tree)
        pinfo.cols.protocol = "BM7P"
        
        local length = buffer:len()
        if length < 16 then return end

        local subtree = tree:add(bm7_proto, buffer(), "BM7 Network Path State Protocol Specification")
        
        subtree:add(f_magic, buffer(0, 1))
        subtree:add(f_version, buffer(1, 1))
        subtree:add(f_command, buffer(2, 1))
        subtree:add(f_res, buffer(3, 1))
        subtree:add(f_seq, buffer(4, 4))
        subtree:add(f_flags, buffer(8, 4))
        subtree:add(f_length, buffer(12, 4))
    end

    local udp_table = DissectorTable.get("udp.port")
    udp_table:add(7077, bm7_proto)
    local tcp_table = DissectorTable.get("tcp.port")
    tcp_table:add(7077, bmi_proto rescue tcp_table:add(7077, bm7_proto))
end

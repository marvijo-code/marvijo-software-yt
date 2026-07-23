import pytest
from dnscodec import parse_packet, build_query

# Response for www.example.com with a CNAME chain using nested compression:
#   answer1 name = ptr->question name; its CNAME rdata = "cdn" + ptr->"example.com"
#   answer2 name = ptr->answer1's rdata name ("cdn.example.com"), A 1.2.3.4
RESPONSE = bytes.fromhex(
    "1234" "8180" "0001" "0002" "0000" "0000"
    "03777777" "076578616d706c65" "03636f6d" "00" "0001" "0001"
    "c00c" "0005" "0001" "0000003c" "0006" "0363646e" "c010"
    "c02d" "0001" "0001" "0000003c" "0004" "01020304"
)


def test_header_and_flags():
    p = parse_packet(RESPONSE)
    assert p["id"] == 0x1234
    f = p["flags"]
    assert f["qr"] is True and f["rd"] is True and f["ra"] is True
    assert f["aa"] is False and f["tc"] is False
    assert f["opcode"] == 0 and f["rcode"] == 0


def test_question_parsing():
    p = parse_packet(RESPONSE)
    assert p["questions"] == [
        {"name": "www.example.com", "qtype": 1, "qclass": 1}]


def test_answer_compressed_names_and_cname_rdata():
    p = parse_packet(RESPONSE)
    a1 = p["answers"][0]
    assert a1["name"] == "www.example.com"
    assert a1["type"] == 5 and a1["class"] == 1 and a1["ttl"] == 60
    assert a1["rdata"] == "cdn.example.com"


def test_answer_nested_pointer_chain_and_a_record():
    p = parse_packet(RESPONSE)
    a2 = p["answers"][1]
    assert a2["name"] == "cdn.example.com"  # ptr -> label+ptr chain
    assert a2["type"] == 1
    assert a2["rdata"] == "1.2.3.4"


def test_unknown_type_rdata_raw_bytes():
    pkt = bytes.fromhex(
        "0001" "8000" "0000" "0001" "0000" "0000"
        "03616263" "00" "0010" "0001" "00000001" "0003" "aabbcc"
    )
    p = parse_packet(pkt)
    a = p["answers"][0]
    assert a["name"] == "abc"
    assert a["type"] == 16
    assert a["rdata"] == bytes.fromhex("aabbcc")


def test_self_pointer_loop_raises():
    pkt = bytes.fromhex(
        "0001" "0000" "0001" "0000" "0000" "0000"
        "c00c" "0001" "0001")
    with pytest.raises(ValueError):
        parse_packet(pkt)


def test_forward_pointer_raises():
    pkt = bytes.fromhex(
        "0001" "0000" "0001" "0000" "0000" "0000"
        "c020" "0001" "0001")
    with pytest.raises(ValueError):
        parse_packet(pkt)


def test_truncated_label_raises():
    pkt = bytes.fromhex(
        "0001" "0000" "0001" "0000" "0000" "0000"
        "07" "777777")  # label claims 7 bytes, only 3 present
    with pytest.raises(ValueError):
        parse_packet(pkt)


def test_truncated_header_raises():
    with pytest.raises(ValueError):
        parse_packet(bytes.fromhex("123481"))


def test_oversized_label_raises():
    hdr = bytes.fromhex("0001" "0000" "0001" "0000" "0000" "0000")
    body = bytes([0x46]) + b"a" * 70 + b"\x00" + bytes.fromhex("0001" "0001")
    with pytest.raises(ValueError):
        parse_packet(hdr + body)


def test_build_query_bytes_exact():
    q = build_query(0xBEEF, "example.org", 1)
    assert q[:2] == bytes.fromhex("beef")
    assert q[2:4] == bytes.fromhex("0100")
    assert q[4:6] == bytes.fromhex("0001")
    assert q[12:] == (b"\x07example\x03org\x00" + bytes.fromhex("0001" "0001"))


def test_build_query_round_trip():
    p = parse_packet(build_query(7, "a.b.co", 28))
    assert p["id"] == 7
    assert p["flags"]["rd"] is True and p["flags"]["qr"] is False
    assert p["questions"] == [{"name": "a.b.co", "qtype": 28, "qclass": 1}]
    assert p["answers"] == []

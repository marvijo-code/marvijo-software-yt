"""DNS wire-format codec (RFC 1035 subset)."""


def _parse_name(data, offset):
    """Parse a (possibly compressed) name starting at offset.

    Returns (name_str, next_offset) where next_offset is the position in the
    original stream immediately after the name (i.e. after the first pointer,
    or after the terminating zero label if no pointer was followed).
    Raises ValueError on truncation, backward-violating pointers, or bad
    label lengths.
    """
    labels = []
    pos = offset
    next_offset = None
    n = len(data)
    while True:
        if pos >= n:
            raise ValueError("truncated name")
        length = data[pos]
        top2 = length & 0xC0
        if top2 == 0x00:
            if length == 0:
                pos += 1
                if next_offset is None:
                    next_offset = pos
                break
            end = pos + 1 + length
            if end > n:
                raise ValueError("truncated label")
            labels.append(data[pos + 1:end].decode("latin-1"))
            pos = end
        elif top2 == 0xC0:
            if pos + 1 >= n:
                raise ValueError("truncated pointer")
            target = ((length & 0x3F) << 8) | data[pos + 1]
            if next_offset is None:
                next_offset = pos + 2
            # Must point STRICTLY BACKWARD relative to the pointer byte.
            if target >= pos:
                raise ValueError("non-backward pointer")
            pos = target
        else:
            # top2 == 0x40 or 0x80 -> label length > 63, illegal.
            raise ValueError("bad label length")
    return ".".join(labels), next_offset


def parse_packet(data: bytes) -> dict:
    if len(data) < 12:
        raise ValueError("truncated header")

    qid = int.from_bytes(data[0:2], "big")
    flags_raw = int.from_bytes(data[2:4], "big")
    qdcount = int.from_bytes(data[4:6], "big")
    ancount = int.from_bytes(data[6:8], "big")

    flags = {
        "qr": bool((flags_raw >> 15) & 1),
        "opcode": (flags_raw >> 11) & 0xF,
        "aa": bool((flags_raw >> 10) & 1),
        "tc": bool((flags_raw >> 9) & 1),
        "rd": bool((flags_raw >> 8) & 1),
        "ra": bool((flags_raw >> 7) & 1),
        "rcode": flags_raw & 0xF,
    }

    n = len(data)
    pos = 12

    questions = []
    for _ in range(qdcount):
        name, pos = _parse_name(data, pos)
        if pos + 4 > n:
            raise ValueError("truncated question")
        qtype = int.from_bytes(data[pos:pos + 2], "big")
        qclass = int.from_bytes(data[pos + 2:pos + 4], "big")
        pos += 4
        questions.append({"name": name, "qtype": qtype, "qclass": qclass})

    answers = []
    for _ in range(ancount):
        name, pos = _parse_name(data, pos)
        if pos + 10 > n:
            raise ValueError("truncated answer")
        rtype = int.from_bytes(data[pos:pos + 2], "big")
        rclass = int.from_bytes(data[pos + 2:pos + 4], "big")
        ttl = int.from_bytes(data[pos + 4:pos + 8], "big")
        rdlength = int.from_bytes(data[pos + 8:pos + 10], "big")
        pos += 10
        rdstart = pos
        if rdstart + rdlength > n:
            raise ValueError("truncated rdata")
        rdraw = data[rdstart:rdstart + rdlength]

        if rtype == 1:
            if rdlength != 4:
                raise ValueError("bad A rdata length")
            rdata = ".".join(str(b) for b in rdraw)
        elif rtype == 5:
            rdata, _ = _parse_name(data, rdstart)
        else:
            rdata = rdraw

        pos = rdstart + rdlength
        answers.append({
            "name": name,
            "type": rtype,
            "class": rclass,
            "ttl": ttl,
            "rdata": rdata,
        })

    return {
        "id": qid,
        "flags": flags,
        "questions": questions,
        "answers": answers,
    }


def build_query(qid: int, name: str, qtype: int) -> bytes:
    header = b"".join([
        qid.to_bytes(2, "big"),
        (0x0100).to_bytes(2, "big"),
        (1).to_bytes(2, "big"),
        (0).to_bytes(2, "big"),
        (0).to_bytes(2, "big"),
        (0).to_bytes(2, "big"),
    ])

    qname = bytearray()
    if name:
        for label in name.split("."):
            enc = label.encode("latin-1")
            if len(enc) > 63:
                raise ValueError("label too long")
            qname.append(len(enc))
            qname.extend(enc)
    qname.append(0)

    question = bytes(qname) + qtype.to_bytes(2, "big") + (1).to_bytes(2, "big")
    return header + question

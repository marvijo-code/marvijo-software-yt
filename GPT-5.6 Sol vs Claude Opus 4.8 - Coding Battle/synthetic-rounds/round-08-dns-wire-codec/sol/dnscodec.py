"""Small DNS wire-format encoder/decoder for the RFC 1035 subset in task.md."""

from __future__ import annotations

import struct


_HEADER = struct.Struct("!HHHHHH")
_QUESTION_TAIL = struct.Struct("!HH")
_RR_FIXED = struct.Struct("!HHIH")


def _read_name(data: bytes, offset: int, direct_end: int | None = None) -> tuple[str, int]:
    """Decode a possibly compressed name and return (name, continuation offset).

    ``direct_end`` limits the bytes belonging to the name at its original
    location (used for a name stored in RDATA).  Once a compression pointer is
    followed, its target is bounded by the complete DNS message instead.
    """

    message_end = len(data)
    if direct_end is None:
        direct_end = message_end
    if offset < 0 or offset >= direct_end or direct_end > message_end:
        raise ValueError("truncated name")

    labels: list[str] = []
    position = offset
    continuation: int | None = None
    limit = direct_end
    visited: set[int] = set()

    while True:
        if position >= limit:
            raise ValueError("truncated name")
        if position in visited:
            raise ValueError("compression pointer loop")
        visited.add(position)

        length = data[position]
        tag = length & 0xC0

        if tag == 0xC0:
            if position + 2 > limit:
                raise ValueError("truncated compression pointer")
            target = ((length & 0x3F) << 8) | data[position + 1]
            if target >= position:
                raise ValueError("compression pointer must point backward")
            if continuation is None:
                continuation = position + 2
            position = target
            limit = message_end
            continue

        if tag:
            raise ValueError("label length exceeds 63 bytes")

        position += 1
        if length == 0:
            if continuation is None:
                continuation = position
            return ".".join(labels), continuation

        label_end = position + length
        if label_end > limit:
            raise ValueError("truncated label")
        try:
            labels.append(data[position:label_end].decode("ascii"))
        except UnicodeDecodeError as exc:
            raise ValueError("non-ASCII label") from exc
        position = label_end


def _need(data: bytes, offset: int, size: int, what: str) -> None:
    if offset < 0 or size < 0 or offset + size > len(data):
        raise ValueError(f"truncated {what}")


def parse_packet(data: bytes) -> dict:
    """Parse a DNS packet containing questions and answers."""

    if not isinstance(data, bytes):
        raise ValueError("data must be bytes")
    _need(data, 0, _HEADER.size, "header")
    qid, flags_word, qdcount, ancount, _nscount, _arcount = _HEADER.unpack_from(data)

    result = {
        "id": qid,
        "flags": {
            "qr": bool(flags_word & 0x8000),
            "opcode": (flags_word >> 11) & 0xF,
            "aa": bool(flags_word & 0x0400),
            "tc": bool(flags_word & 0x0200),
            "rd": bool(flags_word & 0x0100),
            "ra": bool(flags_word & 0x0080),
            "rcode": flags_word & 0xF,
        },
        "questions": [],
        "answers": [],
    }

    offset = _HEADER.size
    for _ in range(qdcount):
        name, offset = _read_name(data, offset)
        _need(data, offset, _QUESTION_TAIL.size, "question fields")
        qtype, qclass = _QUESTION_TAIL.unpack_from(data, offset)
        offset += _QUESTION_TAIL.size
        result["questions"].append(
            {"name": name, "qtype": qtype, "qclass": qclass}
        )

    for _ in range(ancount):
        name, offset = _read_name(data, offset)
        _need(data, offset, _RR_FIXED.size, "answer fields")
        rtype, rclass, ttl, rdlength = _RR_FIXED.unpack_from(data, offset)
        offset += _RR_FIXED.size
        _need(data, offset, rdlength, "rdata")
        rdata_end = offset + rdlength

        if rtype == 1:
            if rdlength != 4:
                raise ValueError("A record rdata must be four bytes")
            rdata = ".".join(str(octet) for octet in data[offset:rdata_end])
        elif rtype == 5:
            rdata, consumed_to = _read_name(data, offset, rdata_end)
            if consumed_to != rdata_end:
                raise ValueError("CNAME rdata length does not match encoded name")
        else:
            rdata = data[offset:rdata_end]

        offset = rdata_end
        result["answers"].append(
            {
                "name": name,
                "type": rtype,
                "class": rclass,
                "ttl": ttl,
                "rdata": rdata,
            }
        )

    return result


def build_query(qid: int, name: str, qtype: int) -> bytes:
    """Build one recursive IN-class DNS question without compression."""

    if not isinstance(qid, int) or not 0 <= qid <= 0xFFFF:
        raise ValueError("qid must be an unsigned 16-bit integer")
    if not isinstance(qtype, int) or not 0 <= qtype <= 0xFFFF:
        raise ValueError("qtype must be an unsigned 16-bit integer")
    if not isinstance(name, str):
        raise ValueError("name must be a string")

    encoded_name = bytearray()
    if name:
        for label in name.split("."):
            if not label:
                raise ValueError("name contains an empty label")
            try:
                encoded_label = label.encode("ascii")
            except UnicodeEncodeError as exc:
                raise ValueError("name labels must be ASCII") from exc
            if len(encoded_label) > 63:
                raise ValueError("label length exceeds 63 bytes")
            encoded_name.append(len(encoded_label))
            encoded_name.extend(encoded_label)
    encoded_name.append(0)

    # A wire-format DNS name, including its root terminator, is at most 255
    # bytes.  Enforce that limit even though parsing only needs the label limit.
    if len(encoded_name) > 255:
        raise ValueError("encoded name exceeds 255 bytes")

    header = _HEADER.pack(qid, 0x0100, 1, 0, 0, 0)
    return header + bytes(encoded_name) + _QUESTION_TAIL.pack(qtype, 1)

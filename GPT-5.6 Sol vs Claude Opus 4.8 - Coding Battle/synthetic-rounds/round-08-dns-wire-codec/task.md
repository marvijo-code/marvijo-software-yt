# Task: DNS wire-format codec (RFC 1035 subset)

Create `dnscodec.py` in this directory exporting:

```python
def parse_packet(data: bytes) -> dict
def build_query(qid: int, name: str, qtype: int) -> bytes
```

## parse_packet
Returns:
```python
{
  "id": int,
  "flags": {"qr": bool, "opcode": int, "aa": bool, "tc": bool,
             "rd": bool, "ra": bool, "rcode": int},
  "questions": [{"name": str, "qtype": int, "qclass": int}],
  "answers":   [{"name": str, "type": int, "class": int, "ttl": int,
                  "rdata": ...}],
}
```
- Test packets always have NSCOUNT = ARCOUNT = 0 (you may ignore those
  sections). QDCOUNT/ANCOUNT govern how many entries to parse.
- **Names**: dot-joined labels, no trailing dot (root = ""). Case
  preserved. Standard message compression MUST be supported: a length
  byte with top bits `11` is a 14-bit pointer to a prior offset; pointers
  can appear after labels and can chain (a pointed-to name may itself
  contain a pointer).
- **rdata** by record type: type 1 (A) -> dotted-quad string
  ("1.2.3.4"); type 5 (CNAME) -> the decompressed name string; any other
  type -> the raw rdata bytes.

### Robustness (all must raise `ValueError`)
- Any compression pointer that does not point STRICTLY BACKWARD (target
  offset < offset of the pointer byte itself) - this also kills loops.
- Truncated data anywhere (header, labels, fixed fields, rdata).
- A label longer than 63 bytes (length byte with top bits `01` or `10`).

## build_query
Standard query: header with the given id, flags = RD only
(0x0100), QDCOUNT=1, other counts 0; the question with the given name
(no compression needed) and qtype, qclass = 1 (IN).
`parse_packet(build_query(...))` must round-trip.

Python 3.13 stdlib only. Work only in this directory. Hidden tests use
hand-crafted byte fixtures, including nested compression chains and
malicious packets. Hard cap: finish within 10 minutes.

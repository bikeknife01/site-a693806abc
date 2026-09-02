import sys, json, struct

def read_varint(buf, i):
    result = 0
    shift = 0
    while True:
        b = buf[i]
        i += 1
        result |= (b & 0x7f) << shift
        if not (b & 0x80):
            break
        shift += 7
    return result, i

def try_decode_string(b):
    try:
        s = b.decode('utf-8')
        if all(32 <= ord(c) < 127 or c in '\n\r\t' for c in s):
            return s
    except Exception:
        pass
    return None

def parse_message(buf, start, end, depth=0):
    fields = {}
    i = start
    while i < end:
        tag, i = read_varint(buf, i)
        field_no = tag >> 3
        wire_type = tag & 0x7
        val = None
        if wire_type == 0:  # varint
            val, i = read_varint(buf, i)
        elif wire_type == 1:  # 64-bit
            raw = buf[i:i+8]
            i += 8
            d = struct.unpack('<d', raw)[0]
            l = struct.unpack('<q', raw)[0]
            val = {"_fixed64_double": d, "_fixed64_int": l}
        elif wire_type == 2:  # length-delimited
            ln, i = read_varint(buf, i)
            chunk = buf[i:i+ln]
            i += ln
            s = try_decode_string(chunk)
            if s is not None:
                val = s
            else:
                try:
                    nested = parse_message(chunk, 0, len(chunk), depth+1)
                    val = nested if nested else chunk.hex()
                except Exception:
                    val = chunk.hex()
        elif wire_type == 5:  # 32-bit
            raw = buf[i:i+4]
            i += 4
            f = struct.unpack('<f', raw)[0]
            l = struct.unpack('<i', raw)[0]
            val = {"_fixed32_float": f, "_fixed32_int": l}
        else:
            raise ValueError(f"unsupported wiretype {wire_type} at {i}")
        fields.setdefault(str(field_no), []).append(val)
    return fields

def dump_file(path, max_top=None):
    data = open(path, 'rb').read()
    parsed = parse_message(data, 0, len(data))
    # unwrap single-list fields for readability
    def unwrap(v):
        if isinstance(v, dict):
            if any(k.startswith('_fixed') for k in v):
                return v
            out = {}
            for k, lst in v.items():
                items = [unwrap(x) for x in lst]
                out[k] = items if len(items) != 1 else items[0]
            return out
        return v
    result = unwrap(parsed)
    if max_top and '1' in result and isinstance(result['1'], list):
        result['1'] = result['1'][:max_top]
    return result

if __name__ == '__main__':
    path = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    result = dump_file(path, limit)
    print(json.dumps(result, indent=2, ensure_ascii=False))

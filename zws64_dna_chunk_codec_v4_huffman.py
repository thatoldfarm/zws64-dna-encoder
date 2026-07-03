# zws64_dna_chunk_codec_v4_huffman.py
#
# Big improvement in final size:
#   text -> gzip (bytes) -> base64 (64-symbol alphabet) -> HUFFMAN over the 64 symbols
#   -> bitstream -> map bits to DNA4 (00=A,01=C,10=G,11=T) -> INNER json
#   -> gzip+base64url -> OUTER chunks.json {"chunks": [...]}
#
# Decode reverses it via canonical Huffman using only code lengths.
# Storing only 64 code lengths (and original b64 symbol count) is tiny, and
# it keeps the “ZWS64-equivalent” semantics (we’re compressing the same 64-code alphabet
# ZWS64 would map, but without expanding into ZWS triplets).
#
# Usage:
#   python3 zws64_dna_chunk_codec_v4_huffman.py encode input.txt chunks.json [--chunk 1500]
#   python3 zws64_dna_chunk_codec_v4_huffman.py decode chunks.json output.txt

import sys, json, gzip, base64
from collections import Counter
from typing import Dict, List, Tuple

B64_ALPH = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
SYMBOLS = list(B64_ALPH)
SYM2IDX = {ch:i for i,ch in enumerate(SYMBOLS)}

# DNA mapping for bits
BIT2DNA = {'00':'A','01':'C','10':'G','11':'T'}
DNA2BIT = {'A':'00','C':'01','G':'10','T':'11'}

# --------- Huffman (canonical) ---------
class Node:
    __slots__ = ('w','sym','left','right')
    def __init__(self, w, sym=None, left=None, right=None):
        self.w=w; self.sym=sym; self.left=left; self.right=right
    def __lt__(self, other):
        if self.w!=other.w: return self.w<other.w
        # tie-break deterministically by symbol id if both leaves
        a = self.sym if self.sym is not None else 1e9
        b = other.sym if other.sym is not None else 1e9
        return a<b

def build_huffman_lengths(freqs: List[int]) -> List[int]:
    """Return canonical code lengths (per symbol index 0..63)."""
    import heapq
    heap=[]
    for i,f in enumerate(freqs):
        if f>0:
            heapq.heappush(heap, Node(f, sym=i))
    if len(heap)==0:
        # degenerate: no data, assign length 1 to symbol 0
        return [1]+[0]*63
    if len(heap)==1:
        # single symbol: give it length 1
        i = heap[0].sym
        L=[0]*64; L[i]=1
        return L
    while len(heap)>1:
        a=heapq.heappop(heap); b=heapq.heappop(heap)
        heapq.heappush(heap, Node(a.w+b.w, left=a, right=b))
    # traverse to get lengths
    L=[0]*64
    def dfs(n, d):
        if n.sym is not None:
            L[n.sym]=max(1,d)
            return
        dfs(n.left, d+1); dfs(n.right, d+1)
    dfs(heap[0],0)
    return L


def canonical_codes_from_lengths(lengths: List[int]) -> Dict[int, Tuple[int,int]]:
    """Return dict: sym_idx -> (code, bitlen) using canonical assignment."""
    # group by length
    maxlen = max(lengths) if lengths else 0
    bl_count = [0]*(maxlen+1)
    for l in lengths:
        if l>0: bl_count[l]+=1
    code=0
    next_code=[0]*(maxlen+1)
    for bits in range(1,maxlen+1):
        code = (code + bl_count[bits-1]) << 1
        next_code[bits]=code
    table={}
    # assign codes in order of (length, symbol index)
    for sym in range(len(lengths)):
        l=lengths[sym]
        if l>0:
            table[sym]=(next_code[l], l)
            next_code[l]+=1
    return table

# --------- Bit/DNA utils ---------

def bits_to_dna(bits: str) -> str:
    if len(bits)%2==1:
        bits+='0'  # pad to even length for DNA pairs
    out=[]
    for i in range(0,len(bits),2):
        out.append(BIT2DNA[bits[i:i+2]])
    return ''.join(out)

def dna_to_bits(dna: str) -> str:
    return ''.join(DNA2BIT[ch] for ch in dna)

# --------- Outer pack/unpack ---------

def pack_chunks(data: bytes, chunk_size: int) -> dict:
    gz = gzip.compress(data)
    b64url = base64.urlsafe_b64encode(gz).decode('utf-8')
    chunks = [b64url[i:i+chunk_size] for i in range(0,len(b64url),chunk_size)]
    return {"chunks": chunks}

def unpack_chunks(obj: dict) -> bytes:
    b64url = ''.join(obj.get('chunks', []))
    missing = len(b64url)%4
    if missing: b64url += '='*(4-missing)
    gz = base64.urlsafe_b64decode(b64url.encode('utf-8'))
    return gzip.decompress(gz)

# --------- Encode/Decode ---------

def encode_file_to_chunks(text: str, chunk_size: int=1500) -> dict:
    # 1) gzip bytes, then Base64 (standard alphabet)
    gz = gzip.compress(text.encode('utf-8'))
    b64 = base64.b64encode(gz).decode('utf-8')
    # 2) frequencies over 64 symbols (skip '=')
    freqs=[0]*64
    for ch in b64:
        if ch=='=': continue
        freqs[SYM2IDX[ch]] += 1
    # 3) canonical lengths + codes
    lengths = build_huffman_lengths(freqs)
    codes = canonical_codes_from_lengths(lengths)
    # 4) encode to bitstream
    bits=[]
    for ch in b64:
        if ch=='=': continue
        code, bl = codes[SYM2IDX[ch]]
        bits.append(format(code, 'b').zfill(bl))
    bitstream=''.join(bits)
    # 5) bits -> DNA
    dna = bits_to_dna(bitstream)
    # 6) inner json (tiny): include lengths and original b64 symbol count for termination
    inner = {
        'schema':'huff-b64-dna-v1',
        'b64_len': len(b64.replace('=','')),
        'lengths': lengths,     # 64 ints (0..maxL)
        'dna': dna
    }
    inner_bytes = json.dumps(inner, separators=(',',':')).encode('utf-8')
    # 7) pack to outer chunks
    return pack_chunks(inner_bytes, chunk_size)


def decode_chunks_to_text(obj: dict) -> str:
    inner_bytes = unpack_chunks(obj)
    inner = json.loads(inner_bytes.decode('utf-8'))
    assert inner.get('schema')=='huff-b64-dna-v1'
    b64_len = int(inner['b64_len'])
    lengths = inner['lengths']
    dna = inner['dna']
    # rebuild canonical code tables
    codes = canonical_codes_from_lengths(lengths)
    # build reverse map: (bitstring)->symbol index, using dict of dict by length
    inv_by_len = {}
    for sym,(code,bl) in codes.items():
        inv_by_len.setdefault(bl, {})[format(code,'b').zfill(bl)] = sym
    maxL = max(inv_by_len) if inv_by_len else 1
    # DNA -> bits
    bits = dna_to_bits(dna)
    # parse variable-length codes
    out_syms=[]
    i=0
    while len(out_syms) < b64_len and i < len(bits):
        # progressively read up to maxL bits
        acc=''
        for L in range(1, maxL+1):
            if i+L>len(bits): break
            acc = bits[i:i+L]
            table=inv_by_len.get(L)
            if table and acc in table:
                out_syms.append(SYMBOLS[table[acc]])
                i += L
                break
        else:
            # no match; stop decoding (corruption?)
            break
    b64_no_pad = ''.join(out_syms)
    # fix padding
    missing = len(b64_no_pad) % 4
    if missing: b64_no_pad += '='*(4-missing)
    gz = base64.b64decode(b64_no_pad.encode('utf-8'))
    text = gzip.decompress(gz).decode('utf-8')
    return text

# --------- CLI ---------
if __name__=='__main__':
    if len(sys.argv)<4:
        print('Usage: python3 zws64_dna_chunk_codec_v4_huffman.py encode <input.txt> <chunks.json> [--chunk 1500]')
        print('       python3 zws64_dna_chunk_codec_v4_huffman.py decode <chunks.json> <output.txt>')
        sys.exit(1)
    mode, A, B = sys.argv[1], sys.argv[2], sys.argv[3]
    if mode=='encode':
        chunk=1500
        if '--chunk' in sys.argv:
            i=sys.argv.index('--chunk'); chunk=int(sys.argv[i+1])
        text=open(A,'r',encoding='utf-8').read()
        obj=encode_file_to_chunks(text, chunk_size=chunk)
        open(B,'w',encoding='utf-8').write(json.dumps(obj, separators=(',',':')))
        print(f"Wrote {len(obj['chunks'])} chunks to {B} (huffman over base64)")
    else:
        obj=json.load(open(A,'r',encoding='utf-8'))
        out=decode_chunks_to_text(obj)
        open(B,'w',encoding='utf-8').write(out)
        print(f"Decoded to {B}")


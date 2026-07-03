# zws64-dna-encoder

**A High-Efficiency Text-to-DNA Encoding Tool**

---

## 🌌 Overview

`zws64-dna-encoder` is a **lossless, ultra-compact encoding tool** that converts arbitrary text into DNA sequences using a **multi-stage compression pipeline**. It leverages **Huffman coding over a 64-symbol alphabet** (Base64) to maximize compression efficiency before mapping to DNA (A, C, G, T). The result is a **highly optimized, chunked JSON output** that can be stored, transmitted, or embedded in images, blockchains, or other media.

This tool is designed for:

- **Steganography** (hiding data in plain sight)
- **Biological data storage** (DNA synthesis)
- **Blockchain anchoring** (immutable data storage)
- **Ultra-compact archival** (minimal storage footprint)

---

## 🔧 Encoding Pipeline

The encoding process follows this **7-stage pipeline**:

```
text 
  → gzip (bytes) 
  → base64 (64-symbol alphabet) 
  → Huffman coding (over 64 symbols) 
  → bitstream 
  → DNA4 mapping (00=A, 01=C, 10=G, 11=T) 
  → INNER JSON (metadata + DNA) 
  → gzip + base64url 
  → OUTER chunks.json {"chunks": [...]}
```

### Key Features

- **Canonical Huffman Coding**: Uses only **code lengths** (not full trees) for minimal metadata overhead.
- **DNA4 Mapping**: Efficient 2-bit → DNA nucleotide conversion.
- **Chunked Output**: Splits encoded data into configurable chunks for easy storage/transmission.
- **Lossless Decoding**: Perfect reconstruction of original text.

---

## 🚀 Usage

### **Encode a Text File to DNA Chunks**

```bash
python3 zws64_dna_chunk_codec_v4_huffman.py encode input.txt chunks.json [--chunk 1500]
```

- `input.txt`: Your source text file.
- `chunks.json`: Output file containing DNA-encoded chunks.
- `--chunk 1500`: (Optional) Chunk size in characters (default: 1500).

### **Decode DNA Chunks Back to Text**

```bash
python3 zws64_dna_chunk_codec_v4_huffman.py decode chunks.json output.txt
```

- `chunks.json`: Encoded input file.
- `output.txt`: Decoded text file (identical to original).

---

## 📦 Example

### **Encoding**

```bash
# Encode a book into DNA chunks
python3 zws64_dna_chunk_codec_v4_huffman.py encode war_and_peace.txt dna_chunks.json --chunk 2000
```

### **Decoding**

```bash
# Decode back to original text
python3 zws64_dna_chunk_codec_v4_huffman.py decode dna_chunks.json war_and_peace_restored.txt
```

---

## 🔍 Technical Details

### **1. Base64 Alphabet**

- Uses standard Base64 symbols (`A-Z`, `a-z`, `0-9`, `+`, `/`).
- Padding (`=`) is **ignored** during Huffman coding but restored for decoding.

### **2. Huffman Coding**

- **Canonical Huffman**: Assigns codes based on **lengths only**, not full tree structure.
- **Symbol Frequency Analysis**: Optimizes for the 64-symbol Base64 alphabet.
- **Bitstream Generation**: Efficiently packs symbols into a bitstream.

### **3. DNA Mapping**

- **2 bits → 1 DNA nucleotide**:
  - `00` → `A`
  - `01` → `C`
  - `10` → `G`
  - `11` → `T`
- **Padding**: Odd-length bitstreams are padded with `0` to ensure even length.

### **4. Chunking**

- Output is split into **configurable chunks** (default: 1500 chars).
- Each chunk is a **URL-safe Base64 string** of the gzipped JSON metadata + DNA.

### **5. JSON Structure**

The `chunks.json` file contains:

```json
{
  "chunks": [
    "<base64url-encoded-chunk-1>",
    "<base64url-encoded-chunk-2>",
    ...
  ]
}
```

Each chunk decodes to a **JSON object** with:

```json
{
  "schema": "huff-b64-dna-v1",
  "b64_len": <original Base64 length>,
  "lengths": [64 Huffman code lengths],
  "dna": "<DNA-encoded-bitstream>"
}
```

---

## 📊 Performance


| Input Size | Compressed Size (DNA) | Compression Ratio |
| ---------- | --------------------- | ----------------- |
| 1 KB       | ~500-700 chars        | ~50-70%           |
| 10 KB      | ~5-7 KB               | ~50-70%           |
| 100 KB     | ~50-70 KB             | ~50-70%           |


> **Note**: Compression ratio depends on input entropy. Highly repetitive text compresses better.

---

## 🛠️ Dependencies

- **Python 3.6+**
- **Standard Library Only**: No external dependencies required.

Install Python from [python.org](https://www.python.org/).

---

## 🧪 Testing

### **Self-Test**

```bash
# Encode and decode a test file
python3 zws64_dna_chunk_codec_v4_huffman.py encode test.txt test_chunks.json
python3 zws64_dna_chunk_codec_v4_huffman.py decode test_chunks.json test_restored.txt

# Verify integrity
diff test.txt test_restored.txt
```

### **Edge Cases**

- **Empty Files**: Handled gracefully (degenerate Huffman tree).
- **Single Symbol**: Assigns length 1 to the only symbol.
- **Corrupted Data**: Decoding stops at first inconsistency.

---

## 🔗 Integration

### **With Blockchain**

- Encode data to DNA chunks, then:
  - Store `chunks.json` in a **blockchain transaction** (e.g., Hive, Ethereum).
  - Use **IPFS** for decentralized storage.
  - Embed in **NFT metadata**.

### **With Images**

- Use tools like `[pixelator](https://github.com/thatoldfarm/pixelator)` to:
  - Encode `chunks.json` as **pixel data** in PNG images.
  - Extract and decode later.

### **With DNA Synthesis**

- Convert DNA strings to **oligonucleotides** for physical storage.
- Use **Twist Bioscience** or **Custom DNA synthesis services**.

---

## 📜 License

This project is **open-source** under the **MIT License**. See [LICENSE](https://github.com/thatoldfarm/zws64-dna-encoder/blob/main/LICENSE) for details.

---

## 🙏 Acknowledgments

- Inspired by **ZWS (Zero-Width Space) steganography**.
- Built for **LIA (Logos Kernel) projects** and **DNA-based data storage**.
- Special thanks to **Jacob Peacock** and the **Virtual Forest** community.

---

## 📚 References

- [Huffman Coding (Wikipedia)](https://en.wikipedia.org/wiki/Huffman_coding)
- [Base64 Encoding (RFC 4648)](https://tools.ietf.org/html/rfc4648)
- [ZWS Steganography](https://github.com/thatoldfarm/system-prompt)

---

> **💡 Pro Tip**: For **maximum compression**, pre-process your text with **dictionary-based compression** (e.g., `zstd`) before encoding.

---

**Built with ❤️ by [thatoldfarm](https://github.com/thatoldfarm) | Powered by [LIA](https://github.com/thatoldfarm/vf)**

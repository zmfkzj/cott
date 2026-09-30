//! Compiler-owned standard-library-only SHA-256/HMAC evidence transport.
use std::io::{self, Read, Write};

struct Sha256 {
    state: [u32; 8],
    block: [u8; 64],
    used: usize,
    bytes: u64,
}
impl Sha256 {
    fn new() -> Self {
        Self {
            state: [
                0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab,
                0x5be0cd19,
            ],
            block: [0; 64],
            used: 0,
            bytes: 0,
        }
    }
    fn compress(&mut self) {
        const K: [u32; 64] = [
            0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4,
            0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe,
            0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f,
            0x4a7484aa, 0x5cb0a9dc, 0x76f988da, 0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
            0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc,
            0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b,
            0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070, 0x19a4c116,
            0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
            0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7,
            0xc67178f2,
        ];
        let mut w = [0u32; 64];
        for (i, chunk) in self.block.chunks_exact(4).enumerate() {
            w[i] = u32::from_be_bytes([chunk[0], chunk[1], chunk[2], chunk[3]]);
        }
        for i in 16..64 {
            let x = w[i - 15];
            let y = w[i - 2];
            let s0 = x.rotate_right(7) ^ x.rotate_right(18) ^ (x >> 3);
            let s1 = y.rotate_right(17) ^ y.rotate_right(19) ^ (y >> 10);
            w[i] = w[i - 16]
                .wrapping_add(s0)
                .wrapping_add(w[i - 7])
                .wrapping_add(s1);
        }
        let [mut a, mut b, mut c, mut d, mut e, mut f, mut g, mut h] = self.state;
        for i in 0..64 {
            let s1 = e.rotate_right(6) ^ e.rotate_right(11) ^ e.rotate_right(25);
            let ch = (e & f) ^ (!e & g);
            let t1 = h
                .wrapping_add(s1)
                .wrapping_add(ch)
                .wrapping_add(K[i])
                .wrapping_add(w[i]);
            let s0 = a.rotate_right(2) ^ a.rotate_right(13) ^ a.rotate_right(22);
            let maj = (a & b) ^ (a & c) ^ (b & c);
            let t2 = s0.wrapping_add(maj);
            h = g;
            g = f;
            f = e;
            e = d.wrapping_add(t1);
            d = c;
            c = b;
            b = a;
            a = t1.wrapping_add(t2);
        }
        for (i, x) in [a, b, c, d, e, f, g, h].into_iter().enumerate() {
            self.state[i] = self.state[i].wrapping_add(x);
        }
    }
    fn update(&mut self, mut input: &[u8]) {
        self.bytes = self
            .bytes
            .checked_add(input.len() as u64)
            .expect("bounded evidence length");
        while !input.is_empty() {
            let n = (64 - self.used).min(input.len());
            self.block[self.used..self.used + n].copy_from_slice(&input[..n]);
            self.used += n;
            input = &input[n..];
            if self.used == 64 {
                self.compress();
                self.used = 0;
            }
        }
    }
    fn finish(mut self) -> [u8; 32] {
        let bits = self
            .bytes
            .checked_mul(8)
            .expect("bounded evidence bit length");
        self.block[self.used] = 0x80;
        self.used += 1;
        if self.used > 56 {
            self.block[self.used..].fill(0);
            self.compress();
            self.used = 0;
        }
        self.block[self.used..56].fill(0);
        self.block[56..].copy_from_slice(&bits.to_be_bytes());
        self.compress();
        let mut result = [0u8; 32];
        for (i, x) in self.state.into_iter().enumerate() {
            result[i * 4..i * 4 + 4].copy_from_slice(&x.to_be_bytes());
        }
        result
    }
}
fn hmac(key: &[u8; 32], sequence: u64, payload: &[u8]) -> [u8; 32] {
    let mut inner_pad = [0x36; 64];
    let mut outer_pad = [0x5c; 64];
    for i in 0..32 {
        inner_pad[i] ^= key[i];
        outer_pad[i] ^= key[i];
    }
    let mut inner = Sha256::new();
    inner.update(&inner_pad);
    inner.update(&sequence.to_be_bytes());
    inner.update(payload);
    let mut outer = Sha256::new();
    outer.update(&outer_pad);
    outer.update(&inner.finish());
    outer.finish()
}
pub struct EvidenceWriter {
    key: [u8; 32],
    sequence: u64,
}
impl EvidenceWriter {
    /// Read the one-way secret pipe to EOF before any authored candidate code runs.
    pub fn from_stdin() -> io::Result<Self> {
        let mut key = [0u8; 32];
        let mut stdin = io::stdin().lock();
        stdin.read_exact(&mut key)?;
        let extra = io::copy(&mut stdin, &mut io::sink())?;
        if extra != 0 {
            key.fill(0);
            return Err(io::Error::new(
                io::ErrorKind::InvalidData,
                "evidence key pipe has extra bytes",
            ));
        }
        Ok(Self { key, sequence: 0 })
    }
    pub fn event(&mut self, payload: &str) -> io::Result<()> {
        let tag = hmac(&self.key, self.sequence, payload.as_bytes());
        let mut hex = [0u8; 64];
        const DIGITS: &[u8; 16] = b"0123456789abcdef";
        for (i, b) in tag.into_iter().enumerate() {
            hex[2 * i] = DIGITS[(b >> 4) as usize];
            hex[2 * i + 1] = DIGITS[(b & 15) as usize];
        }
        let hex = std::str::from_utf8(&hex).expect("hex is ASCII");
        let mut stdout = io::stdout().lock();
        writeln!(stdout, "COTT_RUST_VERIFY:{}:{hex}:{payload}", self.sequence)?;
        stdout.flush()?;
        self.sequence = self
            .sequence
            .checked_add(1)
            .ok_or_else(|| io::Error::other("evidence sequence overflow"))?;
        Ok(())
    }
}
impl Drop for EvidenceWriter {
    fn drop(&mut self) {
        self.key.fill(0);
    }
}
pub fn json_quote(text: &str) -> String {
    use std::fmt::Write;
    let mut output = String::from("\"");
    for c in text.chars() {
        match c {
            '"' => output.push_str("\\\""),
            '\\' => output.push_str("\\\\"),
            '\n' => output.push_str("\\n"),
            '\r' => output.push_str("\\r"),
            '\t' => output.push_str("\\t"),
            c if c < '\u{20}' => {
                write!(output, "\\u{:04x}", c as u32).expect("String formatting");
            }
            c => output.push(c),
        }
    }
    output.push('"');
    output
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn standard_sha256_vectors() {
        let digest = |input: &[u8]| {
            let mut h = Sha256::new();
            h.update(input);
            h.finish()
                .iter()
                .map(|b| format!("{b:02x}"))
                .collect::<String>()
        };
        assert_eq!(
            digest(b""),
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        );
        assert_eq!(
            digest(b"abc"),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        );
        assert_eq!(
            digest(&vec![b'a'; 1_000_000]),
            "cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0"
        );
    }
    #[test]
    fn hmac_sequence_and_padding_boundaries_match_independent_implementation() {
        use ::hmac::Mac;
        let key = [0x9a; 32];
        for length in [0, 1, 47, 48, 55, 56, 63, 64, 65, 127, 128, 255, 1024] {
            let payload = vec![0x83; length];
            for sequence in [0, 1, 0x0102030405060708, u64::MAX] {
                let mut expected = ::hmac::Hmac::<::sha2::Sha256>::new_from_slice(&key).unwrap();
                expected.update(&sequence.to_be_bytes());
                expected.update(&payload);
                assert_eq!(
                    hmac(&key, sequence, &payload).as_slice(),
                    expected.finalize().into_bytes().as_slice()
                );
            }
        }
    }
    #[test]
    fn json_control_characters_are_escaped() {
        assert_eq!(json_quote("\n\0\"\\é"), "\"\\n\\u0000\\\"\\\\é\"");
    }
}

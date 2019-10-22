import struct

class Miner():

    def __init__(self, previous_hash, transactions_hash, timestamp, bits, nonce_start, nonce_end):
        self.previous_hash = previous_hash
        self.transactions_hash = transactions_hash
        self.timestamp = timestamp
        self.bits = bits
        self.nonce_start = nonce_start
        self.nonce_end = nonce_end

    _h = (
        0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
        0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
    )

    _k = (
        0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
        0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
        0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
        0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
        0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
        0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
        0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
        0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
        0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
        0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
        0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
        0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
        0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
        0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
        0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
        0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
    )

    @staticmethod
    def rrot(v, shift):
        return ((v >> shift) | (v << (32-shift))) & 0xFFFFFFFF

    @staticmethod
    def ch(a, b, c):
        return (a & b) ^ ((~a) & c)

    @staticmethod
    def maj(a, b, c):
        return (a & b) ^ (a & c) ^ (b & c)

    @classmethod
    def get_w(cls, block):
        w = [0] * 64
        w[0:16] = [(block >> (480 - i * 32)) & 0xffffffff for i in range(0, 16)]

        for i in range(16, 64):

            w[i] = (
                w[i-16] +
                (cls.rrot(w[i-15], 7) ^ cls.rrot(w[i-15], 18) ^ (w[i-15] >> 3)) +
                w[i-7] +
                (cls.rrot(w[i-2], 17) ^ cls.rrot(w[i-2], 19) ^ (w[i-2] >> 10))
            ) & 0xffffffff

        return w

    @classmethod
    def iteration(cls, w, k, a, b, c, d, e, f, g, h):

        s = (w + k + h + cls.ch(e, f, g) + (cls.rrot(e, 6) ^ cls.rrot(e, 11) ^ cls.rrot(e, 25))) & 0xffffffff

        a, b, c, d, e, f, g, h = (
            ((cls.rrot(a, 2) ^ cls.rrot(a, 13) ^ cls.rrot(a, 22)) + cls.maj(a, b, c) + s) & 0xffffffff,
            a, b, c,
            (d + s) & 0xffffffff,
            e, f, g
        )

        return a, b, c, d, e, f, g, h

    def run(self):

        pack = (
            struct.pack('<L', 0x20000000) +
            bytes.fromhex(self.previous_hash)[::-1] +
            (bytes.fromhex(self.transactions_hash)[::-1])[:-4]
        )
        block = 0
        for i in pack[:512]:
            block = (block << 8) | i

        w = self.get_w(block)
        sha1 = list(self._h)

        for i in range(self.nonce_start, self.nonce_end):
            sha1 = self.iteration(w[i], self._k[i], *sha1)
        sha1 = [(sha1[i] + self._h[i]) & 0xffffffff for i in range(0, 8)]

        results = []

        for nonce in range(0, 0xffffff):

            pack = (
                (bytes.fromhex(self.transactions_hash)[::-1])[-4:] +
                struct.pack('<LLL', self.timestamp, self.bits, nonce) +
                struct.pack('>LLLLLLLLLLLL', 0x80000000, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 640)
            )
            block = 0
            for i in pack[:512]:
                block = (block << 8) | i

            w = self.get_w(block)

            sha2 = list(sha1)
            for i in range(0, 64):
                sha2 = self.iteration(w[i], self._k[i], *sha2)
            sha2 = [((sha2[i] + sha1[i]) & 0xffffffff) for i in range(0, 8)]

            block = 0
            for i in range(0, 8):
                block = block << 32 | sha2[i]
            block = (block << 256) | (1 << 255) | 256

            w = self.get_w(block)

            sha3 = list(self._h)
            for i in range(0, 64):
                sha3 = self.iteration(w[i], self._k[i], *sha3)
            sha3 = [(sha3[i] + self._h[i]) & 0xffffffff for i in range(0, 8)]

            result = 0
            for i in struct.pack('>LLLLLLLL', *sha3)[::-1]:
                result = (result << 8) | i

            print(result)
            results.append(result)

        return results

if __name__ == '__main__':
    previous_hash = '00000000000000000146161cdb757ffc5a8b22dff06b27a76f6f7d0584f5df05'
    transactions_hash = '536e129807282bf22dcb0c169dc0e5cfeb47dac85c7afde3afb2e0fb02161076'
    timestamp = 1474983518
    bits = 0x18048ed4

    for k in (0, 50):
        Miner(previous_hash=previous_hash,
            transactions_hash=transactions_hash,
            timestamp=timestamp,
            bits=bits,
            nonce_start=0,
            nonce_end=k*0xffffff
        ).run()
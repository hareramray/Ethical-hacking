"""A one-byte length-prefixed parser: local failure, fix, bounded corpus."""
import random


def parse_naive(data):
    # Deliberately assumes a complete record; Python raises IndexError safely.
    size = data[0]
    return bytes(data[i + 1] for i in range(size))


def parse_checked(data):
    if not data:
        raise ValueError('missing length')
    size = data[0]
    if size > 32:
        raise ValueError('record exceeds lab capacity')
    if len(data) - 1 != size:
        raise ValueError('declared length differs from payload length')
    return data[1:]


def corpus():
    yield b''
    yield b'\x00'
    yield b'\x03abc'
    yield b'\x05abc'
    yield b'\x01ab'
    yield bytes([32]) + b'a' * 32
    yield bytes([33]) + b'a' * 33
    rng = random.Random(27)
    for _ in range(200):
        yield rng.randbytes(rng.randrange(0, 40))


if __name__ == '__main__':
    for record in (b'\x03abc', b'\x05abc'):
        for parser in (parse_naive, parse_checked):
            try:
                print(parser.__name__, record.hex(), '=>', parser(record))
            except (IndexError, ValueError) as error:
                print(parser.__name__, record.hex(), '=>', type(error).__name__, str(error))

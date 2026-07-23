import struct

class DomainName:
    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return self.name

    def pack(self, packet: bytearray, domain_offsets: dict) -> bytes:
        """Encode le nom de domaine avec l'algorithme de compression par pointeur."""
        encoded = bytearray()
        
        if not self.name or self.name == ".":
            return b'\x00'

        labels = self.name.split('.')
        for i in range(len(labels)):
            sub_domain = ".".join(labels[i:])
            
            if sub_domain in domain_offsets:
                pointer = 0xC000 | domain_offsets[sub_domain]
                encoded.extend(struct.pack('!H', pointer))
                return bytes(encoded)
            
            domain_offsets[sub_domain] = len(packet) + len(encoded)
            
            label = labels[i].encode('utf-8')
            encoded.append(len(label))
            encoded.extend(label)
            
        encoded.append(0)
        return bytes(encoded)

    @classmethod
    def unpack(cls, data: bytes, offset: int) -> tuple['DomainName', int]:
        """Décode le nom de domaine en suivant les éventuels pointeurs."""
        labels = []
        original_offset = offset
        jumped = False

        while offset < len(data) and data[offset] != 0:
            if (data[offset] & 0xC0) == 0xC0:
                if not jumped:
                    original_offset = offset + 2
                jumped = True
                pointer_offset = struct.unpack('!H', data[offset:offset+2])[0] & 0x3FFF
                offset = pointer_offset
            else:
                length = data[offset]
                offset += 1
                labels.append(data[offset:offset+length].decode('utf-8'))
                offset += length
        
        if not jumped:
            original_offset = offset + 1 # +1 pour passer le byte nul

        return cls(".".join(labels)), original_offset

import cPickle as pickle
import struct 
from base import Serializer

import os

class BlockSerializer(Serializer):
    """
    Serialization scheme: get the max length packed node while dumping, then
    pad all others to fit this length
    """
    def __init__(self, filename):
        self.block_size = 0
        Serializer.__init__(self, filename)

    def flush(self, existing=False):
        # grab the block size from the beginning of the file if file already
        # exists
        if existing:
            with open(self.filename, 'r') as f:
                block_size = f.read(struct.calcsize('l'))
                self.block_size = struct.unpack('l', block_size)[0]

        Serializer.flush(self, existing)

        # move the pointer to right after the block size at beginning of file
        self.f.seek(struct.calcsize('l'))

    def _reverse_write(self):
        # write the block size at the beginning of the tree file
        with open(self.filename, 'a') as f:
            block_size = struct.pack('l', self.block_size)
            f.write(block_size)
        Serializer._reverse_write(self)

    def _dump_block(self, block):
        self.f.write(block)
        # pad all nodes up to the max block size
        padding = '\x00' * (self.block_size - len(block))
        self.f.write(padding)

    def _dump_node(self, node):
        p = pickle.dumps(node)
        # determine max block size of any dumped node
        block_len = len(p)
        if block_len > self.block_size:
            self.block_size = block_len
        return p
    
    def _load_node(self):
        # read out a block size
        # node is padded by \x00 bytes
        block = self.f.read(self.block_size)
        self.pos += 1
        return pickle.loads(block)

    def _seek(self, position):
        # seek exact byte offset from current
        offset = position - self.pos
        self.f.seek(offset * self.block_size, 1)

    def _get_block_count(self):
        file_info = os.stat(self.filename)
        return (file_info.st_size - struct.calcsize('l')) / self.block_size

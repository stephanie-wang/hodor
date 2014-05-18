"""
A base class for a serializer
Methods to override are:
    _dump_node
    _load_node
    _seek
"""

import struct
import os
import time

class Serializer:

    def __init__(self, filename):
        """
        Two modes: writing, then reading

        Writing mode: during tree-building, allow api calls to dump lists of
        nodes to tree file. Reads not allowed during this time

        Read mode: After tree-building, or if we're deserializing from an
        existing tree file, allow api calls to load lists of node block
        positions in the tree file. No more writes allowed after this time
        """
        # TODO: consider passing in a node class?

        self.filename = filename
        self.read_mode = False
        self.pos = 0
        self.num_blocks = None

        if os.path.isfile(filename):
            # tree has already been built, so we're in read mode
            self.flush(True)
        else:
            self.f = open(filename, 'a+')

        # for testing: record how many backwards seeks are needed
        self.back_seeks = 0
        self.normal_seeks = 0
        self.back_seek_time = 0
        self.normal_seek_time = 0

    """
    Methods common to all serializers, no matter how serialization of one node
    is done
    """
    def dumps_many(self, nodes):
        """
        In write mode, API call to serialize nodes and append them to the tree
        file. Call self.flush() once done dumping to switch to read mode. No
        dumps will be allowed in read mode. During flush, the contents of the
        tree file will be written in reverse.

        Dump sets pointers into the tree file for each node, in order of append
        - since file gets reversed after done appending, these pointers have to
        be inverted during self.loads to actually look up a node
        """
        if self.read_mode:
            raise Exception("Nope file's already flushed")

        for i, node in enumerate(nodes):
            node.pos = self.pos + i
            block = self._dump_node(node)
            # pack the size of the block as a long immediately after the block
            # contents so we can reverse all nodes after writes are done
            size = struct.pack('l', len(block))
            self.f.write(self._dump_node(node) + size)
        self.pos += len(nodes)

    def dumps(self, node):
        self.dumps_many([node])

    def flush(self, existing=False):
        """
        In write mode, API call that must be called when finished building
        tree, since can't read while still building
        Puts Serializer in read mode
        If we just built tree, not making serializer from existing tree file,
        then reverse the nodes that were appended to the tree file
        """
        if existing:
            self.num_blocks = self._get_block_count()
        else:
            self.f.close()
            self.num_blocks = self.pos
            os.rename(self.filename, self.filename + '-tmp')
            self._reverse_write()
            os.remove(self.filename + '-tmp')

        self.pos = 0

        self.f = open(self.filename, 'r')
        self.read_mode = True

    def _reverse_write(self):
        """
        Reverse the order of nodes currently saved to the tree file
        """
        # long size in bytes in C
        long_size = struct.calcsize('l') 

        # copy the tree file in reverse to a tmp file first
        self.f = open(self.filename, 'a')
        # start at the end of the file
        reader = open(self.filename + '-tmp', 'r')
        reader.seek(0, 2)
        for i in range(self.num_blocks):
            # copy one block at a time, backwards
            reader.seek(-1 * long_size, 1)
            packed = reader.read(long_size)
            block_size = struct.unpack('l', packed)[0]
            reader.seek(-1 * (block_size + long_size), 1)
            block = reader.read(block_size)
            self._dump_block(block)
            # only write the block contents into the reversed file, not the
            # size of the block
            reader.seek(-1 * (block_size), 1)

        reader.close()
        self.f.close()

    def reset(self):
        """
        In read mode, put file pointer back at beginning of file
        maybe useful to call when a query finished?
        """
        self.f.seek(0)

    def kill(self):
        """
        kill the serializer
        """
        self.f.close()

    def loads(self, position):
        if position < 0:
            position = self._get_block_count() + position
        position = self.num_blocks - position - 1

        bs = False
        if self.pos > position:
            bs = True

        seek_start = time.time()
        self._seek(position)
        seek_end = time.time()

        self.pos = position
        node = self._load_node()

        if bs:
            self.back_seeks += 1
            self.back_seek_time += seek_end - seek_start
        else:
            self.normal_seeks += 1
            self.normal_seek_time += seek_end - seek_start

        node.serializer = self
        return node


    """
    Methods defined by different serialization methods - must override these in Serializer
    subclasses
    """
    def _dump_block(self, block):
        self.f.write(block)

    def _dump_node(self, node):
        """
        In append mode, given an instance of a node, serialize it and
        return string
        """
        return ""

    def _load_node(self):
        """
        In read mode, deserialize the node at current position in file
        """
        return None

    def _seek(self, position):
        """
        In read mode, seek to a block position in the file
        """
        return

    def _get_block_count(self):
        """
        In read mode, return the number of blocks in the tree file
        """
        return 0

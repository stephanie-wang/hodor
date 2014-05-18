import cPickle as pickle
import linecache
from base import Serializer

class LineSerializer(Serializer):
    """
    Serialization scheme: variable-length cPickled node on each line
    """
    def flush(self, existing=False):
        Serializer.flush(self, existing)
        self.lines = iter(self.f)

    def _dump_node(self, node):
        # pickle and escape all newline characters
        line = pickle.dumps(node).replace('\n', '\\n')
        return line + '\n'

    def _load_node(self):
        # unenscape newline characters and unpickle
        line = self.lines.next().replace('\\n', '\n')
        self.pos += 1
        return pickle.loads(line)

    def _seek(self, position):
        offset = position - self.pos
        if offset < 0:
            # reset file position and iterator to beginning of file
            self.f.seek(0)
            self.pos = 0
            self.lines = iter(self.f)
            offset = position

        for i in range(offset):
            self.lines.next()

    def _get_block_count(self):
        with open(self.filename) as f:
            for i, l in enumerate(f):
                pass
        return i + 1

class LinecacheSerializer(LineSerializer):
    def flush(self, existing=False):
        Serializer.flush(self, existing)

    def loads(self, position):
        return self._load_node(position)

    def _load_node(self, pos=None):
        # unenscape newline characters and unpickle
        pos = self.num_blocks - pos
        line = linecache.getline(self.filename, pos)
        line = line.replace('\\n', '\n')
        #line = self.lines.next().replace('\\n', '\n')
        self.pos += 1
        node = pickle.loads(line)
        node.serializer = self
        return node


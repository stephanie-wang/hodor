from node import RangeNode

class RangeLeaf(RangeNode):

    # Initialize a leaf with a *sorted* set of data points
    def __init__(self, data, linked_node, dim, prev, full_data=None):
        # [(id, value), ..., ]
        self.data = data
        self.dimension = dim
        self.linked_node = linked_node
        self.full_data = full_data
        self.prev = prev
        self.build()

    def build(self):
        self.min = self.data[0][1]
        self.max = self.data[-1][1]

    # Return a string representing this node for printing.
    def __repr__(self):
        return "<Leaf %s>" % ", ".join([self.dimension, str(self.pos)] +
                map(str, self.data))

    def __getstate__(self):
        out = self.__dict__.copy()
        tdel = ['max', 'min']
        for key in tdel:
            del out[key]
        return out

    def link(self):
        return self.serializer.loads(self.linked_node)

    def load_prev(self):
        return self.serializer.loads(self.prev)

    # Get all data in the specified range - recurse on the previous leaf if this
    # one doesn't have the start value in its range.
    def get_range_data(self, start, end, recurse=True):
        # Figure out how much of our data falls in the given range.
        si = None
        ei = None
        for idx, val in enumerate(self.data):
            if val[1] >= start and si is None:
                si = idx
            if val[1] <= end:
                ei = idx

        # if everything in this leaf is greater than the end, then none of your
        # data should be returned
        if ei is None or si is None:
            si, ei = 0, 0
        # else return a slice
        else:
            ei += 1

        # Get our slice of the data.
        if self.full_data is not None:
            data = self.full_data[si:ei]
        else:
            data = self.data[si:ei]

        # Either return what we have, or recurse on our predecessor node.
        if self.min < start or self.prev is None or not recurse:
            return data

        leaf = self
        ret = data
        while leaf.min >= start and leaf.prev is not None:
            leaf = leaf.load_prev()
            data = leaf.get_range_data(start, end, recurse=False)
            ret.extend(data)

        return ret

    # Return everything in this leaf for the specified ranges
    def range_query(self, ranges, node=None):
        # If the next dimension is ours, search this leaf.
        if self.dimension in ranges:
            (start, end) = ranges[self.dimension]
        else:
            # If there is no key in our dimension, go to the next-level leaf
            if self.linked_node is None:
                return self.get_all_data()
            else:
                return self.link().range_query(ranges)

        # The query in the next dimension includes all ranges minus this one.
        nranges = ranges.copy()
        del nranges[self.dimension]

        # The base case: there are no other dimensions to query, so return
        # all nodes in the range.
        if self.linked_node is None:
            return self.get_range_data(start, end)

        # We want to recurse down to the last dimension, and return everything
        # that fits all the ranges. Perform a (d-1)-dimensional query on our
        # linked leaf, and return the union of that result and our range.
        my_indices = set(i[0] for i in self.get_range_data(start, end,
            recurse=False))

        bs = self.serializer.back_seeks
        pos = self.serializer.pos
        their_results = self.link().range_query(nranges)
        #print ('Backseek! \n' + str(self) + '\nLast pos was ' +\
        #        str(self.serializer.loads(pos - 1))) * \
        #                (self.serializer.back_seeks > bs)

        # Check each one of the lower level's results to see if it's included in
        # our range.
        ret = [r for r in their_results if r[-1] in my_indices]
        return ret

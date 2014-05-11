import bisect
import itertools
import operator
from tree import RangeTree


class RangeNode(object):
    def __init__(self, children, B):
        # This points to the node's children in the tree
        self.children = children
        self.min = children[0].min
        self.max = children[-1].max
        self.B = B

        # This stores values for all of the node's children except for the smallest
        # one. This allows searching for a child quickly with >= comparisons.
        self.values = [child.min for child in children[1:]]

        # Now we make the tree this node links to in the next dimension,
        # linked_tree.  We generate it by passing all of our data into a new
        # RangeTree object.  First, though, we have to re-order the dimensions
        # so that the next level sorts by the correct key.
        new_data = []
        for item in self.get_data():
            # stick the first data item in the back, and we're good
            new_data.append(item[1:] + [item[0]])
            # might as well set our dimension while we're at it
            self.dimension = item[0][0]

        # Next-level shit
        self.linked_tree = RangeTree(data, B)

    # Return a string representing this node for printing.
    def __repr__(self):
        name = getattr(self, "children", 0) and "Branch" or "Leaf"
        return "<%s %s>" % (name, ", ".join(map(str, self.values)))

    # Return the child node which contains the leaf keyed by "key." return
    # value is a (child, index) tuple; "index" is child's position in values.
    # If key is out of our range, return None.
    def get_child_for(self, key):
        if key < self.min or key > self.max:
            return None

        # We want the index of the first child whose minimum value is graater
        # than or equal to key.
        index = next(k[0] for k in enumerate(self.values) if key < k[1],
                default=len(self.values))

        child = self.children[index]
        return (child, index)

    # Recursively chain get_child_for commands to make a path
    def get_path(self, key):
        next_c = get_child_for(self, key)
        if next_c:
            return [next_c] + next_c[0].get_path(key)

    # Recursively chain get_child_for commands to make a path, where each
    # node is guaranteed to be >= key.
    def get_successor_path(self, key):
        next_c = get_child_for(self, key)
        if next_c == None:
            if key < self.min:
                next_c = (self.children[0], 0)
            else:
                return None

        return [next_c] + next_c[0].get_successor_path(key)

    # Make a path, where each node is guaranteed to be <= key.
    def get_predecessor_path(self, key):
        next_c = get_child_for(self, key)
        if next_c == None:
            if key > self.max:
                next_c = (self.children[-1], len(self.values))
            else:
                return None

        return [next_c] + next_c[0].get_path_to(key)

    # Enumerate all the data in the node's children, in order.
    def get_all_data(self):
        data = []
        for child in children:
            data.extend(child.get_all_data())

        # possible optimization:
        # data = map(RangeNode.get_all_data, children)

        return data

    # Get all the data in a range of values. A generalization of get_all_data.
    def get_range_data(self, start, end):
        # Get the indices of the children containing the start and end keys, or
        # note that they are out of our range.
        si = self.get_child_for(start)[1] if start >= self.min
                else -1
        ei = self.get_child_for(end)[1] if end >= self.max
                else len(self.children)

        data = []

        # First, recurse on the child containing the start key.
        if si >= 0:
            data.extend(self.children[si].get_range_data(start, end))

        # Next, grab everything from all the children in between start & end.
        if ei >= si + 2:
            for i in range(si + 1, ei):
                data.extend(self.children[i].get_all_data())

        # Recurse on the child containing the end key.
        if ei > si:
            data.extend(self.children[ei].get_range_data(start, end))

        return data

    # This is the main function we'll be using. 'ranges' should be a list of
    # (dimension/column name, (start, end)) tuples, sorted. Returns a list of
    # items included in the range from this node's subtree.
    # TODO stuff1!!
    def range_query(self, ranges):
        # First get the left and right keys from the first dimension in
        # sorted order, then find their paths
        dim, (start, end) = ranges[0]

        # If there is no key in our dimension, go to the next tree
        if self.dimension != dim:
            return self.linked_tree.range_query(ranges)

        # If the next dimension is ours, search this tree. Otherwise move on to
        # the next dimension's tree and continue.
        # The query in the next dimension is everything other than this one.
        nranges = ranges[1:]

        # The base case: there are no other dimensions to query, so return
        # all nodes in the range.
        if not nranges:
            return self.get_range_data(start, end)

        # Otherwise, search recursively on the nodes in the range.
        # lchild & rchild are the nodes containing the start and end of the
        # range
        left = self.get_child_for(start)
        right = self.get_child_for(end)
        lc, li = left if left else (None, -1)
        rc, ri = right if right else (None, len(self.children))

        # We want to find all subtrees rooted between the two paths, and
        # recursively search those. Perform a (d-1)-dimensional query on the
        # linked trees of all of this node's children completely within the
        # range, and perform the same d-dimensional query on the nodes at
        # the edge of the range (lchild and rchild).
        results = []

        if left:
            results.extend(lc.range_query(ranges))

        if ri - li > 2:
            results.extend(c.linked_tree.range_query(nranges)

        if right and ri > li:
            results.extend(rc.range_query(ranges))

        return results

    # Make this node into a file for storage.
    def serialize(self):
        pass


class RangeLeaf(RangeNode):
    def __init__(self, data):
        self.data =
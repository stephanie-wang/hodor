import os
from node import RangeNode
from leaf import RangeLeaf

# Build a tree from a list of generic objects, represented as lists of (key,
# value) tuples. Each object should have the same d keys, each one of which
# maps to a comparable value. They should already be ordered. If they are
# not, everything will fuck up. Don't make everything fuck up.
# seq is the sequence of keys in the first item of the list of data.
def build_tree(data, B, serializer):
    """
    data is list of lists of (k, v) pairs
    """
    # root will have a block position of 0
    if serializer.read_mode:
        # if we're already in read mode, then the file's already been built, so
        # return the last node in file
        # TODO: allow negative indexing for root node in serializer
        return serializer.loads(-1)

    # sort the fieldnames in each data item before doing field checks
    # last element of each data item is now a unique id for the record
    [data_item.sort(key=lambda field: field[0]) for data_item in data]
    data.sort(key=lambda data_item: data_item[0][1])
    data = [data_item + [i] for i, data_item in enumerate(data)]

    # If the sequence of keys is not the same in every other data item
    # as well, you fucked up. We make it immutable just to be safe.
    seq = tuple(d[0] for d in data[0][:-1])
    for item in data:
        if tuple(d[0] for d in item[:-1]) != seq:
            raise Exception('You fucked up. The sequence of keys is \
                    not the same in every data item.')

    # Now that we've got leaves, let's build their parents, recursively.
    build_upwards(data, 0, B, RangeLeaf, serializer)

    # should be done serializing
    serializer.flush()
    # and output the root
    return serializer.loads(-1)

def build_upwards(data, dim_index, B, NodeClass, serializer,
        children=None,
        children_intervals=None):
    """
    Function to build nodes recursively, bottom-up. Takes chunks of B of
    whatever data type you pass into children, puts them into whatever class
    you set as NodeClass, and recurses up
    Tree gets built in reverse order of range query recursion, so after making
    the level with all the parents the serialization order here is:
        for each parent from left to right (okay to do range query from right to
        left on single level):
            - linked tree in next dimension
            - parent
        then recurse with the parents as the children of next level
    """
    is_leaf = NodeClass == RangeLeaf
    # if this is the lowest level, sort by keys and set the children
    if is_leaf:
        data.sort(key=lambda dp: dp[dim_index][1])
        # set starts and ends for each child
        # a child is in the form: (child_data, start, end)
        # child_data is (id, id)
        # start and end are indices into the larger data list
        children = [(data_item[-1], data_item[dim_index][1]) for data_item in data]

    parents = []
    parent_intervals = []

    num_clusters = len(children) / B
    if len(children) % B != 0:
        num_clusters += 1

    # data[0][0][0] is the dimension name unfortunately...
    dim = data[0][dim_index][0]
    prev_leaf = None
    for i in range(num_clusters):
        # If there is more than one parent's worth of children, chop
        # off the first B in a chunk
        cluster = children[i * B:(i + 1) * B]
        cluster_start = i * B
        cluster_end = i * B + len(cluster)
        if not is_leaf:
            cluster_start = children_intervals[cluster_start][0]
            cluster_end = children_intervals[cluster_end - 1][1]

        # serialize parent's linked tree in next dimension
        linked_root = None
        # last element in data[0] is the id, if we're more than one before
        # that, there's still another dimension to build a tree for
        if dim_index < len(data[0]) - 2:
            # build the next dimension
            linked_root = build_upwards(data[cluster_start : cluster_end],
                    dim_index + 1, B, RangeLeaf, serializer)

        if is_leaf:
            # if we're at the bottom of the last tree, pass in the full data item
            if dim_index == len(data[0]) - 2:
                parent = NodeClass(cluster, linked_root, dim, prev_leaf,
                        data[cluster_start : cluster_end])
            else:
                parent = NodeClass(cluster, linked_root, dim, prev_leaf)
        else:
            parent = NodeClass(cluster, linked_root, dim, serializer)

        # then serialize parent
        serializer.dumps(parent)

        if is_leaf:
            prev_leaf = parent.pos

        # and add it to our collection
        parents.append((parent.pos, parent.min, parent.max))
        parent_intervals.append((cluster_start, cluster_end))
        i += 1

    # If we ended up with more than one parent, we need to give them
    # their own parents. Recurse.
    if len(parents) > 1:
        # On the recursive steps, the parents are always RangeNodes.
        return build_upwards(data, dim_index, B, RangeNode, serializer,
                parents, parent_intervals)

    return parents[0][0]

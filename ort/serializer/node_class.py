"""
A dummy node class to use for serializer testing
The real class should initialize the serializer in the Tree class, then call
serializer.dumps(nodes) while building the tree
"""

class Node:
    def __init__(self, serializer, **kwargs):

        for attr in ["serializer", "value", "data", "min", "max",
                "children_pointers", "children", "B", "is_leaf", "pos"]:
            # being lazy...
            setattr(self, attr, kwargs.get(attr))

    def get_children(indices):
        pointers = [self.children_pointers[index] for index in indices]
        return serializer.loads(pointers)

    """
    We need these methods for cPickle...they'll probably be useful for struct
    packing/unpacking as well
    """
    def __getstate__(self):
        state = self.__dict__.copy()
        del state['serializer']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)

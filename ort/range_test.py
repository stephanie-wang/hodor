import os, random, time, tree
from serializer.line_serializer import LineSerializer, LinecacheSerializer
from serializer.block_serializer import BlockSerializer

test_serializer = BlockSerializer

def build_test():
    return
    data = []

    for j in range(1000):
        data_item = [("field" + str(i), random.random() * 10000) for i in range(3)]
        data.append(data_item)

    tree_file = 'test-tree.hodor'
    if os.path.isfile(tree_file):
        os.remove(tree_file)
    serializer = test_serializer(tree_file)

    root1 = tree.build_tree(data, 28, serializer)
    root2 = root1.link()
    root3 = root2.link()

    dim1 = [data_item[1] for data_item in
            sorted((data_item[0] for data_item in data), key=lambda d: d[1])]
    dim2 = [data_item[1] for data_item in
            sorted((data_item[1] for data_item in data), key=lambda d: d[1])]
    dim3 = [data_item[1] for data_item in
            sorted((data_item[2] for data_item in data), key=lambda d: d[1])]

    # make sure all the roots have all values at bottom
    #assert len(root1.get_all_data()) == len(data)
    #assert len(root2.get_all_data()) == len(data)
    #assert len(root3.get_all_data()) == len(data)

    #for root, dim in zip([root1, root2, root3], [dim1, dim2, dim3]):
    #    root_children = [root.load_child(child) for child in root.children]
    #    root_grandchildren = [child.load_child(grandchild) for child in
    #            root_children for grandchild in child.children]

    #    # test the intervals of the root's children
    #    assert root_children[0].min == dim[0]
    #    assert root_children[0].max == dim[8]
    #    assert root_children[1].min == dim[9]
    #    assert root_children[1].max == dim[9]

    #    for i in range(3):
    #        # test the intervals of the root's grandchildren: leaves
    #        assert root_grandchildren[i].min == dim[i * 3]
    #        assert root_grandchildren[i].max == dim[i * 3 + 2]

    #        # test the linked list at the leaves
    #        if i != 0:
    #            assert root_grandchildren[i].prev == \
    #                root_grandchildren[i - 1].pos
    #
    #        # test that full data is only stored at the last dimension
    #        if root != root3:
    #            assert root_grandchildren[i].full_data == None
    #        else:
    #            assert len(root_grandchildren[i].full_data) > 0
    #            assert len(root_grandchildren[i].full_data[0]) == 4

    ranges = {
        'field0': (0, 3),
        'field1': (2, 6),
        'field2': (0, 10)
    }

    #result = [data_item for data_item in data if
    #        data_item[0] >= ranges['field0'][0] and data_item[0] <= ranges['field0'][1] and
    #        data_item[1] >= ranges['field1'][0] and data_item[1] <= ranges['field1'][1] and
    #        data_item[2] >= ranges['field2'][0] and data_item[2] <= ranges['field2'][1]]

    start, end = 42, 103

    result = [data_item[0] for data_item in data if data_item[0][1] >= start and
            data_item[0][1] <= end]

    #print root1.range_query(ranges)
    #print root1.get_range_data(start, end)

    #print result
    assert len(result) == len(root1.get_range_data(start, end))

    # check that getting leaves is working in final dimension
    result = [data_item[0] for data_item in data if data_item[2][1] >= start
            and data_item[2][1] <= end]
    assert len(result) == len(root3.get_range_data(start, end))

def unit_search_test():
    search(10, 1, 1500)
    assert False

def unit_test():
    return
    B = 2**6
    for m in range(6):
        nq = 2**(3 + (5-m) * 2)
        ni = 2**(10 + m * 2)
        search(B, nq, ni)
    assert False

def search(B, num_query, num_items):
    data = []
    dims = ['x','y','z']

    for i in range(num_items):
        item = [(dimension, random.randrange(-1000, 1000))
                for dimension in ['x', 'y', 'z']]
                #for dimension in ['x']]
        data.append(item)

    tree_file = 'test-tree-2.hodor'
    if os.path.isfile(tree_file):
        os.remove(tree_file)
    serializer = test_serializer(tree_file)

    root = tree.build_tree(data, B, serializer)

    ranges = []
    start = time.time()
    for i in range(num_query):
        ranges = {d: (random.randrange(-1000, 0),
                     random.randrange(0, 1000))
                    for d in ['x', 'y', 'z']}
        result = root.range_query(ranges)
        real_result = []

        for d in data:
            incl = True
            for key in ranges:
                dk = next(i[1] for i in d if i[0] == key)
                if dk < ranges[key][0] \
                        or dk > ranges[key][1]:
                    incl = False
            if incl:
                real_result.append(d)

        if len(real_result) != len(result):
            print 'ranges:', ranges
            print 'result:', len(result), 'should be:', len(real_result), 'items'

            result = [i[:3] for i in result]
            missing = [i for i in real_result if i not in result]
            missing = map(lambda res: tuple(i[1] for i in res), missing)
            print 'should have been in the result:', missing

            extra = [i for i in result if i not in real_result]
            extra = map(lambda res: tuple(i[1] for i in res), extra)
            print 'should not have been in the result:', extra

        assert len(real_result) == len(result)

    total = time.time() - start
    print num_query, 'queries on', num_items, 'items took', total, 'seconds'

    print serializer.normal_seeks, 'forward seeks averaged',\
        10**6 * serializer.normal_seek_time / serializer.normal_seeks, 'microseconds each'
    print serializer.back_seeks#, 'back seeks averaged',\
    #    10**6 * serializer.back_seek_time / serializer.back_seeks, 'microseconds each'
    #print len(result)/B

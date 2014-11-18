HODOR: HODOR On-Disk Orthogonal Range-trees
==========

The orthogonal range tree is a data structure for efficient range
queries on d dimensions. HODOR is an on-disk implementation
introducing the idea of 'back seek' complexity, or complexity in
the number of reads of locations falling before the current disk
position. By serializing the tree in a particular way, HODOR
achieves a constant number of back seeks per range query. Check
out `hodor.pdf` for more details.

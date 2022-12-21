"""Provide the ListProxy class.

.. note::
   This module is mostly intended for the internal use in python-icat.
   Most users will not need to use it directly or even care about it.
"""

from collections.abc import MutableSequence

class ListProxy(MutableSequence):
    """A list that acts as a proxy to another list.

    ListProxy mirrors a target list: all items are stored in the
    target and fetched back from the target on request.  In all other
    aspects, ListProxy tries to mimic as close as possible the
    behavior of an ordinary list.

    This class tries to be a minimal working implementation.  Methods
    like :meth:`append` and :meth:`extent` have deliberately not been
    implemented here.  These operations fall back on the versions
    inherited from :class:`collections.MutableSequence` that are based
    on the elementary methods.  This may be less efficient then
    proxying the operations directly to the target, but this way its
    easier to override the elementary methods.

    >>> l = [ 0, 1, 2, 3, 4 ]
    >>> lp = ListProxy(l)
    >>> lp
    [0, 1, 2, 3, 4]
    >>> lp[2]
    2
    >>> lp[2:4]
    [2, 3]
    >>> lp == l
    True
    >>> lp < l
    False
    >>> l < lp
    False
    >>> lp < [0, 1, 2, 3, 4, 0]
    True
    >>> [0, 1, 2, 3, 3] > lp
    False
    >>> lp[2:4] = ["two", "three"]
    >>> lp
    [0, 1, 'two', 'three', 4]
    >>> l
    [0, 1, 'two', 'three', 4]
    >>> lp *= 2
    >>> l
    [0, 1, 'two', 'three', 4, 0, 1, 'two', 'three', 4]
    >>> del lp[5:]
    >>> l
    [0, 1, 'two', 'three', 4]
    >>> lp += ['...', 'and', 'so', 'on']
    >>> l
    [0, 1, 'two', 'three', 4, '...', 'and', 'so', 'on']
    >>> l[0:] = [ 1, 'b', 'iii' ]
    >>> ll = [ 'x', 'y' ]
    >>> lp + ll
    [1, 'b', 'iii', 'x', 'y']
    >>> ll + lp
    ['x', 'y', 1, 'b', 'iii']
    >>> lp * 3
    [1, 'b', 'iii', 1, 'b', 'iii', 1, 'b', 'iii']
    """

    def __init__(self, target):
        super().__init__()
        if isinstance(target, MutableSequence):
            self.target = target
        else:
            raise TypeError("invalid target type %s, " 
                            "must be a MutableSequence" % (type(target)))


    def __len__(self):
        return len(self.target)

    def __getitem__(self, index):
        return self.target.__getitem__(index)

    def __setitem__(self, index, value):
        self.target.__setitem__(index, value)

    def __delitem__(self, index):
        self.target.__delitem__(index)

    def insert(self, index, value):
        self.target.insert(index, value)


    def __str__(self):
        return str(self.target)

    def __repr__(self):
        return repr(self.target)


    # No need to implement __iadd__ here, the version inherited from
    # MutableSequence works for ListProxy.

    def __imul__(self, other):
        try:
            self.target.__imul__(other)
            return self
        except AttributeError:
            return NotImplemented

    def __add__(self, other):
        res = list(self)
        res.extend(other)
        return res

    def __radd__(self, other):
        res = list(other)
        res.extend(self)
        return res

    def __mul__(self, other):
        res = list(self)
        res *= other
        return res


    # Comparison operators: ListProxy objects try to classify as lists
    # in terms of comparision.
    def __lt__(self, other):
        if isinstance(other, MutableSequence):
            return list(self) < list(other)
        else:
            return NotImplemented

    def __le__(self, other):
        if isinstance(other, MutableSequence):
            return list(self) <= list(other)
        else:
            return NotImplemented

    def __eq__(self, other):
        if isinstance(other, MutableSequence):
            return list(self) == list(other)
        else:
            return NotImplemented

    def __ne__(self, other):
        if isinstance(other, MutableSequence):
            return list(self) != list(other)
        else:
            return NotImplemented

    def __ge__(self, other):
        if isinstance(other, MutableSequence):
            return list(self) >= list(other)
        else:
            return NotImplemented

    def __gt__(self, other):
        if isinstance(other, MutableSequence):
            return list(self) > list(other)
        else:
            return NotImplemented


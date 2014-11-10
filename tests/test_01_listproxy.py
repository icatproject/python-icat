"""Test module icat.listproxy
"""

import pytest
from icat.listproxy import ListProxy

def test_listproxy():
    """Test class ListProxy
    """

    l = [ 0, 1, 2, 3, 4 ]
    lp = ListProxy(l)
    assert lp == [0, 1, 2, 3, 4]
    assert lp[2] == 2
    assert lp[2:4] == [2, 3]

    assert (lp == l) is True
    assert (lp < l) is False
    assert (l < lp) is False
    assert (lp < [0, 1, 2, 3, 4, 0]) is True
    assert ([0, 1, 2, 3, 3] > lp) is False

    lp[2:4] = ["two", "three"]
    assert lp == [0, 1, 'two', 'three', 4]
    assert l == [0, 1, 'two', 'three', 4]

    lp2 = ListProxy(lp)
    assert lp2 == [0, 1, 'two', 'three', 4]
    lp2.append('five')
    assert l == [0, 1, 'two', 'three', 4, 'five']
    assert isinstance(lp2, ListProxy)
    assert isinstance(lp, ListProxy)
    assert isinstance(l, list)
    assert lp2.target is lp
    assert lp.target is l

    lp *= 2
    assert l == [0, 1, 'two', 'three', 4, 'five', 
                 0, 1, 'two', 'three', 4, 'five']
    assert isinstance(lp, ListProxy)
    assert isinstance(l, list)

    del lp[6:]
    assert l == [0, 1, 'two', 'three', 4, 'five']

    lp += ['...', 'and', 'so', 'on']
    assert l == [0, 1, 'two', 'three', 4, 'five', '...', 'and', 'so', 'on']
    assert isinstance(lp, ListProxy)
    assert isinstance(l, list)

    l[0:] = [ 1, 'b', 'iii' ]
    ll = [ 'x', 'y' ]
    assert lp + ll == [1, 'b', 'iii', 'x', 'y']
    assert ll + lp == ['x', 'y', 1, 'b', 'iii']
    assert lp + lp2 == [1, 'b', 'iii', 1, 'b', 'iii']
    assert lp * 3 == [1, 'b', 'iii', 1, 'b', 'iii', 1, 'b', 'iii']

    t = ('a', 'b', 'c')
    with pytest.raises(TypeError):
        lpt = ListProxy(t)


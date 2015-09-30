from collections import Container, Iterable, Sized, Hashable
from functools import reduce
from pyrsistent._pmap import pmap


def _add_to_counters(counters, element):
    return counters.set(element, counters.get(element, 0) + 1)


class PBag(object):
    """
    A persistent bag/multiset type.

    Requires elements to be hashable, and allows duplicates, but has no
    ordering. Bags are hashable.

    Do not instantiate directly, instead use the factory functions :py:func:`b`
    or :py:func:`pbag` to create an instance.

    Some examples:

    >>> s = pbag([1, 2, 3, 1])
    >>> s2 = s.add(4)
    >>> s3 = s2.remove(1)
    >>> s
    pbag([1, 1, 2, 3])
    >>> s2
    pbag([1, 1, 2, 3, 4])
    >>> s3
    pbag([1, 2, 3, 4])
    """

    __slots__ = ('_counts', '__weakref__')

    def __init__(self, counts):
        self._counts = counts

    def add(self, element):
        """
        Add an element to the bag.

        >>> s = pbag([1])
        >>> s2 = s.add(1)
        >>> s3 = s.add(2)
        >>> s2
        pbag([1, 1])
        >>> s3
        pbag([1, 2])
        """
        return PBag(_add_to_counters(self._counts, element))

    def remove(self, element):
        """
        Remove an element from the bag.

        >>> s = pbag([1, 1, 2])
        >>> s2 = s.remove(1)
        >>> s3 = s.remove(2)
        >>> s2
        pbag([1, 2])
        >>> s3
        pbag([1, 1])
        """
        if element not in self._counts:
            raise KeyError(element)
        elif self._counts[element] == 1:
            newc = self._counts.remove(element)
        else:
            newc = self._counts.set(element, self._counts[element] - 1)
        return PBag(newc)

    def count(self, element):
        """
        Return the number of times an element appears.


        >>> pbag([]).count('non-existent')
        0
        >>> pbag([1, 1, 2]).count(1)
        2
        """
        return self._counts.get(element, 0)

    def __len__(self):
        """
        Return the length including duplicates.

        >>> len(pbag([1, 1, 2]))
        3
        """
        return sum(self._counts.itervalues())

    def __iter__(self):
        """
        Return an iterator of all elements, including duplicates.

        >>> list(pbag([1, 1, 2]))
        [1, 1, 2]
        >>> list(pbag([1, 2]))
        [1, 2]
        """
        for elt, count in self._counts.iteritems():
            for i in range(count):
                yield elt

    def __contains__(self, elt):
        """
        Check if an element is in the bag.

        >>> 1 in pbag([1, 1, 2])
        True
        >>> 0 in pbag([1, 2])
        False
        """
        return elt in self._counts

    def __repr__(self):
        return "pbag({0})".format(list(self))

    def __eq__(self, other):
        """
        Check if two bags are equivalent, honoring the number of duplicates,
        and ignoring insertion order.

        >>> pbag([1, 1, 2]) == pbag([1, 2])
        False
        >>> pbag([2, 1, 0]) == pbag([0, 1, 2])
        True
        """
        if type(other) is not PBag:
            raise TypeError("Can only compare PBag with PBags")
        return self._counts == other._counts

    def __lt__(self, other):
        raise TypeError('PBags are not orderable')

    __le__ = __lt__
    __gt__ = __lt__
    __ge__ = __lt__

    # Multiset-style operations from collections.Counter

    def __add__(self, other):
        """ 
        Combine elements from two PBags.

        >>> pbag([1, 2, 2]) + pbag([2, 3, 3])
        pbag([1, 2, 2, 2, 3, 3])
        """
        if not isinstance(other, PBag):
            return NotImplemented
        result = pmap().evolver()
        for elem, count in self._counts.iteritems():
            newcount = count + other.count(elem)
            if newcount > 0:
                result[elem] = newcount
        for elem, count in other._counts.iteritems():
            if elem not in self and count > 0:
                result[elem] = count
        return PBag(result.persistent())

    def __sub__(self, other):
        """ 
        Remove elements from one PBag that are present in another.

        >>> pbag([1, 2, 2, 2, 3]) - pbag([2, 3, 3, 4])
        pbag([1, 2, 2])
        """
        if not isinstance(other, PBag):
            return NotImplemented
        result = pmap().evolver()
        for elem, count in self._counts.iteritems():
            newcount = count - other.count(elem)
            if newcount > 0:
                result[elem] = newcount
        for elem, count in other._counts.iteritems():
            if elem not in self and count < 0:
                result[elem] = 0 - count
        return PBag(result.persistent())

    def __or__(self, other):
        """ 
        Union: Keep elements that are present in either of two PBags.

        >>> pbag([1, 2, 2, 2]) | pbag([2, 3, 3])
        pbag([1, 2, 2, 2, 3, 3])
        """
        if not isinstance(other, PBag):
            return NotImplemented
        result = pmap().evolver()
        for elem, count in self._counts.iteritems():
            other_count = other.count(elem)
            newcount = other_count if count < other_count else count
            if newcount > 0:
                result[elem] = newcount
        for elem, count in other._counts.iteritems():
            if elem not in self and count > 0:
                result[elem] = count
        return PBag(result.persistent())

    def __and__(self, other):
        """
        Intersection: Only keep elements that are present in both PBags.
        
        >>> pbag([1, 2, 2, 2]) & pbag([2, 3, 3])
        pbag([2])
        """
        if not isinstance(other, PBag):
            return NotImplemented
        result = pmap().evolver()
        for elem, count in self._counts.iteritems():
            other_count = other.count(elem)
            newcount = count if count < other_count else other_count
            if newcount > 0:
                result[elem] = newcount
        return PBag(result.persistent())

    def __hash__(self):
        """
        Hash based on value of elements.

        >>> m = pmap({pbag([1, 2]): "it's here!"})
        >>> m[pbag([2, 1])]
        "it's here!"
        >>> pbag([1, 1, 2]) in m
        False
        """
        return hash(self._counts)


Container.register(PBag)
Iterable.register(PBag)
Sized.register(PBag)
Hashable.register(PBag)


def b(*elements):
    """
    Construct a persistent bag.

    Takes an arbitrary number of arguments to insert into the new persistent
    bag.

    >>> b(1, 2, 3, 2)
    pbag([1, 2, 2, 3])
    """
    return pbag(elements)


def pbag(elements):
    """
    Convert an iterable to a persistent bag.

    Takes an iterable with elements to insert.

    >>> pbag([1, 2, 3, 2])
    pbag([1, 2, 2, 3])
    """
    if not elements:
        return _EMPTY_PBAG
    return PBag(reduce(_add_to_counters, elements, pmap()))


_EMPTY_PBAG = PBag(pmap())


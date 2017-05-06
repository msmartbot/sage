r"""
Group algebras

This module implements group algebras for arbitrary groups over
arbitrary commutative rings.

EXAMPLES::

    sage: D4 = DihedralGroup(4)
    sage: kD4 = GroupAlgebra(D4, GF(7))
    sage: a = kD4.an_element(); a
    () + 4*(1,2,3,4) + 2*(1,4)(2,3)
    sage: a * a
    5*() + (2,4) + (1,2,3,4) + (1,3) + 2*(1,3)(2,4) + 4*(1,4)(2,3)

Given the group and the base ring, the corresponding group algebra is unique::

    sage: A = GroupAlgebra(GL(3, QQ), ZZ)
    sage: B = GroupAlgebra(GL(3, QQ), ZZ)
    sage: A is B
    True
    sage: C = GroupAlgebra(GL(3, QQ), QQ)
    sage: A == C
    False

As long as there is no natural map from the group to the base ring,
you can easily convert elements of the group to the group algebra::

    sage: A = GroupAlgebra(DihedralGroup(2), ZZ)
    sage: g = DihedralGroup(2).gen(0); g
    (3,4)
    sage: A(g)
    (3,4)
    sage: A(2) * g
    2*(3,4)

Since there is a natural inclusion from the dihedral group `D_2` of
order 4 into the symmetric group `S_4` of order 4!, and since there is
a natural map from the integers to the rationals, there is a natural
map from `\ZZ[D_2]` to `\QQ[S_4]`::

    sage: A = GroupAlgebra(DihedralGroup(2), ZZ)
    sage: B = GroupAlgebra(SymmetricGroup(4), QQ)
    sage: a = A.an_element(); a
    () + 3*(3,4) + 3*(1,2)
    sage: b = B.an_element(); b
    () + 2*(1,2) + 4*(1,2,3,4)
    sage: B(a)
    () + 3*(3,4) + 3*(1,2)
    sage: a * b  # a is automatically converted to an element of B
    7*() + 3*(3,4) + 5*(1,2) + 6*(1,2)(3,4) + 12*(1,2,3) + 4*(1,2,3,4) + 12*(1,3,4)
    sage: parent(a * b)
    Group algebra of Symmetric group of order 4! as a permutation group
     over Rational Field

    sage: G = GL(3, GF(7))
    sage: ZG = GroupAlgebra(G)
    sage: c, d = G.random_element(), G.random_element()
    sage: zc, zd = ZG(c), ZG(d)
    sage: zc * d == zc * zd  # d is automatically converted to an element of ZG
    True

There is no obvious map in the other direction, though::

    sage: A(b)
    Traceback (most recent call last):
    ...
    TypeError: Don't know how to create an element of
     Group algebra of Dihedral group of order 4 as a permutation group over Integer Ring
     from () + 2*(1,2) + 4*(1,2,3,4)

Group algebras have the structure of Hopf algebras::

    sage: a = kD4.an_element(); a
    () + 4*(1,2,3,4) + 2*(1,4)(2,3)
    sage: a.antipode()
    () + 4*(1,4,3,2) + 2*(1,4)(2,3)
    sage: a.coproduct()
    () # () + 4*(1,2,3,4) # (1,2,3,4) + 2*(1,4)(2,3) # (1,4)(2,3)

.. NOTE::

    As alluded to above, it is problematic to make group algebras fit
    nicely with Sage's coercion model. The problem is that (for
    example) if G is the additive group `(\ZZ,+)`, and `R = \ZZ[G]` is
    its group ring, then the integer 2 can be coerced into R in two
    ways -- via G, or via the base ring -- and *the answers are
    different*. In practice we get around this by preventing elements
    of a group `H` from coercing automatically into a group ring
    `k[G]` if `H` coerces into both `k` and `G`.  This is unfortunate,
    but it seems like the most sensible solution in this ambiguous
    situation.

AUTHOR:

- David Loeffler (2008-08-24): initial version
- Martin Raum (2009-08): update to use new coercion model -- see
  :trac:`6670`.
- John Palmieri (2011-07): more updates to coercion, categories, etc.,
  group algebras constructed using CombinatorialFreeModule -- see
  :trac:`6670`.
"""

#*****************************************************************************
#       Copyright (C) 2008 William Stein <wstein@gmail.com>
#                     2008 David Loeffler <d.loeffler.01@cantab.net>
#                     2009 Martin Raum <mraum@mpim-bonn.mpg.de>
#                     2011 John Palmieri <palmieri@math.washington.edu>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#                  http://www.gnu.org/licenses/
#*****************************************************************************

from sage.rings.all import IntegerRing
from sage.misc.cachefunc import cached_method
from sage.categories.pushout import ConstructionFunctor
from sage.combinat.free_module import CombinatorialFreeModule
from sage.categories.all import Rings, Hom
from sage.categories.fields import Fields
from sage.categories.groups import Groups
from sage.categories.additive_groups import AdditiveGroups
from sage.categories.modules_with_basis import ModulesWithBasis
from sage.categories.morphism import SetMorphism
from sage.categories.sets_cat import Sets


import six


class GroupAlgebraFunctor(ConstructionFunctor):
    r"""
    For a fixed group, a functor sending a commutative ring to the
    corresponding group algebra.

    INPUT :

    - ``group`` -- the group associated to each group algebra under
      consideration

    EXAMPLES::

        sage: from sage.algebras.group_algebra import GroupAlgebraFunctor
        sage: F = GroupAlgebraFunctor(KleinFourGroup())
        sage: loads(dumps(F)) == F
        True
        sage: GroupAlgebra(SU(2, GF(4, 'a')), IntegerModRing(12)).category()
        Category of finite group algebras over Ring of integers modulo 12
    """
    def __init__(self, group) :
        r"""
        See :class:`GroupAlgebraFunctor` for full documentation.

        EXAMPLES::

            sage: from sage.algebras.group_algebra import GroupAlgebraFunctor
            sage: GroupAlgebra(SU(2, GF(4, 'a')), IntegerModRing(12)).category()
            Category of finite group algebras over Ring of integers modulo 12
        """
        self.__group = group

        ConstructionFunctor.__init__(self, Rings(), Rings())

    def group(self) :
        r"""
        Return the group which is associated to this functor.

        EXAMPLES::

            sage: from sage.algebras.group_algebra import GroupAlgebraFunctor
            sage: GroupAlgebraFunctor(CyclicPermutationGroup(17)).group() == CyclicPermutationGroup(17)
            True
         """
        return self.__group

    def _apply_functor(self, base_ring) :
        r"""
        Create the group algebra with given base ring over ``self.group()``.

        INPUT :

        - ``base_ring`` - the base ring of the group algebra.

        OUTPUT:

        A group algebra.

        EXAMPLES::

            sage: from sage.algebras.group_algebra import GroupAlgebraFunctor
            sage: F = GroupAlgebraFunctor(CyclicPermutationGroup(17))
            sage: F(QQ)
            Group algebra of Cyclic group of order 17 as a permutation group
             over Rational Field
        """
        return GroupAlgebra(self.__group, base_ring)

    def _apply_functor_to_morphism(self, f) :
        r"""
        Lift a homomorphism of rings to the corresponding homomorphism
        of the group algebras of ``self.group()``.

        INPUT:

        - ``f`` -- a morphism of rings

        OUTPUT:

        A morphism of group algebras.

        EXAMPLES::

            sage: G = SymmetricGroup(3)
            sage: A = GroupAlgebra(G, ZZ)
            sage: h = sage.categories.morphism.SetMorphism(Hom(ZZ, GF(5), Rings()), lambda x: GF(5)(x))
            sage: hh = A.construction()[0](h)
            sage: hh(A.0 + 5 * A.1)
            (1,2,3)
        """
        codomain = self(f.codomain())
        return SetMorphism(Hom(self(f.domain()), codomain, Rings()),
                           lambda x: sum(codomain(g) * f(c) for (g, c) in six.iteritems(dict(x))))

class GroupAlgebra(CombinatorialFreeModule):
    r"""
    Create the given group algebra.

    INPUT:

    - ``group`` -- a group
    - ``base_ring`` -- (default: `\ZZ`) a commutative ring

    EXAMPLES::

        sage: GroupAlgebra(GL(3, GF(7)))
        Group algebra of General Linear Group of degree 3 over Finite Field of size 7
         over Integer Ring
        sage: GroupAlgebra(GL(3, GF(7)), QQ)
        Group algebra of General Linear Group of degree 3 over Finite Field of size 7
         over Rational Field
        sage: GroupAlgebra(1)
        Traceback (most recent call last):
        ...
        TypeError: "1" is not a group

        sage: GroupAlgebra(SU(2, GF(4, 'a')), IntegerModRing(12)).category()
        Category of finite group algebras over Ring of integers modulo 12
        sage: GroupAlgebra(KleinFourGroup()) is GroupAlgebra(KleinFourGroup())
        True

    The one of the group indexes the one of this algebra::

        sage: A = GroupAlgebra(DihedralGroup(6), QQ)
        sage: A.one_basis()
        ()
        sage: A.one()
        ()

    The product of two basis elements is induced by the product of the
    corresponding elements of the group::

        sage: A = GroupAlgebra(DihedralGroup(3), QQ)
        sage: (a, b) = A._group.gens()
        sage: a*b
        (1,2)
        sage: A.product_on_basis(a, b)
        (1,2)

    The basis elements are group-like for the coproduct:
    `\Delta(g) = g \otimes g`::

        sage: A = GroupAlgebra(DihedralGroup(3), QQ)
        sage: (a, b) = A._group.gens()
        sage: A.coproduct_on_basis(a)
        (1,2,3) # (1,2,3)

    The counit on the basis elements is 1::

        sage: A = GroupAlgebra(DihedralGroup(6), QQ)
        sage: (a, b) = A._group.gens()
        sage: A.counit_on_basis(a)
        1

    The antipode on basis elements is given by `\chi(g) = g^{-1}`::

        sage: A = GroupAlgebra(DihedralGroup(3), QQ)
        sage: (a, b) = A._group.gens(); a
        (1,2,3)
        sage: A.antipode_on_basis(a)
        (1,3,2)

    TESTS::

        sage: A = GroupAlgebra(GL(3, GF(7)))
        sage: A.has_coerce_map_from(GL(3, GF(7)))
        True
        sage: G = SymmetricGroup(5)
        sage: x,y = G.gens()
        sage: A = GroupAlgebra(G)
        sage: A( A(x) )
        (1,2,3,4,5)
    """
    def __init__(self, group, base_ring=IntegerRing(), category=None):
        r"""
        See :class:`GroupAlgebra` for full documentation.

        EXAMPLES::

            sage: GroupAlgebra(GL(3, GF(7)))
            Group algebra of General Linear Group of degree 3 over Finite Field of size 7
             over Integer Ring

        TESTS::

            sage: GroupAlgebra(AbelianGroup(1)) == GroupAlgebra(AbelianGroup(1))
            True
            sage: GroupAlgebra(AbelianGroup(1), QQ) == GroupAlgebra(AbelianGroup(1), ZZ)
            False
            sage: GroupAlgebra(AbelianGroup(2)) == GroupAlgebra(AbelianGroup(1))
            False
            sage: A = GroupAlgebra(KleinFourGroup(), ZZ)
            sage: B = GroupAlgebra(KleinFourGroup(), QQ)
            sage: A == B
            False
            sage: A == A
            True

            sage: GroupAlgebra(SymmetricGroup(2)).is_commutative()
            True
            sage: GroupAlgebra(SymmetricGroup(3)).is_commutative()
            False
        """
        from sage.groups.group import is_Group
        if not base_ring.is_commutative():
            raise NotImplementedError("base ring must be commutative")

        cat = group.category()
        if not (cat.is_subcategory(Groups())
                or cat.is_subcategory(AdditiveGroups())):
            raise TypeError('"%s" is not a group' % group)

        if category is None:
            category = cat.Algebras(base_ring)

        # If base_ring is of characteristic 0, this is handled
        #    in the FiniteGroups.Algebras category
        # Maschke's theorem: under some conditions, the algebra is semisimple.
        if (category.is_subcategory(Sets().Finite())
            and base_ring in Fields
            and base_ring.characteristic() >= 0
            and hasattr(group, "cardinality")
            and group.cardinality() % base_ring.characteristic() != 0):
            category = category.Semisimple()

        # Somewhat dirty hack to wrap non-atomic objects
        if group in ModulesWithBasis:
            prefix = 'B'
            bracket = True
        else:
            prefix = ''
            bracket = False

        self._group = group
        CombinatorialFreeModule.__init__(self, base_ring, group,
                                         prefix=prefix,
                                         bracket=bracket,
                                         category=category)

        if not base_ring.has_coerce_map_from(group) :
            ## some matrix groups assume that coercion is only valid to
            ## other matrix groups. This is a workaround
            ## call _element_constructor_ to coerce group elements
            #try :
            self._populate_coercion_lists_(coerce_list=[group])

    # Methods taken from sage.categories.examples.hopf_algebras_with_basis:

    @cached_method
    def algebra_generators(self):
        r"""
        The generators of this algebra, as per
        :meth:`Algebras.ParentMethods.algebra_generators`.

        They correspond to the generators of the group.

        EXAMPLES::

            sage: A = GroupAlgebra(DihedralGroup(3), QQ); A
            Group algebra of Dihedral group of order 6 as a permutation group
             over Rational Field
            sage: A.algebra_generators()
            Finite family {(1,3): (1,3), (1,2,3): (1,2,3)}
        """
        from sage.sets.family import Family
        return Family(self._group.gens(), self.monomial)

    gens = algebra_generators

    # other methods:

    def ngens(self) :
        r"""
        Return the number of generators.

        EXAMPLES::

            sage: GroupAlgebra(SL2Z).ngens()
            2
            sage: GroupAlgebra(DihedralGroup(4), RR).ngens()
            2
        """
        return self.algebra_generators().cardinality()

    def gen(self, i = 0) :
        r"""
        EXAMPLES::

            sage: A = GroupAlgebra(GL(3, GF(7)))
            sage: A.gen(0)
            [3 0 0]
            [0 1 0]
            [0 0 1]
        """
        return self.monomial(self._group.gen(i))

    def group(self):
        r"""
        Return the group of this group algebra.

        EXAMPLES::

            sage: GroupAlgebra(GL(3, GF(11))).group()
            General Linear Group of degree 3 over Finite Field of size 11
            sage: GroupAlgebra(SymmetricGroup(10)).group()
            Symmetric group of order 10! as a permutation group
        """
        return self._group

    def is_exact(self):
        r"""
        Return ``True`` if elements of ``self`` have exact representations,
        which is true of ``self`` if and only if it is true of
        ``self.group()`` and ``self.base_ring()``.

        EXAMPLES::

            sage: GroupAlgebra(GL(3, GF(7))).is_exact()
            True
            sage: GroupAlgebra(GL(3, GF(7)), RR).is_exact()
            False
            sage: GroupAlgebra(GL(3, pAdicRing(7))).is_exact() # not implemented correctly (not my fault)!
            False
        """
        return self.group().is_exact() and self.base_ring().is_exact()

    # I haven't written is_noetherian(), because I don't know when group
    # algebras are noetherian, and I haven't written is_prime_field(), because
    # I don't know if that means "is canonically isomorphic to a prime field"
    # or "is identical to a prime field".

    def random_element(self, n=2):
        r"""
        Return a 'random' element of ``self``.

        INPUT:

        - ``n`` -- integer (default: 2); number of summands

        ALGORITHM:

        Return a sum of ``n`` terms, each of which is formed by
        multiplying a random element of the base ring by a random
        element of the group.

        EXAMPLES::

            sage: GroupAlgebra(DihedralGroup(6), QQ).random_element()
            -1/95*() - 1/2*(1,4)(2,5)(3,6)
            sage: GroupAlgebra(SU(2, 13), QQ).random_element(1)
            1/2*[       0 4*a + 11]
            [2*a + 12        4]
        """
        a = self(0)
        for i in range(n):
            a += self.term(self.group().random_element(),
                           self.base_ring().random_element())
        return a

    def construction(self):
        r"""
        EXAMPLES::

            sage: A = GroupAlgebra(KleinFourGroup(), QQ)
            sage: A.construction()
            (GroupAlgebraFunctor, Rational Field)
        """
        return GroupAlgebraFunctor(self._group), self.base_ring()

    def _latex_(self):
        r"""
        Latex string of ``self``.

        EXAMPLES::

            sage: A = GroupAlgebra(KleinFourGroup(), ZZ)
            sage: latex(A) # indirect doctest
            \Bold{Z}[\langle (3,4), (1,2) \rangle]
        """
        from sage.misc.all import latex
        return "%s[%s]" % (latex(self.base_ring()), latex(self.group()))

    # coercion methods:

    def _coerce_map_from_(self, S):
        r"""
        True if there is a coercion from ``S`` to ``self``, False otherwise.
        The actual coercion is done by the :meth:`_element_constructor_`
        method.

        INPUT:

        -  ``S`` - a Sage object

        The objects that coerce into a group algebra `k[G]` are:

        - any group algebra `R[H]` as long as `R` coerces into `k` and
          `H` coerces into `G`.

        - any ring `R` which coerces into `k`

        - any group `H` which coerces into either `k` or `G`.

        Note that if `H` is a group which coerces into both `k` and
        `G`, then Sage will always use the map to `k`.  For example,
        if `\ZZ` is the ring (or group) of integers, then `\ZZ` will
        coerce to any `k[G]`, by sending `\ZZ` to `k`.

        EXAMPLES::

            sage: A = GroupAlgebra(SymmetricGroup(4), QQ)
            sage: B = GroupAlgebra(SymmetricGroup(3), ZZ)
            sage: A._coerce_map_from_(B)
            True
            sage: B._coerce_map_from_(A)
            False
            sage: A._coerce_map_from_(ZZ)
            True
            sage: A._coerce_map_from_(CC)
            False
            sage: A._coerce_map_from_(SymmetricGroup(5))
            False
            sage: A._coerce_map_from_(SymmetricGroup(2))
            True
        """
        from sage.rings.ring import is_Ring
        from sage.groups.old import Group
        k = self.base_ring()
        G = self.group()
        if isinstance(S, GroupAlgebra):
            return (k.has_coerce_map_from(S.base_ring())
                    and G.has_coerce_map_from(S.group()))
        if is_Ring(S):
            return k.has_coerce_map_from(S)
        if isinstance(S,Group):
            return k.has_coerce_map_from(S) or G.has_coerce_map_from(S)

    def _element_constructor_(self, x):
        r"""
        Try to turn ``x`` into an element of ``self``.

        INPUT:

        - ``x`` -- an element of some group algebra or of a
          ring or of a group

        OUTPUT:

        ``x`` as a member of ``self``.

        EXAMPLES::

            sage: G = KleinFourGroup()
            sage: f = G.gen(0)
            sage: ZG = GroupAlgebra(G)
            sage: ZG(f)  # indirect doctest
            (3,4)
            sage: ZG(1) == ZG(G(1))
            True
            sage: G = AbelianGroup(1)
            sage: ZG = GroupAlgebra(G)
            sage: f = ZG.group().gen()
            sage: ZG(FormalSum([(1,f), (2, f**2)]))
            f + 2*f^2
            sage: G = GL(2,7)
            sage: OG = GroupAlgebra(G, ZZ[sqrt(5)])
            sage: OG(2)
            2*[1 0]
            [0 1]
            sage: OG(G(2)) # conversion is not the obvious one
            [2 0]
            [0 2]
            sage: OG(FormalSum([ (1, G(2)), (2, RR(0.77)) ]) )
            Traceback (most recent call last):
            ...
            TypeError: Attempt to coerce non-integral RealNumber to Integer
            sage: OG(OG.base_ring().basis()[1])
            sqrt5*[1 0]
            [0 1]
        """
        k = self.base_ring()

        #Coerce ints to Integers
        if isinstance(x, int):
            x = Integer(x)

        if x in k:
            if x == 0:
                return self.zero()
            else:
                return k(x) * self.one()

        G = self.group()
        S = x.parent()
        if S is G:
            return self.monomial(x)

        from sage.rings.ring import is_Ring
        from sage.structure.formal_sum import FormalSum

        if isinstance(S, GroupAlgebra):
            if self.has_coerce_map_from(S):
                # coerce monomials, coerce coefficients, reassemble
                d = x.monomial_coefficients()
                new_d = {}
                for g in d:
                    g1 = G(g)
                    if g1 in new_d:
                        new_d[g1] += k(d[g]) + new_d[g1]
                    else:
                        new_d[g1] = k(d[g])
                return self._from_dict(new_d)

        elif is_Ring(S):
            # coerce to multiple of identity element
            return k(x) * self.one()

        elif isinstance(x, FormalSum) and k.has_coerce_map_from(S.base_ring()):
            y = [(G(g), k(coeff)) for coeff,g in x]
            return self.sum_of_terms(y)

        # Check whether group coerces to base_ring first.
        if k.has_coerce_map_from(S):
            return k(x) * self.one()
        if G.has_coerce_map_from(S):
            return self.monomial(G(x))

        raise TypeError("Don't know how to create an element of %s from %s" % \
                             (self, x))


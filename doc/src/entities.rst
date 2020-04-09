:mod:`icat.entities` --- Provide classes corresponding to the ICAT schema
=========================================================================

.. py:module:: icat.entities

Provide the classes corresponding to the entities in the ICAT schema.

Entity classes defined in this module are derived from the abstract
base class :class:`icat.entity.Entity`.  They override the class
attributes :attr:`icat.entity.Entity.BeanName`,
:attr:`icat.entity.Entity.Constraint`,
:attr:`icat.entity.Entity.InstAttr`,
:attr:`icat.entity.Entity.InstRel`,
:attr:`icat.entity.Entity.InstMRel`,
:attr:`icat.entity.Entity.AttrAlias`, and
:attr:`icat.entity.Entity.SortAttrs` as appropriate.

Furthermore, custom methods are added to a few selected entity
classes.

.. autoclass:: icat.entities.GroupingMixin
    :members:
    :show-inheritance:

.. autoclass:: icat.entities.InstrumentMixin
    :members:
    :show-inheritance:

.. autoclass:: icat.entities.InvestigationMixin
    :members:
    :show-inheritance:

.. autoclass:: icat.entities.Investigation44Mixin
    :members:
    :show-inheritance:

.. autofunction:: icat.entities.getTypeMap

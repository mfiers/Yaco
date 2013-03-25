Yaco.
=====
A YAML serializable, dict like object with implicit branch creation.


Why?
----

To store information and manage configuration files, with an object
that is easy to use and produces readable code.

Example
-------

  >>> y = Yaco.Yaco()
  >>> y.item1.item2 = 2
  >>> print y
  {'item1': {'item2': 2}}
  >>> print y.pretty()
  item1:
    item2: 2

Yaco support implicit lists

  >>> x = Yaco.Yaco()
  >>> x.item3 = 3
  >>> y.item4 = [1,2,3,4, x]
  >>> print y.pretty()
  item1:
    item2: 2
  item4:
  - 1
  - 2
  - 3
  - 4
  - item3: 3

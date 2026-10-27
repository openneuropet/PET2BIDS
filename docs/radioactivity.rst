Radiotracer quantity inference
==============================

PET2BIDS uses the same physical relationships in MATLAB and Python to infer a
missing radiotracer quantity from two supplied quantities. Values are converted
to canonical units before calculation, then converted to the requested output
unit. Supplied values and units are preserved.

Quantities and units
--------------------

.. list-table::
   :header-rows: 1
   :widths: 7 24 26 10 16 16

   * - Index
     - Internal name
     - Output name
     - Symbol
     - Default unit
     - Canonical unit
   * - 1
     - ``InjectedRadioactivity``
     - ``InjectedRadioactivity``
     - :math:`A`
     - ``MBq``
     - ``Bq``
   * - 2
     - ``InjectedMass``
     - ``InjectedMass``
     - :math:`m` or :math:`n`
     - ``ug``
     - ``g`` or ``mol``
   * - 3
     - ``SpecificRadioactivity``
     - ``SpecificRadioactivity``
     - :math:`S`
     - ``Bq/g``
     - ``Bq/g``
   * - 4
     - ``MolarActivity``
     - ``MolarActivity``
     - :math:`R`
     - ``GBq/umol``
     - ``Bq/mol``
   * - 5
     - ``MolecularWeight``
     - ``TracerMolecularWeight``
     - :math:`W`
     - ``g/mol``
     - ``g/mol``

``InjectedMassUnits`` selects one of two relation groups. Mass units such as
``ug`` and ``mg`` select the physical-mass relations. Amount units such as
``nmol`` and ``umol`` select the amount-of-substance relations. If the unit is
omitted, ``InjectedMass`` defaults to ``ug`` and therefore selects the
physical-mass relations.

Supported unit strings are:

* activity: ``Bq``, ``kBq``, ``MBq``, ``GBq``, ``TBq``, ``Ci``, ``mCi``, and
  ``uCi``;
* physical mass: ``kg``, ``g``, ``mg``, ``ug``, and ``ng``; and
* amount of substance: ``mol``, ``mmol``, ``umol``, ``nmol``, and ``pmol``.

Ratio units must combine a supported activity numerator with the appropriate
mass or amount denominator. Unsupported or dimensionally incompatible units
produce a warning and are not used in a calculation.

Calculation sequence
--------------------

1. Normalize micro signs to ``u`` internally for unit matching, then convert
   supplied values to canonical units. The supplied spelling is preserved in
   output metadata.
2. Use ``InjectedMassUnits`` to select the mass or amount relation group.
3. Evaluate a relation only when both source quantities were supplied. An
   inferred value is not reused as source evidence for another relation.
4. Convert the canonical result to the supported requested output unit, or to
   the default unit when no output unit was supplied.
5. Preserve supplied measurements. If an independently inferred result does
   not agree with a supplied value, emit a warning rather than overwriting it.

Physical-mass relations
-----------------------

These relations apply when ``InjectedMassUnits`` is a physical-mass unit:

.. math::

   \begin{aligned}
   S &= \frac{A}{m} \\
   m &= \frac{A}{S} \\
   A &= mS
   \end{aligned}

Their units cancel as follows:

.. math::

   \begin{aligned}
   \frac{\mathrm{Bq}}{\mathrm{g}} &= \mathrm{Bq/g} \\
   \frac{\mathrm{Bq}}{\mathrm{Bq/g}} &= \mathrm{g} \\
   \mathrm{g}\;\frac{\mathrm{Bq}}{\mathrm{g}} &= \mathrm{Bq}
   \end{aligned}

For example, the default units ``MBq`` and ``ug`` give:

.. math::

   \begin{aligned}
   S
   &= \frac{10 \times 10^6\ \mathrm{Bq}}
            {10 \times 10^{-6}\ \mathrm{g}} \\
   &= 10^{12}\ \mathrm{Bq/g}
    = 1\ \mathrm{MBq}/\mu\mathrm{g}
   \end{aligned}

The numerical result therefore depends on the output unit: the same physical
quantity is ``1e12 Bq/g`` or ``1 MBq/ug``.

Amount-of-substance relations
-----------------------------

These relations apply when ``InjectedMassUnits`` is an amount unit:

.. math::

   \begin{aligned}
   R &= \frac{A}{n} \\
   n &= \frac{A}{R} \\
   A &= nR
   \end{aligned}

Their units cancel as follows:

.. math::

   \begin{aligned}
   \frac{\mathrm{Bq}}{\mathrm{mol}} &= \mathrm{Bq/mol} \\
   \frac{\mathrm{Bq}}{\mathrm{Bq/mol}} &= \mathrm{mol} \\
   \mathrm{mol}\;\frac{\mathrm{Bq}}{\mathrm{mol}} &= \mathrm{Bq}
   \end{aligned}

For example:

.. math::

   \begin{aligned}
   R
   &= \frac{100 \times 10^6\ \mathrm{Bq}}
            {2 \times 10^{-9}\ \mathrm{mol}} \\
   &= 5 \times 10^{16}\ \mathrm{Bq/mol}
    = 50\ \mathrm{GBq}/\mu\mathrm{mol}
   \end{aligned}

Molecular-weight relations
--------------------------

These relations apply independently of the ``InjectedMass`` dimension:

.. math::

   \begin{aligned}
   S &= \frac{R}{W} \\
   W &= \frac{R}{S} \\
   R &= WS
   \end{aligned}

The first relation demonstrates the unit cancellation:

.. math::

   \begin{aligned}
   S
   &= \frac{1.5 \times 10^{16}\ \mathrm{Bq/mol}}
            {300\ \mathrm{g/mol}} \\
   &= 5 \times 10^{13}\ \mathrm{Bq/g}
   \end{aligned}

``TracerMolecularWeight`` and ``TracerMolecularWeightUnits`` are the standard
output field names. The legacy ``MolecularWeight`` and ``MolecularWeightUnits``
names remain accepted as input aliases. If both value names are supplied,
``TracerMolecularWeight`` takes precedence. Its matching standard unit, or the
``g/mol`` default when that unit is absent, takes precedence over a conflicting
legacy unit.

MATLAB relation rows
--------------------

The MATLAB implementation represents each formula as:

.. code-block:: text

   [target_index, first_input_index, second_input_index, divide]

``divide`` equal to ``1`` means ``target = first / second``. A value of ``0``
means ``target = first * second``. For example, ``[3 1 2 1]`` means
:math:`S = A/m`, while ``[1 2 3 0]`` means :math:`A = mS`.

.. code-block:: text

   Mass units:   [3 1 2 1]  [2 1 3 1]  [1 2 3 0]
   Amount units: [4 1 2 1]  [2 1 4 1]  [1 2 4 0]
   Always:       [3 4 5 1]  [5 4 3 1]  [4 5 3 0]

The positional definitions are distributed across ``check_metaradioinputs.m``:

* ``names`` defines the five index positions.
* ``defaults`` defines the unit at each matching position.
* ``outputnames`` maps the internal fifth name, ``MolecularWeight``, to the
  standard output name, ``TracerMolecularWeight``.
* ``kinds`` and ``denominators`` define the dimensions for indexes 1 and 3--5.
  Index 2 is special-cased to try physical mass first, then amount of substance.
* ``base_factor`` defines supported unit labels and their canonical scales.

Changing the order of ``names`` therefore requires corresponding changes to
all positional tables, relation rows, and index-specific branches. The Python
implementation uses named relation tuples instead of numeric indexes, but its
quantity names still appear in the defaults, aliases, unit-factor mapping,
dimension helper, and relation tuples; those definitions must remain aligned.

Test coverage
-------------

The MATLAB and Python regression tests use the consistent reference values
``100 MBq``, ``2 ug``, ``5e13 Bq/g``, ``15 GBq/umol``, and ``300 g/mol``.
Each test supplies two quantities and verifies the third for all six
physical-mass and molecular-weight relations. Separate tests use ``2 nmol`` and
``50 GBq/umol`` to verify all three amount-of-substance relations.

The three-column table in ``matlab/unit_tests/check_metaradioinputs_test.m`` is
only ``[target, first_input, second_input]``. It selects the two inputs to pass
to the production helper and the output to assert; it does not perform or encode
the calculation. Python expresses the same cases as named parameter tuples in
``pypet2bids/tests/test_radioactivity.py``.

Additional tests cover equivalent unit representations, explicit output units,
micro-sign spellings, zero denominators, invalid values, inconsistent supplied
measurements, legacy molecular-weight aliases, and the JSON-writing paths.

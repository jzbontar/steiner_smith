Implementation of Steiner and Smith Radar Quality-control algorithm
===================================================================

The quality-control algorithm by Steiner and Smith [1] is a hand-build decision
tree with five binary decision variables. The features are hand-crafted and
include reflectivity value, echo top, spin change, and the vertical gradient.

Test
----

Run the following command to test on the five data sets from the paper:

	$ python2 steiner_smith.py

The outputs are written to `tmp/`.


Notes
-----

- I could not reproduce the results from the paper with the default parameters.
  In particular, I had to changed GRADthresh from 10 dBZ/deg to 20 dBZ/deg to
  match the result from the paper.

- The pyart library, used for reading the radar files, sometimes performs
  linear interpolation in the radial direction when reading files, which
  affects the SPINchange feature. I use a hack to prevent the linear
  interpolation.


References
----------

[1] M. Steiner and J. Smith, "Use of three-dimensional reflectivity structure
for automated detection and removal of non-precipitating echoes in radar data,"
J. Atmos. Ocea. Tech., vol. 19, no. 5, pp. 673–686, 2002.

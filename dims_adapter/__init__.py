"""Export gaitpdb foot-pressure recordings into a DIMS study.

DIMS (https://dims-network.github.io/) reads time series as one CSV per
measure, named ``{videoID}_{dataType}.csv``, with a ``Time`` column in seconds
ascending. That is a near-exact match for what ``gaitdata`` already serves, so
this adapter is a projection, not a translation: it adds nothing and reuses the
existing queries unchanged.

The one thing it must decide is sample rate — see :func:`export_subject`.
"""

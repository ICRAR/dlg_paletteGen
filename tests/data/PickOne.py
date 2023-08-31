import numpy as np


def pickOne(data: np.ndarray, dummy: str = "test") -> tuple:
    """
    Selects the first value of an numpy array and returns that value and the rest

    :param data: Input numpy array
    :param dummy: dummy parameter for testing

    :returns tuple (value, np.array)
    """

    # make sure we always have a ndarray with at least 1dim.
    if type(data) not in (list, tuple) and not isinstance(data, (np.ndarray)):
        raise TypeError
    if isinstance(data, np.ndarray) and data.ndim == 0:
        data = np.array([data])
    else:
        data = np.array(data)
    value = data[0] if len(data) else None
    rest = data[1:] if len(data) > 1 else np.array([])
    return value, rest

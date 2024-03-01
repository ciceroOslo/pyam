import dateutil
import pandas as pd

from pyam.index import append_index_col
from pyam.logging import raise_data_error


def swap_time_for_year(df, inplace, subannual=False):
    """Internal implementation to swap 'time' domain to 'year' (as int)"""
    if not df.time_col == "time":
        raise ValueError("Time domain must be datetime to use this method")

    ret = df.copy() if not inplace else df

    index = ret._data.index
    time = pd.Series(index.get_level_values("time"))
    order = [v if v != "time" else "year" for v in index.names]

    # reduce "time" index column to "year"
    # TODO use `replace_index_values` instead of `append_index_col`
    index = index.droplevel("time")
    new_index_col = time.apply(lambda x: x if isinstance(x, int) else x.year)
    index = append_index_col(index, new_index_col, "year", order=order)

    # if selected, extract the "subannual" info from the "time" index column
    if subannual:
        # if subannual is True, default to simple datetime format without year
        if subannual is True:
            subannual = "%m-%d %H:%M%z"
        if isinstance(subannual, str):
            _subannual = time.apply(lambda x: x.strftime(subannual))
        else:
            _subannual = time.apply(subannual)

        index = append_index_col(index, _subannual, "subannual")
        ret.extra_cols.append("subannual")

    rows = index.duplicated()
    if any(rows):
        error_msg = "Swapping time for year causes duplicates in `data`"
        raise_data_error(error_msg, index[rows].to_frame().reset_index(drop=True))

    # assign data and other attributes
    ret._data.index = index
    ret.time_col = "year"
    ret._set_attributes()

    if not inplace:
        return ret


def swap_year_for_time(df, inplace):
    """Internal implementation to swap 'year' domain to 'time' (as datetime)"""

    if not df.time_col == "year":
        raise ValueError("Time domain must be 'year' to use this method")

    ret = df.copy() if not inplace else df
    index = ret._data.index

    order = [v if v != "year" else "time" for v in index.names]

    if "subannual" in df.extra_cols:
        order = order.remove("subannual")
        time_values = zip(*[index.get_level_values(c) for c in ["year", "subannual"]])
        time = list(map(dateutil.parser.parse, [f"{y}-{s}" for y, s in time_values]))
        index = index.droplevel(["year", "subannual"])
        ret.extra_cols.remove("subannual")
    else:
        time = index.get_level_values("year")
        index = index.droplevel(["year"])

    # add new index column, assign data and other attributes
    index = append_index_col(index, time, "time", order=order)
    ret._data.index = index
    ret.time_col = "time"
    ret._set_attributes()
    delattr(ret, "year")

    if not inplace:
        return ret

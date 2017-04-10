""" Manage datasets --- loading, saving, merging etc. """

# TODO: add singlet dimensions (for all or given vars) ---------------------- #

import numpy as np
import xarray as xr


_DEFAULT_FN_CACHE_PATH = '__xyz_cache__'


def cache_to_disk(fn=None, *, cachedir=_DEFAULT_FN_CACHE_PATH, **kwargs):
    import joblib
    mem = joblib.Memory(cachedir=cachedir, verbose=0, **kwargs)

    if fn:  # bare decorator
        return mem.cache(fn)
    else:  # called with kwargs
        def cache_to_disk_decorator(fn):
            return mem.cache(fn)
        return cache_to_disk_decorator


def _auto_add_extension(file_name, engine):
    """Make sure a file name has an extension that reflects its
    file type.
    """
    if (".h5" not in file_name) and (".nc" not in file_name):
        extension = ".h5" if engine == "h5netcdf" else ".nc"
        file_name += extension
    return file_name


def save_ds(ds, file_name, engine="h5netcdf"):
    """Saves a xarray dataset.

    Parameters
    ----------
        ds: Dataset to save
        file_name: name of file to save to
        engine: engine used to save file

    Returns
    -------
        None
    """
    file_name = _auto_add_extension(file_name, engine)
    ds.to_netcdf(file_name, engine=engine)


def load_ds(file_name, engine="h5netcdf", load_to_mem=True, create_new=False):
    """Loads a xarray dataset.

    Parameters
    ----------
        file_name: name of file
        engine: engine used to load file
        load_to_mem: once opened, load from disk to memory
        create_new: if no file exists make a blank one

    Returns
    -------
        ds: loaded Dataset
    """
    file_name = _auto_add_extension(file_name, engine)
    try:
        try:
            ds = xr.open_dataset(file_name, engine=engine)
        except AttributeError as e1:
            if "object has no attribute" in str(e1) and engine == 'h5netcdf':
                ds = xr.open_dataset(file_name, engine="netcdf4")
            else:
                raise e1
        if load_to_mem:
            ds.load()
            ds.close()
    except (RuntimeError, OSError) as e2:
        if "o such" in str(e2) and create_new:
            ds = xr.Dataset()
        else:
            raise e2
    return ds


xrsave = save_ds
xrload = load_ds


def trimna(obj):
    """Drop values across all dimensions for which all values are NaN.
    """
    trimmed_obj = obj.copy()
    for d in obj.dims:
        trimmed_obj = trimmed_obj.dropna(d, how='all')
    return trimmed_obj


def check_runs(obj, dim='run', var=None, sel=()):
    """Print out information about the range and any missing values for an
    integer dimension.

    Parameters
    ----------
        obj : xarray object
            Data to check.
        dim : str (optional)
            Dimension to check, defaults to 'run'.
        var : str (optional)
            Subselect this data variable first.
        sel : mapping (optional)
            Subselect these other coordinates first.
    """
    if sel:
        obj = obj.loc[sel]
    if var:
        obj = obj[var]

    obj = trimna(obj)
    obj = obj.dropna(dim, how='all')
    obj = obj[dim].values

    if 'int' not in str(obj.dtype):
        raise TypeError("check_runs can only check integer dimesions.")

    xmin, xmax = obj.min(), obj.max() + 1
    xmiss_start = obj[:-1][obj[1:] != obj[:-1] + 1] + 1
    xmiss_end = obj[1:][obj[1:] != obj[:-1] + 1]
    xmissing = list(zip(xmiss_start, xmiss_end))
    msg = "RANGE:  {:>7} -> {:<7} | TOTAL:  {:^7}".format(xmin, xmax, len(obj))
    if xmissing:
        msg += " | MISSING: {}".format(xmissing)
    print(msg)


def auto_xyz_ds(x, y_z):
    """Automatically turn an array into a `xarray` dataset.
    """
    # Infer dimensions to coords mapping
    y_z = np.array(np.squeeze(y_z), ndmin=2)
    x = np.asarray(x)
    if np.size(x) == y_z.shape[0]:
        y_z = np.transpose(y_z)
    n_y = y_z.shape[0]
    # Turn into dataset
    if x.ndim == 2:
        ds = xr.Dataset(data_vars={'y': (['z', '_x'], y_z),
                                   'x': (['z', '_x'], x)})
    else:
        ds = xr.Dataset(coords={'x': x, 'z': np.arange(n_y)},
                        data_vars={'y': (['z', 'x'], y_z)})
    return ds

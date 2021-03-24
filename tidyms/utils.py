"""
Functions used inside several modules.

Functions
---------
gauss(x, mu, sigma, amp) : creates a gaussian curve
gaussian_mixture(x, params) : create an array with several gaussian curves
normalize(df, method) : adjust row values of a DataFrame
scale(df, method) : adjust column values of a DataFrame
transform(df, method) : perform element-wise transformation on a DataFrame
sample_to_path(samples, path) : find files in path with name equal to samples
cv(df) : Computes the coefficient of variation for columns of a DataFrame
sd(df) : Computes the std of a DataFrame and fills missing values with zeroes.
iqr(df) : Computes the inter-quartile range  of a DataFrame and fills missing
values with zeroes.
mad(df) : Computes the median absolute deviation for column in a DataFrame.
Fill missing values with zeroes.
robust_cv(df) : Estimates the coefficient of variation for columns of a
DataFrame using the MAD and median. Fill missing values with zeroes.
find_closest(x, xq) : Finds the elements in xq closest to x.

"""


import numpy as np
import pandas as pd
from statsmodels.api import OLS, add_constant
from statsmodels.stats.stattools import jarque_bera, durbin_watson
from scipy.stats import spearmanr
import os.path
from typing import Optional, Union




def gauss(x: np.ndarray, mu: float, sigma: float,
          amp: float):  # pragma: no cover
    """
    gaussian curve.

    Parameters
    ----------.sum(axis=0)
    x : np.array
    mu : float
    sigma : float
    amp : float

    Returns
    -------
    gaussian : np.array
    """
    gaussian = amp * np.power(np.e, - 0.5 * ((x - mu) / sigma) ** 2)
    return gaussian


def gaussian_mixture(x: np.ndarray, params: np.ndarray
                     ) -> np.ndarray:   # pragma: no cover
    """
    Mixture of gaussian curves.

    Parameters
    ----------
    x : np.array
    params: np.ndarray
        parameter for each curve the shape of the array is n_curves by
        3. Each row has parameters for one curve (mu, sigma, amp)

    Returns
    -------
    mixture: np.ndarray
        array with gaussian curves. Each row is a gaussian curve. The shape
        of the array is `params.shape[0]` by `x.size`.
    """
    mixture = np.zeros((params.shape[0], x.size))
    for k_row, param in enumerate(params):
        mixture[k_row] = gauss(x, *param)
    return mixture


def normalize(df: pd.DataFrame, method: str,
              feature: Optional[str] = None) -> pd.DataFrame:
    """
    Normalize samples using different methods.

    Parameters
    ----------
    df: pandas.DataFrame
    method: {"sum", "max", "euclidean", "feature"}
        Normalization method. `sum` normalizes using the sum along each row,
        `max` normalizes using the maximum of each row. `euclidean` normalizes
        using the euclidean norm of the row. `feature` normalizes area using
        the value of an specified feature
    feature: str, optional
        Feature used for normalization in `feature` mode.

    Returns
    -------
    normalized: pandas.DataFrame

    """
    if method == "sum":
        normalized = df.divide(df.sum(axis=1), axis=0)
    elif method == "max":
        normalized = df.divide(df.max(axis=1), axis=0)
    elif method == "euclidean":
        normalized = df.apply(lambda x: x / np.linalg.norm(x), axis=1)
    elif method == "feature":
        normalized = df.divide(df[feature], axis=0)
    else:
        msg = "method must be `sum`, `max`, `euclidean` or `feature`."
        raise ValueError(msg)
    # replace nans generated by division by zero
    normalized[normalized.isna()] = 0
    return normalized


def scale(df: pd.DataFrame, method: str) -> pd.DataFrame:
    """
    scales features using different methods.

    Parameters
    ----------
    df: pandas.DataFrame
    method: {"autoscaling", "rescaling", "pareto"}
        Scaling method. `autoscaling` performs mean centering scaling of
        features to unitary variance. `rescaling` scales data to a 0-1 range.
        `pareto` performs mean centering and scaling using the square root of
        the standard deviation

    Returns
    -------
    scaled: pandas.DataFrame
    """
    if method == "autoscaling":
        scaled = (df - df.mean()) / df.std()
    elif method == "rescaling":
        scaled = (df - df.min()) / (df.max() - df.min())
    elif method == "pareto":
        scaled = (df - df.mean()) / df.std().apply(np.sqrt)
    else:
        msg = "Available methods are `autoscaling`, `rescaling` and `pareto`."
        raise ValueError(msg)
    # replace nans generated when dividing by zero
    scaled[scaled.isna()] = 0
    return scaled


def transform(df: pd.DataFrame, method: str) -> pd.DataFrame:
    """
    perform common data transformations.

    Parameters
    ----------
    df: pandas.DataFrame
    method: {"log", "power"}
        transform method. `log` applies the base 10 logarithm on the data.
        `power`

    Returns
    -------
    transformed: pandas.DataFrame
    """
    if method == "log":
        transformed = df.apply(np.log10)
    elif method == "power":
        transformed = df.apply(np.sqrt)
    else:
        msg = "Available methods are `log` and `power`"
        raise ValueError(msg)
    return transformed


def sample_to_path(samples, path):
    """
    map sample names to raw path if available.

    Parameters
    ----------
    samples : Iterable[str].
        samples names
    path : str.
        path to raw sample data.

    Returns
    -------
    d : dict

    """
    # TODO: this function should accept an extension parameter to prevent
    #   files with the same name but invalid extensions from being used
    available_files = os.listdir(path)
    filenames = [os.path.splitext(x)[0] for x in available_files]
    full_path = [os.path.join(path, x) for x in available_files]
    d = dict()
    for k, name in enumerate(filenames):
        if name in samples:
            d[name] = full_path[k]
    return d

    
def cv(df: pd.DataFrame, fill_value: Optional[float] = None) -> pd.Series:
    """
    Computes the Coefficient of variation for each column.

    Used by DataContainer objects to compute metrics.

    """
    res = df.std() / df.mean()
    if fill_value is not None:
        res = res.fillna(fill_value)
    return res


def robust_cv(df, fill_value: Optional[float] = None):
    """
    Estimation of the coefficient of variation using the MAD and median.
    Assumes a normal distribution.
    """

    # 1.4826 is used to estimate sigma in an unbiased way assuming a normal
    # distribution for each feature.
    res = 1.4826 * df.mad() / df.median()
    if fill_value is not None:
        res = res.fillna(fill_value)
    return res


def mad(df):
    """
    Computes the median absolute deviation for each column. Fill missing
    values with zero.
    """
    res = df.mad()
    res = res.fillna(0)
    return res


def sd_ratio(df1: pd.DataFrame, df2: pd.DataFrame, robust: bool = False,
             fill_value: Optional[float] = None) -> pd.Series:
    """
    Computes the ratio between the standard deviation of the columns of
    DataFrame1 and DataFrame2.

    Used to compute the D-Ratio metric. NaN values are filled to np.inf.

    Parameters
    ----------
    df1 : DataFrame with shape (n1, m)
    df2 : DataFrame with shape (n2, m)
    robust : bool
        If True uses the MAD as an estimator of the standard deviation. Else
        computes the sample standard deviation.
    fill_value : Number used to input NaNs.

    Returns
    -------
    ratio : pd.Series

    """
    if robust:
        ratio = mad(df1) / mad(df2)
    else:
        ratio = df1.std() / df2.std()

    if fill_value is not None:
        ratio = ratio.fillna(fill_value)
    return ratio


def detection_rate(df: pd.DataFrame, threshold: float = 0.0) -> pd.Series:
    """
    Computes the fraction of values in a column above the `threshold`.

    Parameters
    ----------
    df : DataFrame
    threshold : float

    Returns
    -------
    dr : pd.Series

    """
    # dr = df[df > threshold].count() / df.count()
    dr = (df > threshold).sum().astype(int) / df.shape[0]
    return dr


def metadata_correlation(y, x, mode: str = "ols"):
    """
    Computes correlation metrics between two variables.

    Parameters
    ----------
    y : array
    x : array
    mode: {"ols", "spearman"}
        `ols` computes r squared, Jarque-Bera test p-value and Durwin-Watson
        statistic from the ordinary least squares linear regression. `spearman`
        computes the spearman rank correlation coefficient.

    Returns
    -------
    dict

    """
    if mode == "ols":
        ols = OLS(y, add_constant(x)).fit()
        r2 = ols.rsquared
        jb = jarque_bera(ols.resid)[1]  # Jarque Bera test p-value
        dw = durbin_watson(ols.resid)   # Durwin Watson statistic
        res = {"r2": r2, "DW": dw, "JB": jb}
    else:
        res = spearmanr(y, x)[0]
    return res


def _find_closest_sorted(x: np.ndarray,
                         xq: Union[np.ndarray, float, int]) -> np.ndarray:
    """
    Find the index in x closest to each xq element. Assumes that x is sorted.

    Parameters
    ----------
    x: numpy.ndarray
        Sorted vector
    xq: numpy.ndarray
        search vector

    Returns
    -------
    ind: numpy.ndarray
        array with the same size as xq with indices closest to x.

    Raises
    ------
    ValueError: when x or xq are empty.
    """

    if isinstance(xq, (float, int)):
        xq = np.array(xq)

    if (x.size == 0) or (xq.size == 0):
        msg = "`x` and `xq` must be non empty arrays"
        raise ValueError(msg)

    ind = np.searchsorted(x, xq)

    if ind.size == 1:
        if ind == 0:
            return ind
        elif ind == x.size:
            return ind - 1
        else:
            return ind - ((xq - x[ind - 1]) < (x[ind] - xq))

    else:
        # cases where the index is between 1 and x.size - 1
        mask = (ind > 0) & (ind < x.size)
        ind[mask] -= (xq[mask] - x[ind[mask] - 1]) < (x[ind[mask]] - xq[mask])
        # when the index is x.size, then the closest index is x.size -1
        ind[ind == x.size] = x.size - 1
        return ind


def find_closest(x: np.ndarray, xq: Union[np.ndarray, float, int],
                 is_sorted: bool = True) -> np.ndarray:
    if is_sorted:
        return _find_closest_sorted(x, xq)
    else:
        sorted_index = np.argsort(x)
        closest_index = _find_closest_sorted(x[sorted_index], xq)
        return sorted_index[closest_index]


def get_filename(full_path: str) -> str:
    """
    get the filename from a full path.

    Parameters
    ----------
    full_path: str

    Returns
    -------
    filename: str`
    """
    return os.path.splitext(os.path.split(full_path)[1])[0]


def is_unique(s: pd.Series):
    s_unique = s.unique()
    return (s.size == s_unique.size) and (s.values == s.unique()).all()


class SimulatedExperiment:  # pragma: no cover
    """
    Emulates a pyopenms MSExperiment. Used for tests.
    """
    def __init__(self, mz_values: np.ndarray, rt_values: np.ndarray,
                 mz_params: np.ndarray, rt_params: np.ndarray,
                 ft_noise: Optional[np.ndarray] = None,
                 noise: Optional[float] = None, mode: str = "centroid"):
        """
        Constructor function

        Parameters
        ----------
        mz_values : array
            sorted mz values for each mz scan, used to build spectra in profile
            mode.
        rt_values : array
            sorted rt values, used to set scan time.
        mz_params : array with shape (n, 3)
             Used to build m/z peaks. Each row is the mean, standard deviation
             and amplitude in the m/z dimension.
        rt_params : array with shape (n, 3)
             Used to build rt peaks. Each row is the mean, standard deviation
             and amplitude in the rt dimension
        ft_noise : array_with shape (n, 2), optional
            adds noise to mz and rt values
        noise : positive number, optional
            noise level to add to each scan. the noise is modeled as gaussian
            iid noise in each scan with standard deviation equal to the value
            used. An offset value is added to make the noise contribution
            non negative. To make the noise values reproducible, each scan has
            a seed value associated to generate always the same noise value in
            a given scan. seed values are generated randomly each time a new
            object is instantiated.
        mode : {"centroid", "profile"}

        """
        self.mz = mz_values
        self.mz_params = mz_params
        self.rt = rt_values
        self.n_scans = rt_values.size
        self._seeds = None
        self._noise_level = None
        self.ft_noise = ft_noise
        self.mode = mode
        # seeds are used to ensure that each time that a spectra is generated
        # with get_spectra its values are the same
        self._seeds = np.random.choice(self.n_scans * 10, self.n_scans)
        self._noise_level = noise

        if ft_noise is not None:
            np.random.seed(self._seeds[0])
            rt_params[0] += np.random.normal(scale=ft_noise[1])
        self.rt_array = gaussian_mixture(rt_values, rt_params)

    def getNrSpectra(self):
        return self.n_scans

    def getSpectrum(self, scan_number: int):
        is_valid_scan = (0 <= scan_number) and (self.n_scans > scan_number)
        if not is_valid_scan:
            msg = "Invalid scan number."
            raise ValueError(msg)
        rt = self.rt[scan_number]

        # create a mz array for the current scan
        if self.ft_noise is not None:
            mz_noise = np.random.normal(scale=self.ft_noise[0])
            mz_params = self.mz_params.copy()
            mz_params[:, 0] += mz_noise
        else:
            mz_params = self.mz_params

        if self.mode == "centroid":
            mz = mz_params[:, 0]
            spint = self.rt_array[:, scan_number] * mz_params[:, 1]
        elif self.mode == "profile":
            mz = self.mz
            mz_array = gaussian_mixture(self.mz, mz_params)
            spint = self.rt_array[:, scan_number][:, np.newaxis] * mz_array
            spint = spint.sum(axis=0)
        else:
            raise ValueError("valid modes are centroid or profile")

        if self._noise_level is not None:
            np.random.seed(self._seeds[scan_number])
            noise = np.random.normal(size=mz.size, scale=self._noise_level)
            noise -= noise.min()
            spint += noise
        sp = SimulatedSpectrum(mz, spint, rt)
        return sp


class SimulatedSpectrum:    # pragma: no cover
    """
    Emulates pyopenms Spectrum. Used for tests.
    """
    def __init__(self, mz: np.ndarray, spint: np.ndarray, rt: float):
        self.mz = mz
        self.spint = spint
        self.rt = rt

    def getRT(self):
        return self.rt

    def get_peaks(self):
        return self.mz, self.spint

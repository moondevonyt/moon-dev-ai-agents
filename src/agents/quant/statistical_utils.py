"""
🌙 Moon Dev's Statistical Utilities
Common statistical functions for quantitative trading

Implements statistical calculations used across quantitative agents:
- Z-score calculations
- Rolling statistics
- Correlation analysis
- Significance testing
- Performance metrics (Sharpe ratio, drawdown, etc.)
"""

import numpy as np
import pandas as pd
from typing import Union, Tuple, Optional
from scipy import stats


def calculate_zscore(value: float, mean: float, std: float) -> float:
    """
    Calculate z-score for a value.
    
    Args:
        value: Value to calculate z-score for
        mean: Mean of the distribution
        std: Standard deviation of the distribution
        
    Returns:
        Z-score (number of standard deviations from mean)
    """
    if std == 0:
        return 0.0
    return (value - mean) / std


def rolling_mean(data: Union[list, np.ndarray, pd.Series], window: int) -> np.ndarray:
    """
    Calculate rolling mean.
    
    Args:
        data: Time series data
        window: Rolling window size
        
    Returns:
        Array of rolling means
    """
    if isinstance(data, (list, np.ndarray)):
        data = pd.Series(data)
    return data.rolling(window=window).mean().values


def rolling_std(data: Union[list, np.ndarray, pd.Series], window: int) -> np.ndarray:
    """
    Calculate rolling standard deviation.
    
    Args:
        data: Time series data
        window: Rolling window size
        
    Returns:
        Array of rolling standard deviations
    """
    if isinstance(data, (list, np.ndarray)):
        data = pd.Series(data)
    return data.rolling(window=window).std().values


def calculate_correlation(x: Union[list, np.ndarray], 
                         y: Union[list, np.ndarray]) -> float:
    """
    Calculate Pearson correlation coefficient.
    
    Args:
        x: First time series
        y: Second time series
        
    Returns:
        Correlation coefficient (-1 to 1)
    """
    if len(x) != len(y) or len(x) < 2:
        return 0.0
    
    correlation, _ = stats.pearsonr(x, y)
    return correlation


def calculate_correlation_pvalue(x: Union[list, np.ndarray], 
                                 y: Union[list, np.ndarray]) -> Tuple[float, float]:
    """
    Calculate Pearson correlation with p-value.
    
    Args:
        x: First time series
        y: Second time series
        
    Returns:
        Tuple of (correlation, p_value)
    """
    if len(x) != len(y) or len(x) < 2:
        return 0.0, 1.0
    
    return stats.pearsonr(x, y)


def ttest_significance(returns: Union[list, np.ndarray], 
                      null_hypothesis: float = 0.0) -> Tuple[float, float]:
    """
    Perform one-sample t-test for statistical significance.
    
    Args:
        returns: Array of returns
        null_hypothesis: Null hypothesis value (default 0 for no return)
        
    Returns:
        Tuple of (t_statistic, p_value)
    """
    if len(returns) < 2:
        return 0.0, 1.0
    
    t_stat, p_value = stats.ttest_1samp(returns, null_hypothesis)
    return t_stat, p_value


def calculate_sharpe_ratio(returns: Union[list, np.ndarray], 
                          risk_free_rate: float = 0.0,
                          periods_per_year: int = 252) -> float:
    """
    Calculate Sharpe ratio (risk-adjusted return).
    
    Args:
        returns: Array of returns
        risk_free_rate: Risk-free rate (annualized)
        periods_per_year: Number of periods per year (252 for daily, 365*24 for hourly)
        
    Returns:
        Sharpe ratio
    """
    if len(returns) < 2:
        return 0.0
    
    returns_array = np.array(returns)
    excess_returns = returns_array - (risk_free_rate / periods_per_year)
    
    if np.std(excess_returns) == 0:
        return 0.0
    
    sharpe = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(periods_per_year)
    return sharpe


def calculate_max_drawdown(equity_curve: Union[list, np.ndarray]) -> float:
    """
    Calculate maximum drawdown from equity curve.
    
    Args:
        equity_curve: Array of portfolio values over time
        
    Returns:
        Maximum drawdown as percentage (0 to 100)
    """
    if len(equity_curve) < 2:
        return 0.0
    
    equity = np.array(equity_curve)
    running_max = np.maximum.accumulate(equity)
    drawdown = (equity - running_max) / running_max * 100
    
    return abs(np.min(drawdown))


def calculate_calmar_ratio(returns: Union[list, np.ndarray],
                          equity_curve: Union[list, np.ndarray],
                          periods_per_year: int = 252) -> float:
    """
    Calculate Calmar ratio (return / max drawdown).
    
    Args:
        returns: Array of returns
        equity_curve: Array of portfolio values
        periods_per_year: Number of periods per year
        
    Returns:
        Calmar ratio
    """
    if len(returns) < 2 or len(equity_curve) < 2:
        return 0.0
    
    annual_return = np.mean(returns) * periods_per_year
    max_dd = calculate_max_drawdown(equity_curve)
    
    if max_dd == 0:
        return 0.0
    
    return annual_return / max_dd


def calculate_win_rate(returns: Union[list, np.ndarray]) -> float:
    """
    Calculate win rate (percentage of positive returns).
    
    Args:
        returns: Array of returns
        
    Returns:
        Win rate as percentage (0 to 100)
    """
    if len(returns) == 0:
        return 0.0
    
    returns_array = np.array(returns)
    winning_trades = np.sum(returns_array > 0)
    
    return (winning_trades / len(returns_array)) * 100


def calculate_profit_factor(returns: Union[list, np.ndarray]) -> float:
    """
    Calculate profit factor (gross profit / gross loss).
    
    Args:
        returns: Array of returns
        
    Returns:
        Profit factor
    """
    if len(returns) == 0:
        return 0.0
    
    returns_array = np.array(returns)
    gross_profit = np.sum(returns_array[returns_array > 0])
    gross_loss = abs(np.sum(returns_array[returns_array < 0]))
    
    if gross_loss == 0:
        return float('inf') if gross_profit > 0 else 0.0
    
    return gross_profit / gross_loss


def calculate_autocorrelation(data: Union[list, np.ndarray], 
                              max_lags: int = 20) -> np.ndarray:
    """
    Calculate autocorrelation function (ACF).
    
    Args:
        data: Time series data
        max_lags: Maximum number of lags to calculate
        
    Returns:
        Array of autocorrelation values
    """
    if len(data) < max_lags + 1:
        return np.zeros(max_lags + 1)
    
    data_array = np.array(data)
    mean = np.mean(data_array)
    c0 = np.sum((data_array - mean) ** 2) / len(data_array)
    
    acf = np.zeros(max_lags + 1)
    acf[0] = 1.0
    
    for lag in range(1, max_lags + 1):
        c_lag = np.sum((data_array[:-lag] - mean) * (data_array[lag:] - mean)) / len(data_array)
        acf[lag] = c_lag / c0
    
    return acf


def calculate_mutual_information(x: Union[list, np.ndarray],
                                 y: Union[list, np.ndarray],
                                 bins: int = 10) -> float:
    """
    Calculate mutual information between two variables.
    
    Args:
        x: First variable
        y: Second variable
        bins: Number of bins for discretization
        
    Returns:
        Mutual information score
    """
    if len(x) != len(y) or len(x) < 2:
        return 0.0
    
    # Discretize continuous variables
    x_discrete = np.digitize(x, np.histogram(x, bins=bins)[1][:-1])
    y_discrete = np.digitize(y, np.histogram(y, bins=bins)[1][:-1])
    
    # Calculate joint and marginal probabilities
    joint_hist = np.histogram2d(x_discrete, y_discrete, bins=bins)[0]
    joint_prob = joint_hist / np.sum(joint_hist)
    
    x_prob = np.sum(joint_prob, axis=1)
    y_prob = np.sum(joint_prob, axis=0)
    
    # Calculate mutual information
    mi = 0.0
    for i in range(bins):
        for j in range(bins):
            if joint_prob[i, j] > 0 and x_prob[i] > 0 and y_prob[j] > 0:
                mi += joint_prob[i, j] * np.log(joint_prob[i, j] / (x_prob[i] * y_prob[j]))
    
    return mi


def fisher_z_transform(correlation: float) -> float:
    """
    Apply Fisher z-transformation to correlation coefficient.
    
    Args:
        correlation: Correlation coefficient (-1 to 1)
        
    Returns:
        Fisher z-transformed value
    """
    if correlation >= 1.0:
        correlation = 0.9999
    elif correlation <= -1.0:
        correlation = -0.9999
    
    return 0.5 * np.log((1 + correlation) / (1 - correlation))


def correlation_significance_test(r1: float, r2: float, n: int) -> Tuple[float, bool]:
    """
    Test if two correlations are significantly different using Fisher z-transformation.
    
    Args:
        r1: First correlation coefficient
        r2: Second correlation coefficient
        n: Sample size
        
    Returns:
        Tuple of (z_statistic, is_significant)
    """
    if n < 3:
        return 0.0, False
    
    z1 = fisher_z_transform(r1)
    z2 = fisher_z_transform(r2)
    
    se = np.sqrt(2 / (n - 3))
    z_stat = abs(z1 - z2) / se
    
    # Two-tailed test at 95% confidence (z > 1.96)
    is_significant = z_stat > 1.96
    
    return z_stat, is_significant


def bonferroni_correction(p_values: list, alpha: float = 0.05) -> list:
    """
    Apply Bonferroni correction for multiple testing.
    
    Args:
        p_values: List of p-values
        alpha: Significance level
        
    Returns:
        List of boolean values indicating significance after correction
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return []
    
    corrected_alpha = alpha / n_tests
    return [p < corrected_alpha for p in p_values]

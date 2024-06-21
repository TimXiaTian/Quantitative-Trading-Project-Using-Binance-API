import pandas as pd
import numpy as np
import statsmodels.api as sm
import warnings

warnings.filterwarnings("ignore")


class PairsTradingStrategy:
    def __init__(self, data, label1, label2, z_signal_in, z_signal_out, min_spread, MA_window, OLS_window, pnl_label, boll_window, std_multiplier):
        self.data = data
        self.label1 = label1
        self.label2 = label2
        self.position = 0
        self.z_signal_in = z_signal_in
        self.z_signal_out = z_signal_out
        self.min_spread = min_spread
        self.MA_window = MA_window
        self.OLS_window = OLS_window
        self.pnl_label = pnl_label
        self.boll_window = boll_window
        self.std_multiplier = std_multiplier

    @staticmethod
    def calculate_rolling_beta(data, y_col, x_col, window):
        y = data[y_col]
        x = data[x_col]

        def rolling_ols_beta(y, x):
            x = sm.add_constant(x)
            model = sm.OLS(y, x).fit()
            return model.params[1]

        rolling_beta = y.rolling(window=window).apply(lambda y: rolling_ols_beta(y, x[y.index]), raw=False)
        return rolling_beta

    @staticmethod
    def calculate_rolling_intercept(data, y_col, x_col, window):
        y = data[y_col]
        x = data[x_col]

        def rolling_ols_intercept(y, x):
            x = sm.add_constant(x)
            model = sm.OLS(y, x).fit()
            return model.params[0]

        rolling_intercept = y.rolling(window=window).apply(lambda y: rolling_ols_intercept(y, x[y.index]), raw=False)
        return rolling_intercept

    def pairs_trading_strategy(self):
        """
        Implements the pairs trading strategy.
        """
        self.data['beta'] = self.calculate_rolling_beta(self.data, self.label1, self.label2, self.OLS_window)
        self.data['intercept'] = self.calculate_rolling_intercept(self.data, self.label1, self.label2, self.OLS_window)
        self.data = self.data.dropna()

        self.data['spread'] = ((self.data[self.label1] - self.data['beta'] * self.data[self.label2]) - self.data['intercept'])
        self.data['Spread_MA'] = self.data['spread'].rolling(window=self.MA_window).mean()
        self.data['Spread_Std'] = self.data['spread'].rolling(window=self.MA_window).std()

        self.data['zscors'] = (self.data['spread'] - self.data['Spread_MA']) / self.data['Spread_Std']

        self.data['signal'] = np.nan
        self.data.loc[(self.data['zscors'] > self.z_signal_in) & (np.abs(self.data['spread']) > self.min_spread), 'signal'] = -1
        self.data.loc[(self.data['zscors'] < -self.z_signal_in) & (np.abs(self.data['spread']) > self.min_spread), 'signal'] = 1
        self.data.loc[self.data['zscors'].abs() < self.z_signal_out, 'signal'] = 0

        self.data['position'] = self.data['signal'].fillna(method='ffill').fillna(0).astype(int)

        self.data['return_Y'] = np.log(self.data[self.label1] / self.data[self.label1].shift(1))
        self.data['return_X'] = np.log(self.data[self.label2] / self.data[self.label2].shift(1))
        self.data['position_Y'] = self.data['position']
        self.data['position_Y'] = self.data['position_Y'].shift(1)
        self.data['position_X'] = self.data['position'] * self.data['beta'] * (-1)
        self.data['position_X'] = self.data['position_X'].shift(1)
        self.data['hourlypnl'] = (self.data['position_Y'] * self.data['return_Y'] + self.data['position_X'] * self.data['return_X'])
        self.data['cumpnl'] = self.data['hourlypnl'].cumsum()
        self.data['max_cumpnl'] = self.data['cumpnl'].cummax()

        return self.data

    def bollinger_band_stop_loss(self):
        """
        Implements a Bollinger Band based stop loss strategy.
        """
        stoploss_data = self.data.copy()
        new_data = self.data.copy()
        stoploss_data['Rolling_mean'] = stoploss_data[self.pnl_label].rolling(self.boll_window).mean()
        stoploss_data['Rolling_std'] = stoploss_data[self.pnl_label].rolling(self.boll_window).std()
        stoploss_data['Upper_band'] = stoploss_data['Rolling_mean'] + self.std_multiplier * stoploss_data['Rolling_std']
        stoploss_data['Lower_band'] = stoploss_data['Rolling_mean'] - self.std_multiplier * stoploss_data['Rolling_std']
        stoploss_data['Stop_Loss'] = np.where((stoploss_data[self.pnl_label] < stoploss_data['Lower_band']) |
                                              (stoploss_data[self.pnl_label] > stoploss_data['Upper_band']),
                                              0, np.nan)

        new_data['stop_loss_signal'] = stoploss_data['Stop_Loss']
        new_data['signal'].update(new_data['stop_loss_signal'])

        new_data['position'] = new_data['signal'].fillna(method='ffill').fillna(0).astype(int)
        new_data['position'] = new_data['position'].shift(1)

        new_data['return_Y'] = np.log(new_data[self.label1] / new_data[self.label1].shift(1))
        new_data['return_X'] = np.log(new_data[self.label2] / new_data[self.label2].shift(1))
        new_data['position_Y'] = new_data['position']
        new_data['position_X'] = new_data['position'] * new_data['beta'] * (-1)
        new_data['hourlypnl'] = (new_data['position_Y'] * new_data['return_Y']
                                 + new_data['position_X'] * new_data['return_X'])
        new_data['cumpnl'] = new_data['hourlypnl'].cumsum()
        new_data['max_cumpnl'] = new_data['cumpnl'].cummax()

        return new_data


if __name__ == "__main__":
    data = pd.DataFrame({
        'stock1': np.random.randn(100),
        'stock2': np.random.randn(100)
    })

    strategy = PairsTradingStrategy(data, 'stock1', 'stock2', 2, 1, 0.01, 20, 60, 'cumpnl', 20, 2)
    results = strategy.pairs_trading_strategy()
    results_with_stop_loss = strategy.bollinger_band_stop_loss()

    print(results_with_stop_loss.tail())

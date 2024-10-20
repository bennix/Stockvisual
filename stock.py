import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QComboBox, QPushButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import yfinance as yf
import mplfinance as mpf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import matplotlib as mpl
import os
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.patches import Rectangle
from matplotlib.dates import date2num

class StockApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('股票图表应用')
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.stock_combo = QComboBox()
        layout.addWidget(self.stock_combo)

        self.plot_button = QPushButton("绘制图表")
        self.plot_button.clicked.connect(self.plot_stock)
        layout.addWidget(self.plot_button)

        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        self.toolbar = NavigationToolbar(self.canvas, self)
        layout.addWidget(self.toolbar)

        # 设置中文字体
        font_path = os.path.join(os.path.dirname(__file__), 'SimHei.ttf')
        self.chinese_font = FontProperties(fname=font_path)

        # 获取股票列表并添加到下拉列表
        self.get_stock_list()

    def get_stock_list(self):
        # 获取美股列表（这里使用 S&P 500 作为示例）
        sp500 = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
        stocks = sp500['Symbol'].tolist()

        # 添加到下拉列表
        self.stock_combo.addItems(stocks)

    def plot_stock(self):
        # 设置中文字体
        chinese_font = FontProperties(fname='SimHei.ttf', size=10)
        # 如果您的系统中已经安装了支持中文的字体，可以直接使用字体名称
        # chinese_font = FontProperties(family='SimHei', size=10)

        ticker = self.stock_combo.currentText()
        stock = yf.Ticker(ticker)
        hist = stock.history(period="2y")

        # 计算移动平均线
        hist['MA5'] = hist['Close'].rolling(window=5).mean()
        hist['MA10'] = hist['Close'].rolling(window=10).mean()
        hist['MA20'] = hist['Close'].rolling(window=20).mean()

        # 计算买入卖出信号
        hist['Buy_Signal'] = np.where((hist['Close'] > hist['MA20']) & (hist['Close'].shift(1) <= hist['MA20'].shift(1)), hist['Low'], np.nan)
        hist['Sell_Signal'] = np.where((hist['Close'] < hist['MA20']) & (hist['Close'].shift(1) >= hist['MA20'].shift(1)), hist['High'], np.nan)

        # 清除之前的图形
        self.figure.clear()

        # 创建子图
        ax1 = self.figure.add_subplot(211)
        ax2 = self.figure.add_subplot(212, sharex=ax1)

        # 创建买入卖出信号的绘图对象
        buy_signals = mpf.make_addplot(hist['Buy_Signal'], type='scatter', markersize=100, marker='^', color='lime', ax=ax1)
        sell_signals = mpf.make_addplot(hist['Sell_Signal'], type='scatter', markersize=100, marker='v', color='red', ax=ax1)

        # 定义均线颜色
        ma_colors = ['blue', 'orange', 'green']

        # 绘制K线图和信号
        mpf.plot(hist, type='candle', style='charles',
                 ylabel='价格',
                 volume=ax2,
                 mav=(5, 10, 20),
                 mavcolors=ma_colors,  # 设置均线颜色
                 addplot=[buy_signals, sell_signals],
                 ax=ax1,
                 datetime_format='%Y-%m-%d',
                 show_nontrading=False)

        # 设置标题和标签
        self.figure.suptitle(f'{ticker} 股票图表', fontproperties=chinese_font)
        ax2.set_xlabel('日期', fontproperties=chinese_font)
        ax1.set_ylabel('价格', fontproperties=chinese_font)
        ax2.set_ylabel('成交量', fontproperties=chinese_font)

        # 添加自定义图例
        custom_lines = [Line2D([0], [0], color=ma_colors[0], lw=2),
                         Line2D([0], [0], color=ma_colors[1], lw=2),
                         Line2D([0], [0], color=ma_colors[2], lw=2),
                         Line2D([0], [0], color='lime', marker='^', markersize=10, linestyle='None'),
                         Line2D([0], [0], color='red', marker='v', markersize=10, linestyle='None')]

        ax1.legend(custom_lines, ['MA5', 'MA10', 'MA20', '买入信号', '卖出信号'], 
                   loc='upper left', prop=chinese_font)

        # 调整布局
        self.figure.tight_layout()

        # 更新画布
        self.canvas.draw()

        # 打印最后几个交易日的数据，用于调试
        print(hist.tail())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = StockApp()
    ex.show()
    sys.exit(app.exec_())

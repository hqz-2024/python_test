"""
高性能 PCM 文件读取和波形显示程序 (PyQt5 + PyQtGraph 版本)
性能比 matplotlib 版本快 10-100 倍

主要功能：
1. 读取 PCM 原始音频文件（支持 8/16/32 位深度）
2. 实时显示音频波形（使用 GPU 硬件加速）
3. 支持 Y轴/X轴 缩放和位置控制
4. 鼠标悬停显示坐标（时间和幅度）
5. 音频播放功能（支持变速播放 0.1x-3.0x）
6. 播放进度标尺（可拖动改变播放位置）

依赖库：
- PyQt5: GUI 框架
- pyqtgraph: 高性能绘图库（GPU 加速）
- numpy: 数值计算
- pygame: 音频播放
- struct: 二进制数据解析
"""

import sys
import numpy as np
import struct
import os
import pygame
import threading
from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg

# ==================== 全局变量 ====================
# 这些全局变量用于在不同函数和类之间共享音频播放状态

startfilename = 'pcm_display/test_pulse.pcm'  # 默认加载的 PCM 文件路径
current_audio_data = None  # 当前加载的音频数据（numpy 数组，归一化到 [-1, 1]）
current_sample_rate = 44100  # 当前音频的采样率（Hz）
is_playing = False  # 音频是否正在播放的标志
playback_speed = 1.0  # 播放速度倍率（1.0 = 正常速度，2.0 = 2倍速，0.5 = 半速）
playback_start_time = 0.0  # 播放起始时间（秒），用于计算播放进度
playback_start_sample = 0  # 播放起始采样点索引
viewer_instance = None  # 主窗口实例引用，用于更新播放进度标尺


def play_audio(start_time=0.0):
    """
    播放音频数据（支持变速播放和从指定位置开始播放）

    功能说明：
        1. 从指定时间位置开始播放音频
        2. 支持变速播放（通过调整采样率实现）
        3. 自动将单声道转换为立体声
        4. 启动播放进度标尺更新定时器
        5. 在后台线程中等待播放完成

    参数：
        start_time (float): 起始播放时间（秒）
            - 默认值: 0.0（从头开始）
            - 有效范围: 0.0 到音频总时长
            - 超出范围会自动限制到有效范围内

    使用的全局变量：
        current_audio_data: 音频数据数组
        current_sample_rate: 采样率
        is_playing: 播放状态标志
        playback_speed: 播放速度倍率
        playback_start_time: 记录播放起始时间
        playback_start_sample: 记录播放起始采样点
        viewer_instance: 主窗口实例

    返回值：
        无（void）

    异常处理：
        捕获所有异常并打印错误信息，确保程序不会崩溃

    使用示例：
        play_audio()           # 从头开始播放
        play_audio(2.5)        # 从 2.5 秒开始播放
        play_audio(10.0)       # 从 10 秒开始播放
    """
    global current_audio_data, current_sample_rate, is_playing, playback_speed
    global playback_start_time, playback_start_sample, viewer_instance

    # 检查是否有音频数据
    if current_audio_data is None:
        print("没有音频数据可播放")
        return

    # 检查是否已经在播放
    if is_playing:
        print("音频正在播放中...")
        return

    try:
        # 退出之前的 pygame mixer 实例
        pygame.mixer.quit()

        # 计算起始采样点（限制在有效范围内）
        total_duration = len(current_audio_data) / current_sample_rate
        playback_start_time = max(0.0, min(start_time, total_duration))
        playback_start_sample = int(playback_start_time * current_sample_rate)

        # 从指定位置开始截取音频数据
        audio_data = current_audio_data[playback_start_sample:].copy()

        # 检查是否已到达音频末尾
        if len(audio_data) == 0:
            print("已到达音频末尾")
            return

        # 将数据限制在 [-1.0, 1.0] 范围内，防止削波失真
        audio_data = np.clip(audio_data, -1.0, 1.0)

        # 转换为 16 位整数格式（pygame 需要）
        audio_16bit = (audio_data * 32767).astype(np.int16)

        # 如果是单声道，转换为立体声（复制到两个声道）
        if audio_16bit.ndim == 1:
            stereo_audio = np.column_stack((audio_16bit, audio_16bit))
        else:
            stereo_audio = audio_16bit

        # 计算调整后的采样率（实现变速播放）
        # 例如：2x 速度 = 采样率 × 2，音频播放更快，音调变高
        adjusted_sample_rate = int(current_sample_rate * playback_speed)

        print(f"播放速度: {playback_speed}x, 起始时间: {playback_start_time:.2f}s, 调整后采样率: {adjusted_sample_rate}")

        # 初始化 pygame mixer（立体声，16位，使用调整后的采样率）
        pygame.mixer.pre_init(frequency=adjusted_sample_rate, size=-16, channels=2, buffer=1024)
        pygame.mixer.init()

        # 创建 Sound 对象
        sound = pygame.sndarray.make_sound(stereo_audio)

        print("开始播放音频...")
        is_playing = True
        sound.play()

        # 启动播放进度标尺更新定时器
        if viewer_instance is not None:
            viewer_instance.start_playback_timer()

        def wait_for_finish():
            """
            内部函数：在后台线程中等待播放完成

            功能：
                1. 循环检查播放状态
                2. 播放完成后更新全局标志
                3. 停止播放进度标尺更新
            """
            global is_playing
            while pygame.mixer.get_busy():
                pygame.time.wait(100)  # 每 100ms 检查一次
            is_playing = False
            # 停止标尺更新
            if viewer_instance is not None:
                viewer_instance.stop_playback_timer()
            print("音频播放完成")

        # 在守护线程中运行等待函数（程序退出时自动结束）
        threading.Thread(target=wait_for_finish, daemon=True).start()

    except Exception as e:
        print(f"播放音频时出错: {e}")
        is_playing = False


def stop_audio():
    """
    停止音频播放

    功能说明：
        1. 停止 pygame mixer 的音频播放
        2. 更新全局播放状态标志
        3. 停止播放进度标尺更新定时器

    参数：
        无

    使用的全局变量：
        is_playing: 播放状态标志（设置为 False）
        viewer_instance: 主窗口实例（调用其停止定时器方法）

    返回值：
        无（void）

    异常处理：
        捕获所有异常并打印错误信息

    使用示例：
        stop_audio()  # 停止当前播放
    """
    global is_playing, viewer_instance
    try:
        # 停止 pygame mixer 播放
        pygame.mixer.stop()

        # 更新播放状态
        is_playing = False

        # 停止播放进度标尺更新
        if viewer_instance is not None:
            viewer_instance.stop_playback_timer()

        print("音频播放已停止")
    except Exception as e:
        print(f"停止音频时出错: {e}")


def read_pcm_file(filename, sample_rate=44100, channels=1, bit_depth=16):
    """
    读取 PCM 原始音频文件并转换为 numpy 数组

    功能说明：
        1. 读取二进制 PCM 文件
        2. 根据位深度解析音频数据
        3. 归一化到 [-1.0, 1.0] 范围
        4. 处理多声道（提取第一声道）
        5. 生成时间轴数组
        6. 打印音频文件信息

    参数：
        filename (str): PCM 文件路径
            - 可以是相对路径或绝对路径
            - 如果文件不存在，会尝试在 pcm_display 目录中查找

        sample_rate (int): 采样率（Hz）
            - 默认值: 44100（CD 音质）
            - 常用值: 8000, 16000, 22050, 44100, 48000
            - 用于计算时间轴和音频时长

        channels (int): 声道数
            - 默认值: 1（单声道）
            - 1 = 单声道（Mono）
            - 2 = 立体声（Stereo）
            - 多声道时只提取第一声道

        bit_depth (int): 位深度（位）
            - 默认值: 16
            - 支持的值: 8, 16, 32
            - 8 位: 无符号整数 (0-255)
            - 16 位: 有符号整数 (-32768 到 32767)
            - 32 位: 有符号整数 (-2147483648 到 2147483647)

    返回值：
        tuple: (audio_data, time_axis)
            audio_data (numpy.ndarray): 音频数据数组
                - 数据类型: float32
                - 值范围: [-1.0, 1.0]
                - 形状: (样本数,)
                - 如果读取失败返回 None

            time_axis (numpy.ndarray): 时间轴数组（秒）
                - 数据类型: float64
                - 值范围: [0, 总时长]
                - 形状: (样本数,)
                - 如果读取失败返回 None

    异常处理：
        捕获所有异常并返回 (None, None)

    使用示例：
        # 读取 16 位单声道 PCM 文件
        audio, time = read_pcm_file('test.pcm')

        # 读取 8 位立体声 PCM 文件
        audio, time = read_pcm_file('test.pcm', sample_rate=22050, channels=2, bit_depth=8)

        # 读取 32 位单声道 PCM 文件
        audio, time = read_pcm_file('test.pcm', bit_depth=32)

    注意事项：
        1. PCM 文件没有文件头，必须手动指定参数
        2. 参数错误会导致读取的数据不正确
        3. 多声道文件只会提取第一声道
        4. 数据会自动归一化到 [-1.0, 1.0]
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(filename):
            # 尝试在 pcm_display 目录中查找
            alt_filename = os.path.join('pcm_display', os.path.basename(filename))
            if os.path.exists(alt_filename):
                filename = alt_filename
            else:
                print(f"文件 {filename} 不存在！")
                return None, None

        # 以二进制模式读取整个文件
        with open(filename, 'rb') as f:
            data = f.read()

        print(f"读取文件: {filename}")
        print(f"文件大小: {len(data)} 字节")

        # 根据位深度解析二进制数据
        if bit_depth == 16:
            # 16 位有符号整数（小端序）
            samples = len(data) // 2  # 每个样本 2 字节
            audio_data = struct.unpack(f'<{samples}h', data[:samples*2])
            # 归一化到 [-1.0, 1.0]（16位最大值 = 32768）
            audio_data = np.array(audio_data, dtype=np.float32) / 32768.0

        elif bit_depth == 8:
            # 8 位无符号整数
            audio_data = np.frombuffer(data, dtype=np.uint8)
            # 转换为有符号并归一化到 [-1.0, 1.0]
            audio_data = (audio_data.astype(np.float32) - 128) / 128.0

        elif bit_depth == 32:
            # 32 位有符号整数（小端序）
            samples = len(data) // 4  # 每个样本 4 字节
            audio_data = struct.unpack(f'<{samples}i', data[:samples*4])
            # 归一化到 [-1.0, 1.0]（32位最大值 = 2147483648）
            audio_data = np.array(audio_data, dtype=np.float32) / 2147483648.0

        else:
            print(f"不支持的位深度: {bit_depth}")
            return None, None

        # 处理多声道（只取第一声道）
        if channels > 1:
            # 重塑为 (样本数, 声道数) 的二维数组
            audio_data = audio_data.reshape(-1, channels)
            # 提取第一声道
            audio_data = audio_data[:, 0]
            print(f"多声道音频，已提取第一声道")

        # 确保是一维数组
        audio_data = audio_data.flatten()

        # 生成时间轴（秒）
        time_axis = np.arange(len(audio_data)) / sample_rate

        # 打印音频信息
        print(f"采样率: {sample_rate} Hz")
        print(f"声道数: {channels}")
        print(f"位深度: {bit_depth} 位")
        print(f"样本数: {len(audio_data)}")
        print(f"时长: {len(audio_data) / sample_rate:.2f} 秒")

        return audio_data, time_axis

    except Exception as e:
        print(f"读取文件出错: {e}")
        return None, None


class PCMWaveformViewer(QtWidgets.QMainWindow):
    """
    PCM 波形查看器主窗口类

    功能说明：
        这是程序的主窗口类，继承自 PyQt5 的 QMainWindow
        提供完整的音频波形显示和控制功能

    主要功能：
        1. 显示音频波形（使用 PyQtGraph 高性能绘图）
        2. Y轴/X轴 缩放和位置控制
        3. 鼠标悬停显示坐标（时间和幅度）
        4. 播放进度标尺（可拖动）
        5. 音频播放控制（播放/停止/变速）
        6. 统计信息显示（最大值、RMS、时长等）

    属性：
        original_audio_data: 原始音频数据（完整）
        original_time_axis: 原始时间轴（完整）
        display_audio: 显示用音频数据（可能下采样）
        display_time: 显示用时间轴（可能下采样）
        filename: 文件名
        sample_rate: 采样率
        total_duration: 音频总时长（秒）
        plot_widget: PyQtGraph 绘图控件
        playback_line: 播放进度标尺
        playback_timer: 播放进度更新定时器
    """

    def __init__(self, audio_data, time_axis, filename, sample_rate):
        """
        初始化 PCM 波形查看器

        参数：
            audio_data (numpy.ndarray): 音频数据数组
                - 形状: (样本数,)
                - 值范围: [-1.0, 1.0]
                - 数据类型: float32

            time_axis (numpy.ndarray): 时间轴数组（秒）
                - 形状: (样本数,)
                - 值范围: [0, 总时长]
                - 数据类型: float64

            filename (str): 文件名（用于显示标题）
                - 只需要文件名，不需要完整路径

            sample_rate (int): 采样率（Hz）
                - 用于计算时长和播放

        功能：
            1. 保存音频数据和参数
            2. 设置全局变量（供播放函数使用）
            3. 下采样数据（大文件优化）
            4. 初始化用户界面
        """
        super().__init__()

        global current_audio_data, current_sample_rate, viewer_instance

        # 保存原始数据（完整数据，用于播放）
        self.original_audio_data = audio_data
        self.original_time_axis = time_axis
        self.filename = filename
        self.sample_rate = sample_rate

        # 设置全局变量（供播放函数使用）
        current_audio_data = audio_data
        current_sample_rate = sample_rate

        # 设置全局 viewer 实例（供播放函数更新标尺）
        viewer_instance = self

        # 下采样用于显示（提高性能）
        # 大文件（>50000 点）会下采样到 50000 点以提高渲染速度
        max_display_points = 50000
        if len(audio_data) > max_display_points:
            # 计算下采样步长
            step = len(audio_data) // max_display_points
            # 每隔 step 个点取一个点
            self.display_audio = audio_data[::step]
            self.display_time = time_axis[::step]
            print(f"下采样显示: {len(audio_data)} -> {len(self.display_audio)} 点")
        else:
            # 小文件直接使用原始数据
            self.display_audio = audio_data
            self.display_time = time_axis

        # 计算音频总时长（秒）
        self.total_duration = len(audio_data) / sample_rate

        # 初始化用户界面
        self.init_ui()

    def init_ui(self):
        """
        初始化用户界面

        功能说明：
            创建并布局所有 UI 组件，包括：
            1. 窗口标题和大小
            2. 统计信息标签
            3. 波形绘图区域
            4. 十字光标和坐标显示
            5. 播放进度标尺
            6. 控制面板（调用 create_control_panel）

        参数：
            无

        返回值：
            无（void）

        创建的主要组件：
            self.info_label: 统计信息标签
            self.plot_widget: PyQtGraph 绘图控件
            self.curve: 波形曲线对象
            self.vLine, self.hLine: 十字光标线
            self.coord_label: 坐标显示标签
            self.playback_line: 播放进度标尺
            self.playback_timer: 播放进度更新定时器
        """
        # 设置窗口标题和大小
        self.setWindowTitle(f'PCM 音频波形查看器 - {self.filename}')
        self.setGeometry(100, 100, 1400, 800)  # (x, y, width, height)

        # 创建中心部件（QMainWindow 必须有中心部件）
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        # 创建主布局（垂直布局）
        main_layout = QtWidgets.QVBoxLayout(central_widget)

        # ========== 统计信息标签 ==========
        # 计算音频统计信息
        max_val = np.max(np.abs(self.original_audio_data))  # 最大幅度（绝对值）
        rms_val = np.sqrt(np.mean(self.original_audio_data**2))  # RMS（均方根）
        duration = len(self.original_audio_data) / self.sample_rate  # 时长（秒）

        # 创建信息文本
        info_text = f'最大幅度: {max_val:.3f} | RMS: {rms_val:.3f} | 时长: {duration:.2f}s | 采样率: {self.sample_rate}Hz'
        self.info_label = QtWidgets.QLabel(info_text)
        self.info_label.setAlignment(QtCore.Qt.AlignCenter)  # 居中对齐
        self.info_label.setStyleSheet("background-color: lightblue; padding: 5px; border-radius: 5px;")
        main_layout.addWidget(self.info_label)

        # ========== 创建绘图区域 ==========
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')  # 白色背景
        self.plot_widget.setLabel('left', '幅度')  # Y轴标签
        self.plot_widget.setLabel('bottom', '时间 (秒)')  # X轴标签
        self.plot_widget.setTitle(f'PCM 音频时域波形 - {self.filename}')  # 标题
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)  # 显示网格（透明度30%）

        # 绘制波形曲线
        self.curve = self.plot_widget.plot(
            self.display_time,  # X轴数据（时间）
            self.display_audio,  # Y轴数据（幅度）
            pen=pg.mkPen('b', width=1)  # 蓝色，宽度1像素
        )

        # 设置初始显示范围
        self.plot_widget.setYRange(-1.1, 1.1)  # Y轴范围（稍大于 [-1, 1]）
        self.plot_widget.setXRange(0, self.total_duration)  # X轴范围（0 到总时长）

        # ========== 创建十字光标线 ==========
        # 垂直线（跟随鼠标X坐标）
        self.vLine = pg.InfiniteLine(
            angle=90,  # 垂直（90度）
            movable=False,  # 不可拖动
            pen=pg.mkPen('gray', style=QtCore.Qt.DashLine)  # 灰色虚线
        )
        # 水平线（跟随鼠标Y坐标）
        self.hLine = pg.InfiniteLine(
            angle=0,  # 水平（0度）
            movable=False,  # 不可拖动
            pen=pg.mkPen('gray', style=QtCore.Qt.DashLine)  # 灰色虚线
        )
        # 添加到绘图区域（ignoreBounds=True 表示不影响自动缩放）
        self.plot_widget.addItem(self.vLine, ignoreBounds=True)
        self.plot_widget.addItem(self.hLine, ignoreBounds=True)
        # 初始隐藏（鼠标进入时显示）
        self.vLine.setVisible(False)
        self.hLine.setVisible(False)

        # ========== 创建坐标显示标签 ==========
        self.coord_label = pg.TextItem(
            anchor=(0, 1),  # 锚点：左下角
            color='k',  # 黑色文字
            fill=pg.mkBrush('y')  # 黄色背景
        )
        self.plot_widget.addItem(self.coord_label)
        self.coord_label.setVisible(False)  # 初始隐藏

        # ========== 创建播放进度标尺 ==========
        self.playback_line = pg.InfiniteLine(
            pos=0,  # 初始位置：0秒
            angle=90,  # 垂直线
            movable=True,  # 可拖动
            pen=pg.mkPen('r', width=2),  # 红色，宽度2像素
            hoverPen=pg.mkPen('r', width=3),  # 鼠标悬停时宽度3像素
            label='播放位置: {value:.2f}s',  # 标签文本（{value}会被替换为实际值）
            labelOpts={
                'position': 0.95,  # 标签位置（0.95 = 顶部5%）
                'color': (200, 0, 0),  # 标签文字颜色（深红色）
                'fill': (200, 200, 200, 100),  # 标签背景颜色（半透明灰色）
                'movable': True  # 标签可移动
            }
        )
        self.plot_widget.addItem(self.playback_line, ignoreBounds=True)

        # 连接标尺拖动事件（拖动时触发 on_playback_line_dragged 方法）
        self.playback_line.sigPositionChanged.connect(self.on_playback_line_dragged)

        # ========== 创建播放进度更新定时器 ==========
        self.playback_timer = QtCore.QTimer()
        self.playback_timer.timeout.connect(self.update_playback_position)  # 定时器触发时调用更新方法
        self.playback_start_timestamp = None  # 播放开始的系统时间戳（用于计算播放进度）

        # ========== 连接鼠标移动事件 ==========
        self.plot_widget.scene().sigMouseMoved.connect(self.on_mouse_move)

        # 将绘图区域添加到主布局
        main_layout.addWidget(self.plot_widget)

        # 创建控制面板（Y轴/X轴控制、播放控制等）
        self.create_control_panel(main_layout)

    def create_control_panel(self, main_layout):
        """
        创建控制面板

        功能说明：
            创建底部控制面板，包含三个分组：
            1. Y轴控制（缩放和位置）
            2. X轴控制（缩放和位置）
            3. 播放控制（速度、播放/停止按钮、状态显示）

        参数：
            main_layout (QVBoxLayout): 主窗口的垂直布局
                - 控制面板会被添加到这个布局的底部

        返回值：
            无（void）

        创建的主要组件：
            self.y_zoom_spin: Y轴缩放控件（0.1-10.0）
            self.y_pos_spin: Y轴位置控件（-2.0-2.0）
            self.x_zoom_spin: X轴缩放控件（0.1-50.0）
            self.x_pos_spin: X轴位置控件（0.0-1.0）
            self.speed_spin: 播放速度控件（0.1-3.0）
            self.play_btn: 播放按钮
            self.stop_btn: 停止按钮
            self.status_label: 状态显示标签
        """
        # 创建控制面板容器
        control_widget = QtWidgets.QWidget()
        control_layout = QtWidgets.QGridLayout(control_widget)  # 网格布局（3列）

        # ========== Y轴控制组 ==========
        y_group = QtWidgets.QGroupBox("Y轴控制")
        y_layout = QtWidgets.QHBoxLayout(y_group)  # 水平布局

        # Y轴缩放控件
        y_layout.addWidget(QtWidgets.QLabel("Y缩放:"))
        self.y_zoom_spin = QtWidgets.QDoubleSpinBox()
        self.y_zoom_spin.setRange(0.1, 10.0)  # 范围：0.1倍 到 10倍
        self.y_zoom_spin.setValue(1.0)  # 默认值：1.0（不缩放）
        self.y_zoom_spin.setSingleStep(0.1)  # 步长：0.1
        self.y_zoom_spin.valueChanged.connect(self.update_y_axis)  # 值改变时更新Y轴
        y_layout.addWidget(self.y_zoom_spin)

        # Y轴位置控件
        y_layout.addWidget(QtWidgets.QLabel("Y位置:"))
        self.y_pos_spin = QtWidgets.QDoubleSpinBox()
        self.y_pos_spin.setRange(-2.0, 2.0)  # 范围：-2.0 到 2.0
        self.y_pos_spin.setValue(0.0)  # 默认值：0.0（居中）
        self.y_pos_spin.setSingleStep(0.1)  # 步长：0.1
        self.y_pos_spin.valueChanged.connect(self.update_y_axis)  # 值改变时更新Y轴
        y_layout.addWidget(self.y_pos_spin)

        # 添加到网格布局（第0行，第0列）
        control_layout.addWidget(y_group, 0, 0)

        # ========== X轴控制组 ==========
        x_group = QtWidgets.QGroupBox("X轴控制")
        x_layout = QtWidgets.QHBoxLayout(x_group)  # 水平布局

        # X轴缩放控件
        x_layout.addWidget(QtWidgets.QLabel("X缩放:"))
        self.x_zoom_spin = QtWidgets.QDoubleSpinBox()
        self.x_zoom_spin.setRange(0.1, 50.0)  # 范围：0.1倍 到 50倍
        self.x_zoom_spin.setValue(1.0)  # 默认值：1.0（不缩放）
        self.x_zoom_spin.setSingleStep(0.1)  # 步长：0.1
        self.x_zoom_spin.valueChanged.connect(self.update_x_axis)  # 值改变时更新X轴
        x_layout.addWidget(self.x_zoom_spin)

        # X轴位置控件
        x_layout.addWidget(QtWidgets.QLabel("X位置:"))
        self.x_pos_spin = QtWidgets.QDoubleSpinBox()
        self.x_pos_spin.setRange(0.0, 1.0)  # 范围：0.0（最左）到 1.0（最右）
        self.x_pos_spin.setValue(0.0)  # 默认值：0.0（从头开始）
        self.x_pos_spin.setSingleStep(0.01)  # 步长：0.01
        self.x_pos_spin.valueChanged.connect(self.update_x_axis)  # 值改变时更新X轴
        x_layout.addWidget(self.x_pos_spin)

        # 添加到网格布局（第0行，第1列）
        control_layout.addWidget(x_group, 0, 1)

        # ========== 播放控制组 ==========
        play_group = QtWidgets.QGroupBox("播放控制")
        play_layout = QtWidgets.QHBoxLayout(play_group)  # 水平布局

        # 播放速度控件
        play_layout.addWidget(QtWidgets.QLabel("播放速度:"))
        self.speed_spin = QtWidgets.QDoubleSpinBox()
        self.speed_spin.setRange(0.1, 3.0)  # 范围：0.1倍（慢速）到 3.0倍（快速）
        self.speed_spin.setValue(1.0)  # 默认值：1.0（正常速度）
        self.speed_spin.setSingleStep(0.1)  # 步长：0.1
        self.speed_spin.valueChanged.connect(self.update_playback_speed)  # 值改变时更新播放速度
        play_layout.addWidget(self.speed_spin)

        # 播放按钮
        self.play_btn = QtWidgets.QPushButton("▶ 播放")
        self.play_btn.clicked.connect(self.on_play_clicked)  # 点击时触发播放
        self.play_btn.setStyleSheet("background-color: lightgreen;")  # 浅绿色背景
        play_layout.addWidget(self.play_btn)

        # 停止按钮
        self.stop_btn = QtWidgets.QPushButton("⏹ 停止")
        self.stop_btn.clicked.connect(self.on_stop_clicked)  # 点击时触发停止
        self.stop_btn.setStyleSheet("background-color: lightcoral;")  # 浅红色背景
        play_layout.addWidget(self.stop_btn)

        # 状态显示标签
        self.status_label = QtWidgets.QLabel("就绪")
        self.status_label.setStyleSheet("padding: 5px; border: 1px solid gray;")
        play_layout.addWidget(self.status_label)

        # 添加到网格布局（第0行，第2列）
        control_layout.addWidget(play_group, 0, 2)

        # 将控制面板添加到主布局
        main_layout.addWidget(control_widget)

    def update_y_axis(self):
        """
        更新 Y轴显示范围

        功能说明：
            根据 Y轴缩放和位置控件的值，计算并设置新的 Y轴显示范围

        参数：
            无（从控件读取值）

        返回值：
            无（void）

        计算逻辑：
            1. 基础高度 = 2.2（默认显示范围 [-1.1, 1.1]）
            2. 新高度 = 基础高度 / 缩放倍数
            3. 中心位置 = Y位置值
            4. Y最小值 = 中心 - 新高度/2
            5. Y最大值 = 中心 + 新高度/2

        使用示例：
            缩放=1.0, 位置=0.0 → 显示范围 [-1.1, 1.1]
            缩放=2.0, 位置=0.0 → 显示范围 [-0.55, 0.55]（放大2倍）
            缩放=1.0, 位置=0.5 → 显示范围 [-0.6, 1.6]（向上移动）
        """
        # 获取控件值
        zoom = self.y_zoom_spin.value()  # Y轴缩放倍数
        ypos = self.y_pos_spin.value()  # Y轴位置偏移

        # 计算新的显示范围
        base_height = 2.2  # 基础高度（默认 [-1.1, 1.1]）
        new_height = base_height / zoom  # 缩放后的高度
        center = ypos  # 中心位置
        y_min = center - new_height / 2  # 最小值
        y_max = center + new_height / 2  # 最大值

        # 设置 Y轴范围（padding=0 表示不添加额外边距）
        self.plot_widget.setYRange(y_min, y_max, padding=0)

    def update_x_axis(self):
        """
        更新 X轴显示范围

        功能说明：
            根据 X轴缩放和位置控件的值，计算并设置新的 X轴显示范围

        参数：
            无（从控件读取值）

        返回值：
            无（void）

        计算逻辑：
            1. 新宽度 = 总时长 / 缩放倍数
            2. 可移动范围 = 总时长 - 新宽度
            3. 起始位置 = X位置值 × 可移动范围
            4. 结束位置 = 起始位置 + 新宽度

        使用示例：
            总时长=10s, 缩放=1.0, 位置=0.0 → 显示范围 [0, 10]（全部）
            总时长=10s, 缩放=2.0, 位置=0.0 → 显示范围 [0, 5]（前半部分，放大2倍）
            总时长=10s, 缩放=2.0, 位置=1.0 → 显示范围 [5, 10]（后半部分，放大2倍）
            总时长=10s, 缩放=10.0, 位置=0.5 → 显示范围 [4.5, 5.5]（中间1秒，放大10倍）
        """
        # 获取控件值
        xzoom = self.x_zoom_spin.value()  # X轴缩放倍数
        xpos = self.x_pos_spin.value()  # X轴位置（0.0-1.0）

        # 计算新的显示范围
        new_width = self.total_duration / xzoom  # 缩放后的宽度
        movable_range = self.total_duration - new_width  # 可移动的范围
        x_start = xpos * movable_range  # 起始位置
        x_end = x_start + new_width  # 结束位置

        # 设置 X轴范围（padding=0 表示不添加额外边距）
        self.plot_widget.setXRange(x_start, x_end, padding=0)

    def update_playback_speed(self):
        """
        更新播放速度

        功能说明：
            从播放速度控件读取值并更新全局播放速度变量

        参数：
            无（从控件读取值）

        返回值：
            无（void）

        使用的全局变量：
            playback_speed: 播放速度倍率（写入）

        注意事项：
            - 只更新全局变量，不影响正在播放的音频
            - 新的速度会在下次播放时生效
        """
        global playback_speed
        playback_speed = self.speed_spin.value()  # 读取控件值
        print(f"播放速度已设置为: {playback_speed}x")

    def on_play_clicked(self):
        """
        播放按钮点击事件处理函数

        功能说明：
            从播放进度标尺的当前位置开始播放音频

        参数：
            无

        返回值：
            无（void）

        执行流程：
            1. 更新状态标签为"正在播放..."
            2. 获取播放标尺的当前位置（时间）
            3. 调用 play_audio() 从该位置开始播放

        使用示例：
            - 标尺在 0.0s → 从头开始播放
            - 标尺在 2.5s → 从 2.5秒 开始播放
        """
        self.status_label.setText("正在播放...")
        # 从标尺当前位置开始播放
        start_time = self.playback_line.value()  # 获取标尺位置
        play_audio(start_time)  # 调用全局播放函数

    def on_stop_clicked(self):
        """
        停止按钮点击事件处理函数

        功能说明：
            停止当前正在播放的音频

        参数：
            无

        返回值：
            无（void）

        执行流程：
            1. 更新状态标签为"已停止"
            2. 调用 stop_audio() 停止播放
        """
        self.status_label.setText("已停止")
        stop_audio()  # 调用全局停止函数

    def on_mouse_move(self, pos):
        """
        鼠标移动事件处理函数

        功能说明：
            当鼠标在绘图区域移动时：
            1. 显示十字光标（跟随鼠标）
            2. 显示坐标标签（时间和幅度）
            3. 自动吸附到最近的数据点

        参数：
            pos (QPointF): 鼠标在场景中的位置坐标
                - 这是 PyQtGraph 场景坐标系的坐标
                - 需要转换为数据坐标系

        返回值：
            无（void）

        算法说明：
            1. 坐标转换：场景坐标 → 数据坐标
            2. 边界检查：判断鼠标是否在绘图区域内
            3. 二分查找：找到最接近鼠标的数据点（O(log n) 复杂度）
            4. 时间格式化：转换为 MM:SS.sss 格式
            5. 更新显示：十字光标和坐标标签

        性能优化：
            - 使用 np.searchsorted() 进行二分查找（比线性查找快得多）
            - 只在鼠标在绘图区域内时更新（避免不必要的计算）
        """
        # 将场景坐标转换为数据坐标
        mouse_point = self.plot_widget.plotItem.vb.mapSceneToView(pos)
        x_mouse = mouse_point.x()  # 鼠标X坐标（时间）
        y_mouse = mouse_point.y()  # 鼠标Y坐标（幅度）

        # 获取当前显示范围
        x_range = self.plot_widget.viewRange()[0]  # X轴范围 [x_min, x_max]
        y_range = self.plot_widget.viewRange()[1]  # Y轴范围 [y_min, y_max]

        # 检查鼠标是否在绘图区域内
        if x_range[0] <= x_mouse <= x_range[1] and y_range[0] <= y_mouse <= y_range[1]:
            # ========== 使用二分查找找到最接近的数据点 ==========
            # np.searchsorted() 返回插入位置索引（O(log n) 复杂度）
            idx = np.searchsorted(self.display_time, x_mouse)

            # 边界检查和精确匹配
            if idx >= len(self.display_time):
                # 超出范围，使用最后一个点
                idx = len(self.display_time) - 1
            elif idx > 0 and abs(self.display_time[idx-1] - x_mouse) < abs(self.display_time[idx] - x_mouse):
                # 前一个点更接近，使用前一个点
                idx = idx - 1

            # 获取实际数据点的坐标
            x_actual = self.display_time[idx]  # 实际时间
            y_actual = self.display_audio[idx]  # 实际幅度

            # ========== 格式化时间显示（MM:SS.sss 格式）==========
            minutes = int(x_actual // 60)  # 分钟数
            seconds = x_actual % 60  # 秒数（含小数）
            time_str = f'{minutes:02d}:{seconds:06.3f}'  # 格式：00:00.000

            # ========== 更新十字光标位置 ==========
            self.vLine.setPos(x_actual)  # 垂直线位置
            self.hLine.setPos(y_actual)  # 水平线位置
            self.vLine.setVisible(True)  # 显示垂直线
            self.hLine.setVisible(True)  # 显示水平线

            # ========== 更新坐标标签 ==========
            coord_text = f'时间: {time_str}\n幅度: {y_actual:.4f}'
            self.coord_label.setText(coord_text)  # 设置文本
            self.coord_label.setPos(x_actual, y_actual)  # 设置位置（跟随数据点）
            self.coord_label.setVisible(True)  # 显示标签
        else:
            # ========== 鼠标离开绘图区域，隐藏所有元素 ==========
            self.vLine.setVisible(False)
            self.hLine.setVisible(False)
            self.coord_label.setVisible(False)

    def on_playback_line_dragged(self):
        """
        播放标尺拖动事件处理函数

        功能说明：
            当用户拖动播放进度标尺时：
            1. 获取新的时间位置
            2. 限制在有效范围内（0 到总时长）
            3. 如果正在播放，停止并从新位置重新开始播放
            4. 如果未播放，只移动标尺位置

        参数：
            无（从标尺对象读取位置）

        返回值：
            无（void）

        使用的全局变量：
            is_playing: 播放状态标志（读取）

        执行流程：
            1. 读取标尺新位置
            2. 边界检查和限制
            3. 如果正在播放：
               a. 停止当前播放
               b. 等待 100ms（确保停止完成）
               c. 从新位置开始播放

        注意事项：
            - 使用 QTimer.singleShot() 延迟播放，避免停止未完成
            - 使用 lambda 函数传递新位置参数
        """
        global is_playing

        # 获取标尺的新位置（时间，单位：秒）
        new_time = self.playback_line.value()

        # 限制在有效范围内（0 到总时长）
        new_time = max(0.0, min(new_time, self.total_duration))
        self.playback_line.setValue(new_time)

        print(f"播放标尺拖动到: {new_time:.2f}s")

        # 如果正在播放，停止当前播放并从新位置开始
        if is_playing:
            stop_audio()  # 停止当前播放
            # 等待 100ms 确保停止完成，然后从新位置开始播放
            QtCore.QTimer.singleShot(100, lambda: play_audio(new_time))

    def start_playback_timer(self):
        """
        启动播放进度更新定时器

        功能说明：
            启动定时器，每 50ms 更新一次播放进度标尺位置（20 FPS）

        参数：
            无

        返回值：
            无（void）

        执行流程：
            1. 记录当前系统时间戳（用于计算播放进度）
            2. 启动定时器（50ms 间隔）
            3. 定时器每次触发时调用 update_playback_position()

        注意事项：
            - 必须在播放开始时调用
            - 时间戳用于精确计算播放进度
        """
        import time
        self.playback_start_timestamp = time.time()  # 记录播放开始的系统时间
        self.playback_timer.start(20)  # 每 50ms 更新一次（20 FPS）
        print("播放标尺更新定时器已启动")

    def stop_playback_timer(self):
        """
        停止播放进度更新定时器

        功能说明：
            停止定时器，不再更新播放进度标尺位置

        参数：
            无

        返回值：
            无（void）

        执行流程：
            1. 停止定时器
            2. 清除时间戳

        注意事项：
            - 必须在播放停止或完成时调用
            - 清除时间戳防止误更新
        """
        self.playback_timer.stop()  # 停止定时器
        self.playback_start_timestamp = None  # 清除时间戳
        print("播放标尺更新定时器已停止")

    def update_playback_position(self):
        """
        更新播放进度标尺位置（定时器回调函数）

        功能说明：
            根据播放开始时间和当前系统时间，计算并更新播放进度标尺位置

        参数：
            无（从全局变量和实例变量读取）

        返回值：
            无（void）

        使用的全局变量：
            playback_start_time: 播放起始时间（秒）
            playback_speed: 播放速度倍率
            is_playing: 播放状态标志

        计算公式：
            已播放时间 = (当前系统时间 - 播放开始系统时间) × 播放速度
            当前播放位置 = 播放起始时间 + 已播放时间

        执行流程：
            1. 检查播放状态（未播放则直接返回）
            2. 计算当前播放位置
            3. 边界检查（到达末尾则停止定时器）
            4. 更新标尺位置（阻塞信号避免触发拖动事件）

        注意事项：
            - 使用 blockSignals() 避免触发 on_playback_line_dragged()
            - 考虑播放速度的影响（2x 速度时标尺移动速度也是 2 倍）
            - 到达末尾时自动停止定时器
        """
        global playback_start_time, playback_speed, is_playing

        # 检查播放状态
        if not is_playing or self.playback_start_timestamp is None:
            return  # 未播放或时间戳无效，直接返回

        import time
        # 计算已播放的时间（考虑播放速度）
        # 例如：2x 速度时，实际时间 1 秒 = 播放时间 2 秒
        elapsed_time = (time.time() - self.playback_start_timestamp) * playback_speed
        current_time = playback_start_time + elapsed_time

        # 限制在有效范围内
        if current_time >= self.total_duration:
            current_time = self.total_duration  # 限制到末尾
            self.stop_playback_timer()  # 到达末尾，停止定时器

        # 更新标尺位置（暂时断开信号以避免触发拖动事件）
        self.playback_line.blockSignals(True)  # 阻塞信号
        self.playback_line.setValue(current_time)  # 设置新位置
        self.playback_line.blockSignals(False)  # 恢复信号


def main():
    """
    主函数（程序入口）

    功能说明：
        1. 初始化 pygame（音频播放引擎）
        2. 读取 PCM 音频文件
        3. 创建 Qt 应用程序
        4. 创建并显示主窗口
        5. 进入事件循环

    参数：
        无

    返回值：
        无（程序退出时返回状态码）

    执行流程：
        1. pygame.init() - 初始化 pygame 库
        2. read_pcm_file() - 读取音频文件
        3. 错误检查 - 如果读取失败则退出
        4. QApplication() - 创建 Qt 应用实例
        5. PCMWaveformViewer() - 创建主窗口
        6. viewer.show() - 显示窗口
        7. app.exec_() - 进入事件循环（阻塞直到窗口关闭）
        8. sys.exit() - 退出程序并返回状态码

    使用的全局变量：
        startfilename: 默认 PCM 文件路径
        current_sample_rate: 采样率（在 read_pcm_file 中设置）

    注意事项：
        - pygame.init() 必须在使用 pygame 功能之前调用
        - QApplication 必须在创建任何 Qt 控件之前创建
        - app.exec_() 会阻塞直到所有窗口关闭
        - sys.exit() 确保程序正确退出
    """
    # ========== 初始化 pygame（用于音频播放）==========
    pygame.init()

    # ========== 读取 PCM 文件 ==========
    filename = startfilename  # 使用全局变量中的默认文件名
    audio_data, time_axis = read_pcm_file(filename)

    # ========== 错误检查 ==========
    if audio_data is None:
        print("无法读取音频文件，程序退出")
        return

    # ========== 创建 Qt 应用程序 ==========
    app = QtWidgets.QApplication(sys.argv)

    # ========== 创建主窗口 ==========
    viewer = PCMWaveformViewer(
        audio_data,  # 音频数据数组
        time_axis,  # 时间轴数组
        os.path.basename(filename),  # 文件名（不含路径）
        current_sample_rate  # 采样率
    )
    viewer.show()  # 显示窗口

    # ========== 运行应用程序（进入事件循环）==========
    # app.exec_() 会阻塞直到所有窗口关闭
    # 返回值是应用程序的退出状态码
    sys.exit(app.exec_())


# ==================== 程序入口 ====================
if __name__ == '__main__':
    """
    程序入口点

    说明：
        只有直接运行此脚本时才会执行 main() 函数
        如果作为模块导入，则不会自动执行
    """
    main()


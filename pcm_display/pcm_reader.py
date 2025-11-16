"""
简化版 PCM 文件读取和波形显示程序
"""

import numpy as np
import matplotlib.pyplot as plt
import struct
import os
import pygame
import threading
from matplotlib.widgets import Button, Slider, TextBox


# 全局变量用于音频播放
startfilename = 'pcm_display/test_mixed.pcm'
current_audio_data = None
current_sample_rate = 44100
is_playing = False
playback_speed = 1.0  # 播放速度，1.0为正常速度

def play_audio():
    """
    播放音频数据（支持变速播放）
    """
    global current_audio_data, current_sample_rate, is_playing, playback_speed

    if current_audio_data is None:
        print("没有音频数据可播放")
        return

    if is_playing:
        print("音频正在播放中...")
        return

    try:
        # 停止之前的播放
        pygame.mixer.quit()

        # 准备音频数据
        audio_data = current_audio_data.copy()

        # 确保数据在 [-1, 1] 范围内
        audio_data = np.clip(audio_data, -1.0, 1.0)

        # 转换为 16 位整数
        audio_16bit = (audio_data * 32767).astype(np.int16)

        # 创建立体声数据（复制单声道到两个声道）
        if audio_16bit.ndim == 1:
            # 创建立体声：(samples, 2)
            stereo_audio = np.column_stack((audio_16bit, audio_16bit))
        else:
            stereo_audio = audio_16bit

        # 计算调整后的采样率（通过改变采样率来改变播放速度）
        adjusted_sample_rate = int(current_sample_rate * playback_speed)

        print(f"播放数据形状: {stereo_audio.shape}")
        print(f"播放数据类型: {stereo_audio.dtype}")
        print(f"原始采样率: {current_sample_rate}")
        print(f"播放速度: {playback_speed}x")
        print(f"调整后采样率: {adjusted_sample_rate}")

        # 初始化 pygame mixer（立体声，使用调整后的采样率）
        pygame.mixer.pre_init(frequency=adjusted_sample_rate, size=-16, channels=2, buffer=1024)
        pygame.mixer.init()

        # 创建 Sound 对象并播放
        sound = pygame.sndarray.make_sound(stereo_audio)

        print("开始播放音频...")
        is_playing = True
        sound.play()

        # 等待播放完成
        def wait_for_finish():
            global is_playing
            while pygame.mixer.get_busy():
                pygame.time.wait(100)
            is_playing = False
            print("音频播放完成")

        # 在新线程中等待播放完成
        threading.Thread(target=wait_for_finish, daemon=True).start()

    except Exception as e:
        print(f"播放音频时出错: {e}")
        print(f"音频数据形状: {current_audio_data.shape if current_audio_data is not None else 'None'}")
        print(f"音频数据类型: {current_audio_data.dtype if current_audio_data is not None else 'None'}")
        is_playing = False

def stop_audio():
    """
    停止音频播放
    """
    global is_playing
    try:
        pygame.mixer.stop()
        is_playing = False
        print("音频播放已停止")
    except:
        pass

def read_pcm_simple(filename, sample_rate=44100, channels=1, bit_depth=16):
    """
    简单读取 PCM 文件
    
    参数:
        filename: PCM 文件名
        sample_rate: 采样率，默认 44100 Hz
        channels: 声道数，默认 1
        bit_depth: 位深度，默认 16 位
    """
    try:
        # 检查文件
        if not os.path.exists(filename):
            print(f"文件 {filename} 不存在！")
            return None, None
        
        # 读取文件
        with open(filename, 'rb') as f:
            data = f.read()
        
        print(f"读取文件: {filename}")
        print(f"文件大小: {len(data)} 字节")
        
        # 根据位深度解析数据
        if bit_depth == 16:
            # 16位有符号整数
            samples = len(data) // 2  # 每个样本2字节
            audio_data = struct.unpack(f'<{samples}h', data[:samples*2])
            audio_data = np.array(audio_data, dtype=np.float32) / 32768.0
        elif bit_depth == 8:
            # 8位无符号整数
            audio_data = np.frombuffer(data, dtype=np.uint8)
            audio_data = (audio_data.astype(np.float32) - 128) / 128.0
        elif bit_depth == 32:
            # 32位有符号整数
            samples = len(data) // 4  # 每个样本4字节
            audio_data = struct.unpack(f'<{samples}i', data[:samples*4])
            audio_data = np.array(audio_data, dtype=np.float32) / 2147483648.0
        else:
            print(f"不支持的位深度: {bit_depth}")
            return None, None
        
        # 处理多声道（只取第一声道）
        if channels > 1:
            audio_data = audio_data.reshape(-1, channels)
            audio_data = audio_data[:, 0]  # 取第一声道
            print(f"多声道音频，已提取第一声道")

        # 确保是一维数组
        audio_data = audio_data.flatten()

        # 创建时间轴
        time_axis = np.arange(len(audio_data)) / sample_rate
        
        print(f"采样率: {sample_rate} Hz")
        print(f"声道数: {channels}")
        print(f"位深度: {bit_depth} 位")
        print(f"样本数: {len(audio_data)}")
        print(f"时长: {len(audio_data) / sample_rate:.2f} 秒")
        
        return audio_data, time_axis
        
    except Exception as e:
        print(f"读取文件出错: {e}")
        return None, None

def plot_waveform_simple(audio_data, time_axis, filename, original_audio_data, sample_rate):
    """
    绘制简单的时域波形图，带播放按钮
    """
    global current_audio_data, current_sample_rate

    if audio_data is None:
        print("没有音频数据可显示")
        return

    # 保存原始音频数据用于播放
    current_audio_data = original_audio_data
    current_sample_rate = sample_rate

    # 如果数据太多，进行下采样（仅用于显示）
    display_audio = audio_data.copy()
    display_time = time_axis.copy()

    max_points = 50000
    if len(display_audio) > max_points:
        step = len(display_audio) // max_points
        display_audio = display_audio[::step]
        display_time = display_time[::step]
        print(f"显示数据下采样到 {len(display_audio)} 个点")

    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
    plt.rcParams['axes.unicode_minus'] = False

    # 创建图形和子图
    fig, ax = plt.subplots(figsize=(12, 7))

    # 为按钮和滑块留出空间（优化布局，顶部留更多空间）
    plt.subplots_adjust(left=0.12, bottom=0.18, right=0.97, top=0.90)

    # 绘制波形
    ax.plot(display_time, display_audio, 'b-', linewidth=0.5)

    # 设置标题和标签
    ax.set_title(f'PCM 音频时域波形 - {filename}', fontsize=13, pad=20)
    ax.set_xlabel('时间 (秒)', fontsize=11)
    ax.set_ylabel('幅度', fontsize=11)

    # 设置网格
    ax.grid(True, alpha=0.3, linewidth=0.5)

    # 保存初始显示范围
    total_duration = len(original_audio_data) / sample_rate
    initial_xlim = (0, total_duration)
    initial_ylim = (-1.1, 1.1)

    # 设置初始轴范围
    ax.set_ylim(initial_ylim)
    ax.set_xlim(initial_xlim)

    # 显示统计信息（在标题下方）
    max_val = np.max(np.abs(original_audio_data))
    rms_val = np.sqrt(np.mean(original_audio_data**2))
    duration = len(original_audio_data) / sample_rate

    info_text = f'最大幅度: {max_val:.3f} | RMS: {rms_val:.3f} | 时长: {duration:.2f}s | 采样率: {sample_rate}Hz'
    ax.text(0.5, 1.04, info_text, transform=ax.transAxes,
            ha='center', va='bottom', fontsize=9,
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7, pad=0.3))

    # ========== Y轴控制区域（左侧） ==========
    # Y轴缩放滑块
    ax_yzoom = plt.axes([0.025, 0.30, 0.015, 0.50])
    slider_yzoom = Slider(
        ax=ax_yzoom,
        label='Y缩放',
        valmin=0.1,
        valmax=10.0,
        valinit=1.0,
        orientation='vertical'
    )
    # Y缩放输入框（在滑块正上方）
    ax_yzoom_input = plt.axes([0.012, 0.85, 0.04, 0.025])
    textbox_yzoom = TextBox(ax_yzoom_input, '', initial='1.0')

    # Y轴位置滑块
    ax_ypos = plt.axes([0.07, 0.30, 0.015, 0.50])
    slider_ypos = Slider(
        ax=ax_ypos,
        label='Y位置',
        valmin=-2.0,
        valmax=2.0,
        valinit=0.0,
        orientation='vertical'
    )
    # Y位置输入框（在滑块正上方）
    ax_ypos_input = plt.axes([0.057, 0.85, 0.04, 0.025])
    textbox_ypos = TextBox(ax_ypos_input, '', initial='0.0')

    # ========== X轴控制区域（底部） ==========
    # X轴缩放滑块
    ax_xzoom = plt.axes([0.12, 0.11, 0.35, 0.015])
    slider_xzoom = Slider(
        ax=ax_xzoom,
        label='X缩放',
        valmin=0.1,
        valmax=10.0,
        valinit=1.0,
        orientation='horizontal'
    )
    # X缩放输入框
    ax_xzoom_input = plt.axes([0.48, 0.105, 0.04, 0.025])
    textbox_xzoom = TextBox(ax_xzoom_input, '', initial='1.0')

    # X轴位置滑块
    ax_xpos = plt.axes([0.12, 0.07, 0.35, 0.015])
    slider_xpos = Slider(
        ax=ax_xpos,
        label='X位置',
        valmin=0.0,
        valmax=1.0,
        valinit=0.0,
        orientation='horizontal'
    )
    # X位置输入框
    ax_xpos_input = plt.axes([0.48, 0.065, 0.04, 0.025])
    textbox_xpos = TextBox(ax_xpos_input, '', initial='0.0')

    # ========== 播放控制区域（底部右侧） ==========
    # 播放速度标签和输入框
    ax_speed_label = plt.axes([0.54, 0.105, 0.08, 0.025])
    ax_speed_label.text(0.5, 0.5, '播放速度:', ha='center', va='center', fontsize=9)
    ax_speed_label.set_xticks([])
    ax_speed_label.set_yticks([])
    ax_speed_label.patch.set_visible(False)

    ax_speed_input = plt.axes([0.63, 0.105, 0.04, 0.025])
    textbox_speed = TextBox(ax_speed_input, '', initial='1.0')

    # 播放按钮
    ax_play = plt.axes([0.12, 0.02, 0.08, 0.035])
    button_play = Button(ax_play, '▶ 播放', color='lightgreen', hovercolor='green')

    # 停止按钮
    ax_stop = plt.axes([0.21, 0.02, 0.08, 0.035])
    button_stop = Button(ax_stop, '⏹ 停止', color='lightcoral', hovercolor='red')

    # 状态显示
    ax_status = plt.axes([0.31, 0.02, 0.25, 0.035])
    status_text = ax_status.text(0.5, 0.5, '准备播放', ha='center', va='center',
                                transform=ax_status.transAxes, fontsize=10)
    ax_status.set_xticks([])
    ax_status.set_yticks([])

    # Y轴控制函数（优化性能）
    def update_y_axis(val=None):
        """更新Y轴显示范围"""
        zoom = slider_yzoom.val
        ypos = slider_ypos.val

        # 只在值改变时更新输入框（避免不必要的更新）
        zoom_str = f'{zoom:.2f}'
        ypos_str = f'{ypos:.2f}'
        if textbox_yzoom.text != zoom_str:
            textbox_yzoom.set_val(zoom_str)
        if textbox_ypos.text != ypos_str:
            textbox_ypos.set_val(ypos_str)

        # 计算新的Y轴范围
        base_height = 2.2
        new_height = base_height / zoom
        center = ypos
        y_min = center - new_height / 2
        y_max = center + new_height / 2

        ax.set_ylim(y_min, y_max)
        fig.canvas.draw_idle()

    # X轴控制函数（优化性能）
    def update_x_axis(val=None):
        """更新X轴显示范围"""
        xzoom = slider_xzoom.val
        xpos = slider_xpos.val

        # 只在值改变时更新输入框
        xzoom_str = f'{xzoom:.2f}'
        xpos_str = f'{xpos:.2f}'
        if textbox_xzoom.text != xzoom_str:
            textbox_xzoom.set_val(xzoom_str)
        if textbox_xpos.text != xpos_str:
            textbox_xpos.set_val(xpos_str)

        # 计算新的X轴范围
        # 基础范围是 0 到 total_duration
        base_width = total_duration
        new_width = base_width / xzoom  # 缩放后的宽度

        # 计算可移动的范围
        max_offset = base_width - new_width
        if max_offset < 0:
            max_offset = 0

        # 根据位置滑块计算起始位置
        x_start = xpos * max_offset
        x_end = x_start + new_width

        # 确保不超出边界
        if x_end > base_width:
            x_end = base_width
            x_start = x_end - new_width
        if x_start < 0:
            x_start = 0
            x_end = new_width

        ax.set_xlim(x_start, x_end)
        fig.canvas.draw_idle()

    # 输入框回调函数
    def on_yzoom_input(text):
        """Y缩放输入框回调"""
        try:
            value = float(text)
            # 限制在有效范围内
            value = max(0.1, min(10.0, value))
            slider_yzoom.set_val(value)
        except ValueError:
            # 输入无效，恢复当前值
            textbox_yzoom.set_val(f'{slider_yzoom.val:.2f}')

    def on_ypos_input(text):
        """Y位置输入框回调"""
        try:
            value = float(text)
            # 限制在有效范围内
            value = max(-2.0, min(2.0, value))
            slider_ypos.set_val(value)
        except ValueError:
            # 输入无效，恢复当前值
            textbox_ypos.set_val(f'{slider_ypos.val:.2f}')

    def on_xzoom_input(text):
        """X缩放输入框回调"""
        try:
            value = float(text)
            # 限制在有效范围内
            value = max(0.1, min(10.0, value))
            slider_xzoom.set_val(value)
        except ValueError:
            # 输入无效，恢复当前值
            textbox_xzoom.set_val(f'{slider_xzoom.val:.2f}')

    def on_xpos_input(text):
        """X位置输入框回调"""
        try:
            value = float(text)
            # 限制在有效范围内
            value = max(0.0, min(1.0, value))
            slider_xpos.set_val(value)
        except ValueError:
            # 输入无效，恢复当前值
            textbox_xpos.set_val(f'{slider_xpos.val:.2f}')

    def on_speed_input(text):
        """播放速度输入框回调"""
        global playback_speed
        try:
            value = float(text)
            # 限制在有效范围内（0.1x - 3.0x）
            value = max(0.1, min(3.0, value))
            playback_speed = value
            textbox_speed.set_val(f'{value:.2f}')
            print(f"播放速度已设置为: {playback_speed}x")
        except ValueError:
            # 输入无效，恢复当前值
            textbox_speed.set_val(f'{playback_speed:.2f}')

    # 绑定滑块事件
    slider_yzoom.on_changed(update_y_axis)
    slider_ypos.on_changed(update_y_axis)
    slider_xzoom.on_changed(update_x_axis)
    slider_xpos.on_changed(update_x_axis)

    # 绑定输入框事件
    textbox_yzoom.on_submit(on_yzoom_input)
    textbox_ypos.on_submit(on_ypos_input)
    textbox_xzoom.on_submit(on_xzoom_input)
    textbox_xpos.on_submit(on_xpos_input)
    textbox_speed.on_submit(on_speed_input)

    # 创建坐标显示标注（初始时不可见）
    coord_annotation = ax.annotate('', xy=(0, 0), xytext=(20, 20),
                                   textcoords='offset points',
                                   bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.9),
                                   arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'),
                                   fontsize=10, visible=False)

    # 创建十字光标线（初始时不可见）
    cursor_vline = ax.axvline(x=0, color='gray', linestyle='--', linewidth=1, alpha=0.7, visible=False)
    cursor_hline = ax.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.7, visible=False)

    # 鼠标移动事件处理（优化性能）
    last_mouse_pos = [None, None]  # 缓存上次鼠标位置，避免重复计算

    def on_mouse_move(event):
        """鼠标移动时显示坐标信息"""
        if event.inaxes == ax:
            x_mouse = event.xdata
            y_mouse = event.ydata

            if x_mouse is not None and y_mouse is not None:
                # 如果鼠标位置变化很小，跳过更新（优化性能）
                if last_mouse_pos[0] is not None:
                    dx = abs(x_mouse - last_mouse_pos[0])
                    dy = abs(y_mouse - last_mouse_pos[1])
                    if dx < total_duration * 0.001 and dy < 0.01:  # 变化小于0.1%
                        return

                last_mouse_pos[0] = x_mouse
                last_mouse_pos[1] = y_mouse

                # 使用二分查找找到最接近的点
                idx = np.searchsorted(display_time, x_mouse)
                if idx >= len(display_time):
                    idx = len(display_time) - 1
                elif idx > 0 and abs(display_time[idx-1] - x_mouse) < abs(display_time[idx] - x_mouse):
                    idx = idx - 1

                x_actual = display_time[idx]
                y_actual = display_audio[idx]

                # 格式化时间显示
                minutes = int(x_actual // 60)
                seconds = x_actual % 60
                time_str = f'{minutes:02d}:{seconds:06.3f}'

                # 更新标注和光标
                coord_annotation.set_text(f'时间: {time_str}\n幅度: {y_actual:.4f}')
                coord_annotation.xy = (x_actual, y_actual)
                coord_annotation.set_visible(True)
                cursor_vline.set_xdata([x_actual, x_actual])
                cursor_vline.set_visible(True)
                cursor_hline.set_ydata([y_actual, y_actual])
                cursor_hline.set_visible(True)

                fig.canvas.draw_idle()
        else:
            # 鼠标离开绘图区域时隐藏标注和光标
            if coord_annotation.get_visible():  # 只在可见时才隐藏（避免重复操作）
                coord_annotation.set_visible(False)
                cursor_vline.set_visible(False)
                cursor_hline.set_visible(False)
                last_mouse_pos[0] = None
                last_mouse_pos[1] = None
                fig.canvas.draw_idle()

    # 按钮回调函数（优化更新方式）
    def on_play_clicked(event):
        status_text.set_text('正在播放...')
        fig.canvas.draw_idle()  # 使用 draw_idle 代替 plt.draw()，性能更好
        play_audio()

    def on_stop_clicked(event):
        status_text.set_text('已停止')
        fig.canvas.draw_idle()
        stop_audio()

    # 绑定按钮事件
    button_play.on_clicked(on_play_clicked)
    button_stop.on_clicked(on_stop_clicked)

    # 绑定鼠标移动事件
    fig.canvas.mpl_connect('motion_notify_event', on_mouse_move)

    # 显示图形
    plt.show()

def main():
    """主函数"""
    print("=" * 40)
    print("PCM 文件波形显示程序")
    print("=" * 40)
    
    # 默认参数
    
    sample_rate = 44100
    channels = 1
    bit_depth = 16
    
    # 检查是否有 PCM 文件（检查当前目录和 pcm_display 文件夹）
    pcm_files = []
    # 检查当前目录
    if os.path.exists('.'):
        pcm_files.extend([f for f in os.listdir('.') if f.endswith('.pcm')])
    # 检查 pcm_display 文件夹
    if os.path.exists('pcm_display'):
        pcm_files.extend([f'pcm_display/{f}' for f in os.listdir('pcm_display') if f.endswith('.pcm')])

    if pcm_files:
        print(f"发现 PCM 文件: {pcm_files}")
        filename = startfilename  # 使用默认文件
    else:
        print("当前目录和 pcm_display 文件夹没有找到 .pcm 文件")
        filename = input("请输入 PCM 文件名: ").strip()
        if not filename:
            print("未输入文件名，程序退出")
            return
    
    # 读取音频参数
    print(f"\n使用文件: {filename}")
    print("请输入音频参数（直接回车使用默认值）:")
    
    sr_input = input(f"采样率 (默认 {sample_rate}): ").strip()
    if sr_input:
        sample_rate = int(sr_input)
    
    ch_input = input(f"声道数 (默认 {channels}): ").strip()
    if ch_input:
        channels = int(ch_input)
    
    bd_input = input(f"位深度 (8/16/32, 默认 {bit_depth}): ").strip()
    if bd_input:
        bit_depth = int(bd_input)
    
    # 读取并显示波形
    print(f"\n正在读取 {filename}...")
    audio_data, time_axis = read_pcm_simple(filename, sample_rate, channels, bit_depth)
    
    if audio_data is not None:
        print("\n正在生成波形图...")
        plot_waveform_simple(audio_data, time_axis, filename, audio_data, sample_rate)
        print("完成！")
    else:
        print("读取失败！")

# 快速测试函数
def quick_test():
    """
    快速测试函数 - 直接指定参数
    修改这里的参数来快速测试不同的文件
    """
    filename = "test.pcm"  # 修改为你的文件名
    sample_rate = 44100    # 修改采样率
    channels = 1           # 修改声道数
    bit_depth = 16         # 修改位深度
    
    print(f"快速测试: {filename}")
    audio_data, time_axis = read_pcm_simple(filename, sample_rate, channels, bit_depth)
    
    if audio_data is not None:
        plot_waveform_simple(audio_data, time_axis, filename, audio_data, sample_rate)

if __name__ == "__main__":
    # 运行主程序
    main()
    
    # 如果要快速测试，取消下面的注释
    # quick_test()




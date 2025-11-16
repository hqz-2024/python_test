"""
简化版 PCM 文件读取和波形显示程序
"""

import numpy as np
import matplotlib.pyplot as plt
import struct
import os
import pygame
import threading
from matplotlib.widgets import Button


# 全局变量用于音频播放
startfilename = 'pcm_display/test_mixed.pcm'
current_audio_data = None
current_sample_rate = 44100
is_playing = False

def convert_to_wav_format(audio_data, sample_rate, bit_depth=16):
    """
    将音频数据转换为 WAV 格式的字节数据
    """
    # 转换为 16 位整数
    if bit_depth == 16:
        audio_16bit = (audio_data * 32767).astype(np.int16)
        # 转换为字节
        audio_bytes = audio_16bit.tobytes()
    else:
        # 其他位深度的处理
        audio_16bit = (audio_data * 32767).astype(np.int16)
        audio_bytes = audio_16bit.tobytes()

    return audio_bytes

def play_audio():
    """
    播放音频数据
    """
    global current_audio_data, current_sample_rate, is_playing

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

        print(f"播放数据形状: {stereo_audio.shape}")
        print(f"播放数据类型: {stereo_audio.dtype}")

        # 初始化 pygame mixer（立体声）
        pygame.mixer.pre_init(frequency=current_sample_rate, size=-16, channels=2, buffer=1024)
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

    # 为按钮留出空间
    plt.subplots_adjust(bottom=0.15)

    # 绘制波形
    ax.plot(display_time, display_audio, 'b-', linewidth=0.5)

    # 设置标题和标签
    ax.set_title(f'PCM 音频时域波形 - {filename}', fontsize=14)
    ax.set_xlabel('时间 (秒)', fontsize=12)
    ax.set_ylabel('幅度', fontsize=12)

    # 设置网格
    ax.grid(True, alpha=0.3)

    # 设置 y 轴范围
    ax.set_ylim(-1.1, 1.1)

    # 显示统计信息
    max_val = np.max(np.abs(original_audio_data))
    rms_val = np.sqrt(np.mean(original_audio_data**2))
    duration = len(original_audio_data) / sample_rate

    info_text = f'最大幅度: {max_val:.3f}\nRMS: {rms_val:.3f}\n时长: {duration:.2f}s\n采样率: {sample_rate}Hz'
    ax.text(0.02, 0.98, info_text, transform=ax.transAxes,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))

    # 添加播放按钮
    ax_play = plt.axes([0.3, 0.02, 0.1, 0.06])
    button_play = Button(ax_play, '▶ 播放', color='lightgreen', hovercolor='green')

    # 添加停止按钮
    ax_stop = plt.axes([0.42, 0.02, 0.1, 0.06])
    button_stop = Button(ax_stop, '⏹ 停止', color='lightcoral', hovercolor='red')

    # 添加状态显示
    ax_status = plt.axes([0.54, 0.02, 0.2, 0.06])
    status_text = ax_status.text(0.5, 0.5, '准备播放', ha='center', va='center',
                                transform=ax_status.transAxes, fontsize=10)
    ax_status.set_xticks([])
    ax_status.set_yticks([])

    # 按钮回调函数
    def on_play_clicked(event):
        status_text.set_text('正在播放...')
        plt.draw()
        play_audio()

    def on_stop_clicked(event):
        status_text.set_text('已停止')
        plt.draw()
        stop_audio()

    # 绑定按钮事件
    button_play.on_clicked(on_play_clicked)
    button_stop.on_clicked(on_stop_clicked)

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




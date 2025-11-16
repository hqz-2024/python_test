"""
生成测试用的 PCM 文件
"""

import numpy as np
import struct

def generate_sine_wave(frequency, duration, sample_rate=44100, amplitude=0.5):
    """
    生成正弦波
    
    参数:
        frequency: 频率 (Hz)
        duration: 持续时间 (秒)
        sample_rate: 采样率
        amplitude: 幅度 (0-1)
    """
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = amplitude * np.sin(2 * np.pi * frequency * t)
    return wave

def generate_mixed_wave(duration=3, sample_rate=44100):
    """
    生成混合波形（多个频率）
    """
    # 生成不同频率的正弦波
    wave1 = generate_sine_wave(440, duration, sample_rate, 0.3)   # A4 音符
    wave2 = generate_sine_wave(880, duration, sample_rate, 0.2)   # A5 音符
    wave3 = generate_sine_wave(220, duration, sample_rate, 0.2)   # A3 音符
    
    # 混合波形
    mixed_wave = wave1 + wave2 + wave3
    
    # 添加一些噪声
    noise = np.random.normal(0, 0.05, len(mixed_wave))
    mixed_wave += noise
    
    # 限制幅度
    mixed_wave = np.clip(mixed_wave, -1, 1)
    
    return mixed_wave

def save_pcm_16bit(audio_data, filename, sample_rate=44100):
    """
    保存为 16 位 PCM 文件
    """
    # 转换为 16 位整数
    audio_16bit = (audio_data * 32767).astype(np.int16)
    
    # 写入文件
    with open(filename, 'wb') as f:
        for sample in audio_16bit:
            f.write(struct.pack('<h', sample))
    
    print(f"已生成 {filename}")
    print(f"  采样率: {sample_rate} Hz")
    print(f"  位深度: 16 位")
    print(f"  声道数: 1 (单声道)")
    print(f"  样本数: {len(audio_data)}")
    print(f"  时长: {len(audio_data) / sample_rate:.2f} 秒")
    print(f"  文件大小: {len(audio_data) * 2} 字节")

def main():
    """生成测试文件"""
    print("生成测试 PCM 文件")
    print("=" * 30)
    
    # 生成不同类型的测试文件
    
    # 1. 简单正弦波
    print("\n1. 生成正弦波 (440 Hz, 2秒)")
    sine_wave = generate_sine_wave(440, 2, 44100, 0.7)
    save_pcm_16bit(sine_wave, "test_sine.pcm")
    
    # 2. 混合波形
    print("\n2. 生成混合波形 (3秒)")
    mixed_wave = generate_mixed_wave(3, 44100)
    save_pcm_16bit(mixed_wave, "test_mixed.pcm")
    
    # 3. 扫频信号
    print("\n3. 生成扫频信号 (100-2000 Hz, 3秒)")
    duration = 3
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    # 频率从 100 Hz 线性增加到 2000 Hz
    freq = 100 + (2000 - 100) * t / duration
    sweep_wave = 0.5 * np.sin(2 * np.pi * np.cumsum(freq) / sample_rate)
    save_pcm_16bit(sweep_wave, "test_sweep.pcm")
    
    # 4. 脉冲信号
    print("\n4. 生成脉冲信号 (2秒)")
    duration = 2
    samples = int(sample_rate * duration)
    pulse_wave = np.zeros(samples)
    # 每 0.1 秒一个脉冲
    pulse_interval = int(sample_rate * 0.1)
    for i in range(0, samples, pulse_interval):
        if i + 1000 < samples:  # 脉冲宽度
            pulse_wave[i:i+1000] = 0.8 * np.sin(2 * np.pi * 1000 * np.arange(1000) / sample_rate)
    
    save_pcm_16bit(pulse_wave, "test_pulse.pcm")
    
    print(f"\n已生成 4 个测试文件:")
    print("  test_sine.pcm  - 440Hz 正弦波")
    print("  test_mixed.pcm - 混合频率波形")
    print("  test_sweep.pcm - 扫频信号")
    print("  test_pulse.pcm - 脉冲信号")
    print(f"\n可以使用以下命令测试:")
    print("  python pcm_reader.py")

if __name__ == "__main__":
    main()

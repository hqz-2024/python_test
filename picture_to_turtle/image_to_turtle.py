"""
PNG 图片转 Turtle 绘图程序
将图片转换为坐标点，然后用 turtle 逐笔描绘出来
"""

import turtle
from PIL import Image
import numpy as np

def load_image(image_path):
    """加载图片并转换为灰度图"""
    try:
        img = Image.open(image_path)
        # 转换为灰度图
        img_gray = img.convert('L')
        return img_gray
    except FileNotFoundError:
        print(f"错误：找不到文件 '{image_path}'")
        return None
    except Exception as e:
        print(f"错误：无法加载图片 - {e}")
        return None

def resize_image(img, max_width=200, max_height=200):
    """调整图片大小，避免绘制时间过长"""
    width, height = img.size
    
    # 计算缩放比例
    scale = min(max_width / width, max_height / height)
    
    if scale < 1:
        new_width = int(width * scale)
        new_height = int(height * scale)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        print(f"图片已缩放至: {new_width}x{new_height}")
    
    return img

def image_to_coordinates(img, threshold=64):
    """
    将图片转换为坐标点列表
    threshold: 阈值，低于此值的像素被认为是黑色（需要绘制）
    """
    # 转换为 numpy 数组
    img_array = np.array(img)
    height, width = img_array.shape
    
    coordinates = []
    
    # 遍历每个像素
    for y in range(height):
        for x in range(width):
            # 如果像素值低于阈值（较暗），记录坐标
            if img_array[y, x] < threshold:
                # 转换坐标系：图片左上角为(0,0)，turtle中心为(0,0)
                # 将 y 坐标反转（图片 y 向下，turtle y 向上）
                turtle_x = x - width // 2
                turtle_y = height // 2 - y
                coordinates.append((turtle_x, turtle_y))
    
    print(f"提取了 {len(coordinates)} 个坐标点")
    return coordinates

def detect_edges(img, threshold=128):
    """
    检测图片边缘，只绘制轮廓
    这种方法绘制速度更快
    """
    img_array = np.array(img)
    height, width = img_array.shape
    
    edges = []
    
    # 简单的边缘检测：检查相邻像素的差异
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            # 如果当前像素与周围像素差异较大，认为是边缘
            current = img_array[y, x]
            neighbors = [
                img_array[y-1, x], img_array[y+1, x],
                img_array[y, x-1], img_array[y, x+1]
            ]
            
            # 计算差异
            diff = max(abs(current - n) for n in neighbors)
            
            if diff > 50:  # 边缘阈值
                turtle_x = x - width // 2
                turtle_y = height // 2 - y
                edges.append((turtle_x, turtle_y))
    
    print(f"检测到 {len(edges)} 个边缘点")
    return edges

def draw_with_turtle(coordinates, draw_mode='dots'):
    """
    使用 turtle 绘制坐标点
    draw_mode: 'dots' - 绘制点, 'lines' - 连线绘制
    """
    # 设置屏幕
    screen = turtle.Screen()
    screen.setup(800, 800)
    screen.bgcolor('white')
    screen.title("PNG 图片 Turtle 绘制")
    
    # 设置画笔
    t = turtle.Turtle()
    t.speed(0)  # 最快速度
    t.shape('turtle') # 设为海龟形状
    t.showturtle()  # 显示画笔
    
    # 关闭动画以加快速度
    screen.tracer(0)
    
    if draw_mode == 'dots':
        # 绘制点模式
        t.penup()
        for i, (x, y) in enumerate(coordinates):
            t.goto(x, y)
            t.dot(2, 'black')
            
            # 每100个点更新一次屏幕
            if i % 100 == 0:
                screen.update()
                print(f"绘制进度: {i}/{len(coordinates)} ({i*100//len(coordinates)}%)")
    
    elif draw_mode == 'lines':
        # 连线绘制模式
        t.pensize(1)
        t.pencolor('black')
        
        if coordinates:
            # 移动到第一个点
            t.penup()
            t.goto(coordinates[0][0], coordinates[0][1])
            t.pendown()
            
            # 连接所有点
            for i, (x, y) in enumerate(coordinates[1:], 1):
                t.goto(x, y)
                
                if i % 100 == 0:
                    screen.update()
                    print(f"绘制进度: {i}/{len(coordinates)} ({i*100//len(coordinates)}%)")
    
    # 最终更新
    screen.update()
    print("绘制完成！")
    
    # 保持窗口打开
    turtle.done()

def main():
    """主函数"""
    print("=" * 50)
    print("PNG 图片转 Turtle 绘图程序")
    print("=" * 50)
    
    # 图片路径
    image_path = "picture_to_turtle/图片.png"
    
    # 1. 加载图片
    print(f"\n正在加载图片: {image_path}")
    img = load_image(image_path)
    
    if img is None:
        return
    
    print(f"原始图片大小: {img.size[0]}x{img.size[1]}")
    
    # 2. 调整图片大小
    print("\n正在调整图片大小...")
    img = resize_image(img, max_width=800, max_height=800)#这里调整画布分辨率
    
    coordinates = image_to_coordinates(img, threshold=200)#这里调整灰度识别的阈值

    if not coordinates:
        print("错误：没有提取到任何坐标点")
        return
    draw_mode =  'dots'#设定为点绘制
    
    # 5. 开始绘制
    print(f"\n开始绘制，使用 {draw_mode} 模式...")
    draw_with_turtle(coordinates, draw_mode)
    turtle.done() 
if __name__ == "__main__":
    main()


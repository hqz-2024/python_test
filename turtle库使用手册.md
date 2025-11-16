# Python Turtle 图形库使用手册

## 📚 目录
- [简介](#简介)
- [基础设置](#基础设置)
- [画笔移动](#画笔移动)
- [画笔控制](#画笔控制)
- [颜色设置](#颜色设置)
- [填充功能](#填充功能)
- [画笔状态](#画笔状态)
- [绘制形状](#绘制形状)
- [屏幕控制](#屏幕控制)
- [事件处理](#事件处理)
- [完整示例](#完整示例)

---

## 简介

Turtle（海龟绘图）是 Python 内置的图形绘制库，特别适合：
- 编程入门学习
- 绘制几何图形
- 创作艺术图案
- 可视化算法

**核心概念**：想象一只海龟在画布上爬行，它走过的路径就是绘制的图形。

---

## 基础设置

### 导入库
```python
import turtle

# 创建画笔对象
t = turtle.Turtle()
# 或
t = turtle.Pen()
```

### 初始化设置
```python
# 设置画笔速度（0-10，0最快）
t.speed(0)          # 最快
t.speed(1)          # 最慢
t.speed(5)          # 中等速度

# 设置画笔形状
t.shape('turtle')   # 海龟形状
t.shape('arrow')    # 箭头（默认）
t.shape('circle')   # 圆形
t.shape('square')   # 方形
t.shape('triangle') # 三角形
t.shape('classic')  # 经典形状

# 设置画笔大小
t.shapesize(2, 2)   # 放大2倍
t.shapesize(0.5, 0.5) # 缩小一半
```

---

## 画笔移动

### 前进和后退
```python
t.forward(100)      # 向前移动100像素（简写：t.fd(100)）
t.backward(100)     # 向后移动100像素（简写：t.bk(100)）
```

### 转向
```python
t.right(90)         # 向右转90度（简写：t.rt(90)）
t.left(90)          # 向左转90度（简写：t.lt(90)）

t.setheading(0)     # 设置朝向角度（0=东，90=北，180=西，270=南）
```

### 移动到指定位置
```python
t.goto(100, 100)    # 移动到坐标(100, 100)
t.setx(50)          # 设置x坐标为50
t.sety(50)          # 设置y坐标为50
t.home()            # 回到原点(0, 0)，朝向东
```

### 获取当前位置
```python
x, y = t.position() # 获取当前坐标
heading = t.heading() # 获取当前朝向角度
```

---

## 画笔控制

### 抬笔和落笔
```python
t.penup()           # 抬起画笔（移动时不绘制）简写：t.pu()
t.pendown()         # 放下画笔（移动时绘制）简写：t.pd()

# 判断画笔状态
if t.isdown():
    print("画笔在纸上")
```

### 画笔粗细
```python
t.pensize(5)        # 设置画笔粗细为5像素
t.width(10)         # 同上，设置为10像素
```

### 显示和隐藏画笔
```python
t.hideturtle()      # 隐藏画笔（简写：t.ht()）
t.showturtle()      # 显示画笔（简写：t.st()）
```

### 绘制速度
```python
t.speed(0)          # 最快（无动画）
t.speed(10)         # 快速
t.speed(6)          # 正常
t.speed(3)          # 慢速
t.speed(1)          # 最慢
```

---

## 颜色设置

### 画笔颜色
```python
# 使用颜色名称
t.pencolor('red')
t.pencolor('blue')
t.pencolor('green')

# 使用RGB值（0-1之间的小数）
t.pencolor(0.5, 0.5, 0.5)  # 灰色

# 使用十六进制颜色
turtle.colormode(255)       # 切换到0-255模式
t.pencolor(255, 0, 0)       # 红色
```

### 填充颜色
```python
t.fillcolor('yellow')       # 设置填充颜色
t.fillcolor(0, 255, 0)      # 绿色（需要先设置colormode(255)）
```

### 同时设置画笔和填充颜色
```python
t.color('red', 'yellow')    # 画笔红色，填充黄色
t.color('blue')             # 画笔和填充都是蓝色
```

### 常用颜色名称
```
'red', 'blue', 'green', 'yellow', 'orange', 'purple', 
'pink', 'brown', 'black', 'white', 'gray', 'cyan', 'magenta'
```

---

## 填充功能

### 填充图形
```python
t.begin_fill()      # 开始填充
# 绘制图形
t.circle(50)
t.end_fill()        # 结束填充

# 示例：绘制填充的正方形
t.fillcolor('red')
t.begin_fill()
for _ in range(4):
    t.forward(100)
    t.right(90)
t.end_fill()
```

---

## 画笔状态

### 清除和重置
```python
t.clear()           # 清除画笔绘制的内容，但不改变位置
t.reset()           # 清除内容并重置画笔到初始状态
turtle.clearscreen() # 清除所有内容
```

### 撤销操作
```python
t.undo()            # 撤销上一步操作
```

---

## 绘制形状

### 圆形
```python
t.circle(50)        # 绘制半径为50的圆
t.circle(100, 180)  # 绘制半圆（180度）
t.circle(-50)       # 负数半径，反方向绘制
```

### 点
```python
t.dot(20)           # 绘制直径为20的点
t.dot(30, 'red')    # 绘制红色的点
```

### 多边形
```python
# 正方形
for _ in range(4):
    t.forward(100)
    t.right(90)

# 正三角形
for _ in range(3):
    t.forward(100)
    t.right(120)

# 正六边形
for _ in range(6):
    t.forward(50)
    t.right(60)
```

### 写文字
```python
t.write("Hello Turtle!")                    # 写文字
t.write("标题", font=("Arial", 16, "bold")) # 设置字体
t.write("居中", align="center")              # 居中对齐
t.write("右对齐", align="right")             # 右对齐
```

---

## 屏幕控制

### 屏幕设置
```python
# 获取屏幕对象
screen = turtle.Screen()

# 设置屏幕大小
screen.setup(800, 600)      # 宽800，高600

# 设置背景颜色
screen.bgcolor('black')
screen.bgcolor(0.5, 0.5, 0.5)

# 设置背景图片
screen.bgpic('background.gif')

# 设置标题
screen.title("我的Turtle程序")
```

### 坐标系统
```python
# 设置坐标系统
screen.setworldcoordinates(-100, -100, 100, 100)

# 显示/隐藏坐标轴（需要额外绘制）
```

### 屏幕刷新控制
```python
screen.tracer(0)    # 关闭动画，加快绘制速度
# 绘制代码...
screen.update()     # 手动更新屏幕

screen.tracer(1)    # 恢复动画
```

### 保持窗口打开
```python
turtle.done()       # 保持窗口打开，等待关闭
# 或
screen.mainloop()   # 同上
```

### 退出程序
```python
screen.bye()        # 关闭窗口
turtle.exitonclick() # 点击窗口后退出
```

---

## 事件处理

### 鼠标事件
```python
def click_handler(x, y):
    print(f"点击位置: ({x}, {y})")
    t.goto(x, y)

# 绑定点击事件
screen.onclick(click_handler)

# 绑定画笔点击事件
t.onclick(click_handler)
```

### 键盘事件
```python
def move_up():
    t.setheading(90)
    t.forward(10)

def move_down():
    t.setheading(270)
    t.forward(10)

# 绑定键盘事件
screen.onkey(move_up, "Up")
screen.onkey(move_down, "Down")
screen.listen()     # 开始监听键盘
```

---

## 完整示例

### 示例1：绘制彩色螺旋
```python
import turtle

t = turtle.Turtle()
t.speed(0)
turtle.bgcolor('black')

colors = ['red', 'yellow', 'blue', 'green', 'purple', 'orange']

for x in range(360):
    t.pencolor(colors[x % 6])
    t.width(x / 100 + 1)
    t.forward(x)
    t.left(59)

turtle.done()
```

### 示例2：绘制五角星
```python
import turtle

t = turtle.Turtle()
t.speed(2)
t.color('red', 'yellow')

t.begin_fill()
for _ in range(5):
    t.forward(200)
    t.right(144)
t.end_fill()

turtle.done()
```

### 示例3：绘制同心圆
```python
import turtle

t = turtle.Turtle()
t.speed(0)

colors = ['red', 'orange', 'yellow', 'green', 'blue', 'purple']

for i in range(6):
    t.pencolor(colors[i])
    t.penup()
    t.goto(0, -20 * (i + 1))
    t.pendown()
    t.circle(20 * (i + 1))

turtle.done()
```

### 示例4：随机漫步
```python
import turtle
import random

t = turtle.Turtle()
t.speed(0)
turtle.colormode(255)

for _ in range(200):
    # 随机颜色
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    t.pencolor(r, g, b)
    
    # 随机移动
    t.forward(random.randint(10, 50))
    t.right(random.randint(0, 360))

turtle.done()
```

---

## 常用函数速查表

| 功能 | 函数 | 说明 |
|------|------|------|
| 前进 | `forward(distance)` | 向前移动指定距离 |
| 后退 | `backward(distance)` | 向后移动指定距离 |
| 右转 | `right(angle)` | 向右转指定角度 |
| 左转 | `left(angle)` | 向左转指定角度 |
| 移动到 | `goto(x, y)` | 移动到指定坐标 |
| 画圆 | `circle(radius)` | 绘制圆形 |
| 抬笔 | `penup()` | 抬起画笔 |
| 落笔 | `pendown()` | 放下画笔 |
| 画笔颜色 | `pencolor(color)` | 设置画笔颜色 |
| 填充颜色 | `fillcolor(color)` | 设置填充颜色 |
| 画笔粗细 | `pensize(width)` | 设置画笔粗细 |
| 速度 | `speed(speed)` | 设置绘制速度 |
| 开始填充 | `begin_fill()` | 开始填充 |
| 结束填充 | `end_fill()` | 结束填充 |
| 清除 | `clear()` | 清除绘制内容 |
| 重置 | `reset()` | 重置画笔 |
| 隐藏画笔 | `hideturtle()` | 隐藏画笔 |
| 显示画笔 | `showturtle()` | 显示画笔 |
| 写文字 | `write(text)` | 写文字 |
| 画点 | `dot(size, color)` | 绘制点 |
| 完成 | `done()` | 保持窗口打开 |

---

## 💡 使用技巧

1. **加快绘制速度**：使用 `t.speed(0)` 和 `screen.tracer(0)`
2. **隐藏画笔**：使用 `t.hideturtle()` 让绘制更流畅
3. **使用循环**：绘制重复图案时使用 for 循环
4. **颜色模式**：使用 `turtle.colormode(255)` 切换到 RGB 0-255 模式
5. **保存图片**：使用 `screen.getcanvas().postscript(file="image.eps")` 保存为 EPS 格式

---

## 📖 参考资源

- [Python 官方文档](https://docs.python.org/zh-cn/3/library/turtle.html)
- 更多示例和教程可以在网上搜索 "Python turtle 教程"

---

**祝你使用 Turtle 创作出精彩的图形！** 🐢🎨


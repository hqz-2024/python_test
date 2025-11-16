import turtle

__Pen = turtle.Pen()


# 彩色弹球
t = turtle.Pen()
t.speed(5)
t.shape('turtle')
turtle.bgcolor('black')
# 更改sides变量，可以画出完全不同的图形哦
# 改为2、3、4、5、6等，看看效果吧
sides = 3
colors = ['red','yellow','blue','orange','green','purple']
for x in range(100):
    t.pencolor(colors[(x % sides)])
    t.forward(((x * 3) / sides + x))
    t.left((360 / sides + 1))
    t.pensize(((x * sides) / 200))
    t.left(90)


# 保持窗口打开，点击窗口关闭程序
turtle.done()
import re
import PIL
import jieba
import numpy as np
from PIL import Image
from matplotlib import pyplot as plt
from wordcloud import WordCloud


# 读取文件内容
def read_text():
    file = "123.txt"
    with open(file, encoding='utf-8') as f:
        text = f.read()
    # 去掉标点符号
    pattern = re.compile(u'\t|\n|\.|-|:|;|\)|\(|\?|，|。|：|,|　|·|《|》|”|；|、')
    content = re.sub(pattern, '', text)
    print(content)
    print("=================================================")
    return content

# 执行分词
def jiebafc(s):
    # 分词程度
    cut = jieba.lcut(s, cut_all=False)
    print(cut)
    return cut


# 二值化处理
def cv():
    im = PIL.Image.open("3.png")
    Lim = im.convert('L')
    threshold = 185
    table = []
    for i in range(256):
        if i < threshold:
            table.append(0)
        else:
            table.append(1)
    bim = Lim.point(table, '1')
    bim.save('33.jpg')


def img(text):
    mask = np.array(Image.open('img.png'))
    word_cloud = WordCloud(
        # width=1920,
        # height=1080,
        mask=mask,
        # 背景颜色
        # background_color=random_color_func(),
        background_color="white",
        # 设置字体
        font_path='wawww.ttf',
        # 忽略词
        stopwords={"的", "你", "数据", "外线"},
        # 默认值1。值越大，图像密度越大越清晰
        scale=1,
        # 字号增大的步进间隔 默认1号
        font_step=1,
        # min_font_size=4,
        # 最大号字体
        max_font_size=None,
        max_words=None,
        # 浮点数类型。表示在水平如果不合适，就旋转为垂直方向，水平放置的词数占比
        prefer_horizontal=0.5,
        # 设定按词频倒序排列，上一个词相对下一位词的大小倍数
        relative_scaling=0.9,
    ).generate(text)
    # 从背景图建立颜色方案
    # image_colors = ImageColorGenerator(mask)
    # 将词云颜色设置为背景图方案
    # word_cloud.recolor(color_func=image_colors)
    # word_cloud.to_file("displaycloud.png")
    # show
    plt.imshow(word_cloud, interpolation='bilinear')
    plt.axis("off")
    plt.figure()
    plt.axis("off")
    plt.show()


if __name__ == '__main__':
    img(",".join(jiebafc(read_text())))
    # cv()

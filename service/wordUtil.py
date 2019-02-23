from docx import Document

doc = Document('example.docx')

from docx.shared import Inches, Pt


def chg_font(obj, fontname='微软雅黑', size=None):
    ## 设置字体函数

    obj.font.name = fontname

    obj._element.rPr.rFonts.set(qn('w:eastAsia'), fontname)

    if size and isinstance(size, Pt):
        obj.font.size = size


distance = Inches(0.3)

sec = doc.sections[0]  # sections对应文档中的“节”

sec.left_margin = distance  # 以下依次设置左、右、上、下页面边距

sec.right_margin = distance

sec.top_margin = distance

sec.bottom_margin = distance

sec.page_width = Inches(12)  # 设置页面宽度

sec.page_height = Inches(20)  # 设置页面高度

##设置默认字体

chg_font(doc.styles['Normal'], fontname='宋体')
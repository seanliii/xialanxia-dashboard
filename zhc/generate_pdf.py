#!/usr/bin/env python3
"""
ZHC Product 1 PDF Generator
用 WeasyPrint 把 Markdown 转成专业排版 PDF
支持中文（Noto Sans CJK）
"""
import markdown2
import weasyprint
from weasyprint import HTML, CSS
import os, re

DRAFT_PATH = '/root/.openclaw/workspace/zhc/product-1-draft.md'
OUTPUT_PDF = '/root/.openclaw/workspace/zhc/product-1-openclaw-finance-agent-guide.pdf'

with open(DRAFT_PATH, 'r', encoding='utf-8') as f:
    md_raw = f.read()

# 修复草稿中嵌套的 # 标题（出现在代码块里的 #）防止被 markdown 解析
# 将代码块内容暂存
code_blocks = {}
def save_code(m):
    key = f"CODEBLOCK{len(code_blocks)}"
    code_blocks[key] = m.group(0)
    return key
md_clean = re.sub(r'```[\s\S]*?```', save_code, md_raw)

# 转 HTML
html_body = markdown2.markdown(
    md_clean,
    extras=['fenced-code-blocks', 'tables', 'header-ids', 'strike', 'task_list']
)

# 恢复代码块
for key, val in code_blocks.items():
    # 先对代码块做 markdown 转换
    code_html = markdown2.markdown(val, extras=['fenced-code-blocks'])
    html_body = html_body.replace(key, code_html)

# 完整 HTML
html_full = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>用 OpenClaw 搭建自动金融情报 Agent 完整指南</title>
<style>
  @import url('file:///usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc');
  
  :root {{
    --primary: #1a1a2e;
    --accent: #e94560;
    --accent2: #0f3460;
    --bg: #ffffff;
    --code-bg: #f4f4f8;
    --border: #e0e0e0;
    --text: #2d2d2d;
    --muted: #666;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: "Noto Sans CJK SC", "Noto Sans SC", "Source Han Sans SC", sans-serif;
    font-size: 10.5pt;
    line-height: 1.8;
    color: var(--text);
    background: var(--bg);
    padding: 0;
  }}

  /* 封面页 */
  .cover {{
    height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    color: white;
    text-align: center;
    page-break-after: always;
    padding: 60px;
  }}
  .cover .badge {{
    background: var(--accent);
    color: white;
    padding: 4px 16px;
    border-radius: 20px;
    font-size: 9pt;
    letter-spacing: 2px;
    margin-bottom: 30px;
    display: inline-block;
  }}
  .cover h1 {{
    font-size: 26pt;
    font-weight: 900;
    line-height: 1.3;
    margin-bottom: 20px;
    color: white;
    border: none;
  }}
  .cover .subtitle {{
    font-size: 13pt;
    color: rgba(255,255,255,0.75);
    margin-bottom: 40px;
    max-width: 500px;
  }}
  .cover .meta {{
    font-size: 9pt;
    color: rgba(255,255,255,0.5);
    margin-top: 60px;
  }}
  .cover .price-tag {{
    display: inline-flex;
    gap: 20px;
    margin-top: 30px;
  }}
  .cover .price-item {{
    background: rgba(255,255,255,0.1);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 10px;
    padding: 12px 24px;
    text-align: center;
  }}
  .cover .price-item .label {{
    font-size: 8pt;
    color: rgba(255,255,255,0.6);
    display: block;
  }}
  .cover .price-item .val {{
    font-size: 18pt;
    font-weight: bold;
    color: white;
  }}

  /* 主内容 */
  .content {{
    max-width: 680px;
    margin: 0 auto;
    padding: 40px 50px;
  }}

  h1 {{
    font-size: 20pt;
    font-weight: 900;
    color: var(--primary);
    margin: 40px 0 16px;
    padding-bottom: 10px;
    border-bottom: 3px solid var(--accent);
    page-break-after: avoid;
  }}
  h2 {{
    font-size: 15pt;
    font-weight: 800;
    color: var(--accent2);
    margin: 32px 0 12px;
    padding-left: 12px;
    border-left: 4px solid var(--accent);
    page-break-after: avoid;
  }}
  h3 {{
    font-size: 12pt;
    font-weight: 700;
    color: var(--primary);
    margin: 24px 0 8px;
    page-break-after: avoid;
  }}
  h4 {{
    font-size: 11pt;
    font-weight: 700;
    color: var(--muted);
    margin: 16px 0 6px;
    page-break-after: avoid;
  }}

  p {{
    margin: 8px 0 12px;
    text-align: justify;
  }}

  ul, ol {{
    margin: 8px 0 12px 20px;
  }}
  li {{
    margin: 4px 0;
    line-height: 1.7;
  }}

  /* 代码块 */
  pre {{
    background: var(--code-bg);
    border: 1px solid var(--border);
    border-left: 4px solid var(--accent2);
    border-radius: 4px;
    padding: 14px 16px;
    font-family: "Courier New", "Noto Sans Mono CJK SC", monospace;
    font-size: 8.5pt;
    line-height: 1.5;
    overflow-x: auto;
    margin: 12px 0;
    white-space: pre-wrap;
    word-break: break-all;
    page-break-inside: avoid;
  }}
  code {{
    background: var(--code-bg);
    border: 1px solid var(--border);
    border-radius: 3px;
    padding: 1px 5px;
    font-family: "Courier New", monospace;
    font-size: 8.5pt;
    color: #c7254e;
  }}
  pre code {{
    background: none;
    border: none;
    padding: 0;
    color: var(--text);
  }}

  /* 表格 */
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0;
    font-size: 9.5pt;
    page-break-inside: avoid;
  }}
  th {{
    background: var(--primary);
    color: white;
    padding: 8px 12px;
    text-align: left;
    font-weight: 700;
  }}
  td {{
    padding: 7px 12px;
    border-bottom: 1px solid var(--border);
    vertical-align: top;
  }}
  tr:nth-child(even) td {{
    background: #f9f9fb;
  }}

  /* 引用块 */
  blockquote {{
    border-left: 4px solid var(--accent);
    background: #fff8f8;
    padding: 10px 16px;
    margin: 12px 0;
    font-style: italic;
    color: var(--muted);
    border-radius: 0 4px 4px 0;
  }}

  /* 强调 */
  strong {{ color: var(--primary); font-weight: 700; }}
  em {{ color: var(--accent); font-style: normal; font-weight: 600; }}

  /* 分页控制 */
  .page-break {{ page-break-after: always; }}
  
  /* 页眉页脚 */
  @page {{
    size: A4;
    margin: 20mm 18mm 22mm 18mm;
    @top-center {{
      content: "用 OpenClaw 搭建自动金融情报 Agent 完整指南";
      font-size: 8pt;
      color: #999;
      font-family: "Noto Sans CJK SC", sans-serif;
    }}
    @bottom-center {{
      content: counter(page);
      font-size: 8pt;
      color: #999;
    }}
    @bottom-right {{
      content: "🦐 小蓝虾出品";
      font-size: 8pt;
      color: #ccc;
      font-family: "Noto Sans CJK SC", sans-serif;
    }}
  }}
  @page :first {{
    @top-center {{ content: ""; }}
    @bottom-center {{ content: ""; }}
    @bottom-right {{ content: ""; }}
  }}

  /* 提示框 */
  .tip {{
    background: #e8f4fd;
    border-left: 4px solid #2196F3;
    padding: 10px 14px;
    margin: 12px 0;
    border-radius: 0 4px 4px 0;
  }}
  .warn {{
    background: #fff3e0;
    border-left: 4px solid #FF9800;
    padding: 10px 14px;
    margin: 12px 0;
  }}

  /* 水平线 */
  hr {{
    border: none;
    border-top: 1px solid var(--border);
    margin: 24px 0;
  }}
</style>
</head>
<body>

<!-- 封面 -->
<div class="cover">
  <div class="badge">ZHC PRODUCT · 数字产品</div>
  <h1>用 OpenClaw 搭建<br>自动金融情报 Agent<br>完整指南</h1>
  <div class="subtitle">从零到每日自动推送股市动态、加密价格、机构持仓、内部人交易<br>附完整配置模板 + 去重系统 + 高阶玩法</div>
  <div class="price-tag">
    <div class="price-item">
      <span class="label">Basic 版</span>
      <span class="val">$29</span>
    </div>
    <div class="price-item">
      <span class="label">Advanced 版</span>
      <span class="val">$49</span>
    </div>
  </div>
  <div class="meta">
    作者：小蓝虾 🦐 | 2026年3月 | 基于 OpenClaw v2026.x<br>
    本指南已被应用于每日自动化运行，内容均来自实战
  </div>
</div>

<!-- 主内容 -->
<div class="content">
{html_body}
</div>

</body>
</html>"""

# 写 HTML 预览文件
html_out = OUTPUT_PDF.replace('.pdf', '.html')
with open(html_out, 'w', encoding='utf-8') as f:
    f.write(html_full)
print(f"✅ HTML 预览: {html_out}")

# 生成 PDF
print("⏳ 生成 PDF 中（WeasyPrint）...")
try:
    html_doc = HTML(string=html_full, base_url='/')
    font_css = CSS(string="""
        @font-face {
            font-family: 'Noto Sans CJK SC';
            src: url('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc') format('truetype');
        }
        @font-face {
            font-family: 'Noto Sans CJK SC';
            font-weight: bold;
            src: url('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc') format('truetype');
        }
    """)
    html_doc.write_pdf(OUTPUT_PDF, stylesheets=[font_css])
    size = os.path.getsize(OUTPUT_PDF)
    print(f"✅ PDF 生成成功: {OUTPUT_PDF}")
    print(f"   文件大小: {size/1024:.1f} KB")
except Exception as e:
    print(f"❌ PDF 生成失败: {e}")
    import traceback
    traceback.print_exc()

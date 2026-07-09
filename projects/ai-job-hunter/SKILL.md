---
name: ai-job-hunter
description: "粘贴简历+目标JD，自动分析关键词缺口、匹配度评分，生成定制Cover Letter，提升简历通过率"
triggers:
  - "求职"
  - "简历"
  - "JD匹配"
  - "cover letter"
  - "找工作"
  - "job hunter"
---
# AI 求职猎手

## 功能说明
粘贴你的简历文本 + 目标职位 JD → 自动输出：关键词缺口分析（JD有但简历没有的词）、匹配度评分（0-100）、简历改进建议、Cover Letter 初稿。零后端，纯前端运行。

## 在线使用
直接访问：https://seanliii.github.io/ai-job-hunter/

## 本地部署步骤

### Step 1：下载项目
```bash
git clone https://github.com/seanliii/ai-job-hunter.git
cd ai-job-hunter
```
**成功判断**：目录下存在 `index.html`，约19KB

### Step 2：本地预览
```bash
python3 -m http.server 8080
# 浏览器访问 http://localhost:8080
```
**成功判断**：页面显示简历输入区和JD输入区

### Step 3：分析简历
1. 在左侧「我的简历」区域粘贴你的简历全文（纯文本）
2. 在右侧「目标JD」区域粘贴职位描述全文
3. 点击「分析匹配度」
4. 查看：
   - 匹配分数（0-100）
   - 🔴 缺失关键词（JD有但简历没有）
   - 🟡 弱覆盖词（提到了但次数少）
   - ✅ 强匹配词
5. 点击「生成Cover Letter」获取初稿

**成功判断**：分析结果区域出现评分和关键词列表

### Step 4：改进简历
根据缺失关键词列表，在你的简历中针对性补充经历描述。
例如：JD要求"Cross-functional collaboration"，你的简历里改为"Led cross-functional collaboration with 3 teams to..."

## 踩坑记录
- 纯关键词匹配，不理解语义，"用户增长"和"Growth Hacking"可能视为不同词
- Cover Letter 是模板框架，必须填充你自己的真实故事，否则 HR 一眼看出是 AI 生成的
- 不要试图靠堆关键词通过 ATS，需要真实经历支撑

## 适用场景
- 批量投递前快速诊断哪些 JD 和自己最匹配
- 针对每个职位定制简历（调整描述重点）
- 生成 Cover Letter 框架后人工个性化

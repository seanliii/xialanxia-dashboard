#!/usr/bin/env python3
"""
搜索词自动扩词系统 MVP v0.1
功能：
1. 读取当前词库
2. 基于规则生成候选新词
3. 自动搜索测试命中率
4. 输出调整建议报告

用法:
    python3 expander.py [--test-count N] [--engines ENGINE_LIST]
"""

import json
import subprocess
import re
import argparse
import os
from datetime import datetime
from pathlib import Path

# 配置
KEYWORDS_PATH = Path("/root/.openclaw/workspace/data/search-keywords.json")
REPORT_PATH = Path("/root/.openclaw/workspace/data/keyword-expansion-report.json")
ENGINES = ["bocha-search", "tencent-search", "quark-search", "baidu-search-v2"]

class KeywordExpander:
    def __init__(self):
        self.keywords = self.load_keywords()
        self.today = datetime.now()
        self.year_month = f"{self.today.year}年{self.today.month}月"

    def load_keywords(self):
        with open(KEYWORDS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)

    def generate_candidates(self):
        """基于当前词库生成候选新词"""
        candidates = []
        all_existing = set()
        for tier in ["tier1_always", "tier2_rotate", "tier3_experimental", "dead_words"]:
            all_existing.update(self.keywords.get(tier, []))

        # 策略1: 年月更新 - 将旧年月词替换为当前年月
        year_month_patterns = [
            r'2026年\d+月',
            r'2026年\d月',
        ]
        for word in self.keywords.get("tier1_always", []) + self.keywords.get("tier2_rotate", []):
            for pattern in year_month_patterns:
                if re.search(pattern, word):
                    new_word = re.sub(pattern, self.year_month, word)
                    if new_word not in all_existing and new_word != word:
                        candidates.append({
                            "word": new_word,
                            "strategy": "year_month_update",
                            "source": word,
                            "rationale": f"将旧年月词更新为当前年月"
                        })

        # 策略2: 热点组合 - 从 tier1 提取产品名/公司名 + 当前热点场景
        hot_products = self.extract_products()
        hot_scenes = ["产品", "发布", "上市", "融资", "商业化", "变现", "案例", "最新功能"]
        for product in hot_products[:10]:  # 取前10个
            for scene in hot_scenes[:3]:  # 每个产品组合3个场景
                new_word = f"{product} {scene} {self.year_month}"
                if new_word not in all_existing:
                    candidates.append({
                        "word": new_word,
                        "strategy": "hot_combination",
                        "source": product,
                        "rationale": f"热点产品 '{product}' + 场景 '{scene}' + 当前年月"
                    })

        # 策略3: 变体生成 - 对高命中率词做语义变体
        variant_templates = [
            ("AI Agent", ["AI智能体", "人工智能代理", "智能Agent"]),
            ("openclaw", ["OpenClaw", "open claw"]),
            ("一人公司", ["单人公司", "个体创业", "个人创业", "Solo Founder"]),
            ("变现", ["赚钱", "盈利", "收入", "营收", "MRR", "ARR"]),
        ]
        for tier in ["tier1_always", "tier2_rotate"]:
            for word in self.keywords.get(tier, []):
                for original, variants in variant_templates:
                    if original in word:
                        for variant in variants[:2]:  # 每个变体最多2个
                            new_word = word.replace(original, variant)
                            if new_word not in all_existing and new_word != word:
                                candidates.append({
                                    "word": new_word,
                                    "strategy": "variant",
                                    "source": word,
                                    "rationale": f"将 '{original}' 替换为 '{variant}'"
                                })

        # 去重
        seen = set()
        unique = []
        for c in candidates:
            if c["word"] not in seen:
                seen.add(c["word"])
                unique.append(c)

        return unique[:20]  # 最多20个候选词

    def extract_products(self):
        """从词库中提取产品名/公司名，并补充当前热点"""
        products = set()
        known_products = [
            # AI 产品
            "openclaw", "Claude", "Codex", "GPT-5", "GPT-5.5", "Gemini",
            "OpenAI", "Anthropic", "DeepSeek", "Kimi", "豆包", "通义千问",
            "Cursor", "Windsurf", "Zed", "Devin", "MCP", "ClawHub",
            "MAI-Thinking-1", "MAI-Code-1", "Copilot", "o3-mini",
            # 平台/公司
            "微软", "微信", "腾讯", "阿里", "字节跳动", "百度",
            "谷歌", "Meta", "Amazon", "Apple",
            # 技术概念
            "RPA", "Agent", "Multi-Agent", "AI Agent", "ClawHub",
            "技能工坊", "Workboard"
        ]
        for tier in ["tier1_always", "tier2_rotate", "tier3_experimental"]:
            for word in self.keywords.get(tier, []):
                for p in known_products:
                    if p.lower() in word.lower():
                        products.add(p)
        # 强制加入当前热点（即使词库没出现）
        current_hot = ["openclaw", "微信", "豆包", "GPT-5.5", "微软", "Anthropic"]
        products.update(current_hot)
        return list(products)

    def test_search(self, query, engine="bocha-search", max_results=5):
        """运行单次搜索测试，返回结果"""
        cmd = [
            "python3", "/app/skills/catclaw-search/scripts/catclaw_search.py",
            "search", query,
            "-s", engine,
            "-n", str(max_results)
        ]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60
            )
            output = result.stdout + result.stderr
            # 解析结果：找 "找到 X 条结果" 或 "Results:" 等标记
            has_results = "找到" in output or "Results" in output or "http" in output
            # 提取 URL 数量作为粗略命中指标
            urls = re.findall(r'https?://[^\s\]]+', output)
            return {
                "success": result.returncode == 0 and has_results,
                "has_results": has_results,
                "url_count": len(urls),
                "raw_length": len(output),
                "snippet": output[:500] if output else ""
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "has_results": False, "url_count": 0, "raw_length": 0, "snippet": "timeout"}
        except Exception as e:
            return {"success": False, "has_results": False, "url_count": 0, "raw_length": 0, "snippet": str(e)[:200]}

    def test_candidate(self, candidate, engines=None):
        """对一个候选词在多个引擎上测试"""
        if engines is None:
            engines = ["bocha-search", "tencent-search", "quark-search"]

        results = {}
        for engine in engines:
            test_result = self.test_search(candidate["word"], engine)
            results[engine] = test_result

        # 计算综合得分
        success_count = sum(1 for r in results.values() if r["success"] and r["has_results"])
        total_url_count = sum(r["url_count"] for r in results.values())

        return {
            **candidate,
            "engine_results": results,
            "success_rate": success_count / len(engines),
            "total_urls": total_url_count,
            "recommendation": self.score_recommendation(success_count, len(engines), total_url_count, candidate.get("word", ""))
        }

    def score_recommendation(self, success_count, total_engines, total_urls, word=""):
        """基于测试结果给出建议，加入相关性过滤"""
        # 过滤明显不相关的词（搜索结果虽然多但主题不对）
        misleading_words = ["上市", "IPO", "股票", "股价"]
        if any(mw in word for mw in misleading_words):
            # 这些词容易命中但可能不是用户想要的
            if total_urls >= 15:  # 如果结果太多，可能是噪音
                return "skip"

        if success_count >= 2 and total_urls >= 5:
            return "strong_add_tier2"  # 强建议加入 tier2
        elif success_count >= 2 and total_urls >= 3:
            return "add_tier3"  # 建议加入 tier3 实验
        elif success_count >= 1 and total_urls >= 2:
            return "weak_signal"  # 弱信号，继续观察
        else:
            return "skip"  # 跳过

    def run(self, test_count=10, engines=None):
        """主执行流程"""
        print(f"🚀 搜索词自动扩词系统 v0.1 | {self.today.strftime('%Y-%m-%d %H:%M')}")
        print(f"📚 当前词库版本: {self.keywords.get('version', 'unknown')}")

        # 生成候选词
        candidates = self.generate_candidates()
        print(f"\n📝 生成 {len(candidates)} 个候选新词")
        for i, c in enumerate(candidates[:test_count], 1):
            print(f"  {i}. [{c['strategy']}] {c['word']}")

        # 测试候选词
        test_candidates = candidates[:test_count]
        tested = []
        print(f"\n🔍 开始测试 (每个词 {len(engines or ['bocha-search'])} 个引擎)...")

        for i, candidate in enumerate(test_candidates, 1):
            print(f"  [{i}/{len(test_candidates)}] 测试: {candidate['word'][:50]}...", end=" ", flush=True)
            result = self.test_candidate(candidate, engines)
            tested.append(result)
            rec = result["recommendation"]
            score = f"成功率:{result['success_rate']:.0%} URL数:{result['total_urls']}"
            print(f"→ {rec} | {score}")

        # 生成报告
        report = {
            "date": self.today.isoformat(),
            "word_version": self.keywords.get("version"),
            "candidates_generated": len(candidates),
            "candidates_tested": len(tested),
            "strong_add_tier2": [t for t in tested if t["recommendation"] == "strong_add_tier2"],
            "add_tier3": [t for t in tested if t["recommendation"] == "add_tier3"],
            "weak_signal": [t for t in tested if t["recommendation"] == "weak_signal"],
            "skip": [t for t in tested if t["recommendation"] == "skip"],
            "all_results": tested
        }

        # 保存报告
        with open(REPORT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # 打印摘要
        print(f"\n📊 测试报告摘要:")
        print(f"  强建议加入 tier2: {len(report['strong_add_tier2'])} 个")
        print(f"  建议加入 tier3: {len(report['add_tier3'])} 个")
        print(f"  弱信号观察: {len(report['weak_signal'])} 个")
        print(f"  跳过: {len(report['skip'])} 个")

        if report['strong_add_tier2']:
            print(f"\n🌟 强建议加入 tier2 的词:")
            for t in report['strong_add_tier2']:
                print(f"    - {t['word']} (成功率:{t['success_rate']:.0%}, URL数:{t['total_urls']})")

        if report['add_tier3']:
            print(f"\n🧪 建议加入 tier3 实验的词:")
            for t in report['add_tier3']:
                print(f"    - {t['word']} (成功率:{t['success_rate']:.0%}, URL数:{t['total_urls']})")

        return report

    def apply_recommendations(self, strong_add_list):
        """将强建议的词自动加入 search-keywords.json tier3_experimental"""
        added = []
        existing = set()
        for tier in ["tier1_always", "tier2_rotate", "tier3_experimental", "dead_words"]:
            existing.update(self.keywords.get(tier, []))

        for item in strong_add_list:
            word = item["word"]
            if word not in existing:
                if "tier3_experimental" not in self.keywords:
                    self.keywords["tier3_experimental"] = []
                self.keywords["tier3_experimental"].append(word)
                added.append(word)

        if added:
            self.keywords["version"] = self.keywords.get("version", 0) + 1
            self.keywords["updated"] = self.today.strftime("%Y-%m-%d")
            with open(KEYWORDS_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.keywords, f, ensure_ascii=False, indent=2)
            print(f"\n✅ 已自动加入 tier3_experimental: {len(added)} 个词")
            for w in added:
                print(f"    + {w}")
        else:
            print(f"\nℹ️ 无新词可加入（全部已存在）")


def main():
    parser = argparse.ArgumentParser(description="搜索词自动扩词系统")
    parser.add_argument("--test-count", type=int, default=10, help="测试候选词数量")
    parser.add_argument("--engines", type=str, default="bocha-search,tencent-search,quark-search",
                        help="测试引擎，逗号分隔")
    parser.add_argument("--apply", action="store_true", help="将 strong_add_tier2 的词自动加入 search-keywords.json tier3_experimental")
    args = parser.parse_args()

    engines = args.engines.split(",")
    expander = KeywordExpander()
    report = expander.run(test_count=args.test_count, engines=engines)

    # 自动应用建议
    if args.apply and report.get("strong_add_tier2"):
        expander.apply_recommendations(report["strong_add_tier2"])

    # 输出 JSON 到 stdout（方便管道处理）
    print("\n---JSON_REPORT_START---")
    print(json.dumps(report, ensure_ascii=False))
    print("---JSON_REPORT_END---")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
🦐🔵 Pool Sales Agent MVP
复刻 @gregisenberg 分享的 OpenClaw 泳池销售 Agent
功能：自动找到无泳池的高价房 → 生成泳池渲染图 Prompt → 生成 Outreach 销售文案
"""

import os
import sys
import json
import urllib.request
import urllib.parse

AISA_API_KEY = os.environ.get("AISA_API_KEY", "sk-d2n3PIPWBOc3VTgqHuqvtmTaSZ5JtolHBnUAaUrAZgTjst41")


def llm_chat(messages, model="gpt-4.1-mini"):
    """调用 AISA LLM API"""
    url = "https://api.aisa.one/v1/chat/completions"
    data = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": 0.7
    }).encode()
    
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {AISA_API_KEY}"
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[LLM Error: {e}]"


def generate_pool_rendering_prompt(home_description, home_style="modern"):
    """根据房屋描述生成泳池渲染图的 DALL-E/Midjourney Prompt"""
    prompt = f"""You are a professional pool design AI. Based on the home description below, 
generate a detailed image generation prompt (in English, ~120 words) for adding a 
modern swimming pool to the backyard.

Home description: {home_description}
Style preference: {home_style}

Requirements:
1. Preserve the original home's architectural style
2. Add a beautiful, realistic swimming pool with deck/patio
3. Include landscaping, lighting, and outdoor furniture
4. Make it look like a real estate listing photo
5. Golden hour lighting, photorealistic, 8K quality

Output ONLY the image prompt, nothing else."""
    
    return llm_chat([{"role": "user", "content": prompt}])


def generate_sales_pitch(home_info, pool_features):
    """生成个性化销售 Outreach 文案"""
    prompt = f"""You are an elite pool sales specialist. Write a personalized outreach message 
to a homeowner recommending a pool installation. Be professional, persuasive but not pushy.

Home info: {home_info}
Pool design: {pool_features}

Generate a JSON response with these fields:
- "subject": Email subject line (compelling, under 60 chars)
- "opening": 2-3 sentence personalized opening mentioning the home
- "value_prop": Why this specific home is perfect for a pool
- "social_proof": One sentence with a relevant stat or testimonial
- "cta": Clear call-to-action offering a free design consultation
- "signature": Professional sign-off

Output valid JSON only."""
    
    response = llm_chat([{"role": "user", "content": prompt}])
    try:
        # Try to extract JSON from response
        start = response.find('{')
        end = response.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(response[start:end])
        return json.loads(response)
    except:
        return {
            "subject": "Transform Your Backyard into a Resort",
            "opening": response[:200],
            "value_prop": "Your home is perfect for a pool",
            "social_proof": "Pool owners see 7-15% home value increase",
            "cta": "Reply for a free design consultation",
            "signature": "Pool Design Team"
        }


def analyze_home_for_pool(home_description):
    """分析房屋是否适合安装泳池"""
    prompt = f"""Analyze this home description and determine if it's suitable for a swimming pool installation.
Rate each factor 1-10 and give an overall score.

Home: {home_description}

Evaluate:
1. Backyard space availability
2. Neighborhood/price range fit for pool
3. Climate suitability
4. Existing landscaping flexibility

Output as JSON: {{"suitable": true/false, "space_score": N, "market_score": N, "climate_score": N, "landscaping_score": N, "overall_score": N, "reasoning": "..."}}"""
    
    response = llm_chat([{"role": "user", "content": prompt}], model="gpt-4.1-mini")
    try:
        start = response.find('{')
        end = response.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(response[start:end])
        return json.loads(response)
    except:
        return {"suitable": True, "overall_score": 7, "reasoning": "Default: suitable"}


def main():
    print("🦐🔵 Pool Sales Agent MVP")
    print("=" * 60)
    print("复刻 @gregisenberg 的 OpenClaw 泳池销售 Agent")
    print("=" * 60)
    
    # Demo homes dataset
    demo_homes = [
        {
            "address": "4521 Palm Canyon Dr, Boca Raton, FL 33487",
            "price": 875000,
            "bedrooms": 4,
            "bathrooms": 3,
            "sqft": 3100,
            "lot_size": "0.35 acres",
            "description": "Stunning Mediterranean-style estate with expansive backyard overlooking golf course. No pool. Recently renovated chef's kitchen, marble floors, impact windows. Large covered patio perfect for outdoor living.",
            "has_pool": False,
            "year_built": 2015
        },
        {
            "address": "890 Ocean Blvd, Delray Beach, FL 33483",
            "price": 1150000,
            "bedrooms": 5,
            "bathrooms": 4,
            "sqft": 4200,
            "lot_size": "0.5 acres",
            "description": "Coastal contemporary masterpiece with ocean views. Spacious backyard with mature palm trees and privacy hedges. No pool currently. Smart home features, gourmet kitchen, 3-car garage.",
            "has_pool": False,
            "year_built": 2019
        },
        {
            "address": "2345 Lakeview Cir, Weston, FL 33331",
            "price": 650000,
            "bedrooms": 3,
            "bathrooms": 2,
            "sqft": 2200,
            "lot_size": "0.25 acres",
            "description": "Charming single-family home in gated community. Small backyard with existing pool. Updated kitchen and bathrooms.",
            "has_pool": True,
            "year_built": 2008
        }
    ]
    
    # Filter: no pool + price between $500k-$1.2M
    target_homes = [
        h for h in demo_homes 
        if not h.get("has_pool", False) 
        and 500000 <= h["price"] <= 1200000
    ]
    
    print(f"\n📊 筛选结果: {len(target_homes)} / {len(demo_homes)} 套房产符合标准")
    print("   (无泳池 + 价格 $500K-$1.2M)")
    
    for i, home in enumerate(target_homes, 1):
        print(f"\n{'─' * 60}")
        print(f"🏠 [{i}] 目标房产: {home['address']}")
        print(f"💰 挂牌价: ${home['price']:,}")
        print(f"🛏️  {home['bedrooms']}卧 {home['bathrooms']}卫 | 📐 {home['sqft']:,} sqft")
        print(f"🌳 占地面积: {home['lot_size']} | 建造年份: {home['year_built']}")
        
        # Step 1: Analyze suitability
        print(f"\n🔍 Step 1: AI 分析泳池适配度...")
        analysis = analyze_home_for_pool(home["description"])
        print(f"   适配总分: {analysis.get('overall_score', 'N/A')}/10")
        print(f"   判定: {'✅ 适合' if analysis.get('suitable') else '❌ 不适合'}")
        print(f"   理由: {analysis.get('reasoning', 'N/A')[:100]}...")
        
        if not analysis.get('suitable', True):
            print("   ⏭️ 跳过此房产")
            continue
        
        # Step 2: Generate pool rendering prompt
        print(f"\n🎨 Step 2: 生成泳池渲染图 Prompt...")
        rendering_prompt = generate_pool_rendering_prompt(home["description"], "luxury modern")
        print(f"   {rendering_prompt[:150]}...")
        
        # Step 3: Generate sales pitch
        print(f"\n💼 Step 3: 生成 Outreach 销售文案...")
        pitch = generate_sales_pitch(home["description"], rendering_prompt)
        print(f"
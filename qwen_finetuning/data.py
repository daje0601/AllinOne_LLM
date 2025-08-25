
import json
import anthropic
import random
import os
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List, Dict, Any

# Tools 정의
tools = [
    {
      "name": "add_product",
      "description": "장바구니에 상품을 추가합니다. 사용자가 상품 구매나 주문 의사를 표현할 때 호출됩니다. 특히 '줘', '주세요' 등의 표현이 포함되면 구매 의사로 판단하고 이 함수를 호출해야 합니다. 상품명은 필수이며, 수량을 명시하지 않으면 기본값 1이 적용됩니다. 사이즈는 신발, 의류 등 구매 시 필요한 정보로, 사용자가 명시하지 않으면 반드시 사용자에게 사이즈를 물어봐야 합니다.",
      "parameters": {
        "type": "object",
        "properties": {
          "product_id": {
            "description": "상품 고유 ID (선택사항)",
            "type": "string"
          },
          "product_name": {
            "description": "상품명",
            "type": "string"
          },
          "quantity": {
            "description": "추가할 수량 (기본값: 1)",
            "type": "integer",
            "default": 1
          },
          "size": {
            "description": "상품 사이즈 (해당 상품에 사이즈가 있는 경우 필수)",
            "type": "string"
          },
          "color": {
            "description": "상품 색상",
            "type": "string"
          }
        },
        "required": ["product_name", "quantity", "color"]
      }
    },
    {
      "name": "remove_product",
      "description": "장바구니에서 특정 상품을 제거합니다. 상품명, 수량, 사이즈를 지정하여 정확한 상품을 제거합니다.",
      "parameters": {
        "type": "object",
        "properties": {
          "product_id": {
            "description": "제거할 상품 ID (선택사항)",
            "type": "string"
          },
          "product_name": {
            "description": "제거할 상품명",
            "type": "string"
          },
          "quantity": {
            "description": "제거할 수량",
            "type": "integer"
          },
          "size": {
            "description": "제거할 상품의 사이즈",
            "type": "string"
          },
          "color": {
            "description": "제거할 상품의 색상",
            "type": "string"
          }
        },
        "required": ["product_name", "quantity", "size"]
      }
    },
    {
      "name": "modify_product_options",
      "description": "장바구니에 있는 상품의 옵션(사이즈, 색상 등)을 변경합니다. 현재 옵션과 새로운 옵션을 모두 명시해야 합니다.",
      "parameters": {
        "type": "object",
        "properties": {
          "product_id": {
            "description": "옵션 변경할 상품 ID (선택사항)",
            "type": "string"
          },
          "product_name": {
            "description": "옵션 변경할 상품명",
            "type": "string"
          },
          "current_options": {
            "description": "현재 옵션 (사이즈, 색상)",
            "type": "object",
            "properties": {
              "size": {"type": "string"},
              "color": {"type": "string"}
            }
          },
          "new_options": {
            "description": "변경할 새 옵션",
            "type": "object",
            "properties": {
              "size": {"type": "string"},
              "color": {"type": "string"}
            }
          }
        },
        "required": ["product_name", "current_options", "new_options"]
      }
    },
    {
      "name": "proceed_to_checkout",
      "description": "장바구니 상품들의 구매 프로세스를 진행합니다. '구매할게', '결제할게', '주문 완료', '이걸로 살게요' 등 최종 구매 의사 표현 시 호출됩니다.",
      "parameters": {
        "type": "object",
        "properties": {
          "action": {
            "description": "진행할 액션 (proceed: 결제 진행, cancel: 주문 취소)",
            "type": "string",
            "enum": ["proceed", "cancel"]
          },
          "payment_method": {
            "description": "결제 수단 (선택사항)",
            "type": "string",
            "enum": ["card", "bank_transfer", "mobile_payment", "cash"]
          }
        },
        "required": ["action"]
      }
    },
    {
      "name": "view_cart",
      "description": "장바구니의 현재 상태를 확인합니다. '장바구니 확인', '장바구니에 뭐 있어?', '장바구니 보여줘' 등의 요청 시 호출됩니다.",
      "parameters": {
        "type": "object",
        "properties": {
          "view_type": {
            "description": "조회 타입 (summary: 요약, detailed: 상세)",
            "type": "string",
            "enum": ["summary", "detailed"],
            "default": "summary"
          }
        }
      }
    },
    {
      "name": "calculate_total",
      "description": "장바구니 총 금액을 계산합니다. '총 얼마야?', '전체 금액이 얼마야?' 등의 질문 시 호출됩니다.",
      "parameters": {
        "type": "object",
        "properties": {}
      }
    },
    {
      "name": "reset_cart",
      "description": "장바구니를 비우고 초기 상태로 리셋합니다. '장바구니 비우기', '초기화', '다시 시작' 등의 요청 시 호출됩니다.",
      "parameters": {
        "type": "object",
        "properties": {
          "confirm": {
            "description": "리셋 확인 (안전장치)",
            "type": "boolean"
          }
        },
        "required": ["confirm"]
      }
    },
    {
        "name": "check_inventory",
        "description": "특정 상품의 재고를 확인합니다. '재고 있나요?', '남은 수량 확인' 등의 요청 시 호출됩니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {
                    "description": "재고를 확인할 상품명",
                    "type": "string"
                },
                "color": {
                    "description": "확인할 색상 (선택사항)",
                    "type": "string"
                },
                "size": {
                    "description": "확인할 사이즈 (선택사항)",
                    "type": "string"
                }
            },
            "required": ["product_name"]
        }
    },
    {
        "name": "search_products",
        "description": "상품을 검색합니다. 카테고리, 가격대, 키워드 등으로 검색 가능합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "keyword": {
                    "description": "검색 키워드 (선택사항)",
                    "type": "string"
                },
                "category": {
                    "description": "상품 카테고리 (신발, 의류, 액세서리)",
                    "type": "string",
                    "enum": ["신발", "의류", "액세서리"]
                },
                "price_min": {
                    "description": "최소 가격",
                    "type": "integer"
                },
                "price_max": {
                    "description": "최대 가격",
                    "type": "integer"
                }
            }
        }
    },
    {
        "name": "get_product_info",
        "description": "특정 상품의 상세 정보를 조회합니다. 가격, 색상, 사이즈, 설명 등을 확인할 수 있습니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {
                    "description": "조회할 상품명",
                    "type": "string"
                },
                "info_type": {
                    "description": "조회할 정보 유형",
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["price", "colors", "sizes", "description", "all"]
                    },
                    "default": ["all"]
                }
            },
            "required": ["product_name"]
        }
    },
    {
        "name": "check_price",
        "description": "상품의 가격을 확인합니다. '얼마예요?', '가격이 어떻게 되나요?' 등의 질문 시 호출됩니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {
                    "description": "가격을 확인할 상품명",
                    "type": "string"
                }
            },
            "required": ["product_name"]
        }
    },
    {
        "name": "view_order_history",
        "description": "사용자의 주문 내역을 조회합니다. 과거 구매 내역, 주문 상태 등을 확인할 수 있습니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "description": "사용자 ID",
                    "type": "string"
                },
                "status": {
                    "description": "주문 상태 필터",
                    "type": "string",
                    "enum": ["all", "완료", "배송중", "배송준비중", "취소됨"],
                    "default": "all"
                },
                "limit": {
                    "description": "조회할 주문 개수",
                    "type": "integer",
                    "default": 5
                }
            },
            "required": ["user_id"]
        }
    }
]


products = [
    # 신발 카테고리
    {"id": "SH001", "name": "클라우드 워커", "category": "신발", "type": "스니커즈", "brand": "AI Style", 
     "price": 89000, "colors": ["화이트", "블랙", "그레이", "네이비"], 
     "sizes": ["230", "240", "250", "260", "270", "280"], "stock": 45},
    
    {"id": "SH002", "name": "스트릿 러너", "category": "신발", "type": "런닝화", "brand": "AI Style",
     "price": 129000, "colors": ["레드", "블루", "옐로우", "민트"],
     "sizes": ["235", "240", "245", "250", "255", "260", "265", "270", "275", "280"], "stock": 60},
    
    {"id": "SH003", "name": "빈티지 하이탑", "category": "신발", "type": "하이탑 스니커즈", "brand": "AI Style",
     "price": 109000, "colors": ["베이지", "브라운", "카키"],
     "sizes": ["240", "250", "260", "270", "280"], "stock": 30},
    
    # 의류 카테고리
    {"id": "CL001", "name": "에센셜 후디", "category": "의류", "type": "후드티", "brand": "Daily Wear",
     "price": 69000, "colors": ["블랙", "그레이", "크림", "네이비"],
     "sizes": ["S", "M", "L", "XL", "XXL"], "stock": 80},
    
    {"id": "CL002", "name": "슬림 데님", "category": "의류", "type": "청바지", "brand": "Daily Wear",
     "price": 79000, "colors": ["인디고", "블랙", "라이트블루"],
     "sizes": ["28", "30", "32", "34", "36"], "stock": 50},
    
    {"id": "CL003", "name": "오버핏 셔츠", "category": "의류", "type": "셔츠", "brand": "Daily Wear",
     "price": 59000, "colors": ["화이트", "스카이블루", "베이지", "핑크"],
     "sizes": ["S", "M", "L", "XL"], "stock": 40},
    
    # 액세서리 카테고리
    {"id": "AC001", "name": "미니멀 백팩", "category": "액세서리", "type": "백팩", "brand": "AI Gear",
     "price": 89000, "colors": ["블랙", "네이비", "그레이"], "stock": 35},
    
    {"id": "AC002", "name": "클래식 캡", "category": "액세서리", "type": "모자", "brand": "AI Gear",
     "price": 29000, "colors": ["블랙", "화이트", "베이지", "카키"], "stock": 100},
    
    {"id": "AC003", "name": "레더 벨트", "category": "액세서리", "type": "벨트", "brand": "Premium Line",
     "price": 49000, "colors": ["블랙", "브라운", "네이비"], 
     "sizes": ["85", "90", "95", "100", "105"], "stock": 55}
]
# Tools definition 생성
tool_entries = [
    json.dumps({
        "type": "function",
        "function": {
            "name": tool["name"],
            "description": tool["description"],
            "parameters": tool["parameters"]
        }
    }, ensure_ascii=False)
    for tool in tools
]
tools_definition = "<tools>\n" + "\n".join(tool_entries) + "\n</tools>\n"


# 확장된 시나리오 리스트 (새로운 함수들 포함)
scenario_list = [
    # 기존 시나리오
    "add_product → view_cart → proceed_to_checkout",
    "add_product → add_product → calculate_total → proceed_to_checkout",
    "add_product → modify_product_options → proceed_to_checkout",
    "add_product → remove_product → add_product → proceed_to_checkout",
    "view_cart → add_product → calculate_total → reset_cart",
    
    # 새로운 함수를 활용한 시나리오
    "search_products → get_product_info → add_product → proceed_to_checkout",
    "check_price → check_inventory → add_product → view_cart → proceed_to_checkout",
    "search_products → check_price → add_product → calculate_total → proceed_to_checkout",
    "get_product_info → add_product → modify_product_options → proceed_to_checkout",
    "view_order_history → search_products → add_product → proceed_to_checkout",
    "search_products → get_product_info → check_inventory → add_product → proceed_to_checkout",
    "check_price → add_product → view_cart → add_product → calculate_total → proceed_to_checkout",
    "search_products → add_product → remove_product → search_products → add_product → proceed_to_checkout",
    "get_product_info → check_inventory → add_product → modify_product_options → view_cart → proceed_to_checkout",
    "view_order_history → search_products → check_price → add_product → calculate_total → proceed_to_checkout"
]

# 상품을 카테고리별로 분류
SHOES = [p for p in products if p['category'] == '신발']
CLOTHES = [p for p in products if p['category'] == '의류']
ACCESSORIES = [p for p in products if p['category'] == '액세서리']
ALL_PRODUCTS = products

# Claude API 설정
MODEL_PRICES = {
    "claude-opus-4-1-20250805": {
        "input": 15.0,   # $3.00 per 1M input tokens
        "output": 75.0  # $15.00 per 1M output tokens
    }
}

def calculate_cost(input_tokens, output_tokens, model_name="claude-opus-4-1-20250805"):
    """토큰 사용량에 따른 비용을 계산합니다."""
    if model_name not in MODEL_PRICES:
        raise ValueError(f"Unknown model: {model_name}")
    return (
        input_tokens * MODEL_PRICES[model_name]["input"] / 1000000 +
        output_tokens * MODEL_PRICES[model_name]["output"] / 1000000
    )

def generate_random_date():
    """랜덤 날짜 생성 (최근 3개월 이내)"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    random_days = random.randint(0, 90)
    random_date = start_date + timedelta(days=random_days)
    return random_date.strftime("%Y-%m-%d")

def create_balanced_product_distribution(total_scenarios):
    """시나리오별로 상품이 골고루 분배되도록 하는 함수"""
    min_appearances_per_product = total_scenarios // len(ALL_PRODUCTS)
    product_assignments = []
    product_count = defaultdict(int)
    
    # 각 상품이 최소 횟수만큼 등장하도록 보장
    for i in range(total_scenarios):
        if i < len(ALL_PRODUCTS) * min_appearances_per_product:
            product_idx = i % len(ALL_PRODUCTS)
            selected_product = ALL_PRODUCTS[product_idx]
            product_count[selected_product['name']] += 1
        else:
            # 나머지는 랜덤하게 할당하되, 균형을 맞추기 위해 가중치 적용
            weights = []
            for product in ALL_PRODUCTS:
                current_count = product_count[product['name']]
                avg_count = sum(product_count.values()) / len(ALL_PRODUCTS)
                weight = max(1, avg_count - current_count + 1)
                weights.append(weight)
            
            selected_product = random.choices(ALL_PRODUCTS, weights=weights)[0]
            product_count[selected_product['name']] += 1
        
        product_assignments.append(selected_product)
    
    # 각 시나리오별로 사용할 상품들 결정
    scenario_products = []
    for i in range(total_scenarios):
        primary_product = product_assignments[i]
        
        # 주요 상품의 카테고리에 따라 다른 상품들도 선택
        if primary_product['category'] == '신발':
            available_shoes = [primary_product]
            other_shoes = [s for s in SHOES if s['id'] != primary_product['id']]
            if other_shoes:
                available_shoes.extend(random.sample(other_shoes, min(2, len(other_shoes))))
            available_clothes = random.sample(CLOTHES, min(2, len(CLOTHES)))
            available_accessories = random.sample(ACCESSORIES, min(2, len(ACCESSORIES)))
            
        elif primary_product['category'] == '의류':
            available_clothes = [primary_product]
            other_clothes = [c for c in CLOTHES if c['id'] != primary_product['id']]
            if other_clothes:
                available_clothes.extend(random.sample(other_clothes, min(2, len(other_clothes))))
            available_shoes = random.sample(SHOES, min(2, len(SHOES)))
            available_accessories = random.sample(ACCESSORIES, min(2, len(ACCESSORIES)))
            
        else:  # 액세서리
            available_accessories = [primary_product]
            other_accessories = [a for a in ACCESSORIES if a['id'] != primary_product['id']]
            if other_accessories:
                available_accessories.extend(random.sample(other_accessories, min(2, len(other_accessories))))
            available_shoes = random.sample(SHOES, min(2, len(SHOES)))
            available_clothes = random.sample(CLOTHES, min(2, len(CLOTHES)))
        
        scenario_products.append({
            'primary_product': primary_product,
            'available_shoes': available_shoes,
            'available_clothes': available_clothes,
            'available_accessories': available_accessories
        })
    
    return scenario_products, product_count

def generate_dialogue(scenario_data, client, scenario_index):
    """단일 대화 생성 함수 (새로운 함수들 포함)"""
    product_info = scenario_data
    
    # 확장된 Tools 반환 형식
    tools_return_format = """
    Function Response 형식:
    - add_product: {"success": True/False, "message": "상품이 추가되었습니다", "cart_item": {"product_name": str, "brand": str, "type": str, "color": str, "size": str, "quantity": int, "price": int}}
    - remove_product: {"success": True/False, "message": "상품이 제거되었습니다"}
    - modify_product_options: {"success": True/False, "message": "옵션이 변경되었습니다", "updated_item": {...}}
    - view_cart: {"success": True/False, "items": [...], "total": int}
    - calculate_total: {"success": True/False, "total": int, "item_count": int, "message": "총 X개 상품, 합계: XXX원"}
    - proceed_to_checkout: {"success": True/False, "message": "주문이 완료되었습니다", "order_id": "ORD-YYYYMMDDHHMMSS", "total": int}
    - reset_cart: {"success": True/False, "message": "장바구니가 초기화되었습니다"}
    - check_inventory: {"success": True/False, "inventory": {"product_name": str, "brand": str, "type": str, "total_stock": int}, "message": "재고: X개"}
    - search_products: {"success": True/False, "count": int, "products": [{"id": str, "name": str, "brand": str, "type": str, "price": int, "category": str, "colors": [...]}], "message": "X개의 상품을 찾았습니다"}
    - get_product_info: {"success": True/False, "product": {"id": str, "name": str, "brand": str, "type": str, "price": int, "colors": [...], "sizes": [...]}}
    - check_price: {"success": True/False, "product_name": str, "brand": str, "price": int, "message": "가격은 XXX원입니다"}
    - view_order_history: {"success": True/False, "user_id": str, "count": int, "orders": [...], "message": "최근 X개의 주문 내역입니다"}
    """
    
    try:
        # 사용 가능한 상품 목록 생성
        available_products = []
        available_products.extend(product_info['available_shoes'])
        available_products.extend(product_info['available_clothes'])
        available_products.extend(product_info['available_accessories'])
        
        # 상품 정보를 브랜드와 타입 포함하여 생성
        def format_product_with_details(product):
            return f"{product['name']} ({product['brand']}, {product['type']}) - 가격: {product['price']:,}원 | 색상: {', '.join(product['colors'])} | 사이즈: {', '.join(product.get('sizes', ['프리사이즈']))}"
        
        # 카테고리별 상품 정보 (브랜드, 타입 포함)
        shoes_list_with_details = [format_product_with_details(p) for p in product_info['available_shoes']]
        clothes_list_with_details = [format_product_with_details(p) for p in product_info['available_clothes']]
        accessories_list_with_details = [format_product_with_details(p) for p in product_info['available_accessories']]
        
        # 주요 상품의 상세 정보
        primary = product_info['primary_product']
        
        # 시나리오 선택
        scenario = scenario_list[scenario_index % len(scenario_list)]
        
        # 사용자 ID 생성
        user_id = f"U{random.randint(1, 999):03d}"
        
        # 날짜 생성
        chat_date = generate_random_date()
        
        user_prompt = f"""
당신은 온라인 쇼핑몰 'AI쇼핑몰'의 AI 챗봇을 위한 한국어 멀티턴 대화 데이터를 생성해야 합니다.

### 1. 전체 상품 목록 (브랜드, 타입, 재고 포함)
{json.dumps([{
    'id': p['id'],
    'name': p['name'],
    'brand': p['brand'],
    'type': p['type'],
    'category': p['category'],
    'price': p['price'],
    'colors': p['colors'],
    'sizes': p.get('sizes', ['프리사이즈']),
    'stock': p['stock']
} for p in ALL_PRODUCTS], ensure_ascii=False, indent=2)}

### 2. 이번 대화에서 사용 가능한 상품 (상세 정보)
* 신발:
{chr(10).join(shoes_list_with_details)}

* 의류:
{chr(10).join(clothes_list_with_details)}

* 액세서리:
{chr(10).join(accessories_list_with_details)}

### 3. **주요 상품 (균형된 데이터셋을 위해 필수)**
**이번 대화의 핵심 상품: {primary['name']}**
- ID: {primary['id']}
- 브랜드: {primary['brand']}
- 타입: {primary['type']}
- 가격: {primary['price']:,}원
- 색상: {', '.join(primary['colors'])}
- 사이즈: {', '.join(primary.get('sizes', ['프리사이즈']))}
- 재고: {primary['stock']}개

필수 요구사항:
- 주요 상품({primary['name']})이 대화의 중심이 되어야 합니다
- **가격은 반드시 위에 명시된 정확한 금액을 사용해야 합니다**
- 할인이나 배송비는 없습니다. 정가로만 계산합니다.
- 브랜드와 타입 정보를 자연스럽게 활용하세요.

### 4. 사용 가능한 Function Calling 도구 (12개)

{tools_definition}

### 5. Function Response 형식

{tools_return_format}

### 6. 시나리오 구성
이번 대화 시나리오: {scenario}

시나리오 규칙:
1. 인사로 시작
2. 시나리오의 각 단계를 순서대로 진행
3. 자연스러운 대화 흐름 유지
4. 새로운 함수들을 적극 활용:
   - search_products로 브랜드나 타입별 검색
   - get_product_info로 상세 정보 확인
   - check_inventory로 재고 확인
   - check_price로 가격 문의
   - view_order_history로 이전 구매 내역 참조

### 7. 대화 형식

[고객 ID] {user_id}
[대화날짜] {chat_date}

(고객) 고객 발화
(AI 상담사) AI 상담사 응답  
(function_call) [list of dict with name and arguments]
(function_response) dict with response data
(AI 상담사) function 처리 후 응답

중요 규칙:
- function_call과 function_response는 Python dict/list 형식으로 작성
- 이스케이프 문자(\\\") 사용하지 않기
- true/false 대신 True/False 사용
- 8-15회의 멀티턴 대화로 구성 (새로운 함수 활용으로 더 풍부한 대화)

### 8. 새로운 함수 활용 예시

**search_products 예시:**
(고객) AI Style 브랜드 상품 보여주세요
(function_call) [{{"name": "search_products", "arguments": {{"brand": "AI Style"}}}}]
(function_response) {{"success": True, "count": 3, "products": [{{"id": "SH001", "name": "클라우드 워커", "brand": "AI Style", "type": "스니커즈", "price": 89000, "category": "신발", "colors": ["화이트", "블랙", "그레이", "네이비"]}}], "message": "3개의 상품을 찾았습니다"}}
(AI 상담사) AI Style 브랜드 상품을 3개 찾았습니다! 클라우드 워커 스니커즈(89,000원), 스트릿 러너 런닝화(129,000원), 빈티지 하이탑(109,000원)이 있습니다.

**check_inventory 예시:**
(고객) 클라우드 워커 재고 있나요?
(function_call) [{{"name": "check_inventory", "arguments": {{"product_name": "클라우드 워커", "color": "블랙", "size": "260"}}}}]
(function_response) {{"success": True, "inventory": {{"product_name": "클라우드 워커", "brand": "AI Style", "type": "스니커즈", "total_stock": 45, "color_stock": 11, "size_stock": 7}}, "message": "클라우드 워커 재고: 45개"}}
(AI 상담사) 네, 클라우드 워커 블랙 260 사이즈 재고가 7개 있습니다!

**get_product_info 예시:**
(고객) 에센셜 후디 정보 좀 알려주세요
(function_call) [{{"name": "get_product_info", "arguments": {{"product_name": "에센셜 후디"}}}}]
(function_response) {{"success": True, "product": {{"id": "CL001", "name": "에센셜 후디", "brand": "Daily Wear", "type": "후드티", "price": 69000, "colors": ["블랙", "그레이", "크림", "네이비"], "sizes": ["S", "M", "L", "XL", "XXL"], "stock": 80}}}}
(AI 상담사) 에센셜 후디는 Daily Wear 브랜드의 제품으로 69,000원입니다. 블랙, 그레이, 크림, 네이비 색상이 있고, S부터 XXL까지 사이즈가 준비되어 있습니다.

**view_order_history 예시:**
(고객) 제 주문 내역 보여주세요
(function_call) [{{"name": "view_order_history", "arguments": {{"user_id": "{user_id}", "limit": 3}}}}]
(function_response) {{"success": True, "user_id": "{user_id}", "count": 2, "orders": [{{"order_id": "ORD-20240115143022", "items": [{{"product_name": "클라우드 워커", "brand": "AI Style", "quantity": 1}}], "total": 89000, "status": "배송완료"}}], "message": "최근 2개의 주문 내역입니다"}}
(AI 상담사) 최근 주문 내역을 확인했습니다. 1월 15일에 AI Style 클라우드 워커를 89,000원에 구매하셨고, 배송 완료되었네요!

### 9. 브랜드와 타입 활용

- "AI Style의 스니커즈를 찾고 있어요" → search_products with brand and type
- "Daily Wear 브랜드 제품 중에 7만원 이하 상품 있나요?" → search_products with brand and price_max
- "런닝화 종류 뭐 있나요?" → search_products with type="런닝화"

### 대화 생성

위의 모든 규칙을 따라 자연스럽고 현실적인 한국어 대화를 생성하세요.
**특히 새로운 함수들(search_products, check_inventory, get_product_info, check_price, view_order_history)을 적극 활용하여 더 풍부한 대화를 만드세요.**
**브랜드와 타입 정보를 자연스럽게 대화에 녹여내세요.**
"""

        response = client.messages.create(
            model="claude-opus-4-1-20250805",
            max_tokens=8192,
            temperature=0.3,
            system="당신은 한국 온라인 쇼핑몰의 AI 챗봇 대화 데이터를 생성하는 전문가입니다. 12개의 function을 모두 활용하여 풍부한 대화를 생성하세요.",
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        return {
            'scenario_index': scenario_index,
            'scenario': scenario,
            'primary_product': product_info['primary_product']['name'],
            'primary_brand': product_info['primary_product']['brand'],
            'primary_type': product_info['primary_product']['type'],
            'dialogue': response.content[0].text,
            'input_tokens': response.usage.input_tokens,
            'output_tokens': response.usage.output_tokens,
            'cost': calculate_cost(response.usage.input_tokens, response.usage.output_tokens)
        }
        
    except Exception as e:
        import traceback
        return {
            'error': str(e) + '\n' + traceback.format_exc(),
            'scenario_index': scenario_index,
            'primary_product': product_info.get('primary_product', {}).get('name', 'unknown')
        }

def main():
    """메인 실행 함수"""
    # Claude API 클라이언트 초기화
    api_key = os.environ.get("ANTHROPIC_API_KEY", "YOUR_API_KEY_HERE")
    if api_key == "YOUR_API_KEY_HERE":
        print("⚠️  ANTHROPIC_API_KEY 환경변수를 설정하거나 코드에 직접 입력하세요.")
        return
    
    client = anthropic.Anthropic(api_key=api_key)
    
    # 생성할 대화 수
    total_scenarios = 5  # 원하는 대화 수로 조정
    
    print(f"총 {total_scenarios}개의 시나리오에 대해 균등한 상품 분배를 생성합니다...")
    print(f"사용 가능한 시나리오 패턴: {len(scenario_list)}개")
    print(f"사용 가능한 함수: {len(tools)}개")
    
    # 균등한 상품 분배 생성
    scenario_products, product_count = create_balanced_product_distribution(total_scenarios)
    
    # 상품 분배 결과 출력
    print("\n=== 상품별 등장 횟수 ===")
    for product, count in sorted(product_count.items()):
        prod_info = next(p for p in ALL_PRODUCTS if p['name'] == product)
        print(f"{product} ({prod_info['brand']}, {prod_info['type']}): {count}회")
    
    print(f"\n평균 등장 횟수: {sum(product_count.values()) / len(product_count):.1f}")
    print(f"최소 등장 횟수: {min(product_count.values())}")
    print(f"최대 등장 횟수: {max(product_count.values())}")
    
    # 결과 저장 디렉토리 생성
    output_dir = "generated_dialogues"
    os.makedirs(output_dir, exist_ok=True)
    
    # 상품 분배 정보 저장
    with open(f"{output_dir}/product_distribution.json", "w", encoding='utf-8') as f:
        json.dump({
            'total_products': len(ALL_PRODUCTS),
            'total_scenarios': total_scenarios,
            'scenarios_patterns': len(scenario_list),
            'functions_count': len(tools),
            'product_count': dict(product_count),
            'products_info': ALL_PRODUCTS,
            'scenario_list': scenario_list,
            'scenario_products': [
                {
                    'scenario_index': i,
                    'scenario': scenario_list[i % len(scenario_list)],
                    'primary_product': sp['primary_product']['name'],
                    'primary_brand': sp['primary_product']['brand'],
                    'primary_type': sp['primary_product']['type'],
                    'available_products_count': len(sp['available_shoes']) + len(sp['available_clothes']) + len(sp['available_accessories'])
                }
                for i, sp in enumerate(scenario_products)
            ]
        }, f, ensure_ascii=False, indent=2)
    
    # 대화 생성
    print(f"\n{total_scenarios}개의 대화 생성을 시작합니다...")
    
    results = []
    total_cost = 0
    successful_count = 0
    failed_count = 0
    
    # 배치 처리 (API 속도 제한 고려)
    batch_size = 5  # 한 번에 처리할 대화 수
    test_mode = True  # 테스트 모드
    test_count = 5 if test_mode else total_scenarios  # 테스트로 10개만 생성
    
    for i in range(0, test_count, batch_size):
        batch_end = min(i + batch_size, test_count)
        print(f"\n처리중: {i+1}-{batch_end}/{test_count}")
        
        for j in range(i, batch_end):
            result = generate_dialogue(scenario_products[j], client, j)
            
            if 'error' in result:
                print(f"  ❌ 실패 (시나리오 {j}): {result['error']}")
                failed_count += 1
            else:
                print(f"  ✅ 성공 (시나리오 {j}): {result['primary_product']} ({result['primary_brand']}) - 비용: ${result['cost']:.4f}")
                successful_count += 1
                total_cost += result['cost']
                
                # 대화 저장
                with open(f"{output_dir}/dialogue_{j:04d}.txt", "w", encoding='utf-8') as f:
                    f.write(f"[메타데이터]\n")
                    f.write(f"시나리오 인덱스: {j}\n")
                    f.write(f"시나리오 패턴: {result['scenario']}\n")
                    f.write(f"주요 상품: {result['primary_product']}\n")
                    f.write(f"브랜드: {result['primary_brand']}\n")
                    f.write(f"타입: {result['primary_type']}\n")
                    f.write(f"\n[대화 내용]\n")
                    f.write(result['dialogue'])
            
            results.append(result)
    
    # 최종 결과 출력
    print("\n" + "="*50)
    print("=== 생성 완료 ===")
    print(f"성공: {successful_count}개")
    print(f"실패: {failed_count}개")
    print(f"총 비용: ${total_cost:.4f}")
    if successful_count > 0:
        print(f"평균 비용: ${total_cost/successful_count:.4f}")
    
    # 결과 요약 저장
    with open(f"{output_dir}/generation_summary.json", "w", encoding='utf-8') as f:
        json.dump({
            'configuration': {
                'total_scenarios': total_scenarios,
                'test_mode': test_mode,
                'test_count': test_count if test_mode else total_scenarios,
                'batch_size': batch_size,
                'total_products': len(ALL_PRODUCTS),
                'total_functions': len(tools),
                'scenario_patterns': len(scenario_list)
            },
            'results': {
                'successful': successful_count,
                'failed': failed_count,
                'total_cost': total_cost,
                'average_cost_per_dialogue': total_cost / successful_count if successful_count > 0 else 0
            },
            'timestamp': datetime.now().isoformat()
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 결과가 {output_dir} 디렉토리에 저장되었습니다.")
    print(f"   - 대화 파일: dialogue_XXXX.txt, dialogue_XXXX.json")
    print(f"   - 상품 분배 정보: product_distribution.json")
    print(f"   - 생성 요약: generation_summary.json")

if __name__ == "__main__":
    main()
"""
Qwen3-4B Function Calling 테스트 (간단 버전)
vLLM OpenAI API 호환 서버 사용
"""

import json
import time
from openai import OpenAI
from typing import Dict, List, Optional, Any
from datetime import datetime

# ================== OpenAI 클라이언트 설정 ==================
openai_api_key = "EMPTY"
openai_api_base = "http://localhost:8000/v1"  # vLLM 기본 포트

client = OpenAI(
    api_key=openai_api_key,
    base_url=openai_api_base,
)

# ================== 상품 데이터베이스 ==================

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

# 전역 변수
shopping_cart = []
order_history = []

# ================== 쇼핑몰 함수들 ==================

# 기존 함수들
def add_product(product_id: Optional[str] = None, 
                product_name: str = None, 
                quantity: int = 1, 
                size: Optional[str] = None, 
                color: Optional[str] = None) -> Dict:
    """장바구니에 상품을 추가합니다."""
    if not product_name:
        return {"success": False, "message": "상품명은 필수입니다."}
    
    # 상품 정보 확인 (products 리스트에서 검색)
    product_info = None
    for prod in products:
        if prod["name"] == product_name:
            product_info = prod
            break
    
    if not product_info:
        return {"success": False, "message": f"'{product_name}' 상품을 찾을 수 없습니다."}
    
    # 사이즈 필수 체크 (신발, 의류)
    if product_info["category"] in ["신발", "의류"] and not size:
        return {"success": False, "message": f"'{product_name}'은(는) 사이즈를 선택해야 합니다. 사용 가능한 사이즈: {', '.join(product_info['sizes'])}"}
    
    # 색상 체크
    if color and color not in product_info["colors"]:
        return {"success": False, "message": f"'{color}' 색상은 사용할 수 없습니다. 사용 가능한 색상: {', '.join(product_info['colors'])}"}
    
    # 장바구니에 추가
    cart_item = {
        "product_id": product_id or product_info["id"],
        "product_name": product_name,
        "brand": product_info.get("brand", ""),
        "type": product_info.get("type", ""),
        "quantity": quantity,
        "size": size,
        "color": color,
        "price": product_info["price"],
        "total_price": product_info["price"] * quantity
    }
    
    shopping_cart.append(cart_item)
    
    return {
        "success": True, 
        "message": f"{product_name} {quantity}개가 장바구니에 추가되었습니다.",
        "cart_item": cart_item
    }

def remove_product(product_id: Optional[str] = None,
                  product_name: str = None,
                  quantity: int = None,
                  size: Optional[str] = None,
                  color: Optional[str] = None) -> Dict:
    """장바구니에서 상품을 제거합니다."""
    global shopping_cart
    
    for i, item in enumerate(shopping_cart):
        if item["product_name"] == product_name:
            if size and item["size"] != size:
                continue
            if color and item["color"] != color:
                continue
            
            if quantity and item["quantity"] > quantity:
                item["quantity"] -= quantity
                item["total_price"] = item["price"] * item["quantity"]
                return {"success": True, "message": f"{product_name} {quantity}개가 제거되었습니다."}
            else:
                removed_item = shopping_cart.pop(i)
                return {"success": True, "message": f"{product_name}이(가) 장바구니에서 완전히 제거되었습니다."}
    
    return {"success": False, "message": "해당 상품을 장바구니에서 찾을 수 없습니다."}

def modify_product_options(product_id: Optional[str] = None,
                          product_name: str = None,
                          current_options: Dict = None,
                          new_options: Dict = None) -> Dict:
    """장바구니 상품의 옵션을 변경합니다."""
    for item in shopping_cart:
        if item["product_name"] == product_name:
            if current_options:
                if current_options.get("size") and item["size"] != current_options["size"]:
                    continue
                if current_options.get("color") and item["color"] != current_options["color"]:
                    continue
            
            # 옵션 변경
            if new_options.get("size"):
                item["size"] = new_options["size"]
            if new_options.get("color"):
                item["color"] = new_options["color"]
            
            return {"success": True, "message": f"{product_name}의 옵션이 변경되었습니다.", "updated_item": item}
    
    return {"success": False, "message": "해당 상품을 찾을 수 없습니다."}

def proceed_to_checkout(action: str, payment_method: Optional[str] = None) -> Dict:
    """결제를 진행하거나 취소합니다."""
    global shopping_cart, order_history
    
    if action == "proceed":
        if not shopping_cart:
            return {"success": False, "message": "장바구니가 비어있습니다."}
        
        total = sum(item["total_price"] for item in shopping_cart)
        order = {
            "order_id": f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "items": shopping_cart.copy(),
            "total": total,
            "payment_method": payment_method or "card",
            "status": "배송준비중",
            "order_date": datetime.now().isoformat()
        }
        
        order_history.append(order)
        shopping_cart.clear()
        
        return {
            "success": True, 
            "message": "주문이 완료되었습니다.",
            "order_id": order["order_id"],
            "total": total
        }
    
    elif action == "cancel":
        shopping_cart.clear()
        return {"success": True, "message": "주문이 취소되었습니다."}
    
    return {"success": False, "message": "잘못된 액션입니다."}

def view_cart(view_type: str = "summary") -> Dict:
    """장바구니를 조회합니다."""
    if not shopping_cart:
        return {"success": True, "message": "장바구니가 비어있습니다.", "items": []}
    
    if view_type == "summary":
        return {
            "success": True,
            "item_count": len(shopping_cart),
            "total": sum(item["total_price"] for item in shopping_cart),
            "items": [f"{item['product_name']} ({item['quantity']}개)" for item in shopping_cart]
        }
    else:
        return {
            "success": True,
            "items": shopping_cart,
            "total": sum(item["total_price"] for item in shopping_cart)
        }

def calculate_total() -> Dict:
    """장바구니 총 금액을 계산합니다."""
    if not shopping_cart:
        return {"success": True, "total": 0, "message": "장바구니가 비어있습니다."}
    
    total = sum(item["total_price"] for item in shopping_cart)
    return {
        "success": True,
        "total": total,
        "item_count": len(shopping_cart),
        "message": f"총 {len(shopping_cart)}개 상품, 합계: {total:,}원"
    }

def reset_cart(confirm: bool) -> Dict:
    """장바구니를 초기화합니다."""
    global shopping_cart
    
    if not confirm:
        return {"success": False, "message": "초기화를 확인해주세요."}
    
    shopping_cart.clear()
    return {"success": True, "message": "장바구니가 초기화되었습니다."}

# 새로운 함수들
def check_inventory(product_name: str, color: Optional[str] = None, size: Optional[str] = None) -> Dict:
    """상품의 재고를 확인합니다."""
    for prod in products:
        if prod["name"] == product_name:
            # stock이 없으면 기본값 사용
            stock = prod.get("stock", 50)
            inventory_info = {
                "product_name": product_name,
                "brand": prod.get("brand", ""),
                "type": prod.get("type", ""),
                "total_stock": stock
            }
            
            # 색상별 재고 (간단한 시뮬레이션)
            if color:
                if color in prod["colors"]:
                    inventory_info["color_stock"] = max(5, stock // len(prod["colors"]))
                else:
                    return {"success": False, "message": f"'{color}' 색상은 사용할 수 없습니다."}
            
            # 사이즈별 재고 (간단한 시뮬레이션)
            if size:
                if "sizes" in prod and size in prod["sizes"]:
                    inventory_info["size_stock"] = max(3, stock // len(prod["sizes"]))
                elif "sizes" not in prod:
                    return {"success": False, "message": "이 상품은 사이즈가 없습니다."}
                else:
                    return {"success": False, "message": f"'{size}' 사이즈는 사용할 수 없습니다."}
            
            return {
                "success": True,
                "inventory": inventory_info,
                "message": f"{product_name} 재고: {stock}개"
            }
    
    return {"success": False, "message": f"'{product_name}' 상품을 찾을 수 없습니다."}

def search_products(keyword: Optional[str] = None, 
                   category: Optional[str] = None,
                   price_min: Optional[int] = None,
                   price_max: Optional[int] = None,
                   brand: Optional[str] = None,
                   type: Optional[str] = None) -> Dict:
    """상품을 검색합니다."""
    results = []
    
    for prod in products:
        # 카테고리 필터
        if category and prod["category"] != category:
            continue
        
        # 브랜드 필터
        if brand and prod.get("brand", "").lower() != brand.lower():
            continue
            
        # 타입 필터
        if type and prod.get("type", "").lower() != type.lower():
            continue
        
        # 키워드 검색 (name, brand, type에서 검색)
        if keyword:
            keyword_lower = keyword.lower()
            searchable_text = f"{prod['name']} {prod.get('brand', '')} {prod.get('type', '')}".lower()
            if keyword_lower not in searchable_text:
                continue
        
        # 가격 필터
        if price_min and prod["price"] < price_min:
            continue
        if price_max and prod["price"] > price_max:
            continue
        
        results.append({
            "id": prod["id"],
            "name": prod["name"],
            "brand": prod.get("brand", ""),
            "type": prod.get("type", ""),
            "price": prod["price"],
            "category": prod["category"],
            "colors": prod["colors"]
        })
    
    return {
        "success": True,
        "count": len(results),
        "products": results,
        "message": f"{len(results)}개의 상품을 찾았습니다."
    }

def get_product_info(product_name: str, info_type: List[str] = ["all"]) -> Dict:
    """상품의 상세 정보를 조회합니다."""
    for prod in products:
        if prod["name"] == product_name:
            if "all" in info_type:
                return {"success": True, "product": prod}
            
            result = {
                "success": True, 
                "product_name": product_name,
                "id": prod["id"]
            }
            
            if "price" in info_type:
                result["price"] = prod["price"]
            if "colors" in info_type:
                result["colors"] = prod["colors"]
            if "sizes" in info_type:
                result["sizes"] = prod.get("sizes", [])
            if "brand" in info_type:
                result["brand"] = prod.get("brand", "")
            if "type" in info_type:
                result["type"] = prod.get("type", "")
            if "description" in info_type:
                result["description"] = prod.get("description", f"{prod.get('brand', '')} {prod.get('type', '')}")
            
            return result
    
    return {"success": False, "message": f"'{product_name}' 상품을 찾을 수 없습니다."}

def check_price(product_name: str) -> Dict:
    """상품의 가격을 확인합니다."""
    for prod in products:
        if prod["name"] == product_name:
            return {
                "success": True,
                "product_name": product_name,
                "brand": prod.get("brand", ""),
                "price": prod["price"],
                "message": f"{product_name}의 가격은 {prod['price']:,}원입니다."
            }
    
    return {"success": False, "message": f"'{product_name}' 상품을 찾을 수 없습니다."}

def view_order_history(user_id: str, status: str = "all", limit: int = 5) -> Dict:
    """주문 내역을 조회합니다."""
    if not order_history:
        return {"success": True, "orders": [], "message": "주문 내역이 없습니다."}
    
    filtered_orders = order_history
    
    if status != "all":
        filtered_orders = [order for order in order_history if order["status"] == status]
    
    # 최근 주문부터 표시
    filtered_orders = filtered_orders[-limit:][::-1]
    
    return {
        "success": True,
        "user_id": user_id,
        "count": len(filtered_orders),
        "orders": filtered_orders,
        "message": f"최근 {len(filtered_orders)}개의 주문 내역입니다."
    }

# ================== Tools 정의 ==================
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

# ================== 시스템 프롬프트 ==================
system_prompt = """당신은 AI 쇼핑몰의 친절한 상담사입니다.
고객의 요청을 이해하고 적절한 함수를 호출하여 도움을 줍니다.

판매 상품 예시:
- 클라우드 워커 (AI Style, 스니커즈): 89,000원
- 스트릿 러너 (AI Style, 런닝화): 129,000원
- 에센셜 후디 (Daily Wear, 후드티): 69,000원
- 클래식 캡 (AI Gear, 모자): 29,000원

고객 요청에 따라 상품 검색, 장바구니 추가, 재고 확인, 결제 등을 도와드립니다."""

# ================== 함수 실행 ==================
def execute_function_call(tool_call):
    """함수 호출 실행"""
    function_name = tool_call.function.name
    try:
        arguments = json.loads(tool_call.function.arguments)
    except:
        arguments = {}
    
    # 함수 매핑
    function_map = {
        'add_product': add_product,
        'search_products': search_products,
        'view_cart': view_cart,
        'proceed_to_checkout': proceed_to_checkout,
        'check_inventory': check_inventory,
        'get_product_info': get_product_info,
    }
    
    if function_name in function_map:
        result = function_map[function_name](**arguments)
        return json.dumps(result, ensure_ascii=False)
    else:
        return json.dumps({"error": f"Unknown function: {function_name}"})

# ================== 테스트 함수 ==================
def test_function_calling():
    """Function Calling 테스트"""
    print("="*60)
    print("Qwen2.5-3B Function Calling 테스트")
    print("="*60)
    
    # 테스트 케이스
    test_cases = [
        "AI Style 브랜드의 신발 보여주세요",
        "클라우드 워커 블랙 260 사이즈로 하나 주세요",
        "장바구니 확인해주세요",
        "에센셜 후디 재고 있나요?",
        "결제 진행할게요"
    ]
    
    messages = [{"role": "system", "content": system_prompt}]
    
    success_count = 0
    total_time = 0
    
    for i, test_message in enumerate(test_cases, 1):
        print(f"\n테스트 {i}: {test_message}")
        messages.append({"role": "user", "content": test_message})
        
        start_time = time.time()
        try:
            response = client.chat.completions.create(
                model="Qwen/Qwen3-4B",  # 또는 로컬 모델명
                messages=messages,
                tools=tools,
                temperature=0.3
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            total_time += execution_time
            
            response_message = response.choices[0].message
            
            # Tool call 처리
            if response_message.tool_calls:
                print(f"✅ 함수 호출 감지")
                for tool_call in response_message.tool_calls:
                    print(f"  → {tool_call.function.name}")
                    result = execute_function_call(tool_call)
                    print(f"  결과: {result[:100]}...")
                success_count += 1
                
                # 메시지 추가
                messages.append(response_message.model_dump())
                
                # Tool 결과 추가
                for tool_call in response_message.tool_calls:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": execute_function_call(tool_call)
                    })
            else:
                print(f"⚠️ 함수 호출 없음")
                print(f"응답: {response_message.content[:200]}...")
                messages.append({"role": "assistant", "content": response_message.content})
            
            print(f"실행 시간: {execution_time:.2f}초")
            
        except Exception as e:
            print(f"❌ 에러: {e}")
    
    # 결과 요약
    print("\n" + "="*60)
    print("테스트 결과 요약")
    print("="*60)
    print(f"성공률: {success_count}/{len(test_cases)} ({success_count/len(test_cases)*100:.1f}%)")
    print(f"평균 실행 시간: {total_time/len(test_cases):.2f}초")
    
    if success_count/len(test_cases) >= 0.8:
        print("\n✅ 결론: Function Calling 성능 우수 (튜닝 불필요)")
    elif success_count/len(test_cases) >= 0.5:
        print("\n⚠️ 결론: 부분적 개선 필요 (선택적 튜닝)")
    else:
        print("\n❌ 결론: 성능 부족 (튜닝 필수)")

# ================== 대화형 테스트 ==================
def interactive_test():
    """대화형 테스트"""
    print("\n" + "="*60)
    print("대화형 Function Calling 테스트")
    print("(종료하려면 'quit' 입력)")
    print("="*60)
    
    messages = [{"role": "system", "content": system_prompt}]
    
    while True:
        user_input = input("\n👤 사용자: ")
        
        if user_input.strip().lower() in ['quit', '종료']:
            print("🤖 대화를 종료합니다.")
            break
        
        messages.append({"role": "user", "content": user_input})
        
        start_time = time.time()
        try:
            response = client.chat.completions.create(
                model="Qwen/Qwen3-4B",
                messages=messages,
                tools=tools,
                temperature=0.3
            )
            
            end_time = time.time()
            print(f"⏱️ 실행 시간: {end_time - start_time:.2f}초")
            
            response_message = response.choices[0].message
            
            # Tool call 처리
            if response_message.tool_calls:
                print("🔧 함수 호출:")
                tool_results = []
                
                for tool_call in response_message.tool_calls:
                    print(f"  → {tool_call.function.name}")
                    result = execute_function_call(tool_call)
                    tool_results.append(result)
                    result_json = json.loads(result)
                    if 'message' in result_json:
                        print(f"     {result_json['message']}")
                
                messages.append(response_message.model_dump())
                
                for i, tool_call in enumerate(response_message.tool_calls):
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_results[i]
                    })
                
                # 추가 응답 생성
                follow_up = client.chat.completions.create(
                    model="Qwen/Qwen3-4B",
                    messages=messages,
                    temperature=0.3
                )
                print(f"\n🤖 AI: {follow_up.choices[0].message.content}")
                messages.append({"role": "assistant", "content": follow_up.choices[0].message.content})
                
            else:
                print(f"\n🤖 AI: {response_message.content}")
                messages.append({"role": "assistant", "content": response_message.content})
                
        except Exception as e:
            print(f"❌ 에러: {e}")

# ================== 메인 실행 ==================
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        # 대화형 모드
        interactive_test()
    else:
        # 자동 테스트 모드
        test_function_calling()
        
        # 장바구니 최종 상태
        print(f"\n최종 장바구니: {shopping_cart}")
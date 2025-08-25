import json
from typing import Dict, List, Optional, Any
from datetime import datetime

# 전역 변수로 장바구니와 데이터 관리
shopping_cart = []
order_history = []

# 상품 데이터베이스 (새로운 구조)
products = []

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

# 새로운 상품 데이터 구조
products = [
    # 신발 카테고리
    {"id": "SH001", "name": "클라우드 워커", "category": "신발", "type": "스니커즈", "brand": "Urban Style", 
     "price": 89000, "colors": ["화이트", "블랙", "그레이", "네이비"], 
     "sizes": ["230", "240", "250", "260", "270", "280"], "stock": 45},
    
    {"id": "SH002", "name": "스트릿 러너", "category": "신발", "type": "런닝화", "brand": "Urban Style",
     "price": 129000, "colors": ["레드", "블루", "옐로우", "민트"],
     "sizes": ["235", "240", "245", "250", "255", "260", "265", "270", "275", "280"], "stock": 60},
    
    {"id": "SH003", "name": "빈티지 하이탑", "category": "신발", "type": "하이탑 스니커즈", "brand": "Urban Style",
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
    {"id": "AC001", "name": "미니멀 백팩", "category": "액세서리", "type": "백팩", "brand": "Urban Gear",
     "price": 89000, "colors": ["블랙", "네이비", "그레이"], "stock": 35},
    
    {"id": "AC002", "name": "클래식 캡", "category": "액세서리", "type": "모자", "brand": "Urban Gear",
     "price": 29000, "colors": ["블랙", "화이트", "베이지", "카키"], "stock": 100},
    
    {"id": "AC003", "name": "레더 벨트", "category": "액세서리", "type": "벨트", "brand": "Premium Line",
     "price": 49000, "colors": ["블랙", "브라운", "네이비"], 
     "sizes": ["85", "90", "95", "100", "105"], "stock": 55}
]

# 테스트 시나리오 함수들
def test_scenario_1_basic_shopping():
    """기본 쇼핑 시나리오: 상품 검색 → 정보 확인 → 장바구니 추가 → 결제"""
    print("=== 시나리오 1: 기본 쇼핑 플로우 ===\n")
    
    # 1. 브랜드별 검색
    print("1. Urban Style 브랜드 검색")
    result = search_products(brand="Urban Style")
    print(f"결과: {result['message']}")
    print(f"상품 목록: {[p['name'] for p in result['products']]}\n")
    
    # 2. 런닝화 타입 검색
    print("2. 런닝화 타입 검색")
    result = search_products(type="런닝화")
    print(f"결과: {result['message']}")
    if result['products']:
        print(f"찾은 상품: {result['products'][0]['name']} - {result['products'][0]['brand']}\n")
    
    # 3. 특정 상품 정보 확인
    print("3. 스트릿 러너 정보 확인")
    result = get_product_info("스트릿 러너")
    print(f"브랜드: {result['product']['brand']}")
    print(f"타입: {result['product']['type']}")
    print(f"가격: {result['product']['price']:,}원")
    print(f"색상: {result['product']['colors']}")
    print(f"사이즈: {result['product']['sizes']}\n")
    
    # 4. 가격 확인
    print("4. 가격 재확인")
    result = check_price("스트릿 러너")
    print(f"{result['message']}\n")
    
    # 5. 재고 확인
    print("5. 재고 확인")
    result = check_inventory("스트릿 러너", color="레드", size="260")
    print(f"{result['message']}")
    print(f"브랜드: {result['inventory']['brand']}\n")
    
    # 6. 장바구니에 추가
    print("6. 장바구니에 추가")
    result = add_product(product_name="스트릿 러너", quantity=1, size="260", color="레드")
    print(f"{result['message']}\n")
    
    # 7. 장바구니 확인
    print("7. 장바구니 확인")
    result = view_cart("detailed")
    print(f"장바구니 상품: {len(result['items'])}개")
    print(f"총 금액: {result['total']:,}원\n")
    
    # 8. 결제 진행
    print("8. 결제 진행")
    result = proceed_to_checkout("proceed", "card")
    print(f"{result['message']}")
    print(f"주문번호: {result['order_id']}\n")

def test_scenario_2_cart_management():
    """장바구니 관리 시나리오: 여러 상품 추가 → 수정 → 삭제"""
    print("=== 시나리오 2: 장바구니 관리 ===\n")
    
    # 1. 여러 상품 추가
    print("1. 여러 상품을 장바구니에 추가")
    add_product(product_name="에센셜 후디", quantity=2, size="L", color="블랙")
    print("- 에센셜 후디 (Daily Wear) L 블랙 2개 추가")
    
    add_product(product_name="클래식 캡", quantity=1, color="베이지")
    print("- 클래식 캡 (Urban Gear) 베이지 1개 추가")
    
    add_product(product_name="클라우드 워커", quantity=1, size="260", color="화이트")
    print("- 클라우드 워커 (Urban Style) 260 화이트 1개 추가\n")
    
    # 2. 장바구니 조회
    print("2. 장바구니 현황")
    result = view_cart("summary")
    print(f"상품 수: {result['item_count']}개")
    print(f"총 금액: {result['total']:,}원")
    print(f"상품 목록: {result['items']}\n")
    
    # 3. 옵션 변경
    print("3. 에센셜 후디 색상 변경 (블랙 → 크림)")
    result = modify_product_options(
        product_name="에센셜 후디",
        current_options={"size": "L", "color": "블랙"},
        new_options={"color": "크림"}
    )
    print(f"{result['message']}\n")
    
    # 4. 수량 조정 (일부 제거)
    print("4. 에센셜 후디 1개 제거")
    result = remove_product(product_name="에센셜 후디", quantity=1, size="L")
    print(f"{result['message']}\n")
    
    # 5. 총 금액 계산
    print("5. 총 금액 계산")
    result = calculate_total()
    print(f"{result['message']}\n")
    
    # 6. 장바구니 초기화
    print("6. 장바구니 초기화")
    result = reset_cart(confirm=True)
    print(f"{result['message']}\n")

def test_scenario_3_search_and_filter():
    """검색 및 필터링 시나리오"""
    print("=== 시나리오 3: 상품 검색 및 필터링 ===\n")
    
    # 1. 키워드 검색
    print("1. '후디' 키워드로 검색")
    result = search_products(keyword="후디")
    print(f"검색 결과: {result['count']}개")
    if result['products']:
        for prod in result['products']:
            print(f"- {prod['name']} ({prod['brand']}): {prod['price']:,}원\n")
    
    # 2. 가격대별 검색
    print("2. 50,000원 ~ 90,000원 상품 검색")
    result = search_products(price_min=50000, price_max=90000)
    print(f"검색 결과: {result['count']}개")
    for prod in result['products']:
        print(f"- {prod['name']}: {prod['price']:,}원")
    print()
    
    # 3. 카테고리 + 브랜드 복합 검색
    print("3. Daily Wear 브랜드의 의류")
    result = search_products(category="의류", brand="Daily Wear")
    print(f"검색 결과: {result['count']}개")
    for prod in result['products']:
        print(f"- {prod['name']} ({prod['type']}): {prod['price']:,}원")
    print()
    
    # 4. 타입별 검색
    print("4. 스니커즈 타입 상품 검색")
    result = search_products(type="스니커즈")
    print(f"검색 결과: {result['count']}개")
    for prod in result['products']:
        print(f"- {prod['name']} ({prod['brand']}): {prod['price']:,}원\n")

def test_scenario_4_order_history():
    """주문 내역 시나리오"""
    print("=== 시나리오 4: 주문 및 주문 내역 확인 ===\n")
    
    # 1. 첫 번째 주문
    print("1. 첫 번째 주문 생성")
    add_product(product_name="미니멀 백팩", quantity=1, color="블랙")
    add_product(product_name="레더 벨트", quantity=1, size="95", color="브라운")
    result = proceed_to_checkout("proceed", "card")
    order_id_1 = result['order_id']
    print(f"주문 완료: {order_id_1}")
    print(f"총액: {result['total']:,}원\n")
    
    # 2. 두 번째 주문
    print("2. 두 번째 주문 생성")
    add_product(product_name="빈티지 하이탑", quantity=1, size="270", color="베이지")
    add_product(product_name="오버핏 셔츠", quantity=2, size="L", color="화이트")
    result = proceed_to_checkout("proceed", "mobile_payment")
    order_id_2 = result['order_id']
    print(f"주문 완료: {order_id_2}")
    print(f"총액: {result['total']:,}원\n")
    
    # 3. 주문 내역 조회
    print("3. 주문 내역 조회")
    result = view_order_history("USER001", status="all", limit=5)
    print(f"{result['message']}")
    for order in result['orders']:
        print(f"\n- 주문번호: {order['order_id']}")
        print(f"  총액: {order['total']:,}원")
        print(f"  상품 수: {len(order['items'])}개")
        print(f"  결제수단: {order['payment_method']}")
        print(f"  상태: {order['status']}")
        for item in order['items']:
            print(f"    • {item['product_name']} ({item.get('brand', '')}) - {item['quantity']}개")

def test_error_cases():
    """에러 케이스 테스트"""
    print("=== 에러 케이스 테스트 ===\n")
    
    # 1. 존재하지 않는 상품
    print("1. 존재하지 않는 상품 추가 시도")
    result = add_product(product_name="없는 상품", quantity=1)
    print(f"결과: {result['message']}\n")
    
    # 2. 사이즈 미선택
    print("2. 신발 구매 시 사이즈 미선택")
    result = add_product(product_name="스트릿 러너", quantity=1, color="블루")
    print(f"결과: {result['message']}\n")
    
    # 3. 잘못된 색상
    print("3. 사용 불가능한 색상 선택")
    result = add_product(product_name="클래식 캡", quantity=1, color="보라색")
    print(f"결과: {result['message']}\n")
    
    # 4. 빈 장바구니 결제
    print("4. 빈 장바구니 상태에서 결제 시도")
    result = proceed_to_checkout("proceed")
    print(f"결과: {result['message']}\n")
    
    # 5. 재고 확인 - 잘못된 사이즈
    print("5. 존재하지 않는 사이즈 재고 확인")
    result = check_inventory("클라우드 워커", size="300")
    print(f"결과: {result['message']}\n")

def test_advanced_search():
    """고급 검색 기능 테스트"""
    print("=== 고급 검색 기능 테스트 ===\n")
    
    # 1. 브랜드별 상품 리스트
    print("1. 브랜드별 상품 카운트")
    brands = ["Urban Style", "Daily Wear", "Urban Gear", "Premium Line"]
    for brand in brands:
        result = search_products(brand=brand)
        print(f"- {brand}: {result['count']}개 상품")
    print()
    
    # 2. 가격대별 분포
    print("2. 가격대별 상품 분포")
    price_ranges = [(0, 50000), (50000, 80000), (80000, 120000), (120000, 200000)]
    for min_price, max_price in price_ranges:
        result = search_products(price_min=min_price, price_max=max_price)
        print(f"- {min_price:,}원 ~ {max_price:,}원: {result['count']}개")
    print()
    
    # 3. 복합 검색
    print("3. 10만원 이하 Urban 브랜드 상품")
    result = search_products(keyword="Urban", price_max=100000)
    print(f"검색 결과: {result['count']}개")
    for prod in result['products']:
        print(f"- {prod['name']} ({prod['brand']}): {prod['price']:,}원")

# 테스트 실행 메인 함수
def run_all_tests():
    """모든 테스트 시나리오 실행"""
    print("="*60)
    print("쇼핑 카트 시스템 테스트 시작 (새로운 상품 구조)")
    print("="*60 + "\n")
    
    # 각 시나리오 실행
    test_scenario_1_basic_shopping()
    print("\n" + "="*60 + "\n")
    
    # 장바구니 초기화
    reset_cart(confirm=True)
    
    test_scenario_2_cart_management()
    print("\n" + "="*60 + "\n")
    
    test_scenario_3_search_and_filter()
    print("\n" + "="*60 + "\n")
    
    test_scenario_4_order_history()
    print("\n" + "="*60 + "\n")
    
    test_error_cases()
    print("\n" + "="*60 + "\n")
    
    test_advanced_search()
    
    print("\n" + "="*60)
    print("모든 테스트 완료!")
    print("="*60)

# 테스트 실행
if __name__ == "__main__":
    run_all_tests()
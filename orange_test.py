from Orange.data import Table

# 예시 URL (UCI Machine Learning Repository의 Iris 데이터셋 CSV 파일)
# 실제 사용 시에는 원하는 데이터의 URL로 변경하세요.
url = "https://drive.google.com/file/d/1FiNOjjQwmn2orf81DXEnRV30vmLgUENd/view?usp=drive_link"

# UCI Iris 데이터셋은 헤더가 없으므로, 헤더가 없는 CSV를 로드하는 방식을 가정합니다.
# 만약 URL의 데이터가 헤더를 포함하고 있다면, Orange3가 자동으로 감지하거나
# Table.from_file() 메소드의 파라미터를 조절할 수 있습니다.
# Orange3는 URL을 직접 Table 생성자에 전달하면 자동으로 데이터를 가져옵니다.

try:
    # URL로부터 데이터 테이블 로드
    # Orange3는 파일 확장자나 내용을 보고 구분자를 추측하려고 시도합니다.
    # 이 데이터는 헤더가 없고, 마지막 열이 클래스 변수입니다.
    # 명시적으로 알려주기 위해 Domain을 미리 정의하거나, 로드 후 수정할 수 있습니다.
    # 간단한 예시로, 우선 로드하고 내용을 확인해보겠습니다.
    data_from_url = Table(url)

    # 도메인 정보 접근
    domain_info = data_from_url.domain

    # 도메인 정보 출력
    print(f"--- '{url}' 에서 로드된 데이터의 전체 도메인 정보 ---")
    print(domain_info)
    print("\n")

    # 특성(attributes) 정보 출력
    print("--- 특성 (Attributes) ---")
    if domain_info.attributes:
        for attr in domain_info.attributes:
            print(f"이름: {attr.name}, 타입: {type(attr).__name__}, 값들: {attr.values if attr.is_discrete else 'N/A (Continuous)'}")
    else:
        print("로드된 데이터에 일반 특성이 없습니다. 모든 열이 메타 또는 클래스 변수로 인식되었을 수 있습니다.")
        print("데이터 형식을 확인하거나, 로드 시 Domain을 명시적으로 지정하는 것을 고려해보세요.")
    print("\n")

    # 클래스 변수(class variable) 정보 출력
    if domain_info.class_var: # 클래스 변수가 하나일 경우
        class_var = domain_info.class_var
        print("--- 클래스 변수 (Class Variable) ---")
        print(f"이름: {class_var.name}, 타입: {type(class_var).__name__}, 값들: {class_var.values if class_var.is_discrete else 'N/A (Continuous)'}")
    elif domain_info.class_vars: # 클래스 변수가 여러 개일 경우
        print("--- 클래스 변수 (Class Variables) ---")
        for i, class_var in enumerate(domain_info.class_vars):
            print(f"클래스 변수 {i+1} - 이름: {class_var.name}, 타입: {type(class_var).__name__}, 값들: {class_var.values if class_var.is_discrete else 'N/A (Continuous)'}")
    else:
        # Iris 데이터셋의 경우, Orange3가 마지막 열을 자동으로 클래스 변수로 인식할 가능성이 높습니다.
        # 만약 그렇지 않다면, 데이터 형식 문제이거나 로드 옵션 조정이 필요할 수 있습니다.
        print("--- 클래스 변수 없음 ---")
        print("Orange3가 URL의 데이터에서 클래스 변수를 자동으로 감지하지 못했을 수 있습니다.")
        print("일반적으로 CSV 파일의 경우 마지막 열을 클래스로 인식하려는 경향이 있습니다.")
        print("또는, 'Select Columns' 위젯을 사용하여 수동으로 지정할 수 있습니다.")

    print("\n")

    # 메타(meta) 정보 출력
    print("--- 메타 정보 (Metas) ---")
    if domain_info.metas:
        for meta_attr in domain_info.metas:
            print(f"이름: {meta_attr.name}, 타입: {type(meta_attr).__name__}")
    else:
        print("메타 정보 없음")

    # 데이터 샘플 몇 개 출력 (선택 사항)
    print("\n--- 데이터 샘플 (처음 3개 행) ---")
    for i in range(min(3, len(data_from_url))):
        print(data_from_url[i])

except Exception as e:
    print(f"URL로부터 데이터를 로드하는 중 오류 발생: {e}")
    print("URL이 정확한지, 인터넷 연결이 되어있는지, 해당 URL의 데이터 형식이 올바른지 확인해주세요.")
    print("예를 들어, CSV 파일의 경우 쉼표로 구분되어야 하며, Orange3가 인식할 수 있는 형식이어야 합니다.")
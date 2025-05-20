# grading_criteria_checks.py

import os
import ast
# import requests # 현재 직접 사용 안 함
# import io
# import csv

from ows_parser import (
    load_ows_file,
    get_node_by_name,
    get_node_properties_obj,
    check_link_exists,
    get_data_summary_from_url,
    ORANGE_AVAILABLE_PARSER
)

ORANGE_AVAILABLE = ORANGE_AVAILABLE_PARSER
if ORANGE_AVAILABLE:
    try:
        from Orange.data import Table, Domain, Variable
        from orangewidget.settings import Context as OrangeContext
    except ImportError:
        ORANGE_AVAILABLE = False # 만약 ows_parser에서는 성공했어도 여기서 실패하면 False로
        class Table:
            def __init__(self, *args, **kwargs): self._domain = Domain(); self._len = 0
            def __len__(self): return self._len
            @property
            def domain(self):
                if not hasattr(self, '_domain') or self._domain is None : self._domain = Domain()
                return self._domain
        class Domain:
            def __init__(self): self.attributes = []; self.class_var = None; self.class_vars = []; self.metas = []; self.variables = []
        class Variable: pass
        class OrangeContext: pass
else:
    class Table:
        def __init__(self, *args, **kwargs): self._domain = Domain(); self._len = 0
        def __len__(self): return self._len
        @property
        def domain(self):
            if not hasattr(self, '_domain') or self._domain is None : self._domain = Domain()
            return self._domain
    class Domain:
        def __init__(self): self.attributes = []; self.class_var = None; self.class_vars = []; self.metas = []; self.variables = []
    class Variable: pass
    class OrangeContext: pass

if ORANGE_AVAILABLE:
    print("[Init grading_criteria_checks] Orange3 라이브러리 사용 가능.")
else:
    print("경고: grading_criteria_checks - Orange3 라이브러리 사용 불가. 일부 기능이 제한됩니다.")


def _get_node_id_from_name(xml_root, widget_name):
    node = get_node_by_name(xml_root, widget_name)
    return node.get("id") if node else None

# === 평가 요소 1: 데이터 업로드 ===
def check_criterion_1_1(xml_root):
    if xml_root is None: return False
    return get_node_by_name(xml_root, "File") is not None

def check_criterion_1_2(xml_root, data_summary_output_list=None):
    if xml_root is None: return False
    file_node_check = get_node_by_name(xml_root, "File")
    if file_node_check is None: return False
    file_node_id = file_node_check.get("id")
    file_properties = get_node_properties_obj(xml_root, file_node_id)
    if not isinstance(file_properties, dict): return False

    data_load_and_valid_schema = False
    extracted_data_source_for_summary = "N/A"
    source_to_try_loading = None

    if 'url' in file_properties and isinstance(file_properties['url'], str) and file_properties['url'].strip().startswith('http'):
        source_to_try_loading = file_properties['url'].strip()
        extracted_data_source_for_summary = source_to_try_loading
    elif 'recent_urls' in file_properties and isinstance(file_properties['recent_urls'], list) and file_properties['recent_urls']:
        for url_candidate in file_properties['recent_urls']:
            if isinstance(url_candidate, str) and url_candidate.strip().lower().startswith('http'):
                source_to_try_loading = url_candidate.strip()
                extracted_data_source_for_summary = source_to_try_loading
                break
    if not source_to_try_loading and 'recent_paths' in file_properties and \
       isinstance(file_properties['recent_paths'], list) and file_properties['recent_paths']:
        first_path_obj = file_properties['recent_paths'][0]
        path_str = None
        if hasattr(first_path_obj, 'abspath') and isinstance(first_path_obj.abspath, str): path_str = first_path_obj.abspath.strip()
        elif isinstance(first_path_obj, str): path_str = first_path_obj.strip()
        if path_str:
            source_to_try_loading = path_str
            extracted_data_source_for_summary = f"Local: {os.path.basename(path_str)}"

    summary_for_output = "데이터 소스 정보 없음 또는 요약 실패"
    if source_to_try_loading:
        summary_for_output = get_data_summary_from_url(source_to_try_loading)
    if data_summary_output_list is not None: data_summary_output_list.append(f"소스: {extracted_data_source_for_summary} | 요약: {summary_for_output}")

    if source_to_try_loading and ORANGE_AVAILABLE:
        try:
            data_table = Table(source_to_try_loading)
            if data_table is not None and len(data_table) > 0 and \
               data_table.domain is not None and \
               hasattr(data_table.domain, 'variables') and \
               isinstance(data_table.domain.variables, list) and \
               len(data_table.domain.variables) > 0:
                data_load_and_valid_schema = True
        except: pass
    elif source_to_try_loading and not ORANGE_AVAILABLE:
        if not summary_for_output.startswith("데이터 요약 불가") and \
           not summary_for_output.startswith("데이터 로드 실패") and \
           not summary_for_output.startswith("데이터 로드/분석 오류") and \
           ("총 " in summary_for_output and "개 행" in summary_for_output):
            data_load_and_valid_schema = True
            
    return data_load_and_valid_schema

def check_criterion_1_3(xml_root):
    if xml_root is None: return False
    file_node_id = _get_node_id_from_name(xml_root, "File")     # ID "0"
    dt_node_id = _get_node_id_from_name(xml_root, "Data Table") # ID "1"
    if not (file_node_id and dt_node_id): return False
    # 모범 답안 링크 ID "14": File(0) --Data/data--> Data Table(1) --Data/data-->
    return check_link_exists(xml_root, "0", "1", "data", "data")


# === 평가 요소 2: 데이터 전처리 ===
def check_criterion_2_1(xml_root):
    if xml_root is None: return False
    return get_node_by_name(xml_root, "Preprocess") is not None

def check_criterion_2_2(xml_root):
    if xml_root is None: return False
    preprocess_node_id = _get_node_id_from_name(xml_root, "Preprocess") # ID "2"
    if not preprocess_node_id: return False
    props_text = get_node_properties_obj(xml_root, preprocess_node_id)
    if not isinstance(props_text, str): return False
    try:
        settings = ast.literal_eval(props_text)
        if isinstance(settings, dict) and 'storedsettings' in settings:
            preprocessors = settings['storedsettings'].get('preprocessors', [])
            if isinstance(preprocessors, list):
                for processor in preprocessors:
                    if isinstance(processor, tuple) and len(processor) == 2:
                        if processor[0] == 'orange.preprocess.impute' and \
                           isinstance(processor[1], dict) and \
                           processor[1].get('method') == 5: # 모범 답안 값
                            return True
    except: return False
    return False

def check_criterion_2_3(xml_root):
    if xml_root is None: return False
    file_node_id = _get_node_id_from_name(xml_root, "File")         # ID "0"
    preprocess_node_id = _get_node_id_from_name(xml_root, "Preprocess") # ID "2"
    if not (file_node_id and preprocess_node_id): return False
    # 모범 답안 링크 ID "13": File(0) --Data/data--> Preprocess(2) --Data/data-->
    return check_link_exists(xml_root, "0", "2", "data", "data")

# === 평가 요소 3: 데이터 분류 ===
def check_criterion_3_1(xml_root):
    if xml_root is None: return False
    return get_node_by_name(xml_root, "Data Sampler") is not None

def check_criterion_3_2(xml_root): 
    if xml_root is None: return False
    ds_node_id = _get_node_id_from_name(xml_root, "Data Sampler") # ID "3"
    if not ds_node_id: return False
    props_text = get_node_properties_obj(xml_root, ds_node_id)
    if not isinstance(props_text, str): return False
    try:
        settings = ast.literal_eval(props_text)
        if isinstance(settings, dict):
            sampling_type = settings.get('sampling_type')
            percentage = settings.get('sampleSizePercentage')
            # 모범 답안 ID "3" (Data Sampler) 은 sampleSizePercentage: 80, sampling_type: 0
            if sampling_type == 0 and percentage == 80: 
                return True
    except: return False
    return False

def check_criterion_3_3(xml_root):
    if xml_root is None: return False
    # 모범 답안은 Preprocess에서 연결
    source_node_id = _get_node_id_from_name(xml_root, "Preprocess") # ID "2"
    source_channel_id_val = "preprocessed_data" 
    
    # 만약 Preprocess 위젯이 없다면 File 위젯에서 직접 연결되었는지 확인 (대체 경로)
    if not source_node_id:
        source_node_id = _get_node_id_from_name(xml_root, "File") # ID "0"
        source_channel_id_val = "data"
        # Preprocess 위젯이 존재하는데 File에서 DS로 갔다면, 이는 잘못된 연결일 수 있음.
        # 하지만 여기서는 Preprocess가 아예 없을 경우 File -> DS 연결을 허용.
        if get_node_by_name(xml_root, "Preprocess"): 
            return False # Preprocess가 있는데도 File에서 연결했다면 실패 처리

    ds_node_id = _get_node_id_from_name(xml_root, "Data Sampler") # ID "3"
    if not (source_node_id and ds_node_id): return False
    # 모범 답안 링크 ID "0": Preprocess(2) --Preprocessed Data/preprocessed_data--> Data Sampler(3) --Data/data-->
    return check_link_exists(xml_root, source_node_id, ds_node_id, source_channel_id_val, "data")


# === 평가 요소 4: 모델링 ===
def check_criterion_4_1(xml_root):
    if xml_root is None: return False
    knn_node_id = _get_node_id_from_name(xml_root, "kNN")               # ID "4"
    ds_node_id = _get_node_id_from_name(xml_root, "Data Sampler")      # ID "3"
    if not (knn_node_id and ds_node_id): return False
    # 모범 답안 링크 ID "1": Data Sampler(3) --Data Sample/data_sample--> kNN(4) --Data/data-->
    return check_link_exists(xml_root, "3", "4", "data_sample", "data")

def check_criterion_4_2(xml_root):
    if xml_root is None: return False
    tree_node_id = _get_node_id_from_name(xml_root, "Tree")            # ID "5"
    ds_node_id = _get_node_id_from_name(xml_root, "Data Sampler")      # ID "3"
    if not (tree_node_id and ds_node_id): return False
    return check_link_exists(xml_root, "3", "5", "data_sample", "data")

def check_criterion_4_3(xml_root):
    if xml_root is None: return False
    lr_node_id = _get_node_id_from_name(xml_root, "Logistic Regression") # ID "6"
    ds_node_id = _get_node_id_from_name(xml_root, "Data Sampler")        # ID "3"
    if not (lr_node_id and ds_node_id): return False
    return check_link_exists(xml_root, "3", "6", "data_sample", "data")

# === 평가 요소 5: 성능 평가 ===
def check_criterion_5_1(xml_root, ca_threshold=0.0):
    if xml_root is None: return False
    pred_node_id = _get_node_id_from_name(xml_root, "Predictions") # ID "8"
    if not pred_node_id: return False
    
    pred_properties = get_node_properties_obj(xml_root, pred_node_id)
    if not isinstance(pred_properties, dict): return False

    if ORANGE_AVAILABLE and 'score_table' in pred_properties:
        score_table = pred_properties.get('score_table')
        if isinstance(score_table, dict):
            def find_ca_in_obj(obj_to_search):
                if isinstance(obj_to_search, dict):
                    for key, value in obj_to_search.items():
                        if str(key).upper() == 'CA' and isinstance(value, (int, float)): return value
                        if isinstance(value, (dict, list)):
                            found = find_ca_in_obj(value)
                            if found is not None: return found
                elif isinstance(obj_to_search, list):
                    for item in obj_to_search:
                        found = find_ca_in_obj(item)
                        if found is not None: return found
                return None
            
            ca_value = find_ca_in_obj(score_table.get('results', score_table))
            
            if ca_value is not None:
                return ca_value >= ca_threshold
    return False

def check_criterion_5_2(xml_root):
    if xml_root is None: return False
    ds_node_id = _get_node_id_from_name(xml_root, "Data Sampler")      # ID "3"
    pred_node_id = _get_node_id_from_name(xml_root, "Predictions")    # ID "8"
    if not (ds_node_id and pred_node_id): return False
    # 모범 답안 링크 ID "10": DS(3) --Remaining Data/remaining_data--> Predictions(8) --Data/data-->
    return check_link_exists(xml_root, "3", "8", "remaining_data", "data")


if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    test_file_path = os.path.join(script_dir, "30101 테스트.ows") 
    
    print(f"테스트 파일: {test_file_path}에 대한 채점 기준 검사 시작")
    xml_root_obj = load_ows_file(test_file_path)
    
    if xml_root_obj:
        student_data_summary = []

        print("\n--- 평가 요소 1: 데이터 업로드 ---")
        res_1_1 = check_criterion_1_1(xml_root_obj)
        print(f"  세부 채점 기준 1-1 (File 위젯 사용): {res_1_1}")
        res_1_2 = check_criterion_1_2(xml_root_obj, student_data_summary)
        print(f"  세부 채점 기준 1-2 (실제 데이터 로드 및 내용 확인): {res_1_2}")
        print(f"    데이터 요약: {student_data_summary[0] if student_data_summary else 'N/A'}")
        res_1_3 = check_criterion_1_3(xml_root_obj)
        print(f"  세부 채점 기준 1-3 (File-Data Table 연결): {res_1_3}")

        print("\n--- 평가 요소 2: 데이터 전처리 ---")
        res_2_1 = check_criterion_2_1(xml_root_obj)
        print(f"  세부 채점 기준 2-1 (Preprocess 위젯 사용): {res_2_1}")
        res_2_2 = check_criterion_2_2(xml_root_obj)
        print(f"  세부 채점 기준 2-2 (Preprocess 설정 확인): {res_2_2}")
        res_2_3 = check_criterion_2_3(xml_root_obj)
        print(f"  세부 채점 기준 2-3 (File-Preprocess 연결): {res_2_3}")

        print("\n--- 평가 요소 3: 데이터 분류 ---")
        res_3_1 = check_criterion_3_1(xml_root_obj)
        print(f"  세부 채점 기준 3-1 (Data Sampler 사용): {res_3_1}")
        res_3_2 = check_criterion_3_2(xml_root_obj)
        print(f"  세부 채점 기준 3-2 (Data Sampler 설정): {res_3_2}")
        res_3_3 = check_criterion_3_3(xml_root_obj)
        print(f"  세부 채점 기준 3-3 (Preprocess/File-Data Sampler 연결): {res_3_3}")
        
        print("\n--- 평가 요소 4: 모델링 ---")
        res_4_1 = check_criterion_4_1(xml_root_obj)
        print(f"  세부 채점 기준 4-1 (kNN 사용 및 연결): {res_4_1}")
        res_4_2 = check_criterion_4_2(xml_root_obj)
        print(f"  세부 채점 기준 4-2 (Tree 사용 및 연결): {res_4_2}")
        res_4_3 = check_criterion_4_3(xml_root_obj)
        print(f"  세부 채점 기준 4-3 (Logistic Regression 사용 및 연결): {res_4_3}")

        print("\n--- 평가 요소 5: 성능 평가 ---")
        res_5_1 = check_criterion_5_1(xml_root_obj, ca_threshold=0.0) 
        print(f"  세부 채점 기준 5-1 (Predictions 사용/CA 확인): {res_5_1}")
        res_5_2 = check_criterion_5_2(xml_root_obj)
        print(f"  세부 채점 기준 5-2 (Data Sampler-Predictions 연결): {res_5_2}")
    else:
        print(f"테스트 파일 '{test_file_path}'을 로드할 수 없습니다.")
# ows_parser.py

import xml.etree.ElementTree as ET
import base64
import pickle
import os

try:
    from Orange.data import Table, Domain, Variable
    ORANGE_AVAILABLE_PARSER = True
except ImportError:
    ORANGE_AVAILABLE_PARSER = False
    class Table:
        def __init__(self, *args, **kwargs):
            self._domain = Domain()
            self._len = 0
        def __len__(self): return self._len
        @property
        def domain(self):
            if not hasattr(self, '_domain') or self._domain is None : self._domain = Domain()
            return self._domain
    class Domain:
        def __init__(self): self.attributes = []; self.class_var = None; self.class_vars = []; self.metas = []; self.variables = []
    class Variable:
        def __init__(self, name="dummy_var"):
            self.name = name; self.is_discrete = False; self.is_continuous = False; self.is_string = False; self.values = []

def load_ows_file(file_path):
    try: tree = ET.parse(file_path); root = tree.getroot(); return root
    except FileNotFoundError: return None
    except ET.ParseError: return None

def get_node_by_id(nodes_element_param, node_id_to_find):
    if nodes_element_param is None: return None
    normalized_node_id_to_find = node_id_to_find.strip()
    for node_element in nodes_element_param.findall('node'):
        current_node_id_from_attr = node_element.get('id')
        if current_node_id_from_attr is not None:
            normalized_current_node_id = current_node_id_from_attr.strip()
            if normalized_current_node_id == normalized_node_id_to_find:
                return node_element
    return None

def get_node_by_name(xml_root, widget_name_to_find):
    if xml_root is None: return None
    nodes_element = None
    for child_of_root in xml_root:
        if child_of_root.tag == "nodes": nodes_element = child_of_root; break
    if nodes_element is not None:
        for node in nodes_element.findall('node'):
            if node.get('name') == widget_name_to_find: return node
    return None

def decode_pickle_properties(pickled_string):
    if pickled_string:
        try: decoded_base64 = base64.b64decode(pickled_string); return pickle.loads(decoded_base64)
        except Exception: return None
    return None

def get_node_actual_properties_element(xml_root, node_id_to_find):
    if xml_root is None: return None
    node_properties_section = xml_root.find('node_properties')
    if node_properties_section is not None:
        for props_element in node_properties_section.findall('properties'):
            if props_element.get('node_id') == node_id_to_find: return props_element
    return None

def get_node_properties_obj(xml_root, node_id):
    if xml_root is None or node_id is None: return None
    properties_element = get_node_actual_properties_element(xml_root, node_id)
    if properties_element is not None:
        prop_format = properties_element.get('format', 'literal'); prop_text = properties_element.text
        if prop_format == "pickle" and prop_text: return decode_pickle_properties(prop_text)
        else: return prop_text
    return None

def check_link_exists(xml_root, source_node_id_to_find, sink_node_id_to_find, source_channel_val_to_find, sink_channel_val_to_find):
    # print(f"  [Link Check] 찾기: {source_node_id_to_find}({source_channel_val_to_find}) -> {sink_node_id_to_find}({sink_channel_val_to_find})")
    if xml_root is None: return False
    links_element = xml_root.find('links')
    if links_element is None: return False

    for link_element in links_element.findall('link'):
        if link_element.get('enabled', 'true').lower() == 'true':
            s_node_ok = link_element.get('source_node_id') == source_node_id_to_find
            t_node_ok = link_element.get('sink_node_id') == sink_node_id_to_find

            xml_s_ch_id = link_element.get('source_channel_id')
            xml_s_ch_name = link_element.get('source_channel') # Name for fallback
            xml_t_ch_id = link_element.get('sink_channel_id')
            xml_t_ch_name = link_element.get('sink_channel')   # Name for fallback
            
            # channel_id가 있으면 그것을 우선 사용, 없으면 channel 이름 사용
            s_channel_ok = (xml_s_ch_id == source_channel_val_to_find) or \
                           (xml_s_ch_id is None and xml_s_ch == source_channel_val_to_find)
            t_channel_ok = (xml_t_ch_id == sink_channel_val_to_find) or \
                           (xml_t_ch_id is None and xml_t_ch == sink_channel_val_to_find)
            
            # 디버깅 로그 (필요시 주석 해제하여 상세 비교)
            # current_s_ch_to_log = xml_s_ch_id if xml_s_ch_id is not None else xml_s_ch_name
            # current_t_ch_to_log = xml_t_ch_id if xml_t_ch_id is not None else xml_t_ch_name
            # print(f"    [Link Check {link_element.get('id')}] XML: src_id='{link_element.get('source_node_id')}', sink_id='{link_element.get('sink_node_id')}', actual_src_ch='{current_s_ch_to_log}', actual_sink_ch='{current_t_ch_to_log}'")
            # print(f"                찾는 값: src_id='{source_node_id_to_find}', sink_id='{sink_node_id_to_find}', src_ch_val='{source_channel_val_to_find}', sink_ch_val='{sink_channel_val_to_find}'")
            # print(f"                조건 결과: s_node_ok={s_node_ok}, t_node_ok={t_node_ok}, s_channel_ok={s_channel_ok}, t_channel_ok={t_channel_ok}")

            if s_node_ok and t_node_ok and s_channel_ok and t_channel_ok:
                return True
    return False

def parse_filename(ows_filename):
    base_name = os.path.splitext(ows_filename)[0]; parts = base_name.split(" ", 1)
    student_id = parts[0]; student_name = parts[1] if len(parts) > 1 else ""
    return student_id, student_name

def get_data_summary_from_url(data_url):
    if not data_url: return "데이터 URL 또는 경로 없음"
    if not ORANGE_AVAILABLE_PARSER:
        return f"데이터 요약 불가 (Orange 라이브러리 로드 실패 - URL: {data_url[:30]}...)"
    summary_lines = []
    try:
        data_table = Table(data_url)
        if data_table.domain is None:
            return f"데이터 로드 성공했으나 도메인 정보 없음 (URL: {data_url[:30]}...)"

        domain = data_table.domain
        summary_lines.append(f"총 {len(data_table)}개 행")
        
        attributes_list = domain.attributes if domain.attributes is not None else []
        attributes_info = [f"{attr.name}({type(attr).__name__})" for i, attr in enumerate(attributes_list) if i < 3 or (i == 2 and len(attributes_list) > 3)]
        if len(attributes_list) > 3 and attributes_info and not attributes_info[-1].endswith("..."): attributes_info[-1] += ",..."
        summary_lines.append(f"특성({len(attributes_list)}개): {', '.join(attributes_info) if attributes_info else '없음'}")
        
        class_vars_list = []
        if domain.class_var: class_vars_list = [domain.class_var]
        elif domain.class_vars: class_vars_list = domain.class_vars if domain.class_vars is not None else []
        
        class_vars_info = []
        for i, cv in enumerate(class_vars_list):
            if cv is not None and hasattr(cv, 'name'):
                cv_values_str = ""
                if hasattr(cv, 'is_discrete') and cv.is_discrete and hasattr(cv, 'values'): cv_values_str = str(cv.values)
                elif hasattr(cv, 'is_continuous') and cv.is_continuous: cv_values_str = "연속형"
                else: cv_values_str = "타입 불명확"
                class_vars_info.append(f"{cv.name}({type(cv).__name__}, 값: {cv_values_str})")
                if i >= 0 and len(class_vars_list) > 1: class_vars_info.append("..."); break
        summary_lines.append(f"클래스({len(class_vars_list)}개): {', '.join(class_vars_info) if class_vars_info else '없음'}")
        
        return " | ".join(summary_lines)
    except ImportError:
        return f"데이터 요약 불가 (Orange3 라이브러리 또는 의존성 문제 - URL: {data_url[:30]}...)"
    except Exception as e:
        error_message = str(e)
        if "Cannot determine data type from URL" in error_message or \
           ("drive.google.com" in data_url and ("richiede l'autenticazione" in error_message.lower() or "requires authentication" in error_message.lower())): #이탈리아어, 영어 오류 메시지
            return f"데이터 로드 실패 (URL: {data_url[:30]}...). 구글 드라이브 직접 로드 실패 또는 접근 권한 문제일 수 있습니다."
        return f"데이터 로드/분석 오류: {error_message[:100]}"

if __name__ == '__main__':
    pass
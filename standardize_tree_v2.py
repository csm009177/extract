import json
import re
import os

def identify_convention(name):
    """노드 이름에서 협약 식별"""
    name_upper = name.upper()
    
    # 협약 키워드 매칭 (우선순위 순, 긴 것부터)
    conventions = {
        'FSS CODE': 'FSS',
        'FTP CODE': 'FTP',
        'LSA CODE': 'LSA',
        'ESP CODE': 'ESP',
        'IBC CODE': 'IBC',
        'IGC CODE': 'IGC',
        'IMDG CODE': 'IMDG',
        'BCH CODE': 'BCH',
        'INF CODE': 'INF',
        'LOAD LINE': 'LoadLines',
        'LOADLINE': 'LoadLines',
        'ANTI-FOULING': 'AFS',
        'GAS CARRIER': 'IGC',
        'CHEMICAL TANKER': 'IBC',
        'BULK CARRIER': 'BC',
        'SOLAS': 'SOLAS',
        'MARPOL': 'MARPOL',
        'STCW': 'STCW',
        'COLREG': 'COLREG',
        'TONNAGE': 'Tonnage',
        'BALLAST': 'BWM',
        'OPRC': 'OPRC',
        'BUNKER': 'Bunker',
        'BWM': 'BWM',
        'AFS': 'AFS',
        'SAR': 'SAR',
        'ESP': 'ESP',
        'IBC': 'IBC',
        'IGC': 'IGC',
        'IMDG': 'IMDG',
        'FSS': 'FSS',
        'FTP': 'FTP',
        'LSA': 'LSA',
        'INF': 'INF',
        'BCH': 'BCH'
    }
    
    for keyword, conv_name in conventions.items():
        if keyword in name_upper:
            return conv_name
    
    return None

def parse_chapter(name):
    """Chapter 번호 추출"""
    # "Chapter II-1", "Chapter 1", "CHAPTER 1", "Ch. 2", "CHAPTER XII"
    patterns = [
        r'chapter\s+([IVX]+-\d+)',  # II-1, XI-2
        r'chapter\s+([IVX]+)',       # I, II, XII
        r'chapter\s+(\d+)',          # 1, 2, 3
        r'ch\.\s*(\d+)',             # Ch. 1
    ]
    
    name_lower = name.lower()
    for pattern in patterns:
        match = re.search(pattern, name_lower, re.IGNORECASE)
        if match:
            chapter_num = match.group(1).replace(' ', '').upper()
            return f"Chapter{chapter_num}"
    
    return None

def parse_regulation(name):
    """Regulation 번호 추출"""
    # "Reg. 1", "Regulation 2.3", "Reg 3-4.1"
    patterns = [
        r'reg(?:ulation)?\.?\s+(\d+-?\d*\.?\d*)',
    ]
    
    name_lower = name.lower()
    for pattern in patterns:
        match = re.search(pattern, name_lower, re.IGNORECASE)
        if match:
            reg_num = match.group(1)
            # 점 개수로 깊이 판단
            dots = reg_num.count('.')
            if dots == 0:
                return f"Reg{reg_num}", 'reg'
            elif dots == 1:
                return f"Reg{reg_num}", 'subreg'
            else:
                return f"Reg{reg_num}", 'subsubreg'
    
    return None, None

def parse_part(name):
    """Part 추출"""
    patterns = [
        r'part\s+([A-Z])',    # Part A, Part B
        r'part\s+(\d+)',       # Part 1, Part 2
    ]
    
    for pattern in patterns:
        match = re.search(pattern, name, re.IGNORECASE)
        if match:
            return f"Part{match.group(1)}"
    
    return None

def parse_article(name):
    """Article 추출"""
    # "Article I", "Article II"
    pattern = r'article\s+([IVX]+)'
    match = re.search(pattern, name, re.IGNORECASE)
    if match:
        return f"Article{match.group(1)}"
    
    return None

def parse_annex(name):
    """Annex 추출"""
    patterns = [
        r'annex\s+([A-Z])',   # Annex A
        r'annex\s+(\d+)',      # Annex 1
        r'annex\s+([IVX]+)',   # Annex I
    ]
    
    for pattern in patterns:
        match = re.search(pattern, name, re.IGNORECASE)
        if match:
            return f"Annex{match.group(1)}"
    
    return None

def build_path_hierarchy(nodes):
    """원본 경로 기반 계층 구조 생성"""
    # 경로 -> 노드 매핑
    path_map = {}
    for node in nodes:
        path_map[node['path']] = node
    
    # 각 노드의 부모 찾기
    hierarchy = []
    for node in nodes:
        path = node['path']
        parts = path.split('/')
        
        # 부모 경로들 수집
        parent_paths = []
        for i in range(1, len(parts)):
            parent_path = '/'.join(parts[:i])
            if parent_path in path_map:
                parent_paths.append(parent_path)
        
        hierarchy.append({
            'node': node,
            'parent_paths': parent_paths,
            'depth': len(parts) - 1
        })
    
    return hierarchy

def standardize_with_hierarchy(hierarchy):
    """계층 구조 기반 표준화"""
    # 경로 -> 표준경로 매핑
    std_path_map = {}
    
    for item in hierarchy:
        node = item['node']
        name = node['name']
        node_id = node['id']
        path = node['path']
        parent_paths = item['parent_paths']
        
        # 현재 협약 찾기 (부모들 중에서)
        current_convention = None
        for parent_path in reversed(parent_paths):
            if parent_path in std_path_map:
                parent_std = std_path_map[parent_path]
                # 부모의 표준 경로에서 협약 추출
                conv = parent_std.split('/')[0]
                if conv not in ['Other']:
                    current_convention = conv
                    break
        
        # 현재 노드가 협약인지 확인
        detected_conv = identify_convention(name)
        if detected_conv:
            std_path_map[path] = detected_conv
            continue
        
        # 구조 요소 파싱
        chapter = parse_chapter(name)
        reg, reg_type = parse_regulation(name)
        part = parse_part(name)
        article = parse_article(name)
        annex = parse_annex(name)
        
        # 표준 경로 구성
        std_parts = []
        
        if current_convention:
            std_parts.append(current_convention)
        
        # 우선순위: Chapter > Part > Annex > Article > Reg
        if chapter:
            std_parts.append(chapter)
        elif part:
            std_parts.append(part)
        elif annex:
            std_parts.append(annex)
        elif article:
            std_parts.append(article)
        elif reg:
            std_parts.append(reg)
        else:
            # 식별 실패 - ID 사용
            if node_id:
                std_parts.append(node_id)
            else:
                std_parts.append('Unknown')
        
        # 경로가 비어있으면 Other 사용
        if not std_parts:
            if node_id:
                std_path = f"Other/{node_id}"
            else:
                std_path = "Other/Unknown"
        else:
            std_path = '/'.join(std_parts)
        
        std_path_map[path] = std_path
    
    return std_path_map

def build_standardized_tree_v2(json_file):
    """개선된 표준화 (계층 구조 추적)"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 계층 구조 생성
    hierarchy = build_path_hierarchy(data['nodes'])
    
    # 표준화
    std_path_map = standardize_with_hierarchy(hierarchy)
    
    # 결과 생성
    standardized_nodes = []
    for node in data['nodes']:
        std_path = std_path_map.get(node['path'], 'Other/Unknown')
        
        standardized_nodes.append({
            'original_name': node['name'],
            'original_path': node['path'],
            'standardized_path': std_path,
            'id': node.get('id'),
            'href': node.get('href', '')
        })
    
    return standardized_nodes, data

if __name__ == "__main__":
    print("🔄 트리 구조 표준화 중 (v2 - 계층 추적)...\n")
    
    nodes, original_data = build_standardized_tree_v2('tree_structure.json')
    
    # 샘플 출력
    print("=== 표준화 결과 샘플 (처음 50개) ===\n")
    for i, node in enumerate(nodes[:50], 1):
        print(f"{i}. 원본: {node['original_name'][:60]}")
        print(f"   표준: {node['standardized_path']}")
        print()
    
    # 통계
    depths = [node['standardized_path'].count('/') for node in nodes]
    max_depth = max(depths)
    print(f"\n📊 통계:")
    print(f"   총 노드: {len(nodes)}개")
    print(f"   최대 깊이: {max_depth + 1} 레벨")
    
    # 깊이별
    print(f"\n   레벨별 분포:")
    for d in range(max_depth + 1):
        count = sum(1 for x in depths if x == d)
        print(f"   Level {d}: {count}개")
    
    # 경로 길이 확인
    long_paths = [node for node in nodes if len(node['standardized_path']) > 100]
    print(f"\n   긴 경로 (>100자): {len(long_paths)}개")
    
    very_long = [node for node in nodes if len(node['standardized_path']) > 200]
    print(f"   매우 긴 경로 (>200자): {len(very_long)}개")
    
    # 협약별
    print(f"\n   협약별 분포:")
    conventions = {}
    for node in nodes:
        conv = node['standardized_path'].split('/')[0]
        conventions[conv] = conventions.get(conv, 0) + 1
    
    for conv, count in sorted(conventions.items(), key=lambda x: -x[1])[:15]:
        print(f"   {conv}: {count}개")
    
    # JSON으로 저장
    output_data = {
        'total_nodes': len(nodes),
        'standardized_at': original_data['crawled_at'],
        'nodes': nodes
    }
    
    with open('tree_structure_standardized_v2.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 저장 완료: tree_structure_standardized_v2.json")

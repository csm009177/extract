"""
다운로드 상태 체크 모듈
"""

import os
import json
from datetime import datetime

class DownloadStatus:
    """다운로드 상태 체크 클래스"""
    
    def __init__(self, downloads_dir="output/downloads", progress_file="output/download_progress.json", tree_file="output/tree_structure.json"):
        self.downloads_dir = downloads_dir
        self.progress_file = progress_file
        self.tree_file = tree_file
    
    def get_stats(self):
        """다운로드 폴더 통계 수집"""
        stats = {
            "folder_count": 0,
            "total_files": 0,
            "html_files": 0,
            "pdf_files": 0,
            "other_files": 0,
            "total_size": 0,
            "folder_details": {},
            "progress": 0,
            "total_nodes": 0
        }
        
        # 폴더 존재 확인
        if not os.path.exists(self.downloads_dir):
            return stats
        
        # 폴더/파일 통계
        for root, dirs, files in os.walk(self.downloads_dir):
            stats["folder_count"] += len(dirs)
            
            if files:
                rel_path = os.path.relpath(root, self.downloads_dir)
                file_count = len(files)
                folder_size = sum(os.path.getsize(os.path.join(root, f)) for f in files)
                
                stats["folder_details"][rel_path] = {
                    "count": file_count,
                    "size": folder_size
                }
                
                stats["total_files"] += file_count
                stats["total_size"] += folder_size
                
                # 파일 타입별 분류
                for f in files:
                    if f.endswith('.html'):
                        stats["html_files"] += 1
                    elif f.endswith('.pdf'):
                        stats["pdf_files"] += 1
                    else:
                        stats["other_files"] += 1
        
        # 진행 상황
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    progress_data = json.load(f)
                    stats["progress"] = progress_data.get("last_processed_index", 0)
            except:
                pass
        
        # 전체 노드 수
        if os.path.exists(self.tree_file):
            try:
                with open(self.tree_file, 'r', encoding='utf-8') as f:
                    tree_data = json.load(f)
                    stats["total_nodes"] = tree_data.get("total_nodes", 0)
            except:
                pass
        
        return stats
    
    def format_size(self, size_bytes):
        """바이트를 읽기 쉬운 형식으로 변환"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def print_summary(self):
        """요약 정보 출력 (간단한 버전)"""
        stats = self.get_stats()
        
        print("\n" + "="*50)
        print("📊 다운로드 상태 요약")
        print("="*50)
        
        if not os.path.exists(self.downloads_dir):
            print("❌ downloads 폴더가 없습니다.")
            return stats
        
        print(f"📁 폴더 수: {stats['folder_count']}개")
        print(f"📄 파일 수: {stats['total_files']}개")
        
        if stats['total_files'] > 0:
            print(f"   - HTML: {stats['html_files']}개")
            print(f"   - PDF: {stats['pdf_files']}개")
            if stats['other_files'] > 0:
                print(f"   - 기타: {stats['other_files']}개")
            print(f"💾 총 용량: {self.format_size(stats['total_size'])}")
        
        if stats['total_nodes'] > 0:
            progress_pct = (stats['total_files'] / stats['total_nodes']) * 100
            print(f"📈 진행률: {stats['total_files']}/{stats['total_nodes']} ({progress_pct:.1f}%)")
        
        if stats['total_files'] == 0:
            print("⚠️  파일이 없습니다 (빈 폴더만 존재)")
        
        print("="*50 + "\n")
        
        return stats
    
    def print_detailed(self):
        """상세 정보 출력 (기존 check_status.py와 동일)"""
        stats = self.get_stats()
        
        print("\n" + "="*80)
        print("📊 KR-CON 다운로드 상태 체크")
        print("="*80)
        print(f"🕐 체크 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # downloads 폴더 확인
        if not os.path.exists(self.downloads_dir):
            print("❌ downloads 폴더가 없습니다.")
            print("   → python download_all.py 를 실행하여 다운로드를 시작하세요.\n")
            print("="*80)
            return stats
        
        # 전체 통계
        print("📊 전체 통계")
        print("─"*80)
        print(f"📁 총 폴더 수    : {stats['folder_count']:,}개")
        print(f"📄 총 파일 수    : {stats['total_files']:,}개")
        print(f"💾 총 용량       : {self.format_size(stats['total_size'])}\n")
        
        if stats['total_files'] > 0:
            print(f"📝 HTML 파일    : {stats['html_files']:,}개")
            print(f"📕 PDF 파일     : {stats['pdf_files']:,}개")
            if stats['other_files'] > 0:
                print(f"📦 기타 파일    : {stats['other_files']:,}개")
        
        if stats['progress'] > 0:
            print(f"\n🔄 진행 상황     : {stats['progress']:,}번째까지 처리됨")
        
        print("─"*80)
        
        # 경고 및 권장사항
        if stats['total_files'] == 0:
            print("\n⚠️  경고: 파일이 없습니다! (빈 폴더만 존재)")
            if stats['folder_count'] > 0:
                print(f"   → {stats['folder_count']}개의 빈 폴더가 생성되어 있습니다.")
            print("   → 다운로드를 다시 시작해야 합니다.\n")
        
        # 상위 폴더 (파일이 있는 경우만)
        if stats['folder_details']:
            print("\n📁 파일이 많은 상위 10개 폴더")
            print("─"*80)
            
            sorted_folders = sorted(
                stats['folder_details'].items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )[:10]
            
            for folder, info in sorted_folders:
                count = info['count']
                size = self.format_size(info['size'])
                folder_name = folder if len(folder) < 60 else folder[:57] + "..."
                print(f"  {count:3}개 | {size:>10} | {folder_name}")
            
            print("─"*80)
        
        # 진행률
        if stats['total_nodes'] > 0:
            remaining = stats['total_nodes'] - stats['total_files']
            progress_pct = (stats['total_files'] / stats['total_nodes']) * 100
            
            print(f"\n📈 전체 진행률: {stats['total_files']:,}/{stats['total_nodes']:,} ({progress_pct:.1f}%)")
            print(f"   남은 항목: {remaining:,}개")
        
        print("\n" + "="*80 + "\n")
        
        return stats
    
    def is_empty(self):
        """downloads 폴더가 비어있는지 확인"""
        stats = self.get_stats()
        return stats['total_files'] == 0
    
    def should_restart(self):
        """처음부터 다시 시작해야 하는지 판단"""
        if not os.path.exists(self.downloads_dir):
            return True
        
        stats = self.get_stats()
        
        # 파일이 하나도 없으면 재시작
        if stats['total_files'] == 0:
            return True
        
        # 진행 상황과 실제 파일 수가 너무 차이나면 재시작 권장
        if stats['progress'] > 0:
            expected_files = stats['progress']
            actual_files = stats['total_files']
            
            # 실제 파일이 예상의 50% 미만이면 재시작
            if actual_files < expected_files * 0.5:
                return True
        
        return False


# 스크립트로 직접 실행 시
if __name__ == "__main__":
    checker = DownloadStatus()
    checker.print_detailed()

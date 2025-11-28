"""
報表生成服務
支持 Excel、CSV、PDF、JSON 格式導出
"""
import json
import csv
from io import BytesIO, StringIO
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import os

try:
    import pandas as pd
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

from loguru import logger
from shared.database.models import Report, AdminUser
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


class ReportService:
    """報表生成服務類"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
    
    async def generate_excel(
        self,
        data: List[Dict[str, Any]],
        columns: List[Dict[str, str]],
        filename: str,
        sheet_name: str = "Sheet1"
    ) -> BytesIO:
        """生成 Excel 文件"""
        if not PANDAS_AVAILABLE:
            # 使用 openpyxl 直接生成
            wb = Workbook()
            ws = wb.active
            ws.title = sheet_name
            
            # 寫入表頭
            headers = [col["title"] for col in columns]
            ws.append(headers)
            
            # 設置表頭樣式
            for cell in ws[1]:
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal="center")
            
            # 寫入數據
            for row in data:
                row_data = [row.get(col["key"], "") for col in columns]
                ws.append(row_data)
            
            # 保存到 BytesIO
            output = BytesIO()
            wb.save(output)
            output.seek(0)
            return output
        else:
            # 使用 pandas
            df = pd.DataFrame(data)
            # 重命名列
            column_mapping = {col["key"]: col["title"] for col in columns if col["key"] in df.columns}
            df = df.rename(columns=column_mapping)
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            output.seek(0)
            return output
    
    async def generate_csv(
        self,
        data: List[Dict[str, Any]],
        columns: List[Dict[str, str]]
    ) -> BytesIO:
        """生成 CSV 文件"""
        output = StringIO()
        
        # 寫入表頭
        headers = [col["title"] for col in columns]
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        
        # 寫入數據
        for row in data:
            row_data = {col["title"]: row.get(col["key"], "") for col in columns}
            writer.writerow(row_data)
        
        # 轉換為 BytesIO
        output_bytes = BytesIO(output.getvalue().encode("utf-8-sig"))  # UTF-8 BOM for Excel
        return output_bytes
    
    async def generate_json(
        self,
        data: List[Dict[str, Any]]
    ) -> BytesIO:
        """生成 JSON 文件"""
        output = BytesIO()
        json_str = json.dumps(data, ensure_ascii=False, indent=2, default=str)
        output.write(json_str.encode("utf-8"))
        output.seek(0)
        return output
    
    async def generate_pdf(
        self,
        data: List[Dict[str, Any]],
        columns: List[Dict[str, str]],
        title: str = "Report"
    ) -> BytesIO:
        """生成 PDF 文件（簡化版，使用 HTML 轉 PDF）"""
        # 注意：完整的 PDF 生成需要安裝 reportlab 或 weasyprint
        # 這裡先返回一個簡單的實現
        # 构建 HTML 内容
        headers_html = ''.join([f'<th>{col["title"]}</th>' for col in columns])
        rows_html = []
        for row in data:
            cells = []
            for col in columns:
                key = col.get("key", "")
                value = str(row.get(key, ""))
                cells.append(f"<td>{value}</td>")
            rows_html.append(f"<tr>{''.join(cells)}</tr>")
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <table>
        <thead>
            <tr>{headers_html}</tr>
        </thead>
        <tbody>
            {''.join(rows_html)}
        </tbody>
    </table>
</body>
</html>"""
        output = BytesIO(html_content.encode("utf-8"))
        return output
    
    async def create_report_record(
        self,
        report_type: str,
        name: str,
        config: Dict[str, Any],
        file_format: str,
        generated_by: Optional[int] = None
    ) -> Report:
        """創建報表記錄"""
        report = Report(
            report_type=report_type,
            name=name,
            config=config,
            file_format=file_format,
            status="generating",
            generated_by=generated_by,
            generated_at=datetime.utcnow(),
            expires_at=datetime.utcnow().replace(day=datetime.utcnow().day + 7)  # 7天後過期
        )
        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)
        return report
    
    async def save_report_file(
        self,
        report: Report,
        file_content: BytesIO
    ) -> str:
        """保存報表文件"""
        filename = f"{report.id}_{report.name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{report.file_format}"
        file_path = self.reports_dir / filename
        
        with open(file_path, "wb") as f:
            f.write(file_content.read())
        
        report.file_path = str(file_path)
        report.status = "completed"
        await self.db.commit()
        
        return str(file_path)
    
    async def get_report(self, report_id: int) -> Optional[Report]:
        """獲取報表記錄"""
        result = await self.db.execute(
            select(Report).where(Report.id == report_id)
        )
        return result.scalar_one_or_none()
    
    async def list_reports(
        self,
        report_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Report]:
        """獲取報表列表"""
        query = select(Report)
        if report_type:
            query = query.where(Report.report_type == report_type)
        query = query.order_by(Report.created_at.desc()).limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return result.scalars().all()


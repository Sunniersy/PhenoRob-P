from backend.app.services.asset_query_service import AssetQueryService
from backend.app.services.asset_upload_service import AssetUploadService


class AssetService:
    def __init__(self, db, storage, task_queue, realtime):
        self.upload_service = AssetUploadService(db, storage, task_queue, realtime)
        self.query_service = AssetQueryService(db, storage)
        self.analysis_service = None

    def bind_analysis_service(self, analysis_service):
        self.analysis_service = analysis_service

    def create_upload_session(self, payload: dict) -> dict:
        return self.upload_service.create_upload_session(payload)

    def complete_upload(self, payload: dict) -> dict:
        return self.upload_service.complete_upload(payload)

    def upload_session_content(self, upload_session_id: str, file_name: str, content: bytes) -> dict:
        return self.upload_service.upload_session_content(upload_session_id, file_name, content)

    def complete_uploaded_session(self, upload_session_id: str, metadata: dict | None = None, trigger_analysis: bool = True) -> dict:
        return self.upload_service.complete_uploaded_session(upload_session_id, metadata, trigger_analysis)

    def list_assets(self, filters: dict | None = None) -> dict:
        return self.query_service.list_assets(filters)

    def get_asset(self, asset_id: str) -> dict:
        return self.query_service.get_asset(asset_id)

    def download_asset(self, asset_id: str) -> dict:
        return self.query_service.download_asset(asset_id)

    def serialize_asset(self, session, asset, include_preview: bool = False) -> dict:
        return self.query_service.serialize_asset(session, asset, include_preview)

import threading
from copy import deepcopy
from typing import Dict, List, Optional


class UploadJobStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._jobs: Dict[str, Dict] = {}

    def create_job(self, chat_id: str, title: str, files: List[Dict]):
        with self._lock:
            self._jobs[chat_id] = {
                "chat_id": chat_id,
                "title": title,
                "status": "processing",
                "message": "Indexation en cours",
                "files": files,
                "stats": {
                    "total_files": len(files),
                    "processed_files": 0,
                    "indexed_files": 0,
                    "total_pages": 0,
                    "chunks_added": 0,
                    "chunks_dropped": 0,
                },
            }

    def get_job(self, chat_id: str) -> Optional[Dict]:
        with self._lock:
            data = self._jobs.get(chat_id)
            return deepcopy(data) if data else None

    def mark_file_processing(self, chat_id: str, filename: str):
        with self._lock:
            job = self._jobs.get(chat_id)
            if not job:
                return
            for item in job["files"]:
                if item["filename"] == filename:
                    item["status"] = "processing"
                    item["message"] = "Parsing et indexation"
                    return

    def mark_file_done(
        self,
        chat_id: str,
        filename: str,
        pages_extracted: int,
        chunks_added: int,
        chunks_dropped: int,
    ):
        with self._lock:
            job = self._jobs.get(chat_id)
            if not job:
                return
            for item in job["files"]:
                if item["filename"] == filename:
                    item["status"] = "indexed"
                    item["pages_extracted"] = pages_extracted
                    item["chunks_added"] = chunks_added
                    item["chunks_dropped"] = chunks_dropped
                    item["message"] = "Indexation terminee"
                    break
            stats = job["stats"]
            stats["processed_files"] += 1
            stats["indexed_files"] += 1
            stats["total_pages"] += pages_extracted
            stats["chunks_added"] += chunks_added
            stats["chunks_dropped"] += chunks_dropped

    def mark_file_error(self, chat_id: str, filename: str, message: str):
        with self._lock:
            job = self._jobs.get(chat_id)
            if not job:
                return
            for item in job["files"]:
                if item["filename"] == filename:
                    item["status"] = "error"
                    item["message"] = message
                    break
            job["stats"]["processed_files"] += 1

    def finalize(self, chat_id: str):
        with self._lock:
            job = self._jobs.get(chat_id)
            if not job:
                return
            has_indexed = any(item["status"] == "indexed" for item in job["files"])
            if has_indexed:
                job["status"] = "ready"
                job["message"] = "Indexation terminee"
            else:
                job["status"] = "failed"
                job["message"] = "Aucun document n'a pu etre indexe"


upload_job_store = UploadJobStore()

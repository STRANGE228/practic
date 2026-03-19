from sqlalchemy.orm import Session
from app.models.task_image import TaskImage
from app.repositories.base import BaseRepository
from typing import List


class TaskImageRepository(BaseRepository[TaskImage]):
    def __init__(self, db: Session):
        super().__init__(db, TaskImage)

    def get_task_images(self, task_id):
        return self.db.query(TaskImage).filter(TaskImage.task_id == task_id).all()

    def create_image(self, filename, file_path, task_id, file_size = None):
        return self.create(
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            task_id=task_id
        )

    def delete_task_images(self, task_id):
        self.db.query(TaskImage).filter(TaskImage.task_id == task_id).delete()
        self.db.commit()
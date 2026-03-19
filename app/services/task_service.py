from app.repositories.task_repository import TaskRepository
from app.repositories.task_image_repository import TaskImageRepository
from typing import List, Optional
import os
import logging

logger = logging.getLogger(__name__)


class TaskService:
    def __init__(self, task_repo: TaskRepository, image_repo: TaskImageRepository = None):
        self.task_repo = task_repo
        self.image_repo = image_repo

    def create_task(self, title, description, column_id):
        if not title or not title.strip():
            raise ValueError("Название задачи не может быть пустым")

        if description is None:
            description = ""

        return self.task_repo.create_task(
            title=title.strip(),
            description=description.strip(),
            column_id=column_id
        )

    def get_task_with_images(self, task_id):
        return self.task_repo.get_with_images(task_id)

    def move_task(self, task_id, new_column_id, new_order):
        task = self.task_repo.get(task_id)
        if not task:
            raise ValueError(f"Задача с id {task_id} не найдена")

        if task.column_id == new_column_id and task.order == new_order:
            return task

        updated_task = self.task_repo.move_task(task_id, new_column_id, new_order)
        return updated_task

    def reorder_tasks(self, column_id, task_orders):
        self.task_repo.reorder_tasks(column_id, task_orders)

    def add_image_to_task(self, task_id, filename, file_path, file_size = None):
        if not self.image_repo:
            raise ValueError("Image repository not initialized")

        task = self.task_repo.get(task_id)
        if not task:
            raise ValueError(f"Задача с id {task_id} не найдена")

        return self.image_repo.create_image(filename, file_path, task_id, file_size)

    def delete_task_image(self, image_id):
        if not self.image_repo:
            raise ValueError("Image repository not initialized")

        image = self.image_repo.get(image_id)
        if not image:
            raise ValueError(f"Изображение с id {image_id} не найдено")

        try:
            if os.path.exists(image.file_path):
                os.remove(image.file_path)
        except Exception as e:
            logger.error(f"Failed to delete image file: {e}")

        self.image_repo.delete(image)

    def delete_task(self, task_id):
        task = self.task_repo.get_with_images(task_id)
        if not task:
            raise ValueError(f"Задача с id {task_id} не найдена")

        if self.image_repo and task.images:
            for image in task.images:
                try:
                    if os.path.exists(image.file_path):
                        os.remove(image.file_path)
                except Exception as e:
                    logger.error(f"Failed to delete image file: {e}")

        self.task_repo.delete(task)
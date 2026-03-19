from sqlalchemy.orm import Session
from app.models.column import Column
from app.repositories.base import BaseRepository
from typing import List, Optional


class ColumnRepository(BaseRepository[Column]):
    def __init__(self, db: Session):
        super().__init__(db, Column)

    def get_board_columns(self, board_id):
        return self.db.query(Column).filter(Column.board_id == board_id).order_by(Column.order).all()

    def create_column(self, name, board_id):
        max_order = self.db.query(Column).filter(Column.board_id == board_id).count()

        return self.create(
            name=name,
            order=max_order,
            board_id=board_id
        )

    def update_column(self, column_id, name):
        column = self.get(column_id)
        if column:
            column.name = name
            self.db.commit()
            self.db.refresh(column)
        return column

    def reorder_columns(self, board_id, column_orders):
        columns = self.db.query(Column).filter(Column.board_id == board_id).all()

        for column in columns:
            if column.id in column_orders:
                column.order = column_orders.index(column.id)

        self.db.commit()
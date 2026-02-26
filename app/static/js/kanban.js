let draggedTask = null;
let dragOverColumn = null;

document.addEventListener('DOMContentLoaded', function() {
    initializeDragAndDrop();
});

function initializeDragAndDrop() {
    const tasks = document.querySelectorAll('.task-card');
    const containers = document.querySelectorAll('.tasks-container');
    
    tasks.forEach(task => {
        task.addEventListener('dragstart', handleDragStart);
        task.addEventListener('dragend', handleDragEnd);
    });
    
    containers.forEach(container => {
        container.addEventListener('dragover', handleDragOver);
        container.addEventListener('dragleave', handleDragLeave);
        container.addEventListener('drop', handleDrop);
    });
}

function handleDragStart(e) {
    draggedTask = e.target.closest('.task-card');
    e.dataTransfer.setData('text/plain', draggedTask.id);
    e.dataTransfer.effectAllowed = 'move';
    draggedTask.classList.add('dragging');
}

function handleDragEnd(e) {
    if (draggedTask) {
        draggedTask.classList.remove('dragging');
        draggedTask = null;
    }
    
    if (dragOverColumn) {
        dragOverColumn.classList.remove('drag-over');
        dragOverColumn = null;
    }
}

function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    
    const container = e.target.closest('.tasks-container');
    if (container && container !== dragOverColumn) {
        if (dragOverColumn) {
            dragOverColumn.classList.remove('drag-over');
        }
        dragOverColumn = container;
        dragOverColumn.classList.add('drag-over');
    }
}

function handleDragLeave(e) {
    const container = e.target.closest('.tasks-container');
    if (container && container === dragOverColumn) {
        container.classList.remove('drag-over');
        dragOverColumn = null;
    }
}

async function handleDrop(e) {
    e.preventDefault();
    
    if (dragOverColumn) {
        dragOverColumn.classList.remove('drag-over');
    }
    
    const container = e.target.closest('.tasks-container');
    if (!container || !draggedTask) return;
    
    const targetColumn = container.closest('.column');
    const newStatus = targetColumn.dataset.status;
    const taskId = draggedTask.dataset.taskId;
    const boardId = document.querySelector('.kanban-board').dataset.boardId;
    
    // Получаем все задачи в целевой колонке для определения порядка
    const tasksInColumn = Array.from(container.querySelectorAll('.task-card:not(.dragging)'));
    let newOrder = tasksInColumn.length;
    
    // Определяем позицию, куда вставили задачу
    const mouseY = e.clientY;
    for (let i = 0; i < tasksInColumn.length; i++) {
        const task = tasksInColumn[i];
        const rect = task.getBoundingClientRect();
        const taskMiddle = rect.top + rect.height / 2;
        
        if (mouseY < taskMiddle) {
            newOrder = i;
            break;
        }
    }
    
    try {
        const response = await fetch(`/tasks/${taskId}/move`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                status: newStatus,
                order: newOrder
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Перемещаем задачу в DOM
            if (newOrder < tasksInColumn.length) {
                container.insertBefore(draggedTask, tasksInColumn[newOrder]);
            } else {
                container.appendChild(draggedTask);
            }
            
            // Обновляем счетчики
            updateTasksCounters();
            
            // Переупорядочиваем задачи в колонке
            reorderColumn(container, boardId, newStatus);
        } else {
            alert('Ошибка при перемещении задачи: ' + data.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Ошибка при перемещении задачи');
    }
}

async function reorderColumn(container, boardId, status) {
    const tasks = Array.from(container.querySelectorAll('.task-card'));
    const taskOrders = tasks.map(task => parseInt(task.dataset.taskId));
    
    try {
        await fetch(`/tasks/reorder`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                board_id: parseInt(boardId),
                status: status,
                task_orders: taskOrders
            })
        });
    } catch (error) {
        console.error('Error reordering tasks:', error);
    }
}

function updateTasksCounters() {
    document.querySelectorAll('.column').forEach(column => {
        const tasksCount = column.querySelectorAll('.task-card').length;
        const counter = column.querySelector('.task-count');
        if (counter) {
            counter.textContent = tasksCount;
        }
    });
}

// Добавляем стиль для drag-over
const style = document.createElement('style');
style.textContent = `
    .tasks-container.drag-over {
        background: rgba(52, 152, 219, 0.1);
        border: 2px dashed #3498db;
    }
`;
document.head.appendChild(style);
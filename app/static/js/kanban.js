let draggedTask = null;
let dragOverColumn = null;
let originalStatus = null;
let originalOrder = null;
let originalContainer = null;

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
    const taskId = draggedTask.dataset.taskId;

    // Сохраняем исходное состояние
    originalContainer = draggedTask.closest('.tasks-container');
    originalStatus = draggedTask.closest('.column').dataset.status;

    // Получаем исходный порядок
    const tasks = Array.from(originalContainer.querySelectorAll('.task-card'));
    originalOrder = tasks.indexOf(draggedTask);

    e.dataTransfer.setData('text/plain', taskId);
    e.dataTransfer.effectAllowed = 'move';
    draggedTask.classList.add('dragging');

    console.log(`Drag start: task ${taskId}, status ${originalStatus}, order ${originalOrder}`);
}

function handleDragEnd(e) {
    if (draggedTask) {
        draggedTask.classList.remove('dragging');
    }

    if (dragOverColumn) {
        dragOverColumn.classList.remove('drag-over');
    }

    // Сбрасываем переменные, но не сразу, чтобы handleDrop мог использовать их
    setTimeout(() => {
        draggedTask = null;
        dragOverColumn = null;
        originalContainer = null;
        originalStatus = null;
        originalOrder = null;
    }, 100);
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

    const targetContainer = e.target.closest('.tasks-container');
    if (!targetContainer || !draggedTask) {
        console.log('Drop cancelled: missing container or task');
        return;
    }

    const targetColumn = targetContainer.closest('.column');
    const newStatus = targetColumn.dataset.status;
    const taskId = draggedTask.dataset.taskId;
    const boardId = document.querySelector('.kanban-board').dataset.boardId;

    // Получаем все задачи в целевой колонке (кроме перетаскиваемой)
    const tasksInColumn = Array.from(targetContainer.querySelectorAll('.task-card:not(.dragging)'));
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

    console.log(`Drop: task ${taskId} from ${originalStatus}(${originalOrder}) to ${newStatus}(${newOrder})`);

    // Проверяем, действительно ли что-то изменилось
    if (newStatus === originalStatus && newOrder === originalOrder) {
        console.log('No changes, ignoring drop');
        return;
    }

    // Визуально перемещаем задачу сразу для лучшего UX
    if (newOrder < tasksInColumn.length) {
        targetContainer.insertBefore(draggedTask, tasksInColumn[newOrder]);
    } else {
        targetContainer.appendChild(draggedTask);
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
        console.log('Server response:', data);

        if (response.ok && data.success) {
            // Успешно - обновляем счетчики
            updateTasksCounters();

            // Если статус изменился, переупорядочиваем обе колонки
            if (newStatus !== originalStatus) {
                const originalContainer = document.querySelector(`.column[data-status="${originalStatus}"] .tasks-container`);
                if (originalContainer) {
                    await reorderColumn(originalContainer, boardId, originalStatus);
                }
            }

            // Переупорядочиваем целевую колонку
            await reorderColumn(targetContainer, boardId, newStatus);

            console.log('Task moved successfully');
        } else {
            // Ошибка - возвращаем задачу на место
            console.error('Server error:', data.error || 'Unknown error');
            revertTaskPosition();
            alert('Ошибка при перемещении задачи: ' + (data.error || 'Неизвестная ошибка'));
        }
    } catch (error) {
        console.error('Network error:', error);
        revertTaskPosition();
        alert('Ошибка сети при перемещении задачи');
    }
}

function revertTaskPosition() {
    if (draggedTask && originalContainer) {
        console.log('Reverting task to original position');

        // Возвращаем задачу на исходное место
        const tasksInOriginal = Array.from(originalContainer.querySelectorAll('.task-card:not(.dragging)'));

        if (originalOrder < tasksInOriginal.length) {
            originalContainer.insertBefore(draggedTask, tasksInOriginal[originalOrder]);
        } else {
            originalContainer.appendChild(draggedTask);
        }

        updateTasksCounters();
    }
}

async function reorderColumn(container, boardId, status) {
    const tasks = Array.from(container.querySelectorAll('.task-card'));
    const taskOrders = tasks.map(task => parseInt(task.dataset.taskId));

    try {
        const response = await fetch(`/tasks/reorder`, {
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

        if (!response.ok) {
            console.error('Failed to reorder column');
        }
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
        min-height: 100px;
    }
    
    .task-card.dragging {
        opacity: 0.5;
        transform: rotate(2deg);
        box-shadow: 0 5px 10px rgba(0,0,0,0.2);
    }
`;
document.head.appendChild(style);
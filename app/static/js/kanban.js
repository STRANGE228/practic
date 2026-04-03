let draggedTask = null;
let dragOverColumn = null;
let originalColumnId = null;
let originalOrder = null;
let originalContainer = null;
let dragStartY = 0;

// ========== WebSocket для real-time синхронизации ==========
let ws = null;
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;

function connectWebSocket() {
    const boardElement = document.querySelector('.kanban-board');
    if (!boardElement) return;

    const boardId = boardElement.dataset.boardId;
    // Получаем токен из cookie
    const cookies = document.cookie.split('; ');
    let token = '';
    for (let cookie of cookies) {
        if (cookie.startsWith('access_token=')) {
            token = cookie.split('=')[1].replace('Bearer ', '');
            break;
        }
    }

    if (!token || !boardId) {
        console.log('No token or boardId found');
        return;
    }

    const wsUrl = `ws://${window.location.host}/ws/${boardId}/${token}`;
    ws = new WebSocket(wsUrl);

    ws.onopen = function() {
        console.log('WebSocket connected');
        reconnectAttempts = 0;

        // Отправляем ping каждые 30 секунд
        setInterval(() => {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ type: 'ping' }));
            }
        }, 1000);
    };

    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        console.log('WebSocket message:', data);

        switch (data.type) {
            case 'task_updated':
                updateTaskInUI(data.task);
                break;
            case 'task_deleted':
                removeTaskFromUI(data.task_id);
                break;
            case 'column_updated':
                updateColumnInUI(data.column);
                break;
            case 'user_connected':
                showNotification(`Пользователь подключился`);
                break;
            case 'user_disconnected':
                showNotification(`Пользователь отключился`);
                break;
        }
    };

    ws.onclose = function() {
        console.log('WebSocket disconnected');
        if (reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++;
            setTimeout(connectWebSocket, 2000 * reconnectAttempts);
        }
    };

    ws.onerror = function(error) {
        console.error('WebSocket error:', error);
    };
}

function updateTaskInUI(taskData) {
    const taskElement = document.getElementById(`task-${taskData.id}`);
    if (taskElement) {
        // Обновляем содержимое задачи без перезагрузки
        const titleElement = taskElement.querySelector('h4');
        if (titleElement) titleElement.textContent = taskData.title;

        const descElement = taskElement.querySelector('.task-description');
        if (descElement && taskData.description) {
            descElement.textContent = taskData.description.length > 100 ?
                taskData.description.substring(0, 100) + '...' :
                taskData.description;
        }

        // Обновляем дату
        const dateElement = taskElement.querySelector('.task-date');
        if (dateElement && taskData.updated_at) {
            dateElement.textContent = new Date(taskData.updated_at).toLocaleString();
        }
    } else {
        location.reload();
    }
}

function removeTaskFromUI(taskId) {
    const taskElement = document.getElementById(`task-${taskId}`);
    if (taskElement) {
        taskElement.remove();
        updateTasksCounters();
    }
}

function updateColumnInUI(columnData) {
    const columnElement = document.querySelector(`.column[data-column-id="${columnData.id}"]`);
    if (columnElement) {
        const titleElement = columnElement.querySelector('.column-title h2');
        if (titleElement) {
            titleElement.textContent = columnData.name;
        }
    }
}

function showNotification(message) {
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: #2c3e50;
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        z-index: 9999;
        animation: slideIn 0.3s ease-out;
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Добавляем стили для уведомлений
const notificationStyle = document.createElement('style');
notificationStyle.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(notificationStyle);

// Подключаем WebSocket при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    connectWebSocket();
});

document.addEventListener('DOMContentLoaded', function() {
    initializeDragAndDrop();
});

function initializeDragAndDrop() {
    const tasks = document.querySelectorAll('.task-card');
    const containers = document.querySelectorAll('.tasks-container');

    tasks.forEach(task => {
        task.addEventListener('dragstart', handleDragStart);
        task.addEventListener('dragend', handleDragEnd);
        task.setAttribute('draggable', 'true');
    });

    containers.forEach(container => {
        container.addEventListener('dragover', handleDragOver);
        container.addEventListener('dragleave', handleDragLeave);
        container.addEventListener('drop', handleDrop);
    });

    console.log('Drag and drop initialized');
}

function handleDragStart(e) {
    draggedTask = e.target.closest('.task-card');
    if (!draggedTask) return;

    const taskId = draggedTask.dataset.taskId;
    dragStartY = e.clientY;

    // Сохраняем исходное состояние
    originalContainer = draggedTask.closest('.tasks-container');
    if (!originalContainer) return;

    originalColumnId = originalContainer.dataset.columnId;

    // Получаем исходный порядок
    const tasks = Array.from(originalContainer.querySelectorAll('.task-card'));
    originalOrder = tasks.indexOf(draggedTask);

    e.dataTransfer.setData('text/plain', taskId);
    e.dataTransfer.effectAllowed = 'move';
    draggedTask.classList.add('dragging');

    console.log(`Drag start: task ${taskId}, column ${originalColumnId}, order ${originalOrder}`);
}

function handleDragEnd(e) {
    if (draggedTask) {
        draggedTask.classList.remove('dragging');
    }

    if (dragOverColumn) {
        dragOverColumn.classList.remove('drag-over');
    }

    // Удаляем все индикаторы
    removeDropIndicators();

    // Сбрасываем переменные
    setTimeout(() => {
        draggedTask = null;
        dragOverColumn = null;
        originalContainer = null;
        originalColumnId = null;
        originalOrder = null;
    }, 100);
}

function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';

    const container = e.target.closest('.tasks-container');
    if (container) {
        // Подсвечиваем весь контейнер
        if (dragOverColumn && dragOverColumn !== container) {
            dragOverColumn.classList.remove('drag-over');
        }

        container.classList.add('drag-over');
        dragOverColumn = container;

        // Показываем индикатор позиции
        showDropPositionIndicator(e, container);
    }
}

function showDropPositionIndicator(e, container) {
    // Удаляем старые индикаторы
    removeDropIndicators();

    const tasks = Array.from(container.querySelectorAll('.task-card:not(.dragging)'));
    const mouseY = e.clientY;

    // Создаем индикатор
    const indicator = document.createElement('div');
    indicator.className = 'drop-position-indicator';

    if (tasks.length === 0) {
        // Если в колонке нет задач, индикатор вверху
        container.insertBefore(indicator, container.firstChild);
        return;
    }

    // Определяем позицию для вставки
    for (let i = 0; i < tasks.length; i++) {
        const task = tasks[i];
        const rect = task.getBoundingClientRect();
        const taskMiddle = rect.top + rect.height / 2;

        if (mouseY < taskMiddle) {
            container.insertBefore(indicator, task);
            return;
        }
    }

    // Вставляем в конец
    container.appendChild(indicator);
}

function removeDropIndicators() {
    document.querySelectorAll('.drop-position-indicator').forEach(el => el.remove());
}

function handleDragLeave(e) {
    const container = e.target.closest('.tasks-container');
    if (container) {
        container.classList.remove('drag-over');
        removeDropIndicators();
    }
}

async function handleDrop(e) {
    e.preventDefault();

    removeDropIndicators();

    if (dragOverColumn) {
        dragOverColumn.classList.remove('drag-over');
    }

    const targetContainer = e.target.closest('.tasks-container');
    if (!targetContainer || !draggedTask) {
        console.log('Drop cancelled: missing container or task');
        return;
    }

    const targetColumnId = targetContainer.dataset.columnId;
    const taskId = draggedTask.dataset.taskId;
    const boardId = document.querySelector('.kanban-board').dataset.boardId;

    if (!targetColumnId || !boardId) {
        console.error('Missing column or board ID');
        return;
    }

    // Получаем все задачи в целевой колонке
    const tasksInColumn = Array.from(targetContainer.querySelectorAll('.task-card:not(.dragging)'));
    let newOrder = tasksInColumn.length;

    // Определяем позицию для вставки
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

    console.log(`Drop: task ${taskId} from column ${originalColumnId}(${originalOrder}) to column ${targetColumnId}(${newOrder})`);

    // Проверяем, действительно ли что-то изменилось
    if (originalColumnId === targetColumnId && originalOrder === newOrder) {
        console.log('No changes, ignoring drop');
        return;
    }

    // Визуально перемещаем задачу
    try {
        // Удаляем задачу из исходного контейнера
        draggedTask.remove();

        // Вставляем в новое место
        if (newOrder < tasksInColumn.length) {
            targetContainer.insertBefore(draggedTask, tasksInColumn[newOrder]);
        } else {
            targetContainer.appendChild(draggedTask);
        }

        // Отправляем запрос на сервер
        const response = await fetch(`/tasks/${taskId}/move`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                column_id: parseInt(targetColumnId),
                order: newOrder
            })
        });

        const data = await response.json();
        console.log('Server response:', data);

        if (response.ok && data.success) {
            // Успешно - обновляем счетчики
            updateTasksCounters();

            // Если колонка изменилась, переупорядочиваем исходную колонку
            if (originalColumnId !== targetColumnId) {
                const originalContainer = document.querySelector(`.tasks-container[data-column-id="${originalColumnId}"]`);
                if (originalContainer) {
                    await reorderColumn(originalContainer, boardId, originalColumnId);
                }
            }

            // Переупорядочиваем целевую колонку
            await reorderColumn(targetContainer, boardId, targetColumnId);

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

        const tasksInOriginal = Array.from(originalContainer.querySelectorAll('.task-card:not(.dragging)'));

        if (originalOrder < tasksInOriginal.length) {
            originalContainer.insertBefore(draggedTask, tasksInOriginal[originalOrder]);
        } else {
            originalContainer.appendChild(draggedTask);
        }

        updateTasksCounters();
    }
}

async function reorderColumn(container, boardId, columnId) {
    const tasks = Array.from(container.querySelectorAll('.task-card'));
    const taskOrders = tasks.map(task => parseInt(task.dataset.taskId));

    if (taskOrders.length === 0) return;

    try {
        const response = await fetch(`/tasks/reorder`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                column_id: parseInt(columnId),
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

// Добавляем стили
const style = document.createElement('style');
style.textContent = `
    .tasks-container.drag-over {
        background: rgba(52, 152, 219, 0.15);
        border: 3px dashed #3498db;
        min-height: 100px;
        border-radius: 4px;
        box-shadow: inset 0 0 10px rgba(52, 152, 219, 0.2);
    }
    
    .task-card.dragging {
        opacity: 0.5;
        transform: rotate(2deg) scale(0.98);
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        cursor: grabbing;
    }
    
    .task-card {
        cursor: grab;
        transition: transform 0.2s, box-shadow 0.2s;
        user-select: none;
    }
    
    .task-card:active {
        cursor: grabbing;
    }
    
    .drop-position-indicator {
        height: 4px;
        background: linear-gradient(90deg, #3498db, #9b59b6);
        margin: 5px 0;
        border-radius: 2px;
        animation: pulse 1.5s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 0.5; }
        50% { opacity: 1; }
    }
`;
document.head.appendChild(style);
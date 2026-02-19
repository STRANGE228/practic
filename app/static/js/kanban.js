// Drag & Drop
document.addEventListener('DOMContentLoaded', function() {
    initializeDragAndDrop();
});

function initializeDragAndDrop() {
    const tasks = document.querySelectorAll('.task-card');
    const containers = document.querySelectorAll('.tasks-container');

    // Добавляем обработчики для задач
    tasks.forEach(task => {
        task.addEventListener('dragstart', handleDragStart);
        task.addEventListener('dragend', handleDragEnd);
    });

    // Добавляем обработчики для контейнеров
    containers.forEach(container => {
        container.addEventListener('dragover', handleDragOver);
        container.addEventListener('drop', handleDrop);
    });
}

function handleDragStart(e) {
    e.dataTransfer.setData('text/plain', e.target.id);
    e.dataTransfer.effectAllowed = 'move';
    e.target.classList.add('dragging');
}

function handleDragEnd(e) {
    e.target.classList.remove('dragging');
}

function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
}

function handleDrop(e) {
    e.preventDefault();

    const taskId = e.dataTransfer.getData('text/plain');
    const task = document.getElementById(taskId);
    const targetContainer = e.target.closest('.tasks-container');
    const targetColumn = targetContainer.closest('.column');

    if (!task || !targetContainer || !targetColumn) return;

    const newStatus = targetColumn.dataset.status;

    // Отправляем запрос на сервер
    fetch(`/tasks/${taskId.split('-')[1]}/move`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Перемещаем задачу в новый контейнер
            targetContainer.appendChild(task);
            updateTasksCounters();
        } else {
            alert('Ошибка при перемещении задачи: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Ошибка при перемещении задачи');
    });
}

function updateTasksCounters() {
    document.querySelectorAll('.column').forEach(column => {
        const status = column.dataset.status;
        const tasksCount = column.querySelectorAll('.task-card').length;
        const counter = column.querySelector('.task-count');
        if (counter) {
            counter.textContent = tasksCount;
        }
    });
}
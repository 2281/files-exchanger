// Основная логика интерфейса файлового обменника

document.addEventListener('DOMContentLoaded', function() {
    loadFiles();
});

function loadFiles() {
    fetch('/api/files')
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById('files-table-body');
            tableBody.innerHTML = '';
            
            if (data.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="5" class="text-center">Файлы отсутствуют</td></tr>';
                return;
            }
            
            data.forEach(file => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${escapeHtml(file.name)}</td>
                    <td>${file.type}</td>
                    <td>${formatFileSize(file.size)}</td>
                    <td>${formatDate(file.created_at)}</td>
                    <td>
                        <a href="/api/download/${file.id}" class="btn btn-sm btn-primary">
                            <i class="fas fa-download"></i> Скачать
                        </a>
                        <button onclick="createLink('${file.id}')" class="btn btn-sm btn-info">
                            <i class="fas fa-link"></i> Ссылка
                        </button>
                        <button onclick="deleteFile('${file.id}')" class="btn btn-sm btn-danger">
                            <i class="fas fa-trash"></i> Удалить
                        </button>
                    </td>
                `;
                tableBody.appendChild(row);
            });
        })
        .catch(error => {
            console.error('Ошибка загрузки файлов:', error);
            alert('Ошибка загрузки списка файлов');
        });
}

function createLink(fileId) {
    fetch(`/api/links/${fileId}`, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            alert(`Прямая ссылка:\n${data.url}`);
        })
        .catch(error => {
            console.error('Ошибка создания ссылки:', error);
            alert('Ошибка создания прямой ссылки');
        });
}

function deleteFile(fileId) {
    if (confirm('Вы уверены, что хотите удалить этот файл?')) {
        fetch(`/api/files/${fileId}`, { method: 'DELETE' })
            .then(response => {
                if (response.ok) {
                    loadFiles(); // Обновляем список файлов
                } else {
                    alert('Ошибка удаления файла');
                }
            })
            .catch(error => {
                console.error('Ошибка удаления:', error);
                alert('Ошибка удаления файла');
            });
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDate(dateString) {
    const options = {year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit'};
    return new Date(dateString).toLocaleDateString('ru-RU', options);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
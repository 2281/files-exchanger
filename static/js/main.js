// ID открытой папки (null — корень)
const currentFolderId = new URLSearchParams(window.location.search).get('folder_id');

// Запрос к API: при 401 — переход на страницу входа, при ошибке — Error с текстом из ответа
async function api(url, options = {}) {
    if (options.json !== undefined) {
        options = {
            ...options,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(options.json)
        };
    }
    const response = await fetch(url, options);
    if (response.status === 401) {
        window.location.href = '/login';
        throw new Error('Требуется вход');
    }
    const data = await response.json().catch(() => null);
    if (!response.ok) {
        const detail = data && typeof data.detail === 'string' ? data.detail : response.statusText;
        throw new Error(detail);
    }
    return data;
}

// Выполнить действие и показать ошибку, если оно не удалось
async function run(errorPrefix, action) {
    try {
        return await action();
    } catch (error) {
        console.error(`${errorPrefix}:`, error);
        alert(`${errorPrefix}: ${error.message}`);
    }
}

// Загрузка списка файлов текущей папки
async function loadFiles() {
    const tableBody = document.getElementById('files-list');
    let data;
    try {
        data = await api(currentFolderId ? `/api/files/folder/${encodeURIComponent(currentFolderId)}/list` : '/api/files');
    } catch (error) {
        console.error('Ошибка загрузки файлов:', error);
        tableBody.innerHTML = `<tr><td colspan="6" class="text-center">Ошибка: ${escapeHtml(error.message)}</td></tr>`;
        document.getElementById('owner-actions').classList.add('d-none');
        return;
    }

    if (data.folder) {
        document.getElementById('page-title').textContent = `Папка: ${data.folder.name}`;
        document.getElementById('back-to-root').classList.remove('d-none');
        if (data.up_id) {
            const up = document.getElementById('back-to-parent');
            up.href = `/?folder_id=${encodeURIComponent(data.up_id)}`;
            up.classList.remove('d-none');
        }
        // Загружать и создавать можно только в своих папках
        document.getElementById('owner-actions').classList.toggle('d-none', !data.folder.is_owner);
    }

    if (data.files.length === 0) {
        const emptyText = currentFolderId ? 'Данная папка пуста' : 'Файлы отсутствуют';
        tableBody.innerHTML = `<tr><td colspan="6" class="text-center">${emptyText}</td></tr>`;
        return;
    }

    tableBody.innerHTML = data.files.map(renderRow).join('');
}

// Строка таблицы для файла или папки
function renderRow(file) {
    const id = escapeHtml(file.id);
    const name = escapeHtml(file.name);
    const isFolder = file.type === 'folder';
    const icon = isFolder ? 'fa-folder text-warning' : 'fa-file text-secondary';
    const access = file.is_public
        ? '<span class="badge bg-success">Видна всем</span>'
        : '<span class="badge bg-secondary">Только владелец</span>';

    return `
        <tr>
            <td>
                <i class="fas ${icon}"></i>
                ${isFolder ? `<a href="/?folder_id=${id}">${name}</a>` : name}
            </td>
            <td>${isFolder ? '—' : formatFileSize(file.size)}</td>
            <td>${file.is_owner ? 'Я' : escapeHtml(file.owner_email)}</td>
            <td>${access}</td>
            <td>${formatDate(file.created_at)}</td>
            <td class="text-nowrap">
                <a href="/api/files/download/${id}" class="btn btn-sm btn-primary" title="Скачать">
                    <i class="fas fa-download"></i>
                </a>
                <button onclick="showCreateLink(this.dataset)" data-id="${id}" data-name="${name}" class="btn btn-sm btn-info" title="Временная ссылка">
                    <i class="fas fa-link"></i>
                </button>
                ${file.is_owner ? `
                    <button onclick="setPublic(this.dataset.id, ${!file.is_public})" data-id="${id}" class="btn btn-sm btn-outline-success"
                            title="${file.is_public ? 'Сделать видимой только мне' : 'Сделать видимой всем'}">
                        <i class="fas ${file.is_public ? 'fa-eye-slash' : 'fa-eye'}"></i>
                    </button>
                    <button onclick="deleteFile(this.dataset.id)" data-id="${id}" class="btn btn-sm btn-danger" title="Удалить">
                        <i class="fas fa-trash"></i>
                    </button>` : ''}
            </td>
        </tr>
    `;
}

// Пометить файл или папку как «видна всем» / только владельцу
function setPublic(fileId, isPublic) {
    run('Ошибка изменения доступа', async () => {
        await api(`/api/files/${encodeURIComponent(fileId)}`, { method: 'PATCH', json: { is_public: isPublic } });
        loadFiles();
    });
}

// Удаление файла или папки
function deleteFile(fileId) {
    if (!confirm('Вы уверены, что хотите удалить этот файл/папку?')) {
        return;
    }
    run('Ошибка удаления', async () => {
        await api(`/api/files/${encodeURIComponent(fileId)}`, { method: 'DELETE' });
        loadFiles();
    });
}

// Окно создания временной ссылки (данные берутся из data-атрибутов кнопки)
function showCreateLink({ id, name }) {
    document.getElementById('linkFileId').value = id;
    document.getElementById('linkFileName').textContent = name;
    document.getElementById('linkResult').classList.add('d-none');
    showModal('createLinkModal');
}

function copyLink() {
    const input = document.getElementById('linkUrl');
    // navigator.clipboard доступен только по HTTPS или на localhost
    if (navigator.clipboard) {
        navigator.clipboard.writeText(input.value);
    } else {
        input.select();
        document.execCommand('copy');
    }
}

// Список своих ссылок
async function showLinks() {
    const tableBody = document.getElementById('links-list');
    const links = await run('Ошибка загрузки ссылок', () => api('/api/links'));
    if (!links) {
        return;
    }
    tableBody.innerHTML = links.length === 0
        ? '<tr><td colspan="4" class="text-center">Действующих ссылок нет</td></tr>'
        : links.map(link => `
            <tr>
                <td>
                    <i class="fas ${link.file_type === 'folder' ? 'fa-folder text-warning' : 'fa-file text-secondary'}"></i>
                    ${escapeHtml(link.file_name)}
                </td>
                <td>${formatDateTime(link.created_at)}</td>
                <td>${formatDateTime(link.expires_at)}</td>
                <td class="text-end">
                    <button onclick="revokeLink(this.dataset.id)" data-id="${escapeHtml(link.id)}" class="btn btn-sm btn-outline-danger">
                        Отозвать
                    </button>
                </td>
            </tr>
        `).join('');
    showModal('linksModal');
}

function revokeLink(linkId) {
    if (!confirm('Отозвать ссылку? Скачать по ней будет больше нельзя.')) {
        return;
    }
    run('Ошибка отзыва ссылки', async () => {
        await api(`/api/links/${encodeURIComponent(linkId)}`, { method: 'DELETE' });
        showLinks();
    });
}

async function logout() {
    await fetch('/api/auth/logout', { method: 'POST' });
    window.location.href = '/login';
}

function showModal(modalId) {
    bootstrap.Modal.getOrCreateInstance(document.getElementById(modalId)).show();
}

function hideModal(modalId) {
    bootstrap.Modal.getInstance(document.getElementById(modalId))?.hide();
}

// Вспомогательные функции
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('ru-RU');
}

function formatDateTime(dateString) {
    return new Date(dateString).toLocaleString('ru-RU', { dateStyle: 'short', timeStyle: 'short' });
}

document.addEventListener('DOMContentLoaded', function() {
    // Загрузка файла в текущую папку
    document.getElementById('uploadForm').addEventListener('submit', function(e) {
        e.preventDefault();

        const fileInput = document.getElementById('file');
        if (!fileInput.files[0]) {
            alert('Пожалуйста, выберите файл');
            return;
        }

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        const url = currentFolderId
            ? `/api/files/folder/${encodeURIComponent(currentFolderId)}/upload`
            : '/api/files/upload';

        run('Ошибка загрузки файла', async () => {
            await api(url, { method: 'POST', body: formData });
            fileInput.value = '';
            hideModal('uploadModal');
            loadFiles();
        });
    });

    // Создание папки в текущей папке
    document.getElementById('createFolderForm').addEventListener('submit', function(e) {
        e.preventDefault();

        const folderNameInput = document.getElementById('folderName');
        const folderName = folderNameInput.value.trim();
        if (!folderName) {
            alert('Пожалуйста, введите название папки');
            return;
        }

        run('Ошибка создания папки', async () => {
            await api('/api/files/folder', { method: 'POST', json: { name: folderName, parent_id: currentFolderId } });
            folderNameInput.value = '';
            hideModal('createFolderModal');
            loadFiles();
        });
    });

    // Создание временной ссылки
    document.getElementById('createLinkForm').addEventListener('submit', function(e) {
        e.preventDefault();

        const fileId = document.getElementById('linkFileId').value;
        const hours = parseInt(document.getElementById('linkExpires').value, 10);

        run('Ошибка создания ссылки', async () => {
            const data = await api(`/api/links/${encodeURIComponent(fileId)}`, {
                method: 'POST',
                json: { expires_in_hours: hours }
            });
            document.getElementById('linkUrl').value = data.url;
            document.getElementById('linkExpiresAt').textContent = formatDateTime(data.link.expires_at);
            document.getElementById('linkResult').classList.remove('d-none');
            document.getElementById('linkUrl').select();
        });
    });

    loadFiles();
});
